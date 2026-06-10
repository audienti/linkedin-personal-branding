---
name: linkedin-personal-branding
description: >
  Review a LinkedIn profile through the user's own logged-in browser and build an
  evidence-backed personal branding blueprint that establishes the person as a market
  operator (a recognized expert): authority scores, findings, activity review,
  strategy, a full profile rewrite, eight generated value artifacts laddering to the
  person's offer, and a 60-day content plan with ready-to-paste posts. Use when the
  user says "review my LinkedIn", "LinkedIn review", "LinkedIn profile audit", "audit
  my LinkedIn", "personal branding review", "authority blueprint", "LinkedIn content
  plan", "60-day LinkedIn plan", or asks to analyze a LinkedIn profile and plan
  content for it. Read-only toward LinkedIn: never posts, edits, likes, connects, or
  messages.
---

# LinkedIn Personal Branding Blueprint

Turn a LinkedIn profile plus its recent activity into a complete personal
branding kit. All collection happens through the user's own logged-in browser
session — no Harvest, Unipile, or any third-party scraping API.

## Core invariants

1. **Evidence before judgment.** Collect profile, posts, comments, and website
   first. Never invent activity, metrics, clients, or outcomes that are not in
   the evidence.
2. **Deterministic metrics are facts.** `compute_metrics.py` output is the
   source of truth for cadence, mix, and engagement. Never contradict it; quote
   it.
3. **Read-only toward LinkedIn.** Navigate, scroll, and read. Never like,
   follow, connect, comment, post, message, or edit anything (v1 scope).
4. **Rubric before prose.** Scores come from `references/scoring-rubric.md`
   criteria applied to evidence, with confidence levels — not vibes.
5. **Stable taxonomy only.** Classify observed and generated posts with the
   labels in `references/post-taxonomy.md`. No invented labels.
6. **Exact deliverable counts.** 3 headline variants, 8 weekly artifacts
   (generated as real files), 60 content-plan rows. `validate_blueprint.py`
   must pass before close-out.
7. **Thin evidence is stated, not papered over.** Few posts or no website means
   lower confidence scores and an honest note, with the plan adjusted to a
   restart posture.
8. **Files are the deliverable.** Write progressively; a crash should leave
   usable partial output.
9. **All killer, no filler — operator positioning is the goal.** The plan
   exists to establish the person as a market operator: an expert who runs
   the motions they talk about and ships useful things. Every post must pass
   the five kill-filler tests in `references/artifact-system.md` (extract,
   forward, strip, conversation, operator). Posts demonstrate judgment —
   thresholds, sequencing calls, tradeoffs, failure modes — backed by the
   person's lived evidence, and are excerpts of that week's artifact, not
   standalone musings. Artifacts are the person's real operating assets
   published, never "lead magnets." A post that merely sounds good is a
   defect.
10. **Everything ladders to the offer.** The artifact sequence is a value
    ladder ending one rung below the offer. No artifact may be hollow bait;
    each delivers fully and bridges honestly.

## Requirements

- A browser automation tool connected to the user's real browser with a
  logged-in LinkedIn session (Claude in Chrome, chrome-devtools MCP, Playwright
  MCP, or equivalent). If none is available, stop and tell the user what to
  connect.
- `python3` for `scripts/compute_metrics.py` and `scripts/validate_blueprint.py`.

## Outcome

One directory, `linkedin-review/<username>-<YYYYMMDD>/`, containing
`evidence.json`, `metrics.json`, `blueprint.json`, `report.md`,
`content-plan.md`, `artifacts/week-1-<slug>.md` … `week-8-<slug>.md` (the
eight generated value assets), and `posts/day-01.md` … `posts/day-60.md` —
per `references/report-format.md`.

## Workflow

### Step 0: Inputs

Establish, asking only for what's missing:

- **Profile**: a LinkedIn URL, or "me" (resolve via
  `https://www.linkedin.com/in/me/` redirect). Reviewing someone else's public
  profile is fine — the user's session just needs to be able to view it.
- **Target ICP** (optional, strongly improves output): who the person sells to
  or wants to reach — role, company type, pains, jobs to be done. One or two
  sentences from the user is enough. If the user declines, infer the audience
  from evidence and proceed.
