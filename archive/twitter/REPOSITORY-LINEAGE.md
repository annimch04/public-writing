# Repository lineage

Canonical home: [annimch04/public-writing — archive/twitter](https://github.com/annimch04/public-writing/tree/main/archive/twitter).

- July 22, 2026: sanitized exported posts were added to public-writing (`5483cd8`). The public export already excluded direct messages, deleted-post files, and account/security sources.
- September 9, 2026: `ab40cd2` moved the archive and sync tools to a separate repository. Its README records a byte-identical copy from public-writing `af12769`, with subtree history `3dd8f6ffa741f349bb6869cea1fd8931bb285982` preserved.
- September 11, 2026: the separate repository became public; public-writing linked it in `9dd0105`.
- September 14, 2026: Anni approved public-writing as the canonical home again. This restoration starts with every tracked archive file from twitter-archive `9a3ade0`, including the paper acquisition/recurrence context note, plus its three collection/export tools and test suite. Further changes are reviewable in this repository's diff and history.

The separate repository is retained as a legacy historical copy. It is not a second independently maintained source of truth. Its existing commits are retained; no history rewrite or deletion is needed.

## Public/private boundary

Publish only sanitized public-post records, their dated indexes, and reviewed public context. `.twitter-sync/` remains ignored for collection and review batches. Raw source exports and private source material remain in the private archive. Returning public records here does not authorize publishing deleted-post exports, DMs, contacts, credentials, security logs, or private review material.

A public-profile collection records what the profile served at collection time. Missing profile cards are not evidence of deletion. Repost sightings remain provisional observations rather than fabricated repost timestamps. The original export and each later collection retain their own provenance.
