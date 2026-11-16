#!/usr/bin/env python3
"""Narrow orchestration for the trusted main-branch stream publishing workflow."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from publish_stream import OWNER, REPOSITORY, PostError, publish_issue

SITE_BASE = "https://fieldlight.com"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PostError("Unexpected GitHub API redirect; publishing stopped.")


def api(path, *, data=None, method=None):
    if not path.startswith(f"/repos/{REPOSITORY}/") and path != "/graphql":
        raise PostError("Unexpected GitHub API destination.")
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        raise PostError("The workflow GitHub token is missing.")
    request = Request("https://api.github.com" + path, method=method,
                      data=None if data is None else json.dumps(data).encode(), headers={
                          "Authorization": "Bearer " + token,
                          "Accept": "application/vnd.github+json",
                          "X-GitHub-Api-Version": "2022-11-28",
                          "Content-Type": "application/json",
                          "User-Agent": "Fieldlight-stream-publisher/1.0",
                      })
    with build_opener(NoRedirect()).open(request, timeout=30) as response:
        return json.load(response)


def current_issue(number: int) -> dict:
    """Read text and its editor in one snapshot, not separate race-prone calls."""
    query = """query($number: Int!) {
      repository(owner: "annimch04", name: "public-writing") {
        issue(number: $number) {
          number title body createdAt updatedAt url lastEditedAt
          author { login }
          editor { login }
        }
      }
    }"""
    response = api("/graphql", data={"query": query, "variables": {"number": number}})
    if response.get("errors"):
        raise PostError("GitHub could not verify the current issue editor; retry this workflow.")
    value = (response.get("data", {}).get("repository") or {}).get("issue")
    if not value:
        raise PostError("The requested issue was not found in the canonical repository.")
    return {"number": value["number"], "title": value["title"], "body": value["body"],
            "created_at": value["createdAt"], "updated_at": value["updatedAt"],
            "html_url": value["url"], "user": value["author"] or {},
            "editor": value["editor"], "last_edited_at": value["lastEditedAt"]}


def save_report(path: Path, report: dict):
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def trusted_context():
    if (os.environ.get("GITHUB_ACTOR") != OWNER or os.environ.get("GITHUB_TRIGGERING_ACTOR") != OWNER
            or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY):
        raise PostError("Publishing is restricted to annimch04 in the canonical repository.")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise PostError("Run this workflow from main only.")


def prepare(args):
    trusted_context()
    requested = os.environ.get("REQUESTED_ISSUE", "")
    dry_run = os.environ.get("DRY_RUN", "false") == "true"
    if requested and not re.fullmatch(r"[1-9][0-9]{0,8}", requested):
        raise PostError("Issue number must be a positive number.")
    if not requested and not dry_run:
        raise PostError("Choose an existing post issue, or enable dry run.")
    report = {"dry_run": dry_run, "requested_issue": int(requested) if requested else None,
              "posts": [], "errors": [], "stage": "preparing"}
    save_report(args.report, report)
    # An empty dry run validates existing real data, fixtures, and deployment access.
    # A requested dry run changes only this temporary checkout, never either remote.
    if not requested:
        report["stage"] = "prepared"
        save_report(args.report, report)
        return
    selected = current_issue(int(requested))
    if selected.get("user", {}).get("login") != OWNER:
        raise PostError("The requested issue must have been written by annimch04.")
    candidates = {int(requested): selected}
    if not dry_run:
        # GitHub keeps at most one pending run per concurrency group. Reconcile all
        # posts, including closed ones, so replacing a pending run cannot drop a
        # rapid submission or an edit to a closed post. Closing is not withdrawal.
        for page in range(1, 101):
            batch = api(f"/repos/{REPOSITORY}/issues?creator={OWNER}&state=all&per_page=100&page={page}")
            for issue in batch:
                if (issue.get("user", {}).get("login") == OWNER
                        and issue.get("title", "").startswith("[Post] ") and not issue.get("pull_request")):
                    candidates[issue["number"]] = issue
            if len(batch) < 100:
                break
        else:
            raise PostError("Too many issues to reconcile safely; contact the site maintainer.")
    for number, issue in sorted(candidates.items()):
        try:
            issue = current_issue(number)
            result = publish_issue(issue, args.source, actor=OWNER, repository=REPOSITORY)
            # Reconcile unchanged records too, so later runs can confirm posts
            # whose source was saved before an interrupted/delayed site update.
            report["posts"].append({"number": number, "id": result["id"],
                                    "changed": result["changed"],
                                    "content_hash": result["record"]["content_hash"]})
        except PostError as exc:
            # Only this exact owner's issues can receive automated error comments.
            if issue.get("user", {}).get("login") == OWNER and not issue.get("pull_request"):
                report["errors"].append({"number": number, "message": str(exc)})
            if number == int(requested) and issue.get("user", {}).get("login") != OWNER:
                raise
    report["stage"] = "prepared"
    save_report(args.report, report)
    for error in report["errors"]:
        print(f"Issue #{error['number']}: {error['message']}")


def git(root: Path, *command: str, capture=False):
    result = subprocess.run(["git", "-C", str(root), *command], check=True,
                            text=True, stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def allowed_site_path(path: str) -> bool:
    return bool(re.fullmatch(
        r"(?:feed\.(?:xml|json)|stream/(?:index\.html|publications/index\.html|feed\.(?:xml|json)|"
        r"posts/post-[1-9][0-9]*/index\.html|media/post-[1-9][0-9]*/[a-f0-9]{24}\.(?:jpg|png)))", path
    ))


def commit_and_push(root: Path, paths: list[str], message: str, expected_remote: str):
    remote = git(root, "remote", "get-url", "origin", capture=True)
    if remote not in {f"https://github.com/{expected_remote}", f"https://github.com/{expected_remote}.git",
                      f"git@github.com:{expected_remote}.git", f"git@github.com:{expected_remote}"}:
        raise PostError("Unexpected Git destination; publishing stopped.")
    git(root, "config", "user.name", "Fieldlight stream publisher")
    git(root, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    if paths:
        git(root, "add", "-A", "--", *paths)
    staged = git(root, "diff", "--cached", "--name-only", capture=True).splitlines()
    if any(path not in paths for path in staged):
        raise PostError("Unexpected staged files; publishing stopped.")
    if staged:
        git(root, "commit", "-m", message)
    # Even an unchanged tree verifies the destination and repairs a prior push.
    for attempt in range(3):
        try:
            git(root, "push", "origin", "HEAD:main")
            return
        except subprocess.CalledProcessError:
            if attempt == 2:
                raise
            git(root, "pull", "--rebase", "origin", "main")


def publish(args):
    trusted_context()
    report = json.loads(args.report.read_text())
    manifest = json.loads(args.manifest.read_text())
    if manifest.get("version") != 1:
        raise PostError("Unexpected site output manifest version.")
    paths = manifest.get("generated_paths", []) + manifest.get("removed_paths", [])
    if not isinstance(paths, list) or any(not isinstance(p, str) or not allowed_site_path(p) for p in paths):
        raise PostError("The builder requested a change outside generated stream and feed files.")
    if report["dry_run"]:
        report["stage"] = "dry_run_validated"
        save_report(args.report, report)
        print("Dry run validated. No posts, comments, commits, or remote changes were published.")
        return
    source_paths = []
    for folder in (args.source / "stream/posts", args.source / "stream/media"):
        if folder.exists():
            source_paths.extend(str(p.relative_to(args.source)) for p in folder.rglob("*")
                                if p.is_file() and p.name not in {".gitkeep", "README.md"})
    if any(not re.fullmatch(r"stream/(?:posts/post-[1-9][0-9]*\.json|media/post-[1-9][0-9]*/[a-f0-9]{24}\.(?:jpg|png))", p)
           for p in source_paths):
        raise PostError("Unexpected canonical post or media filename.")
    commit_and_push(args.source, source_paths, "Publish Fieldlight stream source", REPOSITORY)
    report["stage"] = "source_saved"
    save_report(args.report, report)


def comment(number: int, body: str, marker: str, *, update_existing=False):
    issue = api(f"/repos/{REPOSITORY}/issues/{number}")
    if issue.get("user", {}).get("login") != OWNER or issue.get("pull_request"):
        raise PostError("Refusing to comment on another author's issue.")
    for page in range(1, 101):
        comments = api(f"/repos/{REPOSITORY}/issues/{number}/comments?per_page=100&page={page}")
        for existing in comments:
            if marker in existing.get("body", "") and existing.get("user", {}).get("login") == "github-actions[bot]":
                content = body + "\n\n" + marker
                # Never downgrade an already confirmed version while reconciling.
                if existing["body"].startswith("Published:") and not body.startswith("Published:"):
                    return
                if update_existing and existing["body"] != content:
                    api(f"/repos/{REPOSITORY}/issues/comments/{existing['id']}", data={"body": content}, method="PATCH")
                return
        if len(comments) < 100:
            break
    api(f"/repos/{REPOSITORY}/issues/{number}/comments", data={"body": body + "\n\n" + marker})


def verify_live(posts: list[dict], *, timeout=60):
    if not posts:
        return True
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            request = Request(SITE_BASE + f"/stream/feed.json?verify={int(time.time())}",
                              headers={"Cache-Control": "no-cache", "User-Agent": "Fieldlight-stream-publisher/1.0"})
            with urlopen(request, timeout=12) as response:
                feed = json.load(response)
            items = {item.get("url"): item for item in feed.get("items", [])}
            if all(items.get(SITE_BASE + f"/stream/posts/{post['id']}/", {}).get("_fieldlight_content_hash")
                   == post["content_hash"] for post in posts):
                return True
        except (HTTPError, OSError, ValueError):
            pass
        time.sleep(min(10, max(0, deadline - time.monotonic())))
    return False


def finish(args):
    trusted_context()
    report = json.loads(args.report.read_text())
    if report["dry_run"]:
        if report["errors"]:
            raise PostError("Dry run found invalid post input; review the validation messages above.")
        return
    if report["stage"] != "source_saved":
        raise PostError("The canonical source push has not been confirmed.")
    for post in report["posts"]:
        status_url = SITE_BASE + f"/post/status/?post={post['id']}&version={post['content_hash']}"
        comment(post["number"], f"Saved; waiting for the next website update. [Check publication]({status_url}).",
                f"<!-- fieldlight-stream:status:{post['id']}:{post['content_hash']} -->", update_existing=True)
    live = verify_live(report["posts"])
    if not live:
        report["stage"] = "awaiting_pages"
        save_report(args.report, report)
        for post in report["posts"]:
            status_url = SITE_BASE + f"/post/status/?post={post['id']}&version={post['content_hash']}"
            comment(post["number"], "Saved; awaiting the next website update. "
                    f"[Check publication]({status_url}). "
                    "Website updates run about every ten minutes and can be delayed by GitHub.",
                    f"<!-- fieldlight-stream:status:{post['id']}:{post['content_hash']} -->", update_existing=True)
        print("Source saved. Scheduled website publication has not yet been confirmed; this is an expected pending state.")
    else:
        report["stage"] = "live"
        save_report(args.report, report)
        for post in report["posts"]:
            comment(post["number"], f"Published: {SITE_BASE}/stream/posts/{post['id']}/",
                    f"<!-- fieldlight-stream:status:{post['id']}:{post['content_hash']} -->", update_existing=True)
    for error in report["errors"]:
        comment(error["number"], "Post not published: " + error["message"] +
                " Edit this issue to correct it and retry.",
                f"<!-- fieldlight-stream:validation:{error['number']}:{os.environ.get('GITHUB_RUN_ID', '')} -->")
    if report["errors"]:
        raise PostError("Valid posts were saved; an invalid post needs correction in its issue.")


def failure(args):
    trusted_context()
    if not args.report.exists():
        # Missing-secret or checkout failures are visible in Actions, with no
        # canonical writes and no unvalidated issue used as a comment target.
        print("Publishing stopped before post preparation. Review the failed Actions step; no new source was saved.")
        return
    report = json.loads(args.report.read_text())
    if report["dry_run"] or report["stage"] == "live":
        return
    stage = report["stage"]
    if stage in {"source_saved", "awaiting_pages"}:
        status = "The post is saved in the canonical source; live website publication has not yet been confirmed."
    else:
        status = "Publication stopped before a confirmed source push."
    run = f"https://github.com/{REPOSITORY}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    for post in report["posts"]:
        comment(post["number"], status + f" Review [this workflow run]({run}), then rerun it or edit the issue to retry.",
                f"<!-- fieldlight-stream:failure:{post['id']}:{os.environ.get('GITHUB_RUN_ID', '')} -->")
    for error in report["errors"]:
        comment(error["number"], "Post not published: " + error["message"] + " Edit this issue to correct it and retry.",
                f"<!-- fieldlight-stream:validation:{error['number']}:{os.environ.get('GITHUB_RUN_ID', '')} -->")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "publish", "finish", "failure"])
    parser.add_argument("--source", type=Path, default=Path("source"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    try:
        globals()[args.command](args)
    except (PostError, HTTPError, subprocess.CalledProcessError) as exc:
        # GitHub token and signed attachment URLs never appear in our error text.
        print(f"Stream publisher stopped: {exc if isinstance(exc, PostError) else type(exc).__name__}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
