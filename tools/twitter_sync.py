#!/usr/bin/env python3
"""Stage incremental public X posts without changing the published archive.

This command is intentionally dry-run only. It compares a collector batch with
the current sanitized archive, rejects private source classes, and writes a
review bundle containing only new public posts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from twitter_archive_export import (
    classify,
    clean_text,
    collect_media,
    iso_date,
    load_js_array,
    parse_tweet,
    safe_year,
)

DEFAULT_BASELINE = Path("archive/twitter/staging/tweets.sanitized.jsonl")
DEFAULT_STATE = Path("archive/twitter/sync/state.json")

FORBIDDEN_EXACT_NAMES = {
    "deleted-tweets.js",
    "deleted-tweet-headers.js",
    "direct-messages.js",
    "direct-messages-group.js",
    "ip-audit.js",
    "contact.js",
    "device-token.js",
    "account-creation-ip.js",
    "phone-number.js",
    "email-address-change.js",
    "like.js",
    "follower.js",
    "following.js",
}
FORBIDDEN_PATH_MARKERS = {
    "deleted_tweets_media",
    "direct_messages_media",
    "direct_messages_group_media",
}
PRIVATE_RECORD_KEYS = {
    "dmConversation",
    "directMessage",
    "directMessages",
    "messageCreate",
    "messageData",
}


class PrivacyBoundaryError(ValueError):
    """Raised when an input may contain intentionally excluded private data."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_public_source(path: Path) -> None:
    lowered_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if name in FORBIDDEN_EXACT_NAMES or name.startswith("ad-"):
        raise PrivacyBoundaryError(f"Refusing excluded source: {path}")
    if lowered_parts & FORBIDDEN_PATH_MARKERS:
        raise PrivacyBoundaryError(f"Refusing private media source: {path}")
    if path.suffix.lower() == ".js" and name != "tweets.js":
        raise PrivacyBoundaryError(
            "JavaScript imports are restricted to the active public data/tweets.js file."
        )


