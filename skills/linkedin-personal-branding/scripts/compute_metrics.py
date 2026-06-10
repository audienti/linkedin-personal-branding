#!/usr/bin/env python3
"""Compute deterministic LinkedIn activity metrics from evidence.json.

Port of Audienti v10's LinkedinStrategyReviews::ActivityNormalizer and
MetricsBuilder. Stdlib only.

Usage:
    python3 compute_metrics.py <output-dir | evidence.json> [--window DAYS]

Reads evidence.json, writes metrics.json next to it, prints a short summary.
The numbers in metrics.json are deterministic facts: the review must use them
as-is and never contradict them.
"""

import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NUMBER_BACKED_RE = re.compile(r"\b\d+(?:[.,]\d+)?(?:%|x)?\b")
URL_IN_TEXT_RE = re.compile(r"https?://[^\s)\]>\"']+", re.IGNORECASE)


def parse_ts(value):
    """ISO 8601 string -> aware datetime, or None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def domain_of(url):
    """Registrable-ish domain: hostname minus leading www."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return None
    return host[4:] if host.startswith("www.") else (host or None)


def to_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def rnd(value):
    return round(value + 1e-9, 2)


def squish(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def compact_text(text, limit=160):
    value = squish(text)
    return value if len(value) <= limit else value[: limit - 1] + "…"


def normalize_activity(evidence, window_days, collected_at):
    """Merge posts + comments into one normalized stream, newest first."""
    site_domain = domain_of(evidence.get("website", {}).get("url") or "") or None
    window_start = collected_at - timedelta(days=window_days)
    items, dropped, out_of_window = [], 0, 0

    def add(raw, activity_type):
        nonlocal dropped, out_of_window
        url = str(raw.get("url") or "").strip()
        occurred_at = parse_ts(raw.get("occurred_at"))
        if not url or occurred_at is None:
            dropped += 1
            return
        if occurred_at < window_start or occurred_at > collected_at + timedelta(days=1):
            out_of_window += 1
            return
        text = str(raw.get("text") or "")
        link_urls = list(raw.get("link_urls") or [])
        link_urls += URL_IN_TEXT_RE.findall(text)
        link_domains = sorted(
            {
                d
                for d in (domain_of(u) for u in link_urls)
                if d and d != "linkedin.com" and not d.endswith(".linkedin.com")
            }
        )
        items.append(
            {
                "activity_type": activity_type,
                "url": url,
                "occurred_at": occurred_at,
                "text": text,
                "link_domains": link_domains,
                "self_link": bool(site_domain) and any(d == site_domain or d.endswith("." + site_domain) for d in link_domains),
                "is_repost": raw.get("is_repost") is True,
                "comment_count": to_int(raw.get("comment_count")),
                "reaction_count": to_int(raw.get("reaction_count")),
                "like_count": to_int(raw.get("like_count")),
                "share_count": to_int(raw.get("share_count")),
                "author_name": raw.get("author_name"),
            }
        )

    for raw in evidence.get("posts") or []:
        if raw.get("kind") in ("other", "reaction", "comment_activity"):
            dropped += 1
            continue
        add(raw, "post")
    for raw in evidence.get("comments") or []:
        add(raw, "comment")

    items.sort(key=lambda r: r["occurred_at"], reverse=True)
    return items, {"dropped_invalid": dropped, "out_of_window": out_of_window}


def question_led(text):
    first_line = next((l.strip() for l in str(text or "").split("\n") if l.strip()), "")
    return "?" in first_line


def number_backed(text):
    return bool(NUMBER_BACKED_RE.search(str(text or "")))


class Metrics:
    def __init__(self, activity, window_days):
        self.activity = activity
        self.window_days = window_days
        self.posts = [r for r in activity if r["activity_type"] == "post"]
        self.comments = [r for r in activity if r["activity_type"] == "comment"]

    def build(self):
        return {
            "summary": self.summary(),
            "cadence": self.cadence(),
            "schedule": self.schedule(),
            "content_mix": self.content_mix(),
            "campaign_signals": self.campaign_signals(),
            "engagement": self.engagement(),
        }

    def summary(self):
        return {
            "post_count": len(self.posts),
            "comment_count": len(self.comments),
            "active_days_count": len({r["occurred_at"].date() for r in self.activity}),
            "post_received_comment_count": sum(r["comment_count"] for r in self.posts),
            "post_received_reaction_count": sum(r["reaction_count"] for r in self.posts),
        }

    def weekly_rate(self, count):
        if self.window_days <= 0:
            return 0.0
        return rnd(count / self.window_days * 7)

    def cadence(self):
        return {
            "posts_per_week": self.weekly_rate(len(self.posts)),
            "comments_per_week": self.weekly_rate(len(self.comments)),
            "active_days_per_week": self.weekly_rate(len({r["occurred_at"].date() for r in self.activity})),
        }

    def bucket_counts(self, labeler):
        counts = Counter(labeler(r) for r in self.activity)
        return [
            {"label": label, "count": count}
            for label, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

    def schedule(self):
        # Local time: URN timestamps are UTC; readers think in their own clock.
        return {
            "weekday_distribution": self.bucket_counts(
                lambda r: WEEKDAYS[r["occurred_at"].astimezone().weekday()]
            ),
            "hour_distribution": self.bucket_counts(
                lambda r: r["occurred_at"].astimezone().strftime("%H:00")
            ),
        }

    def rate_for_posts(self, count):
        return rnd(count / len(self.posts)) if self.posts else 0.0

    def content_mix(self):
        self_link_count = sum(1 for r in self.posts if r["self_link"])
        external_count = sum(1 for r in self.posts if r["link_domains"])
        repost_count = sum(1 for r in self.posts if r["is_repost"])
        dup_count = self.duplicate_text_post_count()
        domains = Counter(d for r in self.activity for d in r["link_domains"])
        return {
            "post_comment_ratio": f"{len(self.posts)}:{len(self.comments)}",
            "self_link_post_count": self_link_count,
            "self_link_rate": self.rate_for_posts(self_link_count),
            "external_link_post_count": external_count,
            "external_link_post_rate": self.rate_for_posts(external_count),
            "repost_post_count": repost_count,
            "repost_post_rate": self.rate_for_posts(repost_count),
            "duplicate_text_post_count": dup_count,
            "duplicate_text_post_rate": self.rate_for_posts(dup_count),
            "external_domains": [
                {"domain": domain, "count": count}
                for domain, count in sorted(domains.items(), key=lambda kv: (-kv[1], kv[0]))
            ],
        }

    def duplicate_text_post_count(self):
        normalized = [squish(r["text"]).lower() for r in self.posts]
        groups = Counter(t for t in normalized if t)
        return sum(count - 1 for count in groups.values() if count > 1)

    def campaign_signals(self):
        q_count = sum(1 for r in self.posts if question_led(r["text"]))
        n_count = sum(1 for r in self.posts if number_backed(r["text"]))
        return {
            "question_led_post_count": q_count,
            "question_led_post_rate": self.rate_for_posts(q_count),
            "number_backed_post_count": n_count,
            "number_backed_post_rate": self.rate_for_posts(n_count),
        }

    def average_for(self, rows, field):
        return rnd(sum(r[field] for r in rows) / len(rows)) if rows else 0.0

    def compact_post(self, row, field):
        return {
            "url": row["url"],
            "occurred_at": row["occurred_at"].isoformat(),
            "snippet": compact_text(row["text"]),
            "comment_count": row["comment_count"],
            "reaction_count": row["reaction_count"],
            "primary_metric": field,
            "primary_metric_count": row[field],
        }

    def ranked_posts(self, field, limit=3):
        ranked = sorted(
            (r for r in self.posts if r[field] > 0),
            key=lambda r: (-r[field], -r["reaction_count"], -r["occurred_at"].timestamp()),
        )
        return [self.compact_post(r, field) for r in ranked[:limit]]

    def comparative(self, pattern_label, matcher):
        matching = [r for r in self.posts if matcher(r["text"])]
        baseline = [r for r in self.posts if not matcher(r["text"])]
        top = max(
            matching,
            key=lambda r: (r["comment_count"] + r["reaction_count"], r["occurred_at"].timestamp()),
            default=None,
        )
        out = {
            "pattern_label": pattern_label,
            "matching_post_count": len(matching),
            "matching_average_comment_count": self.average_for(matching, "comment_count"),
            "matching_average_reaction_count": self.average_for(matching, "reaction_count"),
            "baseline_post_count": len(baseline),
            "baseline_average_comment_count": self.average_for(baseline, "comment_count"),
            "baseline_average_reaction_count": self.average_for(baseline, "reaction_count"),
        }
        if top is not None:
            out["top_matching_post"] = self.compact_post(top, "comment_count")
        return out

    def engagement(self):
        return {
            "total_post_comment_count": sum(r["comment_count"] for r in self.posts),
            "total_post_reaction_count": sum(r["reaction_count"] for r in self.posts),
            "average_comments_per_post": self.average_for(self.posts, "comment_count"),
            "average_reactions_per_post": self.average_for(self.posts, "reaction_count"),
            "top_posts_by_comments": self.ranked_posts("comment_count"),
            "top_posts_by_reactions": self.ranked_posts("reaction_count"),
            "hook_performance": self.comparative("question_led", question_led),
            "proof_performance": self.comparative("number_backed", number_backed),
        }


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    path = Path(args[0])
    evidence_path = path / "evidence.json" if path.is_dir() else path
    if not evidence_path.exists():
        print(f"error: {evidence_path} not found")
        return 1

    evidence = json.loads(evidence_path.read_text())

    window_days = None
    for arg in argv:
        if arg.startswith("--window"):
            window_days = int(arg.split("=", 1)[1]) if "=" in arg else None
    window_days = window_days or int(evidence.get("analysis_window_days") or 90)

    collected_at = parse_ts(evidence.get("collected_at")) or datetime.now(timezone.utc)
    activity, notes = normalize_activity(evidence, window_days, collected_at)

    metrics = Metrics(activity, window_days).build()
    out = {
        "analysis_window_days": window_days,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "normalization_notes": notes,
        **metrics,
    }

    out_path = evidence_path.parent / "metrics.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    s, c = out["summary"], out["cadence"]
    print(f"metrics.json written: {out_path}")
    print(
        f"  {s['post_count']} posts, {s['comment_count']} comments over {window_days} days "
        f"({c['posts_per_week']}/wk posts, {c['comments_per_week']}/wk comments)"
    )
    print(
        f"  engagement: {out['engagement']['average_reactions_per_post']} avg reactions, "
        f"{out['engagement']['average_comments_per_post']} avg comments per post"
    )
    if notes["dropped_invalid"] or notes["out_of_window"]:
        print(
            f"  note: dropped {notes['dropped_invalid']} invalid items, "
            f"{notes['out_of_window']} outside the {window_days}-day window"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
