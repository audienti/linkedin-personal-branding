# Changelog

## 0.1.0 - 2026-06-10

Architecture revision after first full run, before release — the plan is now
an expertise engine, not a posting calendar:

- **Market-operator positioning** is the explicit goal: artifacts are the
  person's real operating standards published; posts demonstrate judgment
  (thresholds, sequencing, tradeoffs, failure modes) backed by lived
  evidence. New "operator test" added to the kill-filler quality bar.
- **The offer is a first-class input** (name, URL, CTA keyword) — the
  artifact sequence is a value ladder ending one rung below it.
- **8 weekly artifacts, generated as real files** (`artifacts/week-N-*.md`),
  replace the 3 described-but-unbuilt lead magnets. Each week's 7 posts orbit
  its artifact through fixed roles: tease → drop → application → objection →
  proof → operator → activation; days 57–60 are the offer week.
- Schema/validator updated: `offer` + `weekly_artifacts` sections, per-row
  `artifact_week`/`artifact_role`, artifact-file existence checks, weekly-arc
  coverage rules, and a kill-filler heuristic warning.

Hardened against a live end-to-end run (collection through validated blueprint
on a real profile) before first release:

- `extract_profile.js` detects LinkedIn's new React profile shell
  (`main#workspace`, hashed classes) and signals page-text fallback.
- `extract_activity.js` parses named reaction buttons ("Jane Doe and 6
  others") and strips query strings from captured links.
- `extract_comments.js` captures `comment_author` so other people's thread
  replies can be filtered out.
- Collection guide: JS-evaluation time limits, chunked exports, data-loss
  filter avoidance, DOM-variant map, and comment-truncation handling.

### Initial release

- Initial release, ported from Audienti v10's `linkedin_blueprint_report` agent
  skill with the `linkedin_strategy_review_report` deterministic activity
  metrics folded in as evidence.
- Browser-based collection through the user's own logged-in session (Claude in
  Chrome, chrome-devtools MCP, or any JS-capable browser automation) — replaces
  the Harvest API dependency. Bundled DOM extractors with accumulate-across-
  scroll caching and snowflake-id timestamp decoding.
- Deterministic metrics port (`compute_metrics.py`): cadence, schedule, content
  mix, campaign signals, engagement, hook/proof comparative performance.
- Five-dimension authority scoring rubric, findings tags, post taxonomy, and
  60-day post system carried over from v10 references.
- Deliverable kit: `report.md`, `content-plan.md`, 60 ready-to-paste post
  files, `evidence.json`, `metrics.json`, and schema-validated
  `blueprint.json` (`validate_blueprint.py`).
- Read-only toward LinkedIn in v1: no posting, editing, or messaging.
