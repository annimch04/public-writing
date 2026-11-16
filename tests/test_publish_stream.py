from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image, PngImagePlugin
from pillow_heif import register_heif_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import publish_stream as publisher
import stream_workflow as workflow

URL = "https://github.com/user-attachments/assets/01234567-89ab-cdef-0123-456789abcdef"


def issue(body="A short public post.", title="_No response_", number=17):
    return {
        "number": number, "user": {"login": "annimch04"}, "title": "[Post] New post",
        "body": f"### Post\n\n{body}\n\n### Title (optional)\n\n{title}\n\n### Publication\n\n- [x] {publisher.ACK}",
        "created_at": "2026-11-16T12:30:00Z", "updated_at": "2026-11-16T12:30:00Z",
        "html_url": f"https://github.com/annimch04/public-writing/issues/{number}",
        "editor": None, "last_edited_at": None,
    }


def photo(format="JPEG", size=(8, 6), *, exif=False):
    image = Image.new("RGB", size, "purple")
    output = io.BytesIO()
    options = {}
    if exif:
        metadata = Image.Exif()
        metadata[0x010E] = "private description"
        metadata[0x0112] = 6
        options["exif"] = metadata
    image.save(output, format=format, **options)
    return output.getvalue()


class StreamPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def publish(self, value, **kwargs):
        return publisher.publish_issue(value, self.root, actor="annimch04",
                                       repository=publisher.REPOSITORY, **kwargs)

    def test_only_owner_in_canonical_repository_can_publish(self):
        for actor, repository in [("stranger", publisher.REPOSITORY), ("annimch04", "someone/fork")]:
            with self.subTest(actor=actor, repository=repository), self.assertRaises(publisher.PostError):
                publisher.validate_issue(issue(), actor=actor, repository=repository)
        for change in [{"user": {"login": "stranger"}}, {"pull_request": {}}, {"number": "17"},
                       {"html_url": "https://github.com/elsewhere/repo/issues/17"}, {"title": "New post"}]:
            value = issue()
            value.update(change)
            with self.subTest(change=change), self.assertRaises(publisher.PostError):
                self.publish(value)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_form_and_public_acknowledgment_required(self):
        for mutation in [lambda x: x.replace("[x]", "[ ]"), lambda x: x.replace("### Post", "### Draft"),
                         lambda x: x + "\nextra content", lambda x: x.replace("public post", "private\x00post")]:
            value = issue()
            value["body"] = mutation(value["body"])
            with self.assertRaises(publisher.PostError):
                self.publish(value)

    def test_owner_original_author_does_not_authorize_a_collaborator_edit(self):
        value = issue()
        value.update(editor={"login": "collaborator"}, last_edited_at="2026-11-16T13:00:00Z")
        with self.assertRaisesRegex(publisher.PostError, "edited by annimch04"):
            self.publish(value)
        value["editor"] = {"login": "annimch04"}
        self.assertTrue(self.publish(value)["changed"])
        value.pop("editor")
        with self.assertRaisesRegex(publisher.PostError, "could not be verified"):
            self.publish(value)

    def test_edits_preserve_guid_and_original_publication_date(self):
        first = self.publish(issue())
        value = issue("Revised text.", title="A title")
        value["created_at"] = "2026-11-15T00:00:00Z"  # Existing source retains the original date.
        value["updated_at"] = "2026-11-17T15:00:00+02:00"
        second = self.publish(value)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["record"]["published_at"], second["record"]["published_at"])
        self.assertEqual(second["record"]["updated_at"], "2026-11-17T13:00:00Z")
        self.assertEqual(second["record"]["title"], "A title")
        self.assertNotEqual(first["record"]["content_hash"], second["record"]["content_hash"])

    def test_identical_body_is_idempotent_even_if_issue_metadata_changed(self):
        self.publish(issue(f"Photo\n\n![Trees]({URL})"), fetch_image=lambda _: photo())
        destination = self.root / "stream/posts/post-17.json"
        original = destination.read_bytes()
        value = issue(f"Photo\n\n![Trees]({URL})")
        value["updated_at"] = "2026-11-17T15:00:00Z"
        result = self.publish(value, fetch_image=lambda _: self.fail("Unchanged photos must not be downloaded"))
        self.assertFalse(result["changed"])
        self.assertEqual(original, destination.read_bytes())

    def test_html_and_markdown_photos_are_extracted_in_order(self):
        body = f'Before\n\n![A tree]({URL})\n\n<img width="600" alt="A &amp; B" src="{URL}" />\n\nAfter'
        result = self.publish(issue(body), fetch_image=lambda _: photo())
        self.assertEqual(result["record"]["body"], "Before\n\nAfter")
        self.assertEqual([x["alt"] for x in result["record"]["images"]], ["A tree", "A & B"])
        self.assertTrue(all((self.root / image["path"]).exists() for image in result["record"]["images"]))

    def test_no_partial_post_when_one_attachment_is_invalid(self):
        calls = 0
        def fetch(_):
            nonlocal calls
            calls += 1
            return photo() if calls == 1 else b"not a photo"
        with self.assertRaises(publisher.PostError):
            self.publish(issue(f"![One]({URL})\n![Two]({URL})"), fetch_image=fetch)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_dry_run_validates_without_writing_source(self):
        result = self.publish(issue(f"![Photo]({URL})"), fetch_image=lambda _: photo(), dry_run=True)
        self.assertTrue(result["changed"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_image_urls_cannot_access_arbitrary_hosts_or_local_services(self):
        urls = ["http://127.0.0.1/photo.jpg", "https://127.0.0.1/photo.jpg", "file:///etc/passwd",
                "https://example.com/photo.jpg", "https://user-images.githubusercontent.com.evil.test/a.jpg",
                "https://user-images.githubusercontent.com@evil.test/a.jpg",
                "https://github.com:443/user-attachments/assets/01234567-89ab-cdef-0123-456789abcdef",
                "https://github.com/annimch04/private/raw/photo.jpg",
                "https://user-images.githubusercontent.com/1/%2e%2e/secret.png"]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(publisher.PostError):
                publisher.validate_image_url(url)
            with self.subTest(redirect=url), self.assertRaises(publisher.PostError):
                publisher.validate_image_url(url, redirect=True)
        with self.assertRaises(publisher.PostError):
            publisher.SafeImageRedirect().redirect_request(None, None, 302, "", {}, "https://example.com/photo.jpg")

    def test_unsupported_image_syntax_and_excess_photos_are_errors(self):
        for body in ["![External](https://example.com/photo.jpg)", "![Reference][photo]\n[photo]: " + URL,
                     f"![]({URL})", f'<img src="{URL}">',
                     "\n".join([f"![Photo]({URL})"] * 9)]:
            with self.subTest(body=body), self.assertRaises(publisher.PostError):
                publisher.extract_images(body)

    def test_reencoding_removes_metadata_and_honors_orientation(self):
        result, extension = publisher.clean_image(photo(exif=True))
        self.assertEqual(extension, "jpg")
        image = Image.open(io.BytesIO(result))
        self.assertEqual(image.size, (6, 8))
        self.assertEqual(dict(image.getexif()), {})
        self.assertNotIn(b"private description", result)

    def test_png_transparency_survives_but_comments_do_not(self):
        raw = io.BytesIO()
        info = PngImagePlugin.PngInfo()
        info.add_text("private", "sensitive note")
        Image.new("RGBA", (3, 3), (1, 2, 3, 0)).save(raw, format="PNG", pnginfo=info)
        result, extension = publisher.clean_image(raw.getvalue())
        image = Image.open(io.BytesIO(result))
        self.assertEqual(extension, "png")
        self.assertEqual(image.getpixel((0, 0))[3], 0)
        self.assertNotIn("private", image.info)

    def test_large_photo_is_resized_to_4096_edge(self):
        result, _ = publisher.clean_image(photo(size=(8192, 8)))
        self.assertEqual(Image.open(io.BytesIO(result)).size, (4096, 4))

    def test_heic_photo_file_attachment_is_supported(self):
        register_heif_opener()
        raw = photo(format="HEIF")
        attachment = "https://github.com/user-attachments/files/1234/IMG_1000.HEIC"
        result = self.publish(issue(f"[IMG_1000.HEIC]({attachment})"), fetch_image=lambda _: raw)
        self.assertEqual(result["record"]["body"], "")
        self.assertTrue(result["record"]["images"][0]["path"].endswith(".jpg"))

    def test_animated_and_oversized_images_are_rejected(self):
        output = io.BytesIO()
        Image.new("RGB", (2, 2), "red").save(output, format="GIF", save_all=True,
                    append_images=[Image.new("RGB", (2, 2), "blue")], duration=100, loop=0)
        with self.assertRaisesRegex(publisher.PostError, "Animated"):
            publisher.clean_image(output.getvalue())
        with patch.object(publisher, "MAX_PIXELS", 40), self.assertRaisesRegex(publisher.PostError, "megapixels"):
            publisher.clean_image(photo())
        with patch.object(publisher, "MAX_IMAGE_BYTES", 2), self.assertRaisesRegex(publisher.PostError, "15 MB"):
            publisher.clean_image(photo())

    def test_manifest_cannot_stage_code_or_arbitrary_paths(self):
        for path in ["feed.xml", "stream/feed.json", "stream/posts/post-17/index.html",
                     "stream/media/post-17/" + "a" * 24 + ".jpg"]:
            self.assertTrue(workflow.allowed_site_path(path), path)
        for path in ["scripts/build-stream.py", ".github/workflows/deploy.yml", "stream/../../index.html",
                     "/feed.xml", "stream/publications.json", "stream/media/post-17/arbitrary.svg"]:
            self.assertFalse(workflow.allowed_site_path(path), path)

    def test_live_verification_requires_matching_content_hash(self):
        posts = [{"id": "post-17", "content_hash": "expected"}]
        feed = {"items": [{"url": "https://fieldlight.com/stream/posts/post-17/",
                           "_fieldlight_content_hash": "expected"}]}
        with patch.object(workflow, "urlopen", return_value=io.StringIO(json.dumps(feed))):
            self.assertTrue(workflow.verify_live(posts, timeout=1))
        self.assertFalse(workflow.verify_live(posts, timeout=0))

    def test_current_issue_fetch_keeps_body_and_editor_in_one_snapshot(self):
        value = issue()
        snapshot = {"number": 17, "title": value["title"], "body": value["body"],
                    "createdAt": value["created_at"], "updatedAt": value["updated_at"],
                    "url": value["html_url"], "author": value["user"],
                    "editor": {"login": "annimch04"}, "lastEditedAt": value["updated_at"]}
        with patch.object(workflow, "api", return_value={"data": {"repository": {"issue": snapshot}}}) as api:
            actual = workflow.current_issue(17)
        self.assertEqual(actual["body"], value["body"])
        self.assertEqual(actual["editor"]["login"], "annimch04")
        self.assertEqual(api.call_args.args[0], "/graphql")
        self.assertIn("editor { login }", api.call_args.kwargs["data"]["query"])

    def test_other_person_cannot_rerun_owner_job_with_owner_authority(self):
        environment = {"GITHUB_ACTOR": "annimch04", "GITHUB_TRIGGERING_ACTOR": "collaborator",
                       "GITHUB_REPOSITORY": publisher.REPOSITORY, "GITHUB_REF": "refs/heads/main"}
        with patch.dict(workflow.os.environ, environment), self.assertRaises(publisher.PostError):
            workflow.trusted_context()

    def test_reconciliation_recovers_unchanged_posts_and_isolates_invalid_photo(self):
        self.publish(issue())
        records = {17: issue(), 18: issue(f"![]({URL})", number=18), 19: issue("New post", number=19)}
        args = SimpleNamespace(source=self.root, report=self.root / "report.json")
        with patch.object(workflow, "trusted_context"), patch.dict(workflow.os.environ, {"REQUESTED_ISSUE": "19", "DRY_RUN": "false"}), \
             patch.object(workflow, "current_issue", side_effect=lambda n: records[n]), \
             patch.object(workflow, "api", return_value=list(records.values())) as api:
            workflow.prepare(args)
        report = json.loads(args.report.read_text())
        self.assertEqual([p["number"] for p in report["posts"]], [17, 19])
        self.assertFalse(report["posts"][0]["changed"])
        self.assertEqual([e["number"] for e in report["errors"]], [18])
        self.assertIn("state=all", api.call_args.args[0])

    def test_empty_dry_run_creates_no_posts_and_uses_no_issue_api(self):
        args = SimpleNamespace(source=self.root, report=self.root / "report.json")
        with patch.object(workflow, "trusted_context"), patch.dict(workflow.os.environ, {"REQUESTED_ISSUE": "", "DRY_RUN": "true"}), \
             patch.object(workflow, "api", side_effect=AssertionError("No issue lookup should occur")):
            workflow.prepare(args)
        self.assertEqual(json.loads(args.report.read_text())["posts"], [])
        self.assertFalse((self.root / "stream/posts").exists())

    def test_source_publication_never_pushes_website_repository(self):
        self.publish(issue())
        args = SimpleNamespace(source=self.root, report=self.root / "report.json", manifest=self.root / "manifest.json")
        args.report.write_text(json.dumps({"dry_run": False, "stage": "prepared"}))
        args.manifest.write_text(json.dumps({"version": 1, "generated_paths": ["stream/index.html"], "removed_paths": []}))
        with patch.object(workflow, "trusted_context"), patch.object(workflow, "commit_and_push") as push:
            workflow.publish(args)
        self.assertEqual(push.call_count, 1)
        self.assertEqual(push.call_args.args[0], self.root)
        self.assertEqual(push.call_args.args[-1], publisher.REPOSITORY)
        self.assertEqual(json.loads(args.report.read_text())["stage"], "source_saved")

    def test_scheduled_site_delay_is_pending_success_with_precise_status_link(self):
        args = SimpleNamespace(report=self.root / "report.json")
        args.report.write_text(json.dumps({"dry_run": False, "stage": "source_saved", "errors": [],
                    "posts": [{"number": 17, "id": "post-17", "content_hash": "a" * 64}]}))
        with patch.object(workflow, "trusted_context"), patch.object(workflow, "verify_live", return_value=False), \
             patch.object(workflow, "comment") as comment:
            workflow.finish(args)
        self.assertEqual(json.loads(args.report.read_text())["stage"], "awaiting_pages")
        self.assertIn("/post/status/?post=post-17&version=" + "a" * 64, comment.call_args.args[1])
        self.assertFalse(any(call.args[1].startswith("Published:") for call in comment.call_args_list))

    def test_confirmed_feed_produces_published_permalink(self):
        args = SimpleNamespace(report=self.root / "report.json")
        args.report.write_text(json.dumps({"dry_run": False, "stage": "source_saved", "errors": [],
                    "posts": [{"number": 17, "id": "post-17", "content_hash": "a" * 64}]}))
        with patch.object(workflow, "trusted_context"), patch.object(workflow, "verify_live", return_value=True), \
             patch.object(workflow, "comment") as comment:
            workflow.finish(args)
        self.assertEqual(json.loads(args.report.read_text())["stage"], "live")
        self.assertEqual(comment.call_args.args[1], "Published: https://fieldlight.com/stream/posts/post-17/")


if __name__ == "__main__":
    unittest.main()
