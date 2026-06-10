# Deliverable Kit Format

Everything lands in one output directory:
`linkedin-review/<username>-<YYYYMMDD>/`

```
evidence.json     # collected profile + posts + comments + website + ICP
metrics.json      # deterministic metrics (compute_metrics.py output)
blueprint.json    # machine-readable deliverable (validated against assets/blueprint-schema.json)
report.md         # the human review: scores, findings, activity review, strategy, rewrite, artifact ladder
content-plan.md   # 60-day plan overview
artifacts/week-1-<slug>.md … week-8-<slug>.md   # the 8 generated value assets
posts/day-01.md … posts/day-60.md   # one ready-to-paste post per day
```

`evidence.json` and `metrics.json` are inputs to the synthesis and stay exactly
as produced. `blueprint.json` is the contract for downstream automation
(posting tools, the corporate brand content plan, re-reviews). The markdown
files are for the human.

## report.md structure

```markdown
# LinkedIn Personal Branding Review — <Name>

> Generated <date> · <linkedin_url> · window: <N> days ·
> <post_count> posts / <comment_count> comments collected

## Authority Score: <NN>/100

One-paragraph scores summary.

| Dimension | Score | Confidence |
|---|---|---|
| Profile Optimization | n/10 | high/med/low |
| Content Presence | n/10 | … |
| Outbound Systems | n/10 | … |
| Inbound Infrastructure | n/10 | … |
| Social Proof | n/10 | … |

### <Each dimension>
Subscores, then 2–4 bullet evidence observations (concrete, quoted where useful).

## What's Working
One `### <title>` block per finding (tag in small text), description grounded in evidence.

## Revenue Leaks
Same shape. End with **Bottom line:** one paragraph.

## Activity Review
- Cadence and schedule facts (from metrics.json — never restate incorrectly)
- Post classification: archetype / goal / CTA distributions (top entries with %)
- Themes, tone patterns, hook patterns, proof patterns (label + evidence count + 1-line summary each)
- What earned engagement: hook/proof comparative performance, top posts with links

## Strategy
Buyer persona · strategic gap · strategic opportunity · ICP fit (score /100 + assessment, only if ICP provided) · next steps (numbered).

## Profile Rewrite
### Headlines
A (outcome): …
B (authority): …
C (hybrid): …
**Recommended: <A|B|C>** — reason.

### About (recommended bio)
The full rewritten About section, ready to paste (8-part structure per rubric).

### Full profile rewrite notes
Profile analysis paragraph, then per-section rewrite guidance (banner, featured,
experience bullets), then improvement suggestions as a checklist.

### Voice & style guide
Tone · structure habits · CTA habits · proof usage · avoid-list.

## The Offer & The Ladder
The offer (name, URL, keyword) and how the 8 artifacts ladder to it.

## Weekly Artifacts
One `### Week <n>: <title>` per artifact: type, ladder rung, what's inside
(concretely), drop day + keyword, offer bridge, and the file path in
`artifacts/`.

## 60-Day Content Plan
Pointer to content-plan.md and posts/, the weekly promotion arc being
followed, and the offer-week (days 57-60) framing.
```

## content-plan.md structure

```markdown
# 60-Day Content Plan — <Name>

Campaign arc: Weeks 1–2 Reposition · 3–4 Prove · 5–6 Productize · 7–8 Activate
Waves: lm1 = <magnet 1 headline> (weeks 3–4) · lm2 = … (weeks 5–6) · lm3 = … (weeks 7–8)

| Day | Week | Role | Archetype | Goal | CTA | Title | Ready |
|---|---|---|---|---|---|---|---|
| 1 | 1 | tease | diagnostic_framework | awareness | comment_prompt | <title> | ✅ |
…all 60 rows…
```

`Role` is the post's job in its week's artifact arc (tease/drop/application/
objection/proof/operator/activation, recap in the offer week). `Ready` is ✅
when `post_ready` is true, ⚠️ otherwise.

## posts/day-NN.md structure

```markdown
---
day: 7
week: 1
title: <title>
archetype: audience_activation
primary_goal: engagement
cta_type: comment_prompt
artifact_week: 1
artifact_role: activation
artifact: <week-1 artifact slug>
target_persona: <persona or null>
proof_required: []
review_status: ready
post_ready: true
items_to_verify: []
to_fix: []
---

<the full post exactly as it should be pasted into LinkedIn — the first line is
the hook (`first_sentence`), line breaks as they should appear>
```

The body equals `finalized_content` (which equals `post_content` once review
passes). No placeholders, no "[Your X here]", no invented numbers.

## blueprint.json

Must validate against `assets/blueprint-schema.json` via
`scripts/validate_blueprint.py` (pass the output DIRECTORY so artifact files
are checked too). Sections: `meta`, `offer`, `observed_profile`, `scores`,
`findings`, `activity_review`, `strategy`, `rewrite`, `weekly_artifacts`
(exactly 8, files must exist), `content_plan` (exactly 60 rows). The markdown
files are renderings of this object — when fixing validation errors, fix both.
