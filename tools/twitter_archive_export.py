#!/usr/bin/env python3
"""Create a sanitized staging export from a Twitter/X archive.

This script reads only data/tweets.js from the archive. It does not parse or
export deleted tweets, direct messages, ads, account-security records, contacts,
IP logs, or device data.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TWITTER_DATE = "%a %b %d %H:%M:%S %z %Y"

EXCLUDED_BY_POLICY = [
    "data/deleted-tweets.js",
    "data/deleted-tweet-headers.js",
    "data/deleted_tweets_media/",
    "data/direct-messages.js",
    "data/direct-messages-group.js",
    "data/direct_messages_media/",
    "data/direct_messages_group_media/",
    "data/ip-audit.js",
    "data/contact.js",
    "data/device-token.js",
    "data/account-creation-ip.js",
    "data/phone-number.js",
    "data/email-address-change.js",
    "data/ad-*",
    "data/like.js",
    "data/follower.js",
    "data/following.js",
]


def load_js_array(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    idx = text.find("=")
    if idx == -1:
        raise ValueError(f"No assignment found in {path}")
    payload = text[idx + 1 :].strip().rstrip(";")
    return json.loads(payload)


def parse_tweet(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("tweet", row)


def clean_text(text: str, urls: list[dict[str, Any]]) -> str:
    cleaned = text or ""
    for url in urls:
        short = url.get("url")
        expanded = url.get("expanded_url") or url.get("display_url")
        if short and expanded:
            cleaned = cleaned.replace(short, expanded)
    return cleaned.strip()


def classify(tweet: dict[str, Any], account_username: str | None) -> str:
    text = tweet.get("full_text") or tweet.get("text") or ""
    if text.startswith("RT @"):
        return "retweet"
    if tweet.get("in_reply_to_status_id_str"):
        if account_username and tweet.get("in_reply_to_screen_name", "").lower() == account_username.lower():
            return "self_thread_reply"
        return "reply"
    if tweet.get("quoted_status_id_str") or tweet.get("quoted_status_permalink"):
        return "quote"
    return "original"


def iso_date(created_at: str) -> str:
    dt = datetime.strptime(created_at, TWITTER_DATE)
    return dt.astimezone(timezone.utc).isoformat()


def safe_year(created_at: str) -> str:
    return datetime.strptime(created_at, TWITTER_DATE).strftime("%Y")


def collect_media(tweet: dict[str, Any]) -> list[dict[str, Any]]:
    entities = tweet.get("extended_entities") or tweet.get("entities") or {}
    media = entities.get("media") or []
    out = []
    for item in media:
        out.append(
            {
                "media_id": item.get("id_str") or item.get("id"),
                "type": item.get("type"),
                "media_url": item.get("media_url_https") or item.get("media_url"),
                "expanded_url": item.get("expanded_url"),
                "display_url": item.get("display_url"),
            }
        )
    return out


def account_username(root: Path) -> str | None:
    path = root / "data" / "account.js"
    if not path.exists():
        return None
    try:
        rows = load_js_array(path)
    except Exception:
        return None
    if not rows:
        return None
    account = rows[0].get("account", {})
    return account.get("username")


def sanitize(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    tweets_path = root / "data" / "tweets.js"
    if not tweets_path.exists():
        raise FileNotFoundError(f"Missing {tweets_path}")

    username = account_username(root)
    rows = load_js_array(tweets_path)
    records: list[dict[str, Any]] = []
    media_map: list[dict[str, Any]] = []
    counts = Counter()
    years = Counter()

    for row in rows:
        tweet = parse_tweet(row)
        created_at = tweet.get("created_at")
        tweet_id = tweet.get("id_str")
        entities = tweet.get("entities") or {}
        urls = entities.get("urls") or []
        media = collect_media(tweet)
        kind = classify(tweet, username)

        record = {
            "id": tweet_id,
            "created_at": created_at,
            "created_at_utc": iso_date(created_at) if created_at else None,
            "year": safe_year(created_at) if created_at else None,
            "kind": kind,
            "text": clean_text(tweet.get("full_text") or tweet.get("text") or "", urls),
            "tweet_url": f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else None,
            "in_reply_to_status_id": tweet.get("in_reply_to_status_id_str"),
            "in_reply_to_screen_name": tweet.get("in_reply_to_screen_name"),
            "quoted_status_id": tweet.get("quoted_status_id_str"),
            "urls": [
                {
                    "expanded_url": u.get("expanded_url"),
                    "display_url": u.get("display_url"),
                }
                for u in urls
            ],
            "media": media,
            "review_status": "pending",
            "canonical_status": "archive_fragment_not_canon",
        }
        records.append(record)
        counts[kind] += 1
        if created_at:
            years[record["year"]] += 1
        for item in media:
            media_map.append({"tweet_id": tweet_id, **item})

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Twitter/X archive data/tweets.js only",
        "account_username": username,
        "active_tweets": len(records),
        "kind_counts": dict(counts),
        "year_counts": dict(sorted(years.items())),
        "media_references": len(media_map),
        "excluded_by_policy": EXCLUDED_BY_POLICY,
        "canonical_note": "Public posts are archival fragments, not canonical essays.",
    }
    return records, media_map, manifest


def write_outputs(records: list[dict[str, Any]], media_map: list[dict[str, Any]], manifest: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)

    with (out / "tweets.sanitized.jsonl").open("w", encoding="utf-8") as f:
        for record in sorted(records, key=lambda r: r.get("created_at_utc") or ""):
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (out / "media-map.json").open("w", encoding="utf-8") as f:
        json.dump(media_map, f, indent=2, ensure_ascii=False)

    with (out / "excluded-summary.json").open("w", encoding="utf-8") as f:
        json.dump({"excluded_by_policy": EXCLUDED_BY_POLICY}, f, indent=2)

    with (out / "export-manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    with (out / "review.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "review_status",
                "year",
                "created_at_utc",
                "kind",
                "id",
                "tweet_url",
                "text_preview",
                "has_media",
                "has_urls",
                "theme",
                "linked_work",
            ],
        )
        writer.writeheader()
        for record in sorted(records, key=lambda r: r.get("created_at_utc") or ""):
            preview = re.sub(r"\s+", " ", record.get("text") or "")[:220]
            writer.writerow(
                {
                    "review_status": "pending",
                    "year": record.get("year"),
                    "created_at_utc": record.get("created_at_utc"),
                    "kind": record.get("kind"),
                    "id": record.get("id"),
                    "tweet_url": record.get("tweet_url"),
                    "text_preview": preview,
                    "has_media": bool(record.get("media")),
                    "has_urls": bool(record.get("urls")),
                    "theme": "",
                    "linked_work": "",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize a Twitter/X archive into local staging files.")
    parser.add_argument("archive", type=Path, help="Path to the unzipped Twitter/X archive folder")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("archive/twitter/staging"),
        help="Output directory for local staging files",
    )
    args = parser.parse_args()

    records, media_map, manifest = sanitize(args.archive)
    write_outputs(records, media_map, manifest, args.out)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
