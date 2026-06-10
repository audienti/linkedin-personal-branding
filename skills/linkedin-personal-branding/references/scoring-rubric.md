# LinkedIn Authority Scoring Rubric

## Goal

Score the profile with deterministic criteria first, then use generation only for
summary and synthesis. Where `metrics.json` provides a deterministic number
(cadence, engagement, content mix), that number is the fact — score against it,
never against an impression.

## 1. Profile Optimization

Score out of 10 using:

- headline clarity
- ICP clarity
- offer clarity
- CTA presence
- about-section structure
- proof density in profile copy
- featured section alignment
- banner support

## 2. Content Presence

Score out of 10 using:

- post recency (`metrics.summary`, newest post date in evidence)
- posting cadence (`metrics.cadence.posts_per_week`)
- topic coherence (themes across collected posts)
- originality vs genericity (duplicate-text rate, repost rate from `metrics.content_mix`)
- founder voice strength
- CTA consistency

Cadence anchors: 3+ posts/week is strong, 1–3 is workable, under 1 is weak,
zero posts in the window caps this dimension at 3.

## 3. Outbound Systems

Score out of 10 using:

- visible DM CTA
- outbound method clarity
- trust-first / conversation-led process evidence
- comment-to-DM workflow evidence (`comment_keyword`, `comment_prompt`, `dm_me` CTAs in posts)
- explicit prospecting motion
- commenting activity on others' posts (`metrics.cadence.comments_per_week`)

## 4. Inbound Infrastructure

Score out of 10 using:

- website clarity
- lead magnet presence
- booking CTA presence (website `booking_links`)
- featured section conversion quality
- opt-in / nurture evidence
- product or offer page quality

If no website was found, score from the profile alone, cap at 5, and lower confidence.

## 5. Social Proof

Score out of 10 using:

- founder/operator credibility
- customer proof
- quantified outcomes (proof snippets in profile, posts, and website)
- testimonials or screenshots
- community or audience proof (follower count relative to activity)
- visible case studies

## Authority Score

Compute as weighted sum of the five dimension scores.

Recommended starting weights:

- profile_optimization: 0.22
- content_presence: 0.22
- outbound_systems: 0.18
- inbound_infrastructure: 0.18
- social_proof: 0.20

Convert the weighted 10-point composite to a 100-point score.

Each dimension also carries:

- `confidence` (0.0–1.0): how much evidence backed the score. Thin or missing
  evidence means low confidence, stated plainly in the dimension evidence list.
- `evidence`: short concrete observations (quote or describe the actual artifact),
  never generic statements.
- `subscores`: one entry per criterion above, scored 0–10.

## Findings Tags

### `whats_working`

- `credibility_stack`
- `offer_clarity`
- `category_positioning`
- `proof_marker`
- `distribution_asset`
- `community_asset`
- `differentiated_narrative`
- `funnel_readiness`

### `revenue_leaks`

- `generic_content`
- `weak_founder_voice`
- `missing_pov`
- `invisible_social_proof`
- `poor_cta_design`
- `weak_featured_section`
- `profile_feed_mismatch`
- `content_strategy_gap`
- `proof_distribution_gap`

## Rewrite Constraints

### Headline styles

- `A`: outcome
- `B`: authority
- `C`: hybrid

### Bio structure

1. painful present state
2. why current approach fails
3. operator identity
4. product / method explanation
5. proof
6. named framework or methodology
7. CTA
8. disqualifier

## Lead Magnet Metadata

### Content types

- Template
- PDF
- Tool
- Checklist
- Guide
- Calculator
- Swipe File
- Audit
- Framework
- Workshop

## Post Review Checks

Each generated post should be reviewed for:

- unsupported metrics
- placeholders
- vague CTA
- ungrounded proof claims
- weak authority grounding
- product capability overclaims

A post that fails any check gets `review_status: "needs_review"` (or
`"needs_revision"` when the fix is known) and `post_ready: false`, with the
problem named in `items_to_verify` or `to_fix`.
