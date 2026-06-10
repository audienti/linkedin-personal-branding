# LinkedIn Collection Guide

How to collect profile and activity evidence through the user's own logged-in
browser. No third-party scraping API (Harvest, Unipile, etc.) is used or needed.

## Browser tooling

Use whichever browser automation is connected in this session, in order of
preference:

1. **Claude in Chrome** (`navigate`, `javascript_tool`, `get_page_text`, `read_page`)
2. **chrome-devtools MCP** (`new_page`/`navigate_page`, `evaluate_script`, `take_snapshot`)
3. **Playwright MCP or similar** — anything that can navigate, scroll, and
   evaluate JavaScript in the page works.

If no browser automation is available, stop and tell the user what to connect
(Claude in Chrome extension, or a chrome-devtools/playwright MCP server pointed
at their real Chrome profile). Do not fall back to fetching LinkedIn over HTTP —
logged-out fetches get walled and violate the design of this skill.

### Running the extraction scripts

Each extractor in `scripts/` is a single **arrow function expression** —
`() => { ... }` — that returns a JSON string.

- **chrome-devtools MCP**: pass the file contents as the `function` argument of
  `evaluate_script`, unmodified.
- **Claude in Chrome / raw JS eval tools**: wrap the file contents in an
  invocation: `(<file contents>)()` and evaluate that expression.

The result is a JSON string. Parse it, sanity-check it (see below), and write
the data into `evidence.json` yourself. The scripts never touch disk.

### Tool limits learned from live runs

- **Keep each JS evaluation under ~30 seconds.** Browser tools time out
  (Claude in Chrome's CDP call dies at 45s) and long scroll loops can wedge
  the renderer. Do 3–4 scroll steps per call, return, call again. Install
  heavy logic once on `window` (e.g. `window.__lipbCapture = () => {...}`)
  and keep subsequent calls tiny.
- **Tool results truncate.** Claude in Chrome displays roughly 1.5KB of a JS
  result. Export collected data in chunks (2–4 items per call via
  `JSON.stringify(items.slice(a, b))`) rather than one big dump.
- **Data-loss filters can block exports.** Returning URLs with query strings
  can trigger a `[BLOCKED: Cookie/query string data]` response. The bundled
  extractors strip query strings from captured links; do the same in any
  ad-hoc export expression.
- **Promises are awaited.** An async IIFE as the final expression works (the
  tool awaits it); the bare `await` keyword at the top level may not.

### LinkedIn DOM variants (as of mid-2026)

LinkedIn is mid-migration. Expect both DOMs and plan per page type:

- **Profile page and contact-info overlay**: many accounts get a new React
  shell — `main#workspace` is the scroll container, CSS classes are hashed,
  and there are no `h1`/`#about`/`#experience` anchors. `extract_profile.js`
  detects this and returns `{"new_dom": true}`. Fall back to reading the page
  text (it contains the full top card) plus
  `/in/<username>/details/experience/` for the experience history — both read
  cleanly as text.
- **recent-activity pages (posts and comments)**: still the legacy DOM
  (`feed-shared-update-v2[data-urn]`, `comments-comment-entity`) — the
  bundled extractors work there.
- **An absent About/Featured section is a finding, not a DOM miss** — verify
  by reading the page text before recording it as missing.

### Session check

Before collecting, navigate to `https://www.linkedin.com/feed/` and confirm the
user is logged in (the feed renders rather than a sign-in wall). If a sign-in
page appears, stop and ask the user to log into LinkedIn in that browser first.

## Conduct rules

- Read-only. Never like, follow, connect, comment, post, or message. Never
  navigate to URLs that perform actions.
- Only view what the user's session can already view normally.
- Human pacing: wait 1–2 seconds between scrolls and navigations. Do not
  hammer the page.
- Caps: stop scrolling after ~30 rounds per page even if the window is not
  fully covered, and record the truncation in `collection_notes`.
- Everything collected stays in local files in the output directory.

## Step 1: Profile page

Navigate to the profile, e.g. `https://www.linkedin.com/in/<username>/`.
If the user said "me" / "my profile", navigate to
`https://www.linkedin.com/in/me/` and capture the URL it redirects to — that
reveals the real username for all later URLs.

Scroll down the page two or three times so lazy sections (About, Experience,
Featured) mount, then run `scripts/extract_profile.js`.

The script returns `profile` fields plus a `warnings` array naming anything it
could not find. For each warned field, look at the page yourself
(`get_page_text` / snapshot) and fill the gap manually if the content is
visible. LinkedIn's DOM drifts; the script is an accelerator, not an oracle —
you are responsible for the final data quality.

## Step 2: Contact info and website

Navigate to `https://www.linkedin.com/in/<username>/overlay/contact-info/` and
run `scripts/extract_profile.js` again — when the contact overlay is open it
also returns a `contact` object (websites, email if visible). Merge the
websites into the profile's `website_url` (first non-LinkedIn website wins
unless the user specified one).

