#!/usr/bin/env node
// Review-only collection of the separate public Reposts surface.
import fs from 'node:fs/promises';
import {prepareProfileTab, safariEvaluate, extractionScript, canonicalizeRepost} from './x_safari_scraper.mjs';

const output = process.argv[2];
if (!output) throw new Error('Usage: node tools/x_reposts_safari.mjs PRIVATE_OUTPUT.json');
const username = process.argv[3] || 'SayitSalty';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const found = new Map();
await prepareProfileTab(username, 'reposts');
await pause(3000);
let unchanged = 0, stop = 'scroll_budget', steps = 0;
for (; steps < 100; steps++) {
  await safariEvaluate(username, `document.querySelectorAll('[data-testid="tweet-text-show-more-link"]').forEach(x=>x.click()); 'ok'`);
  const raw = JSON.parse(await safariEvaluate(username, extractionScript(username)));
  if (!raw.ready) { stop = raw.temporarilyLimited ? 'loading_error' : 'no_rendered_posts'; break; }
  const previous = found.size;
  for (const post of raw.repostObservations) found.set(`${post.sourceUsername.toLowerCase()}:${post.id}`, post);
  unchanged = previous === found.size ? unchanged + 1 : 0;
  await fs.writeFile(output + '.partial.json', JSON.stringify({status:'incomplete_collection_not_for_publication',steps,observations:[...found.values()]},null,2));
  console.log(JSON.stringify({step:steps,observations:found.size,unchanged}));
  if (unchanged >= 6) { stop = 'no_new_cards_after_six_scrolls'; break; }
  await safariEvaluate(username, `[...document.querySelectorAll('article[data-testid="tweet"]')].at(-1)?.scrollIntoView({block:'end'}); window.scrollBy(0,500); 'ok'`);
  await pause(2200);
}
const now = new Date().toISOString();
await fs.writeFile(output, JSON.stringify({schema_version:2,source:{adapter:'trusted_safari_public_reposts_scraper',account_username:username,collected_at_utc:now,surface:'reposts',stop_reason:stop,scrolls:steps,coverage:'observed_public_cards_not_proof_of_complete_account_history',private_surfaces_requested:false,cookies_exported:false},posts:[],repost_observations:[...found.values()].map(x=>canonicalizeRepost(x,username,now)).filter(Boolean)},null,2));
console.log(JSON.stringify({output,observations:found.size,stop}));
