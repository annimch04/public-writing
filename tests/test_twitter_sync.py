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


if __name__ == "__main__":
    unittest.main()