## Step 3: Posts (recent activity)

Navigate to `https://www.linkedin.com/in/<username>/recent-activity/all/`.

Loop:

1. Run `scripts/extract_activity.js`. It returns
   `{count, new_count, oldest_occurred_at, items}`.
2. If `oldest_occurred_at` is older than the analysis window start, or
   `new_count` was 0 twice in a row, or you hit the scroll cap — stop.
3. Otherwise scroll to the bottom of the page (e.g. `window.scrollTo(0,
   document.body.scrollHeight)`), wait 1.5–2 seconds, and repeat.

The extractor **accumulates across runs** in `window.__lipbActivityCache`,
keyed by post URN, because LinkedIn unmounts off-screen feed items as you
scroll. The final run's `items` is the merged set — use that.

The All tab can surface non-authored activity (reactions, comment stubs). Each
item carries a `kind`: keep `post` and `repost` items as `evidence.posts` and
drop `other` (comments are collected properly in the next step).

Timestamps: LinkedIn post URNs encode creation time (`id >> 22` = epoch ms),
so `occurred_at` is exact even though the page shows only "3w". The relative
label is kept as `relative_time` for cross-checking.

Reaction/comment/repost counts come from the social counts bar of each post.
Spot-check 2–3 posts against what you can see on the page before trusting the
whole set.

## Step 4: Comments

Navigate to `https://www.linkedin.com/in/<username>/recent-activity/comments/`
and run the same loop with `scripts/extract_comments.js` (cache:
`window.__lipbCommentCache`). Items are the user's comments on other people's
posts: text, timestamp, the post's author, and post URL.

Two caveats from live runs:

- Threads include **replies from other people**. Each item carries a
  `comment_author` — drop items whose author is not the profile owner.
- Heavy commenters (several per day) make full window coverage impractical:
  "Show more" pagination can stop hydrating after a few pages (empty
  occludable shells with stuck spinners). Accept the covered span, record
  `comments_truncated: true` with the oldest covered date in
  `collection_notes`, and report comment cadence over the covered span — the
  90-day per-week division would understate a truncated sample. (v10 accepted
  the same tradeoff with a 2-page Harvest cap.)

Comment timestamps fall back to relative-time parsing ("3w" ≈ 21 days) when no
URN-encoded id is found; that approximation is fine for cadence metrics.

## Step 5: Website evidence

If a website URL was found (or provided), fetch its homepage — via the browser
(navigate + `get_page_text`) or `curl -L` if the site is public. Capture into
`evidence.website`:

- `url`
- `markdown_excerpt`: readable text content, first ~6,000 characters
- `links`: up to 40 `{url, label}` pairs from the page
- `booking_links`: links whose URL or label matches
  `book|demo|call|consult|contact|schedule|calendly` (case-insensitive), max 6
- `resource_links`: links matching
  `guide|template|checklist|audit|framework|resource|newsletter|ebook|playbook|pdf|tool`, max 8
- `proof_snippets`: lines from the page text matching
  `\b(\d+[%x+]|clients?|customers?|case study|results?|revenue|pipeline|wins?|followers?|connections?)\b`
  (case-insensitive), deduplicated, max 8

If there is no website, set `website` to
`{"url": null, "markdown_excerpt": null, "links": [], "booking_links": [], "resource_links": [], "proof_snippets": []}`
— the inbound-infrastructure score will reflect that honestly.

## Step 6: Assemble evidence.json

Write one file matching `assets/example-evidence.json`:

- `collected_at` (ISO 8601, with timezone), `analysis_window_days`,
  `linkedin_url`, `username`
- `profile` from steps 1–2
- `posts`, `comments` from steps 3–4 (keep items inside the window plus a small
  margin; `compute_metrics.py` applies the exact window cut)
- `website` from step 5
- `target_icp`: `{"description": "..."}` plus any structured details the user
  gave (role, company size, pains, jobs to be done), or `null`
- `collection_notes`: method used, scroll rounds, truncation flags, oldest
  timestamps seen, and any fields you filled manually

## Fallbacks

- **Extractor returns almost nothing**: the DOM changed. Read the page directly
  (`get_page_text` / snapshot), extract the same fields by hand into
  `evidence.json`, and note `"method": "manual"` in `collection_notes`.
- **Profile has no activity**: proceed — metrics will be zeros, the review says
  so honestly, and the content plan becomes the person's restart plan.
- **Numbers like "1.2K"**: extractors convert K/M suffixes; if you extract by
  hand, convert to integers (1.2K → 1200).
- **Private/inaccessible profile**: report it to the user; do not try to work
  around access controls.
