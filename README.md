# LinkedIn Personal Branding

Codex and Claude Code plugin that reviews a LinkedIn profile through **your own
logged-in browser** and produces a complete personal branding kit — no
third-party scraping APIs.

## What it produces

One run yields `linkedin-review/<username>-<date>/`:

| File | Contents |
| --- | --- |
| `report.md` | Authority score (5-dimension rubric), what's working, revenue leaks, activity review, strategy, full profile rewrite (3 headline variants + bio), the offer ladder |
| `artifacts/week-1…8-*.md` | **Eight generated value assets** — real tools, templates, audits, and playbooks extracted from your method, one shipped per week |
| `content-plan.md` | 60-day campaign overview: weekly artifact promotion arcs, 8-week ladder to your offer |
| `posts/day-01.md` … `day-60.md` | Ready-to-paste posts, one per day, each extracting a threshold/check/formula from its week's artifact, written in your observed voice |
| `evidence.json` | Everything collected: profile, posts, comments, website |
| `metrics.json` | Deterministic activity metrics (cadence, schedule, content mix, engagement) |
| `blueprint.json` | The full machine-readable deliverable, schema-validated |

## How it works

1. **Collect** — drives your browser (Claude in Chrome, chrome-devtools MCP, or
   any JS-capable browser automation) to read your profile, recent posts,
   comments, and website using your existing LinkedIn session. Bundled
   extraction scripts handle the DOM; the agent verifies and fills gaps.
2. **Measure** — `compute_metrics.py` turns the raw activity into deterministic
   facts: posts/week, posting schedule, content mix, hook and proof
   performance.
3. **Score** — a five-dimension authority rubric (profile optimization, content
   presence, outbound systems, inbound infrastructure, social proof), weighted
   to a 100-point score, every score backed by quoted evidence.
4. **Rewrite** — three headline variants, a rewritten About section in your
   voice, featured-section and banner recommendations, and a voice & style
   guide.
5. **Build** — designs a value ladder to your offer and **generates eight
   real artifacts** (tools, templates, audits, playbooks) from your actual
   method — one per week, each a publishable asset on its own.
6. **Plan** — a 60-day campaign where each week's posts orbit that week's
   artifact (tease → drop → application → objection → proof → operator →
   activation), every post passing a five-test kill-filler bar that enforces
   market-operator positioning: judgment shown, lived evidence, no generic
   commentary. Validated end-to-end by `validate_blueprint.py`.

**Read-only by design (v1):** it never posts, edits, likes, connects, or
messages on LinkedIn. Publishing the plan is yours to do.

## Requirements

- A browser automation tool connected to your real browser with LinkedIn
  logged in:
  - Claude Code: [Claude in Chrome](https://www.anthropic.com/chrome) or a
    chrome-devtools MCP server
  - Codex: a chrome-devtools or Playwright MCP server attached to your Chrome
    profile
- `python3` (stdlib only — no packages to install)

## Usage

> Review my LinkedIn profile and build my personal branding blueprint.

> Run a LinkedIn personal branding review for https://www.linkedin.com/in/someone/ — my ICP is bootstrapped B2B SaaS founders.

> Build my 60-day LinkedIn content plan from my profile and recent posts.

Providing your target ICP (who you sell to) materially improves the strategy,
rewrite, and plan. The skill will ask once if you don't volunteer it.

## Repository layout

```text
.claude-plugin/plugin.json
.codex-plugin/plugin.json
skills/linkedin-personal-branding/SKILL.md
skills/linkedin-personal-branding/references/scoring-rubric.md
skills/linkedin-personal-branding/references/post-taxonomy.md
skills/linkedin-personal-branding/references/post-system.md
skills/linkedin-personal-branding/references/artifact-system.md
skills/linkedin-personal-branding/references/collection-guide.md
skills/linkedin-personal-branding/references/report-format.md
skills/linkedin-personal-branding/scripts/extract_profile.js
skills/linkedin-personal-branding/scripts/extract_activity.js
skills/linkedin-personal-branding/scripts/extract_comments.js
skills/linkedin-personal-branding/scripts/compute_metrics.py
skills/linkedin-personal-branding/scripts/validate_blueprint.py
skills/linkedin-personal-branding/assets/blueprint-schema.json
skills/linkedin-personal-branding/assets/example-evidence.json
```

## Marketplace metadata

```json
{
  "name": "linkedin-personal-branding",
  "source": {
    "source": "url",
    "url": "https://github.com/audienti/linkedin-personal-branding.git"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Marketing"
}
```

## Validation

```bash
python3 skills/linkedin-personal-branding/scripts/compute_metrics.py skills/linkedin-personal-branding/assets/example-evidence.json
node --check skills/linkedin-personal-branding/scripts/extract_profile.js
node --check skills/linkedin-personal-branding/scripts/extract_activity.js
node --check skills/linkedin-personal-branding/scripts/extract_comments.js
```

(`compute_metrics.py` writes a `metrics.json` next to the evidence file; safe
to delete.)

## Privacy & conduct

- Uses only your own logged-in session and views only what it can already view.
- Human pacing and scroll caps during collection; stops immediately on any
  LinkedIn checkpoint.
- Everything collected stays in local files in the output directory.

## Roadmap

- Corporate companion plugin: brand content plan (ICP + offer → 60-day,
  multi-format campaign).
- Apply/publish automation (profile rewrite application, post scheduling) as
  an explicit opt-in follow-up.