def assert_public_record(row: dict[str, Any]) -> None:
    private_keys = PRIVATE_RECORD_KEYS.intersection(row)
    if private_keys:
        names = ", ".join(sorted(private_keys))
        raise PrivacyBoundaryError(f"Private message record shape detected: {names}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(value)
    return rows


def load_input(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    assert_public_source(path)
    suffix = path.suffix.lower()
    metadata: dict[str, Any] = {"source_path": str(path), "adapter": suffix.lstrip(".")}

    if suffix == ".js":
        rows = load_js_array(path)
        metadata["adapter"] = "twitter_archive_tweets_js"
    elif suffix == ".jsonl":
        rows = load_jsonl(path)
        metadata["adapter"] = "public_jsonl"
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and isinstance(payload.get("posts"), list):
            rows = payload["posts"]
            source = payload.get("source")
            if isinstance(source, dict):
                metadata["collector"] = source
        elif isinstance(payload, dict) and isinstance(payload.get("tweets"), list):
            rows = payload["tweets"]
        else:
            raise ValueError("JSON input must be a list or contain a posts/tweets list.")
        metadata["adapter"] = "public_json"
    else:
        raise ValueError("Supported inputs are .js, .json, and .jsonl public-post files.")

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every input record must be a JSON object.")
        assert_public_record(row)
    return rows, metadata


def load_baseline(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Baseline archive not found: {path}")
    return load_jsonl(path)


def canonical_record(row: dict[str, Any], username: str) -> dict[str, Any]:
    assert_public_record(row)

    if row.get("canonical_status") == "archive_fragment_not_canon":
        record = dict(row)
        record["review_status"] = "pending"
        validate_record(record)
        return record

    tweet = parse_tweet(row)
    assert_public_record(tweet)
    tweet_id = str(tweet.get("id_str") or tweet.get("id") or "").strip()
    created_at = tweet.get("created_at")
    if not tweet_id or not created_at:
        raise ValueError("Public post is missing id/id_str or created_at.")

    entities = tweet.get("entities") or {}
    urls = entities.get("urls") or []
    media = collect_media(tweet)
    record = {
        "id": tweet_id,
        "created_at": created_at,
        "created_at_utc": iso_date(created_at),
        "year": safe_year(created_at),
        "kind": classify(tweet, username),
        "text": clean_text(tweet.get("full_text") or tweet.get("text") or "", urls),
        "tweet_url": f"https://x.com/{username}/status/{tweet_id}",
        "in_reply_to_status_id": tweet.get("in_reply_to_status_id_str"),
        "in_reply_to_screen_name": tweet.get("in_reply_to_screen_name"),
        "quoted_status_id": tweet.get("quoted_status_id_str"),
        "urls": [
            {
                "expanded_url": item.get("expanded_url"),
                "display_url": item.get("display_url"),
            }
            for item in urls
        ],
        "media": media,
        "review_status": "pending",
        "canonical_status": "archive_fragment_not_canon",
    }
    validate_record(record)
    return record


def validate_record(record: dict[str, Any]) -> None:
    required = ("id", "created_at_utc", "year", "kind", "text", "canonical_status")
    missing = [name for name in required if record.get(name) is None or record.get(name) == ""]
    if missing:
        raise ValueError(f"Sanitized record is missing required fields: {', '.join(missing)}")
    if record.get("canonical_status") != "archive_fragment_not_canon":
        raise ValueError("Incremental posts must remain archive fragments, not public canon.")
    datetime.fromisoformat(str(record["created_at_utc"]))


def archive_cursor(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"post_count": 0, "last_archived_post_id": None, "last_archived_at_utc": None}
    latest = max(
        records,
        key=lambda row: (
            str(row.get("created_at_utc") or ""),
            int(str(row.get("id") or "0")),
        ),
    )
    return {
        "post_count": len(records),
        "last_archived_post_id": latest.get("id"),
        "last_archived_at_utc": latest.get("created_at_utc"),
    }


def stage(
    rows: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
    username: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    baseline_ids = {str(row.get("id")) for row in baseline if row.get("id")}
    seen_input: set[str] = set()
    new_records: list[dict[str, Any]] = []
    duplicate_count = 0

    for row in rows:
        record = canonical_record(row, username)
        post_id = str(record["id"])
        if post_id in baseline_ids or post_id in seen_input:
            duplicate_count += 1
            continue
        seen_input.add(post_id)
        new_records.append(record)

    new_records.sort(key=lambda row: (str(row["created_at_utc"]), int(str(row["id"]))))
    report = {
        "schema_version": 1,
        "mode": "dry_run_review_only",
        "generated_at_utc": utc_now(),
        "account_username": username,
        "input_records": len(rows),
        "baseline_records": len(baseline),
        "duplicate_records": duplicate_count,
        "new_public_records": len(new_records),
        "new_kind_counts": dict(Counter(row["kind"] for row in new_records)),
        "baseline_cursor": archive_cursor(baseline),
        "proposed_cursor": archive_cursor(baseline + new_records),
        "privacy_policy": {
            "direct_messages": "hard_rejected",
            "deleted_posts": "hard_rejected",
            "account_security_and_ip_data": "hard_rejected",
            "automatic_publication": False,
        },
    }
    return new_records, report


def write_review_bundle(
    output_dir: Path,
    records: list[dict[str, Any]],
    report: dict[str, Any],
    source: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)

    with (output_dir / "new-posts.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (output_dir / "review.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "decision",
            "created_at_utc",
            "kind",
            "id",
            "tweet_url",
            "text_preview",
            "has_media",
            "theme",
            "linked_work",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "decision": "pending",
                    "created_at_utc": record["created_at_utc"],
                    "kind": record["kind"],
                    "id": record["id"],
                    "tweet_url": record.get("tweet_url"),
                    "text_preview": re.sub(r"\s+", " ", record.get("text") or "")[:220],
                    "has_media": bool(record.get("media")),
                    "theme": "",
                    "linked_work": "",
                }
            )

    full_report = dict(report)
    full_report["source"] = source
    (output_dir / "sync-report.json").write_text(
        json.dumps(full_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        "# Twitter/X Incremental Review Bundle\n\n"
        "This is a dry-run artifact. Nothing in this folder has been added to the\n"
        "published archive. Review `review.csv` before a separate publish step is\n"
        "ever introduced or run.\n\n"
        "Direct messages, deleted posts, IP/security data, contacts, device records,\n"
        "ads, likes, followers, and following records are outside this pipeline.\n",
        encoding="utf-8",
    )


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(".twitter-sync") / f"review-{stamp}"


def status_command(args: argparse.Namespace) -> int:
    baseline = load_baseline(args.baseline)
    current = archive_cursor(baseline)
    if args.state.exists():
        current["persisted_state"] = json.loads(args.state.read_text(encoding="utf-8"))
    print(json.dumps(current, indent=2))
    return 0


def dry_run_command(args: argparse.Namespace) -> int:
    rows, source = load_input(args.input)
    baseline = load_baseline(args.baseline)
    records, report = stage(rows, baseline, args.username)
    write_review_bundle(args.output_dir, records, report, source)
    print(json.dumps({**report, "review_bundle": str(args.output_dir)}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review new public X posts without mutating the published archive."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show the published archive cursor.")
    status_parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    status_parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    status_parser.set_defaults(func=status_command)

    dry_parser = subparsers.add_parser("dry-run", help="Build a review-only incremental bundle.")
    dry_parser.add_argument("--input", required=True, type=Path)
    dry_parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    dry_parser.add_argument("--output-dir", type=Path, default=None)
    dry_parser.add_argument("--username", default="SayitSalty")
    dry_parser.set_defaults(func=dry_run_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "output_dir", None) is None and args.command == "dry-run":
        args.output_dir = default_output_dir()
    try:
        return args.func(args)
    except (PrivacyBoundaryError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"twitter-sync: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
