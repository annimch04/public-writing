#!/usr/bin/env node

import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

function parseArgs(argv) {
  const values = {
    username: "SayitSalty",
    cursor: "",
    cutoff: "",
    output: "",
    maxScrolls: 80,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--username") values.username = argv[++index];
    else if (value === "--cursor") values.cursor = argv[++index];
    else if (value === "--cutoff") values.cutoff = argv[++index];
    else if (value === "--output") values.output = argv[++index];
    else if (value === "--max-scrolls") values.maxScrolls = Number(argv[++index]);
    else throw new Error(`Unknown argument: ${value}`);
  }
  return values;
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function normalizeText(value) {
  return String(value || "").replace(/\u00a0/g, " ").trim();
}

function postKind({ socialContext, replyContext, statusLinks, username }) {
  if (/reposted/i.test(socialContext)) return "retweet";
  if (replyContext) {
    return replyContext.toLowerCase().includes(`@${username.toLowerCase()}`)
      ? "self_thread_reply"
      : "reply";
  }
  return statusLinks.length > 1 ? "quote" : "original";
}

function canonicalize(post, username) {
  const created = new Date(post.datetime);
  if (!post.id || Number.isNaN(created.getTime())) return null;

  const kind = postKind({
    socialContext: post.socialContext,
    replyContext: post.replyContext,
    statusLinks: post.statusLinks,
    username,
  });
  const quoted = post.statusLinks.find(
    (item) => item.id !== post.id && item.username.toLowerCase() !== username.toLowerCase(),
  );

  return {
    id: post.id,
    created_at: post.datetime,
    created_at_utc: created.toISOString(),
    year: String(created.getUTCFullYear()),
    kind,
    text: normalizeText(post.text),
    tweet_url: `https://x.com/${username}/status/${post.id}`,
    in_reply_to_status_id: null,
    in_reply_to_screen_name: post.replyContext || null,
    quoted_status_id: quoted?.id || null,
    urls: [],
    media: post.media,
    review_status: "pending",
    canonical_status: "archive_fragment_not_canon",
  };
}

async function runAppleScript(script, args = []) {
  try {
    const { stdout } = await execFileAsync("osascript", ["-e", script, ...args], {
      maxBuffer: 16 * 1024 * 1024,
    });
    return stdout.trim();
  } catch (error) {
    const detail = String(error.stderr || error.message || error);
    if (detail.includes("Allow JavaScript from Apple Events")) {
      throw new Error(
        "Safari blocks local page automation. In Safari Settings, enable Developer > " +
          "Allow JavaScript from Apple Events, then run the scraper again.",
      );
    }
    throw new Error(`Safari automation failed: ${detail.trim()}`);
  }
}

async function prepareProfileTab(username) {
  const target = `https://x.com/${username}/with_replies`;
  const script = `
on run argv
  set accountNeedle to item 1 of argv
  set targetURL to item 2 of argv
  tell application "Safari"
    activate
    repeat with browserWindow in windows
      repeat with browserTab in tabs of browserWindow
        set tabURL to URL of browserTab
        if tabURL contains accountNeedle then
          set URL of browserTab to targetURL
          set current tab of browserWindow to browserTab
          set index of browserWindow to 1
          return targetURL
        end if
      end repeat
    end repeat
    if (count of windows) is 0 then make new document
    set URL of current tab of front window to targetURL
    return targetURL
  end tell
end run`;
  await runAppleScript(script, [`x.com/${username}`, target]);
}

async function safariEvaluate(username, javascript) {
  const script = `
on run argv
  set accountNeedle to item 1 of argv
  set javascriptSource to item 2 of argv
  tell application "Safari"
    repeat with browserWindow in windows
      repeat with browserTab in tabs of browserWindow
        set tabURL to URL of browserTab
        if tabURL contains accountNeedle then
          return do JavaScript javascriptSource in browserTab
        end if
      end repeat
    end repeat
  end tell
  error "No trusted Safari tab is open for " & accountNeedle
end run`;
  return runAppleScript(script, [`x.com/${username}`, javascript]);
}

function extractionScript(username) {
  return `(() => {
    const account = ${JSON.stringify(username)};
    const clean = (value) => String(value || "").replace(/\\u00a0/g, " ").trim();
    const ownPattern = new RegExp("/" + account + "/status/(\\\\d+)", "i");
    const statusPattern = /\\/([^/]+)\\/status\\/(\\d+)/i;
    const posts = [...document.querySelectorAll('article[data-testid="tweet"]')].flatMap((article) => {
      const anchors = [...article.querySelectorAll('a[href*="/status/"]')];
      const ownAnchor =
        anchors.find((anchor) => anchor.querySelector("time") && ownPattern.test(anchor.getAttribute("href") || "")) ||
        anchors.find((anchor) => ownPattern.test(anchor.getAttribute("href") || ""));
      if (!ownAnchor) return [];

      const ownMatch = (ownAnchor.getAttribute("href") || "").match(ownPattern);
      if (!ownMatch) return [];

      const statusLinks = anchors
        .map((anchor) => (anchor.getAttribute("href") || "").match(statusPattern))
        .filter(Boolean)
        .map((match) => ({ username: match[1], id: match[2] }))
        .filter((item, index, items) =>
          items.findIndex((candidate) => candidate.username === item.username && candidate.id === item.id) === index
        );
      const textNode = article.querySelector('[data-testid="tweetText"]');
      const timeNode = ownAnchor.querySelector("time") || article.querySelector("time");
      const socialNode = article.querySelector('[data-testid="socialContext"]');
      const articleText = clean(article.innerText);
      const replyMatch = articleText.match(/Replying to\\s+([^\\n]+)/i);
      const media = [...article.querySelectorAll('[data-testid="tweetPhoto"] img, video[poster]')]
        .map((node) => ({
          type: node.tagName.toLowerCase() === "video" ? "video" : "photo",
          media_url: node.getAttribute("src") || node.getAttribute("poster"),
          alt_text: node.getAttribute("alt") || null,
        }));

      return [{
        id: ownMatch[1],
        datetime: timeNode?.getAttribute("datetime") || null,
        text: clean(textNode?.innerText),
        socialContext: clean(socialNode?.innerText),
        replyContext: replyMatch ? clean(replyMatch[1]) : "",
        statusLinks,
        media,
      }];
    });
    return JSON.stringify({
      ready: document.querySelectorAll('article[data-testid="tweet"]').length > 0,
      loginRequired: Boolean(document.querySelector('a[href="/login"]')),
      temporarilyLimited: /temporarily limited|rate limit|try again later/i.test(document.body.innerText),
      posts,
    });
  })()`;
}

async function scrape(options) {
  if (!options.cursor) throw new Error("--cursor is required.");
  if (!options.cutoff || Number.isNaN(new Date(options.cutoff).getTime())) {
    throw new Error("--cutoff must be a valid date.");
  }
  if (!options.output) throw new Error("--output is required.");

  await prepareProfileTab(options.username);
  await sleep(5000);

  const found = new Map();
  const cutoffTime = new Date(options.cutoff).getTime();
  let cursorSeen = false;
  let cutoffReached = false;
  let unchangedRounds = 0;
  let previousSize = 0;
  let scrolls = 0;

  for (; scrolls < options.maxScrolls; scrolls += 1) {
    const raw = await safariEvaluate(options.username, extractionScript(options.username));
    const observation = JSON.parse(raw || "{}");
    if (observation.loginRequired && !observation.ready) {
      throw new Error(
        "The trusted Safari tab is not signed in to X. Do not retry while X has a temporary login limit.",
      );
    }
    if (observation.temporarilyLimited && !observation.ready) {
      throw new Error(
        "X is temporarily limiting this Safari session. No review bundle was written; wait before retrying.",
      );
    }
    for (const post of observation.posts || []) {
      found.set(post.id, post);
      if (post.id === options.cursor) cursorSeen = true;
    }
    const postsAtOrBeforeCutoff = [...found.values()].filter((post) => {
      const timestamp = new Date(post.datetime).getTime();
      return Number.isFinite(timestamp) && timestamp <= cutoffTime;
    });
    // X can omit an individual post from profile pagination. Multiple older
    // authored posts prove that the scraper crossed the saved time boundary.
    cutoffReached = postsAtOrBeforeCutoff.length >= 3;
    if (cursorSeen || cutoffReached) break;

    unchangedRounds = found.size === previousSize ? unchangedRounds + 1 : 0;
    previousSize = found.size;
    if (unchangedRounds >= 5) break;

    await safariEvaluate(
      options.username,
      "window.scrollBy(0, Math.max(window.innerHeight * 0.85, 800)); 'ok'",
    );
    await sleep(1300);
  }

  if (!cursorSeen && !cutoffReached) {
    throw new Error(
      `The scraper stopped after ${scrolls} scrolls without crossing the saved archive boundary. ` +
        "No partial review bundle was written. Retry later or increase --max-scrolls.",
    );
  }

  const records = [...found.values()]
    .filter((post) => BigInt(post.id) > BigInt(options.cursor))
    .map((post) => canonicalize(post, options.username))
    .filter(Boolean)
    .sort((left, right) => left.created_at_utc.localeCompare(right.created_at_utc));

  const payload = {
    schema_version: 1,
    source: {
      adapter: "trusted_safari_public_profile_scraper",
      account_username: options.username,
      collected_at_utc: new Date().toISOString(),
      since_id: options.cursor,
      cutoff_at_utc: new Date(cutoffTime).toISOString(),
      cursor_seen: cursorSeen,
      cutoff_reached: cutoffReached,
      scrolls,
      public_posts_observed: found.size,
      private_surfaces_requested: false,
      cookies_exported: false,
    },
    posts: records,
  };
  await fs.mkdir(path.dirname(path.resolve(options.output)), { recursive: true });
  await fs.writeFile(options.output, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify(payload.source, null, 2)}\n`);
}

const options = parseArgs(process.argv.slice(2));
await scrape(options);
