from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from twitter_sync import (  # noqa: E402
    PrivacyBoundaryError,
    XApiError,
    collect_x_posts,
    load_input,
    stage,
    write_review_bundle,
)


def public_record(post_id: str, created_at: str = "Wed Jul 22 04:00:00 +0000 2026") -> dict:
    return {
        "tweet": {
            "id_str": post_id,
            "created_at": created_at,
            "full_text": "A public test fragment.",
            "entities": {"urls": []},
        }
    }


class TwitterSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = [
            {
                "id": "100",
                "created_at": "Wed Jul 22 03:00:00 +0000 2026",
                "created_at_utc": "2026-07-22T03:00:00+00:00",
                "year": "2026",
                "kind": "original",
                "text": "Already archived.",
                "tweet_url": "https://x.com/SayitSalty/status/100",
                "in_reply_to_status_id": None,
                "in_reply_to_screen_name": None,
                "quoted_status_id": None,
                "urls": [],
                "media": [],
                "review_status": "pending",
                "canonical_status": "archive_fragment_not_canon",
            }
        ]

    def test_duplicate_is_skipped_and_new_post_is_staged(self) -> None:
        rows = [public_record("100"), public_record("101")]
        new_records, report = stage(rows, self.baseline, "SayitSalty")
        self.assertEqual([row["id"] for row in new_records], ["101"])
        self.assertEqual(report["duplicate_records"], 1)
        self.assertEqual(report["new_public_records"], 1)

    def test_forbidden_direct_message_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "direct-messages.js"
            path.write_text("window.YTD.direct_messages.part0 = [];", encoding="utf-8")
            with self.assertRaises(PrivacyBoundaryError):
                load_input(path)

    def test_private_message_record_shape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "public-batch.json"
            path.write_text(json.dumps([{"dmConversation": {"messages": []}}]), encoding="utf-8")
            with self.assertRaises(PrivacyBoundaryError):
                load_input(path)

    def test_missing_public_post_identity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage([{"tweet": {"full_text": "Missing identity."}}], self.baseline, "SayitSalty")

    def test_review_bundle_does_not_mutate_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline_path = root / "baseline.jsonl"
            baseline_path.write_text(json.dumps(self.baseline[0]) + "\n", encoding="utf-8")
            before = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
            records, report = stage([public_record("101")], self.baseline, "SayitSalty")
            output = root / "review"
            write_review_bundle(output, records, report, {"adapter": "test"})
            after = hashlib.sha256(baseline_path.read_bytes()).hexdigest()

            self.assertEqual(before, after)
            self.assertTrue((output / "new-posts.jsonl").exists())
            self.assertTrue((output / "review.csv").exists())
            self.assertTrue((output / "sync-report.json").exists())

    def test_official_collector_uses_baseline_cutoff_and_normalizes_posts(self) -> None:
        requests = []

        def fake_request(path, params, token, api_base):
            requests.append((path, params, token, api_base))
            if path == "users/by/username/SayitSalty":
                return {"data": {"id": "42", "username": "SayitSalty"}}
            return {
                "data": [
                    {
                        "id": "101",
                        "text": "New public post.",
                        "created_at": "2026-07-23T12:00:00.000Z",
                        "attachments": {"media_keys": ["3_101"]},
                    },
                    {
                        "id": "102",
                        "text": "A reply.",
                        "created_at": "2026-07-23T12:05:00.000Z",
                        "in_reply_to_user_id": "99",
                        "referenced_tweets": [{"type": "replied_to", "id": "88"}],
                    },
                ],
                "includes": {
                    "media": [
                        {
                            "media_key": "3_101",
                            "type": "photo",
                            "url": "https://pbs.twimg.com/media/example.jpg",
                        }
                    ]
                },
                "meta": {"result_count": 2},
            }

        records, source = collect_x_posts(
            "SayitSalty",
            "100",
            "secret-token",
            request_json=fake_request,
        )

        timeline_request = requests[1]
        self.assertEqual(timeline_request[0], "users/42/tweets")
        self.assertEqual(timeline_request[1]["since_id"], "100")
        self.assertEqual([record["id"] for record in records], ["101", "102"])
        self.assertEqual(records[0]["kind"], "original")
        self.assertEqual(records[0]["media"][0]["type"], "photo")
        self.assertEqual(records[1]["kind"], "reply")
        self.assertEqual(source["private_sources_requested"], False)

    def test_official_collector_paginates(self) -> None:
        calls = []

        def fake_request(path, params, token, api_base):
            calls.append(dict(params))
            post_id = "101" if len(calls) == 1 else "102"
            payload = {
                "data": [
                    {
                        "id": post_id,
                        "text": f"Post {post_id}",
                        "created_at": "2026-07-23T12:00:00.000Z",
                    }
                ],
                "meta": {},
            }
            if len(calls) == 1:
                payload["meta"]["next_token"] = "next-page"
            return payload

        records, source = collect_x_posts(
            "SayitSalty",
            "100",
            "secret-token",
            user_id="42",
            request_json=fake_request,
        )
        self.assertEqual([record["id"] for record in records], ["101", "102"])
        self.assertIsNone(calls[0]["pagination_token"])
        self.assertEqual(calls[1]["pagination_token"], "next-page")
        self.assertEqual(source["pages_read"], 2)

    def test_collector_error_does_not_expose_token(self) -> None:
        def failing_request(path, params, token, api_base):
            raise XApiError("Credential rejected.")

        with self.assertRaisesRegex(XApiError, "Credential rejected"):
            collect_x_posts(
                "SayitSalty",
                "100",
                "do-not-print-me",
                user_id="42",
                request_json=failing_request,
            )


if __name__ == "__main__":
    unittest.main()