- **The offer** (required before Step 6): what the person is ultimately moving
  readers toward — the product, the call, the engagement. Capture `name`,
  `primary_url`, a `cta_keyword` for DM/comment plays, and a one-line
  description. Propose it from the website evidence (booking links, product
  pages) and confirm with the user in the same question as the ICP. The whole
  plan ladders to this; without it the plan is content for content's sake.
- **Website** (optional): override or confirm later auto-discovery.
- **Analysis window**: default 90 days.

### Step 1: Workspace and resume check

Create `linkedin-review/<username>-<YYYYMMDD>/` (and `posts/` inside it).

If an output directory for this username already has an `evidence.json` less
than a day old, offer to reuse it and skip to Step 3 — useful when iterating on
synthesis.

### Step 2: Collect evidence

Follow `references/collection-guide.md` exactly. In short:

1. Verify the session is logged in (`linkedin.com/feed/` renders).
2. Profile page → scroll → run `scripts/extract_profile.js` → fill gaps
   manually for any `warnings`.
3. Contact-info overlay → same script → website URL.
4. `/recent-activity/all/` → scroll loop with `scripts/extract_activity.js`
   (accumulates across runs) until the window is covered or capped. Keep items
   with `kind` `post` or `repost` as `evidence.posts`.
5. `/recent-activity/comments/` → same loop with `scripts/extract_comments.js`
   → `evidence.comments`.
6. Fetch the website homepage; build `booking_links`, `resource_links`,
   `proof_snippets` per the guide.
7. Assemble and write `evidence.json` matching
   `assets/example-evidence.json`, including `collection_notes` (method,
   truncation, anything filled manually).

Sanity-check before moving on: does the post count roughly match what the
activity page shows? Do 2–3 spot-checked posts have the right text and counts?
If extraction looks broken, fall back to manual page reading per the guide —
do not proceed with silently bad data.

### Step 3: Compute metrics

```
python3 <skill-dir>/scripts/compute_metrics.py <output-dir>
```

Read `metrics.json`. These numbers are now facts. If `post_count` is 0, say so
to the user and continue — scores and the plan will reflect a restart.

### Step 4: Review synthesis (report.md, part 1)

Work as four layers: observable evidence → rubric scores → strategic synthesis
→ content generation. Read `references/scoring-rubric.md` and
`references/post-taxonomy.md` before scoring. Then write the first half of
`report.md` (structure in `references/report-format.md`):

1. **Scores.** Score the five dimensions with subscores, confidence, and
   concrete evidence bullets (quote actual headline text, post lines, website
   copy). Compute the weighted authority score per the rubric.
2. **Findings.** `whats_working` and `revenue_leaks` items using the rubric's
   tags, each grounded in a specific observation. End with a bottom line.
3. **Activity review.** Classify every authored post in the window with exactly
   one archetype, one primary goal, and one CTA type (taxonomy labels only;
   distributions over authored posts, not comments). Surface themes, tone
   patterns, hook patterns, proof patterns — each with an evidence count. Use
   `metrics.engagement` to explain which hook/proof styles actually earned
   comments and reactions, and `metrics.content_mix` for repost/duplicate
   observations. If the sample is thin, say so directly.
