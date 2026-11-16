#!/usr/bin/env python3
"""Turn an explicitly public, owner-authored GitHub issue into a stream record.

No GitHub writes happen here. Untrusted text is data, never a shell command.
Image downloads accept only GitHub attachment hosts and are re-encoded without
metadata before they enter the canonical repository.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import warnings

OWNER = "annimch04"
REPOSITORY = "annimch04/public-writing"
ACK = "Publish this post publicly on Fieldlight."
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGES = 8
MAX_PIXELS = 80_000_000
MAX_BODY = 10_000
FORM = re.compile(
    r"\A### Post\n\n(?P<body>.*?)\n\n"
    r"### Title \(optional\)\n\n(?P<title>.*?)\n\n"
    r"### Publication\n\n- \[[xX]\] " + re.escape(ACK) + r"\s*\Z",
    re.DOTALL,
)
MARKDOWN_IMAGE = re.compile(
    r'!\[(?P<alt>(?:\\.|[^\]\\])*)\]\(\s*<?(?P<url>https?://[^\s<>\)]+)>?'
    r'(?:\s+["\'][^"\']*["\'])?\s*\)', re.IGNORECASE,
)
HTML_IMAGE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
PHOTO_FILE_LINK = re.compile(
    r'\[(?P<file_alt>[^\]\n]+)\]\((?P<file_url>https://github\.com/user-attachments/files/'
    r'[0-9]+/[A-Za-z0-9._-]+\.(?:heic|heif|jpe?g|png|webp|gif))\)', re.IGNORECASE,
)


class PostError(ValueError):
    """An actionable validation failure safe to show to the owner."""


def normalized_timestamp(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("timezone required")
        return stamp.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except (AttributeError, TypeError, ValueError) as exc:
        raise PostError("The issue has an invalid timestamp.") from exc


def validate_issue(issue: dict, *, actor: str, repository: str) -> tuple[str, str, str]:
    if actor != OWNER or repository != REPOSITORY:
        raise PostError("Only annimch04 in annimch04/public-writing may publish.")
    if not isinstance(issue, dict) or issue.get("user", {}).get("login") != OWNER:
        raise PostError("The issue must have been written by annimch04.")
    if "editor" not in issue or "last_edited_at" not in issue:
        raise PostError("The current issue editor could not be verified; retry from the publishing workflow.")
    if issue["last_edited_at"] and (issue.get("editor") or {}).get("login") != OWNER:
        raise PostError("The current post text must have been edited by annimch04. Edit and save it yourself to publish.")
    number = issue.get("number")
    if type(number) is not int or number < 1 or issue.get("pull_request") is not None:
        raise PostError("A normal GitHub issue number is required.")
    if issue.get("html_url") != f"https://github.com/{REPOSITORY}/issues/{number}":
        raise PostError("The issue does not belong to the canonical repository.")
    if not isinstance(issue.get("title"), str) or not issue["title"].startswith("[Post] "):
        raise PostError("Keep the issue title beginning with [Post].")
    body = issue.get("body")
    if not isinstance(body, str) or len(body) > MAX_BODY + 1000:
        raise PostError("Use the New stream post form; keep the post under 10,000 characters.")
    body = body.replace("\r\n", "\n")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", body):
        raise PostError("Remove control characters from the post.")
    match = FORM.fullmatch(body)
    if not match:
        raise PostError("Use the New stream post form, keep its section headings, and check the public-publication box.")
    title = match["title"].strip()
    if title == "_No response_":
        title = ""
    if "\n" in title or len(title) > 180:
        raise PostError("The optional title must be one line, at most 180 characters.")
    post = match["body"].strip()
    if post == "_No response_" or not post or len(post) > MAX_BODY:
        raise PostError("Add text or a photo; keep the post under 10,000 characters.")
    normalized_timestamp(issue.get("created_at"))
    normalized_timestamp(issue.get("updated_at"))
    digest = hashlib.sha256(json.dumps({"title": title, "body": post}, ensure_ascii=False,
                                       sort_keys=True).encode("utf-8")).hexdigest()
    return title, post, digest


def validate_image_url(url: str, *, redirect: bool = False) -> str:
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.port
                or parsed.fragment or "\\" in url or re.search(r"[\x00-\x20\x7f]", url)):
            raise ValueError("invalid URL")
        host, path = parsed.hostname, parsed.path
        valid = (
            host == "github.com" and re.fullmatch(r"/user-attachments/assets/[a-fA-F0-9-]{36}", path)
        ) or (
            host == "github.com" and re.fullmatch(
                r"/user-attachments/files/[0-9]+/[A-Za-z0-9._-]+\.(?:heic|heif|jpe?g|png|webp|gif)", path, re.IGNORECASE)
        ) or (
            host == "user-images.githubusercontent.com"
            and re.fullmatch(r"/\d+/[A-Za-z0-9._-]+", path)
        )
        if redirect:
            valid = valid or (
                host == "private-user-images.githubusercontent.com"
                and re.fullmatch(r"/\d+/\d+/[A-Za-z0-9._-]+", path)
            ) or (
                host == "objects.githubusercontent.com"
                and path.startswith(("/github-production-user-asset-", "/github-production-repository-file-"))
            ) or host in {
                "github-production-user-asset-6210df.s3.amazonaws.com",
                "github-production-user-asset-6210df.s3.us-east-1.amazonaws.com",
                "github-production-repository-file-5c1aeb.s3.amazonaws.com",
                "github-production-repository-file-5c1aeb.s3.us-east-1.amazonaws.com",
            }
        if not valid or "%" in path or "/../" in path:
            raise ValueError("unapproved attachment location")
    except ValueError as exc:
        raise PostError("Attach photos to this GitHub issue. External image URLs are not downloaded.") from exc
    return url


class SafeImageRedirect(HTTPRedirectHandler):
    max_redirections = 4
    max_repeats = 1

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_image_url(newurl, redirect=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_image(url: str) -> bytes:
    validate_image_url(url)
    deadline = time.monotonic() + 45
    request = Request(url, headers={"User-Agent": "Fieldlight-stream-publisher/1.0"})
    try:
        with build_opener(SafeImageRedirect()).open(request, timeout=12) as response:
            validate_image_url(response.url, redirect=True)
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_IMAGE_BYTES:
                raise PostError("Each photo must be 15 MB or smaller.")
            chunks, size = [], 0
            while True:
                if time.monotonic() > deadline:
                    raise PostError("Photo download timed out; try again by editing the issue.")
                chunk = response.read(min(64 * 1024, MAX_IMAGE_BYTES + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > MAX_IMAGE_BYTES:
                    raise PostError("Each photo must be 15 MB or smaller.")
            return b"".join(chunks)
    except PostError:
        raise
    except Exception as exc:
        # Do not echo signed URLs or remote response content into a public issue.
        raise PostError("Could not download a GitHub photo. Reattach it and edit the issue to retry.") from exc


def clean_image(data: bytes) -> tuple[bytes, str]:
    from PIL import Image, ImageOps, UnidentifiedImageError
    from pillow_heif import register_heif_opener
    register_heif_opener()
    if len(data) > MAX_IMAGE_BYTES:
        raise PostError("Each photo must be 15 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as original:
                if original.format not in {"JPEG", "PNG", "WEBP", "GIF", "HEIF"}:
                    raise PostError("Use a JPEG, PNG, WebP, HEIC/HEIF, or still GIF photo.")
                if getattr(original, "n_frames", 1) > 1:
                    raise PostError("Animated images are not supported. Attach a still photo.")
                if original.width * original.height > MAX_PIXELS:
                    raise PostError("Photos must be at most 80 megapixels; resize this photo first.")
                oriented = ImageOps.exif_transpose(original)
                oriented.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
                has_alpha = oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info
                pixels = oriented.convert("RGBA" if has_alpha else "RGB")
                # A new image contains pixel data only: no EXIF, GPS, ICC, XMP, or comments.
                clean = Image.new(pixels.mode, pixels.size)
                clean.paste(pixels)
                output = io.BytesIO()
                extension = "png" if has_alpha or original.format not in {"JPEG", "HEIF"} else "jpg"
                clean.save(output, format="PNG" if extension == "png" else "JPEG", **(
                    {"optimize": True} if extension == "png" else {"quality": 92, "optimize": True}
                ))
                result = output.getvalue()
                if len(result) > MAX_IMAGE_BYTES:
                    raise PostError("The cleaned photo is too large; resize it before attaching.")
                return result, extension
    except PostError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise PostError("This attachment is not a supported, readable photo.") from exc


class ImageTag(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs = {}

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.attrs = dict(attrs)


def extract_images(body: str) -> tuple[str, list[dict]]:
    images = []
    combined = re.compile(MARKDOWN_IMAGE.pattern + "|" + HTML_IMAGE.pattern + "|" + PHOTO_FILE_LINK.pattern,
                          re.IGNORECASE)

    def replace(match):
        if match.group().lower().startswith("<img"):
            parser = ImageTag()
            parser.feed(match.group())
            url, alt = parser.attrs.get("src"), parser.attrs.get("alt", "")
            if not isinstance(url, str):
                raise PostError("A photo is missing its attachment URL.")
        elif match["file_url"]:
            url, alt = match["file_url"], match["file_alt"]
        else:
            url, alt = match["url"], re.sub(r"\\(.)", r"\1", match["alt"])
        validate_image_url(url)
        alt = str(alt or "").strip()[:500]
        if not alt:
            raise PostError("Add a short photo description between ![ and ] in each photo's image text (or its alt attribute).")
        images.append({"url": url, "alt": alt})
        if len(images) > MAX_IMAGES:
            raise PostError("Use at most eight photos per post.")
        return ""

    cleaned = combined.sub(replace, body)
    if re.search(r"!\[|<img\b", cleaned, re.IGNORECASE):
        raise PostError("Use GitHub's attached-photo Markdown or image tag; reference-style images are not supported.")
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip(), images


def publish_issue(issue: dict, root: Path, *, actor: str, repository: str,
                  fetch_image=download_image, dry_run: bool = False) -> dict:
    title, body, digest = validate_issue(issue, actor=actor, repository=repository)
    post_id = f"post-{issue['number']}"
    destination = root / "stream" / "posts" / f"{post_id}.json"
    prior = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else None
    if prior and prior.get("content_hash") == digest:
        return {"id": post_id, "changed": False, "record": prior}
    body, image_inputs = extract_images(body)
    media, files = [], []
    for attachment in image_inputs:
        content, extension = clean_image(fetch_image(attachment["url"]))
        name = hashlib.sha256(content).hexdigest()[:24] + "." + extension
        path = f"stream/media/{post_id}/{name}"
        media.append({"path": path, "alt": attachment["alt"]})
        files.append((path, content))
    if not body and not media:
        raise PostError("Add text or at least one photo.")
    record = {
        "id": post_id,
        "published_at": prior["published_at"] if prior else normalized_timestamp(issue["created_at"]),
        "updated_at": normalized_timestamp(issue["updated_at"]),
        "body": body,
        "images": media,
        "source_url": f"https://github.com/{REPOSITORY}/blob/main/stream/posts/{post_id}.json",
        "issue_url": issue["html_url"],
        "content_hash": digest,
    }
    if title:
        record["title"] = title
    if not dry_run:
        # Complete validation and downloads precede writes, so a failed attachment
        # cannot leave a partially updated post. Git adds the whole result together.
        for relative, content in files:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         prefix=".post-", delete=False) as pending:
            json.dump(record, pending, ensure_ascii=False, indent=2)
            pending.write("\n")
        os.replace(pending.name, destination)
    return {"id": post_id, "changed": True, "record": record}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-json", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path("."))
    parser.add_argument("--actor", required=True)
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        issue = json.loads(args.issue_json.read_text(encoding="utf-8"))
        result = publish_issue(issue, args.source, actor=args.actor,
                               repository=args.repository, dry_run=args.dry_run)
        print(json.dumps({"id": result["id"], "changed": result["changed"], "dry_run": args.dry_run}))
    except (PostError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Post not published: {exc}\n")


if __name__ == "__main__":
    main()
