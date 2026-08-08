# alt: a record of return — public data record

This directory contains the sanitized dataset used by the interactive reading surface for [alt: a record of return](../../field-notes-and-signal-work/alt-a-record-of-return.md).

## Source

- Source format: Apple Music XML playlist export
- Playlist: `alt`
- Export timestamp: `2026-08-08T00:09:09Z`
- Public records: 202 playlist entries

The playlist was not manually sequenced. Its exported order approximates the order in which tracks became favorites, except for one or two tracks that disappeared and were later added back.

## Privacy boundary

The original XML is intentionally excluded. It contains local file paths, track and library identifiers, persistent identifiers, and other machine-specific metadata.

`alt-sanitized.json` retains only:

- exported playlist order
- title, artist, album, and genre
- release year
- library-entry and last-played dates
- play and skip counts
- duration
- favorite status

`Date Added` is a library-entry date, not a favorite date. Counts are preserved as reported by Apple Music at the time of export.