4. **Strategy.** Buyer persona (from `target_icp` when provided — ground it in
   the ICP's roles, responsibilities, and jobs to be done; otherwise infer),
   strategic gap, strategic opportunity, fit score with honest assessment — if
   the profile is a poor fit for the selected ICP, say so clearly — and 3–6
   next steps.

### Step 5: Profile rewrite (report.md, part 2)

Produce, per the rubric's rewrite constraints:

- 3 headline variants: A outcome, B authority, C hybrid — then recommend one
  with a reason.
- Recommended bio following the 8-part structure, written in the person's
  observed voice, using only real proof from evidence.
- Profile analysis and full profile rewrite notes: banner, featured section
  (use the lead magnets from Step 6 once defined), experience bullets.
- Voice & style guide derived from their strongest observed posts: tone,
  structure habits, CTA habits, proof usage, avoid-list. This guide governs
  every post generated in Step 7.
- Improvement suggestions checklist.

### Step 6: Design and GENERATE the 8 weekly artifacts

Per `references/artifact-system.md`. Design the value ladder first: 8
artifacts mapped to the campaign arc (Reposition → Prove → Productize →
Activate), each a different type where possible, each ending in an honest
`offer_bridge`, the last one sitting one rung below the offer. Reuse assets
that already exist (check `website.resource_links`) — packaging an existing
calculator beats describing a hypothetical one.

Then **write each artifact as a real file**: `artifacts/week-N-<slug>.md`.
This is the core of the deliverable — opinionated thresholds, complete
checks, worked examples, fill-in templates with example entries. An artifact
the ICP can't use within 30 minutes of receiving it fails the bar. Claims
must be evidence-grounded; composite examples labeled as composites; anything
needing the user's real data gets flagged in the artifact header.

Summarize each in report.md (type, ladder rung, what's inside, offer bridge,
drop day, keyword).

### Step 7: 60-day content plan

Follow `references/post-system.md`: 8 weekly promotion arcs around the
artifacts (tease → drop → application → objection → proof → operator →
activation), the archetype mapping and mix, CTA discipline, and days 57–60
as the offer week.

Generate week by week, artifact first, then that week's posts — **every post
extracts something specific from its artifact**: a check, a threshold, a
formula, a template field, a failure mode. Run each post through the four
kill-filler tests (extract, forward, strip, conversation) before marking it
`post_ready`; a post that fails gets rewritten from a sharper piece of the
artifact, not padded. For each day write `posts/day-NN.md` (format in
`references/report-format.md`) with full post copy — the first line is the
hook. Posts that need user-supplied proof get `proof_required` entries,
`review_status: "needs_review"`, and `post_ready: false` — never an invented
number. Maintain `content-plan.md` (overview table) as you go.

Pace yourself across batches: week 7 posts deserve the same specificity as
week 1 posts. Vary hooks — no reused openers, no more than 2 consecutive
posts of the same archetype.

### Step 8: Assemble and validate blueprint.json

Write `blueprint.json` covering every section of
`assets/blueprint-schema.json` (meta, offer, observed_profile, scores,
findings, activity_review, strategy, rewrite, weekly_artifacts, content_plan
— consistent with the markdown files). Then:

```
python3 <skill-dir>/scripts/validate_blueprint.py <output-dir>
```

Fix every ERROR and re-run until exit 0. Review warnings deliberately: fix the
cheap ones (hook reuse, mix drift), and surface any you accept to the user
with a reason.

### Step 9: Close-out

Tell the user, briefly:

- Authority score with the one-sentence bottom line
- Top 3 revenue leaks
- The recommended headline
- The 8 weekly artifacts (one line each) and the offer they ladder to
- Where everything lives, and that posts marked `needs_review` are waiting on
  proof points only they can supply
- What this skill deliberately did NOT do: post, edit, or schedule anything on
  LinkedIn. Applying the rewrite and publishing the plan is theirs to do (or a
  future version's).

## Safety boundaries

- Use only the user's own logged-in session, viewing only what it can already
  view. No credential handling, no access workarounds, no logged-out scraping.
- Read-only on LinkedIn — no clicks that produce side effects (react, follow,
  connect, subscribe). Navigation and scrolling only.
- Human pacing: 1–2s waits between scrolls/navigations; respect the scroll
  caps in the collection guide.
- Collected data stays in the local output directory. Don't send it anywhere.
- If LinkedIn shows a checkpoint/captcha or unusual-activity interstitial,
  stop collecting immediately and hand control back to the user.

## Failure handling

- **No browser tool**: stop after Step 0 and tell the user exactly what to
  connect; offer to proceed from a user-supplied profile export instead
  (paste/PDF) with `collection_notes.method: "manual"`.
- **Extractors return junk**: LinkedIn DOM drift — extract manually from page
  text per the collection guide, note it, continue.
- **Zero activity**: proceed honestly; content_presence is scored low with the
  evidence note, and the plan becomes the restart plan.
- **Mid-run interruption**: everything written so far is valid; rerunning
  resumes from the evidence reuse check in Step 1.
