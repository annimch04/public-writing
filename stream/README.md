# Fieldlight stream

Short posts and photos are authored here and appear on [Fieldlight’s Everything stream](https://fieldlight.com/stream/), alongside developed publications. They are a new authored stream; this workflow does not import the Twitter archive.

## Post from your phone or Mac

1. Open [New stream post](https://github.com/annimch04/public-writing/issues/new?template=stream-post.yml), signed in as **annimch04**. Bookmark this link on your phone and Mac.
2. Write in **Post**. Attach photos with GitHub’s image button or drag and drop. Add a short description between `![` and `]` in each photo’s image text. A title is optional.
3. Check the publication box and submit. **Submitting publishes publicly.** The issue and its original attachments are also public; the form is not a private draft.
4. Follow the comment’s **Check publication** link. It checks for this exact version in the live feed and refreshes automatically. A **Published** comment means the live feed was verified. **Saved; awaiting the next website update** means the source was saved successfully but public deployment has not yet been confirmed.

The website checks for new source posts about every ten minutes. GitHub can delay scheduled jobs. A successfully submitted issue, saved source record, and live post are distinct states.

The post supports paragraphs, line breaks, ordinary links, and photos. HTTP(S) Markdown links are supported; other Markdown formatting is shown literally. Raw HTML is displayed as text except for GitHub’s photo tags, which are extracted as photos. The workflow accepts up to eight JPEG, PNG, WebP, HEIC/HEIF, or still GIF images per post, each at most 15 MB and 80 megapixels. Photos are resized to fit a 4096-pixel edge while preserving their proportions. Animated images are rejected with an explanation.

## Edit an existing post

Edit the original issue’s **body** and save it. Keep the form’s section headings and publication checkbox. The owner must make the edit. The same issue updates the same post URL and feed identifier, retaining its original publication date. An unchanged body does not create a new revision or duplicate feed item.

Closing an issue does **not** unpublish its post. Editing a closed post still updates it. Withdrawal is a separate, deliberate source-and-site change; request withdrawal rather than closing the issue.

For maintainers, withdrawal also requires removing the issue’s `[Post]` title prefix before removing its canonical record and regenerating the website. Otherwise the next reconciliation would restore the still-authorized issue post.

## Where the record lives

- Canonical post: `stream/posts/post-<issue-number>.json`.
- Canonical cleaned photos: `stream/media/post-<issue-number>/<content-hash>.jpg` or `.png`.
- Public post: `https://fieldlight.com/stream/posts/post-<issue-number>/`.
- Everything feeds: `https://fieldlight.com/stream/feed.xml` and `https://fieldlight.com/stream/feed.json`.
- Publications feeds: `https://fieldlight.com/feed.xml` and `https://fieldlight.com/feed.json`.

Each record has `id`, `published_at`, `updated_at`, `body`, `images`, `source_url`, `issue_url`, `content_hash`, and an optional `title`. Each image has its repository-relative `path` and descriptive `alt` text. The hash covers the title and original post text, including attachment references, so repeated events are idempotent. The JSON feed exposes this hash as `_fieldlight_content_hash` for exact-version publication checks.

The copied images are re-encoded from pixels, removing EXIF, GPS, comments, and other embedded metadata from those copies. **This does not remove metadata from the original public GitHub attachments.** Remove sensitive metadata before uploading an original attachment.

## Publishing setup and maintenance

This pipeline uses each repository’s own GitHub Actions token. It needs no personal access token, SSH key, deploy key, or cross-repository write secret.

1. Install the issue form, publisher, tests, pinned photo dependencies, and workflow on `main` in `annimch04/public-writing`. Enable Issues and Actions. The workflow needs `contents: write` for canonical post commits and `issues: write` for its publication-status comments.
2. Install the stream generator, templates, feeds, and independent scheduled Pages workflow in `fieldlight-institute/fieldlight.com`. That workflow reads this public repository, builds the website, and deploys with its own Pages permissions. Keep the existing `fieldlight.com` custom domain and Pages configuration.
3. In this repository’s **Actions → Publish Fieldlight stream → Run workflow**, select `main`, leave the issue number empty, and keep **dry run** checked. This runs safety tests and builds the real existing website data in an isolated checkout. It creates no public test post, issue comment, commit, or remote change. An existing post issue number can be supplied to validate that post without publishing it.
4. Check the website’s independent Pages workflow and its live feeds. A source dry run validates the source processor and site build; it cannot by itself establish that Pages has deployed.

The source workflow runs only for **annimch04**, including the person rerunning a job. Each candidate’s current body, author, and last editor are fetched together; another collaborator’s edit cannot be published by a later owner-triggered reconciliation. Only the owner’s form posts are accepted, and failure comments go only to the owner’s issues.

Runs are serialized. Each run reconciles owner-authored post issues, including closed ones, because GitHub can replace a pending run when another submission arrives. This also recovers records whose source was saved before an interrupted or delayed website update. Validation failures are isolated per issue. The source workflow commits only canonical posts and copied media; its website checkout is read-only and is used solely to validate the build. It briefly checks the live feed after saving, then provides the exact-version status link if the scheduled deployment is still pending.

Attachments are downloaded only from approved GitHub attachment hosts with HTTPS, validated redirects, size limits, and timeouts. Arbitrary external image URLs, SVGs, unreadable files, missing photo descriptions, and malformed forms are rejected before that post is written. Post text is data and is never interpolated into a shell command. The site generator escapes it when creating HTML and feeds.

If a real error occurs, the owner receives an actionable comment or the failed Actions step explains it. Correct and save the same issue, or rerun the workflow from `main`. The workflow summary distinguishes `prepared`, `dry_run_validated`, `source_saved`, `awaiting_pages`, and `live`.

## Local verification

Use Python 3.12 in an isolated environment:

```sh
python -m pip install -r tools/requirements-stream.txt
python -m unittest discover -s tests -p 'test_publish_stream.py'
python /path/to/fieldlight.com/scripts/build-stream.py --source /path/to/public-writing --manifest /tmp/stream-manifest.json
```

The tests cover ownership and reruns, current-editor verification, form consent, stable identifiers and dates, replay idempotency, safe image hosts and redirects, HEIC conversion, orientation and metadata removal, resize limits, atomic validation failures, cross-repository write prevention, delayed deployment, and exact-version live confirmation. Test post fixtures exist only in temporary directories.
