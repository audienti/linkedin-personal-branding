#!/usr/bin/env python3
"""Validate blueprint.json structure and campaign quality rules.

Usage:
    python3 validate_blueprint.py <blueprint.json | output-dir>

Exit 0 when there are no errors (warnings allowed), 1 otherwise.
Errors are structural violations that must be fixed. Warnings are quality
signals to review deliberately — fix them or accept them knowingly.

When given the output DIRECTORY (recommended), also verifies that each
weekly artifact's file exists under it.
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

DIMENSION_KEYS = [
    "profile_optimization",
    "content_presence",
    "outbound_systems",
    "inbound_infrastructure",
    "social_proof",
]
DIMENSION_WEIGHTS = {
    "profile_optimization": 0.22,
    "content_presence": 0.22,
    "outbound_systems": 0.18,
    "inbound_infrastructure": 0.18,
    "social_proof": 0.20,
}
ARCHETYPES = [
    "tactical_blueprint",
    "contrarian_pov",
    "results_case_study",
    "diagnostic_framework",
    "resource_guide",
    "audience_activation",
    "founder_story",
    "feature_announcement",
    "community_milestone",
]
RECOMMENDED_MIX = {
    "contrarian_pov": 9,
    "tactical_blueprint": 9,
    "results_case_study": 9,
    "resource_guide": 8,
    "diagnostic_framework": 8,
    "audience_activation": 7,
    "founder_story": 6,
    "feature_announcement": 2,
    "community_milestone": 2,
}
PRIMARY_GOALS = [
    "awareness",
    "category_education",
    "authority",
    "proof",
    "engagement",
    "lead_gen",
    "product_education",
    "conversion",
]
CTA_TYPES = [
    "comment_keyword",
    "comment_prompt",
    "dm_me",
    "visit_link",
    "follow_for_more",
    "repost",
    "soft_reflection",
]
ARTIFACT_ROLES = ["tease", "drop", "application", "objection", "proof", "operator", "activation", "recap", "none"]
ARTIFACT_TYPES = ["Guide", "Template", "Checklist", "Calculator", "Audit", "Framework", "Teardown", "Worksheet", "Playbook", "Swipe File"]
REVIEW_STATUSES = ["ready", "needs_review", "needs_revision"]
HEADLINE_STYLE_BY_LABEL = {"A": "outcome", "B": "authority", "C": "hybrid"}
WHATS_WORKING_TAGS = [
    "credibility_stack", "offer_clarity", "category_positioning", "proof_marker",
    "distribution_asset", "community_asset", "differentiated_narrative", "funnel_readiness",
]
REVENUE_LEAK_TAGS = [
    "generic_content", "weak_founder_voice", "missing_pov", "invisible_social_proof",
    "poor_cta_design", "weak_featured_section", "profile_feed_mismatch",
    "content_strategy_gap", "proof_distribution_gap",
]
PLACEHOLDER_RE = re.compile(
    r"\[(insert|your|add|company name|client name|placeholder)[^\]]*\]|\bTODO\b|\bTBD\b|lorem ipsum|\bXXX\b",
    re.IGNORECASE,
)
CONTENT_ROW_REQUIRED = [
    "day_number", "week_number", "title", "archetype", "primary_goal",
    "target_persona", "post_content", "first_sentence", "cta_type",
    "artifact_week", "artifact_role", "proof_required",
    "review_status", "post_ready", "items_to_verify", "to_fix",
    "action_items", "finalized_content",
]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def filled(value):
    return isinstance(value, str) and value.strip() != ""


def squish(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def check_offer(offer):
    if not isinstance(offer, dict):
        return err("offer: missing or not an object — the plan must ladder to a named offer")
    for key in ("name", "primary_url", "cta_keyword", "description"):
        if not filled(offer.get(key)):
            err(f"offer.{key}: required")


def check_scores(scores):
    if not isinstance(scores, dict):
        return err("scores: missing or not an object")
    if not (is_num(scores.get("authority_score")) and 0 <= scores["authority_score"] <= 100):
        err("scores.authority_score: must be a number 0-100")
    if not filled(scores.get("summary")):
        err("scores.summary: required")
    dims = scores.get("dimensions") or []
    keys = [d.get("key") for d in dims if isinstance(d, dict)]
    if sorted(keys) != sorted(DIMENSION_KEYS):
        err(f"scores.dimensions: need exactly the 5 keys {DIMENSION_KEYS}, got {keys}")
        return
    weighted = 0.0
    for dim in dims:
        key = dim.get("key")
        if not (is_num(dim.get("score")) and 0 <= dim["score"] <= 10):
            err(f"scores.dimensions[{key}].score: must be 0-10")
            continue
        if not (is_num(dim.get("confidence")) and 0 <= dim["confidence"] <= 1):
            err(f"scores.dimensions[{key}].confidence: must be 0-1")
        if not (isinstance(dim.get("evidence"), list) and dim["evidence"]):
            err(f"scores.dimensions[{key}].evidence: non-empty list required")
        subs = dim.get("subscores")
        if not (isinstance(subs, list) and subs):
            err(f"scores.dimensions[{key}].subscores: non-empty list required")
        else:
            for sub in subs:
                if not (isinstance(sub, dict) and filled(sub.get("key")) and is_num(sub.get("score")) and 0 <= sub["score"] <= 10):
                    err(f"scores.dimensions[{key}].subscores: each needs key + score 0-10")
                    break
        weighted += dim["score"] * DIMENSION_WEIGHTS[key]
    expected = weighted * 10
    if is_num(scores.get("authority_score")) and abs(scores["authority_score"] - expected) > 5:
        warn(
            f"scores.authority_score {scores['authority_score']} differs from weighted composite "
            f"{expected:.1f} by more than 5"
        )


def check_findings(findings):
    if not isinstance(findings, dict):
        return err("findings: missing or not an object")
    for group, known in (("whats_working", WHATS_WORKING_TAGS), ("revenue_leaks", REVENUE_LEAK_TAGS)):
        items = findings.get(group)
        if not (isinstance(items, list) and items):
            err(f"findings.{group}: non-empty list required")
            continue
        for item in items:
            if not (isinstance(item, dict) and filled(item.get("tag")) and filled(item.get("title")) and filled(item.get("description"))):
                err(f"findings.{group}: each item needs tag, title, description")
                break
            if item["tag"] not in known:
                warn(f"findings.{group}: unknown tag '{item['tag']}'")
    if not filled(findings.get("bottom_line")):
        err("findings.bottom_line: required")


def check_strategy(strategy):
    if not isinstance(strategy, dict):
        return err("strategy: missing or not an object")
    for key in ("buyer_persona", "strategic_gap", "strategic_opportunity", "fit_assessment"):
        if not filled(strategy.get(key)):
            err(f"strategy.{key}: required")
    if not (is_num(strategy.get("fit_score")) and 0 <= strategy["fit_score"] <= 100):
        err("strategy.fit_score: must be a number 0-100")
    if not (isinstance(strategy.get("next_steps"), list) and strategy["next_steps"]):
        err("strategy.next_steps: non-empty list required")


def check_rewrite(rewrite):
    if not isinstance(rewrite, dict):
        return err("rewrite: missing or not an object")
    headlines = rewrite.get("headlines") or []
    if len(headlines) != 3:
        err(f"rewrite.headlines: exactly 3 required, got {len(headlines)}")
    else:
        labels = sorted(h.get("label") for h in headlines if isinstance(h, dict))
        if labels != ["A", "B", "C"]:
            err(f"rewrite.headlines: labels must be A, B, C — got {labels}")
        for h in headlines:
            expected = HEADLINE_STYLE_BY_LABEL.get(h.get("label"))
            if expected and h.get("style") != expected:
                err(f"rewrite.headlines[{h.get('label')}]: style must be '{expected}'")
            if not filled(h.get("text")):
                err(f"rewrite.headlines[{h.get('label')}]: text required")
    if rewrite.get("recommended_style") not in ("A", "B", "C"):
        err("rewrite.recommended_style: must be A, B, or C")
    for key in ("recommended_headline", "recommended_reason", "recommended_bio", "profile_analysis", "profile_rewrite"):
        if not filled(rewrite.get(key)):
            err(f"rewrite.{key}: required")
    guide = rewrite.get("voice_style_guide")
    if not isinstance(guide, dict):
        err("rewrite.voice_style_guide: required object")
    else:
        for key in ("structure_habits", "cta_habits", "proof_usage", "avoid"):
            if not isinstance(guide.get(key), list):
                err(f"rewrite.voice_style_guide.{key}: list required")
    if not isinstance(rewrite.get("improvement_suggestions"), list):
        err("rewrite.improvement_suggestions: list required")


def check_weekly_artifacts(artifacts, out_dir):
    if not isinstance(artifacts, list) or len(artifacts) != 8:
        return err(f"weekly_artifacts: exactly 8 required (one per week), got {len(artifacts) if isinstance(artifacts, list) else 'none'}")
    weeks = sorted(a.get("week") for a in artifacts if isinstance(a, dict))
    if weeks != [1, 2, 3, 4, 5, 6, 7, 8]:
        err(f"weekly_artifacts: weeks must be exactly 1..8 — got {weeks}")
    keywords = Counter()
    for a in artifacts:
        week = a.get("week")
        tag = f"weekly_artifacts[week {week}]"
        if a.get("artifact_type") not in ARTIFACT_TYPES:
            err(f"{tag}: artifact_type must be one of {ARTIFACT_TYPES}")
        for key in ("slug", "title", "file", "summary", "offer_bridge", "cta_keyword"):
            if not filled(a.get(key)):
                err(f"{tag}.{key}: required")
        drop = a.get("drop_day")
        if is_num(week) and is_num(drop) and not ((week - 1) * 7 + 1 <= drop <= week * 7):
            err(f"{tag}: drop_day {drop} is outside week {week} (days {(week - 1) * 7 + 1}-{week * 7})")
        if filled(a.get("cta_keyword")):
            keywords[a["cta_keyword"].upper()] += 1
        if out_dir is not None and filled(a.get("file")):
            if not (out_dir / a["file"]).exists():
                err(f"{tag}: artifact file does not exist: {a['file']} (the artifact must be GENERATED, not just described)")
    for kw, count in keywords.items():
        if count > 1:
            err(f"weekly_artifacts: cta_keyword '{kw}' reused across {count} artifacts — one keyword per artifact")
    types = Counter(a.get("artifact_type") for a in artifacts)
    for atype, count in types.items():
        if count > 3:
            warn(f"weekly_artifacts: {count} artifacts of type '{atype}' — vary the types")


def check_activity_review(review):
    if not isinstance(review, dict):
        return err("activity_review: missing or not an object")
    pc = review.get("post_classification")
    if not isinstance(pc, dict):
        err("activity_review.post_classification: required object")
    else:
        for key, known in (
            ("archetype_distribution", ARCHETYPES),
            ("primary_goal_distribution", PRIMARY_GOALS),
            ("cta_distribution", CTA_TYPES),
        ):
            dist = pc.get(key)
            if not isinstance(dist, list):
                err(f"activity_review.post_classification.{key}: list required")
                continue
            for entry in dist:
                if entry.get("label") not in known:
                    warn(f"activity_review.post_classification.{key}: label '{entry.get('label')}' not in taxonomy")
    for key in ("themes", "tone_patterns", "hook_patterns", "proof_patterns", "posting_guidance"):
        if not isinstance(review.get(key), list):
            err(f"activity_review.{key}: list required")
    if not filled(review.get("whats_working_summary")):
        err("activity_review.whats_working_summary: required")


def check_content_plan(plan, artifacts):
    if not isinstance(plan, list) or len(plan) != 60:
        return err(f"content_plan: exactly 60 rows required, got {len(plan) if isinstance(plan, list) else 'none'}")

    days = [row.get("day_number") for row in plan]
    if sorted(days) != list(range(1, 61)):
        err("content_plan: day_number must be exactly 1..60, each once")

    plan = sorted(plan, key=lambda r: (r.get("day_number") or 0))
    by_week_artifact = {a.get("week"): a for a in (artifacts or []) if isinstance(a, dict)}
    hooks = Counter()

    for row in plan:
        day = row.get("day_number")
        tag = f"content_plan[day {day}]"
        for key in CONTENT_ROW_REQUIRED:
            if key not in row:
                err(f"{tag}: missing field '{key}'")
        if is_num(row.get("week_number")) and is_num(day) and row["week_number"] != math.ceil(day / 7):
            err(f"{tag}: week_number must be {math.ceil(day / 7)}")
        if row.get("archetype") not in ARCHETYPES:
            err(f"{tag}: invalid archetype '{row.get('archetype')}'")
        if row.get("primary_goal") not in PRIMARY_GOALS:
            err(f"{tag}: invalid primary_goal '{row.get('primary_goal')}'")
        if row.get("cta_type") not in CTA_TYPES:
            err(f"{tag}: invalid cta_type '{row.get('cta_type')}'")
        if row.get("artifact_role") not in ARTIFACT_ROLES:
            err(f"{tag}: invalid artifact_role '{row.get('artifact_role')}'")
        if row.get("review_status") not in REVIEW_STATUSES:
            err(f"{tag}: invalid review_status '{row.get('review_status')}'")
        for key in ("title", "post_content", "first_sentence"):
            if not filled(row.get(key)):
                err(f"{tag}: {key} required")

        # Artifact linkage: days 1-56 orbit their own week's artifact.
        aweek = row.get("artifact_week")
        role = row.get("artifact_role")
        if is_num(day) and day <= 56:
            expected_week = math.ceil(day / 7)
            if role not in ("none", "recap") and aweek != expected_week:
                err(f"{tag}: artifact_week must be {expected_week} for role '{role}' (posts orbit their own week's artifact)")
            if aweek is not None and aweek != expected_week:
                err(f"{tag}: artifact_week {aweek} does not match calendar week {expected_week}")
        elif is_num(day):
            if aweek is not None:
                err(f"{tag}: days 57-60 are the offer week — artifact_week must be null")
            if role not in ("recap", "none"):
                err(f"{tag}: days 57-60 must use artifact_role 'recap' or 'none'")

        if role == "drop":
            if row.get("archetype") != "resource_guide":
                err(f"{tag}: drop posts must be archetype resource_guide")
            if row.get("cta_type") not in ("comment_keyword", "visit_link"):
                err(f"{tag}: drop posts must use cta comment_keyword or visit_link")
            art = by_week_artifact.get(aweek)
            if art and is_num(art.get("drop_day")) and art["drop_day"] != day:
                err(f"{tag}: artifact for week {aweek} declares drop_day {art['drop_day']}, but this drop is day {day}")

        if row.get("post_ready") is True and not filled(row.get("finalized_content")):
            err(f"{tag}: post_ready true requires finalized_content")
        content = str(row.get("post_content") or "")
        if PLACEHOLDER_RE.search(content):
            err(f"{tag}: post_content contains a placeholder ({PLACEHOLDER_RE.search(content).group(0)!r})")
        if filled(row.get("first_sentence")) and not squish(content).startswith(squish(row["first_sentence"])[:40]):
            warn(f"{tag}: first_sentence is not the opening of post_content")
        if len(content) < 280:
            warn(f"{tag}: post_content is short ({len(content)} chars)")
        # Kill-filler heuristic: a post with no digits and no list/structure is
        # usually a musing. Soft signal only — the real bar is editorial.
        if not re.search(r"\d", content) and content.count("\n\n") < 3:
            warn(f"{tag}: no numbers and little structure — check it passes the kill-filler tests")
        hooks[squish(row.get("first_sentence"))] += 1

    for hook, count in hooks.items():
        if hook and count > 1:
            warn(f"content_plan: hook reused {count} times: \"{hook[:60]}\"")

    # Weekly arc coverage: each artifact week needs its drop and a real orbit.
    for week in range(1, 9):
        rows = [r for r in plan if r.get("artifact_week") == week]
        drops = [r for r in rows if r.get("artifact_role") == "drop"]
        if len(drops) != 1:
            err(f"content_plan: week {week} needs exactly 1 drop post, got {len(drops)}")
        if len(rows) < 4:
            err(f"content_plan: week {week} has only {len(rows)} posts linked to its artifact (need ≥4 — the week promotes the artifact)")
        roles = {r.get("artifact_role") for r in rows} - {"none"}
        if len(roles) < 5:
            warn(f"content_plan: week {week} covers only {len(roles)} distinct artifact roles — vary the angles (tease/drop/application/objection/proof/operator/activation)")

    # No more than 2 consecutive rows with the same archetype.
    run_archetype, run_length = None, 0
    for row in plan:
        archetype = row.get("archetype")
        if archetype == run_archetype:
            run_length += 1
            if run_length == 3:
                err(f"content_plan: more than 2 consecutive '{archetype}' posts around day {row.get('day_number')}")
        else:
            run_archetype, run_length = archetype, 1

    mix = Counter(row.get("archetype") for row in plan)
    for archetype, target in RECOMMENDED_MIX.items():
        if abs(mix.get(archetype, 0) - target) > 2:
            warn(f"content_plan: {archetype} count {mix.get(archetype, 0)} drifts from recommended {target} by more than 2")

    # Two-week block quality rules.
    for block_start in (1, 15, 29, 43):
        block = [r for r in plan if is_num(r.get("day_number")) and block_start <= r["day_number"] <= min(block_start + 13, 60)]
        label = f"days {block_start}-{min(block_start + 13, 60)}"
        if sum(1 for r in block if r.get("artifact_role") == "proof" or r.get("archetype") == "results_case_study") < 2:
            warn(f"content_plan ({label}): fewer than 2 proof posts")
        if sum(1 for r in block if r.get("archetype") in ("tactical_blueprint", "resource_guide", "diagnostic_framework")) < 2:
            warn(f"content_plan ({label}): fewer than 2 actionable posts")
        if sum(1 for r in block if r.get("archetype") in ("founder_story", "feature_announcement")) < 1:
            warn(f"content_plan ({label}): no operator post (founder_story / feature_announcement)")
        if sum(1 for r in block if r.get("primary_goal") in ("lead_gen", "conversion") or r.get("cta_type") in ("comment_keyword", "dm_me", "visit_link")) < 1:
            warn(f"content_plan ({label}): no conversion-oriented post")

    not_ready = sum(1 for r in plan if r.get("post_ready") is not True)
    if not_ready > 10:
        warn(f"content_plan: {not_ready} of 60 posts are not post_ready")


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    path = Path(argv[0])
    if path.is_dir():
        blueprint_path = path / "blueprint.json"
        out_dir = path
    else:
        blueprint_path = path
        out_dir = path.parent if (path.parent / "artifacts").exists() else None
    if not blueprint_path.exists():
        print(f"error: {blueprint_path} not found")
        return 1
    try:
        blueprint = json.loads(blueprint_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: blueprint.json is not valid JSON: {exc}")
        return 1

    for key in ("meta", "offer", "observed_profile", "scores", "findings", "activity_review", "strategy", "rewrite", "weekly_artifacts", "content_plan"):
        if key not in blueprint:
            err(f"top-level key missing: {key}")

    meta = blueprint.get("meta") or {}
    for key in ("linkedin_url", "username", "generated_at", "analysis_window_days"):
        if not meta.get(key):
            err(f"meta.{key}: required")

    check_offer(blueprint.get("offer"))
    check_scores(blueprint.get("scores"))
    check_findings(blueprint.get("findings"))
    check_strategy(blueprint.get("strategy"))
    check_rewrite(blueprint.get("rewrite"))
    check_weekly_artifacts(blueprint.get("weekly_artifacts"), out_dir)
    check_activity_review(blueprint.get("activity_review"))
    check_content_plan(blueprint.get("content_plan"), blueprint.get("weekly_artifacts"))

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"warn:  {message}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) — {blueprint_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
