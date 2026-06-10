// LinkedIn activity (posts) extractor.
// A single arrow-function expression returning a JSON string.
// chrome-devtools MCP: pass this file's contents as `function` to evaluate_script.
// Raw JS eval tools (Claude in Chrome javascript_tool): evaluate `(<file contents>)()`.
//
// Run on https://www.linkedin.com/in/<username>/recent-activity/all/ in a
// scroll loop. Results ACCUMULATE across runs in window.__lipbActivityCache
// (keyed by activity id) because LinkedIn unmounts off-screen feed items.
// The final run returns the merged set.
//
// item.kind: "post" (authored), "repost", or "other" (reaction/comment
// activity surfaced in the All tab — exclude from evidence.posts).
() => {
  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
  const txt = (el) => clean(el && (el.innerText || el.textContent));
  const q = (sel, root) => (root || document).querySelector(sel);
  const qa = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const parseCount = (s) => {
    const m = String(s || "").replace(/,/g, "").match(/([\d.]+)\s*([KkMm]?)\+?/);
    if (!m) return null;
    let n = parseFloat(m[1]);
    if (/k/i.test(m[2])) n *= 1000;
    if (/m/i.test(m[2])) n *= 1000000;
    return Math.round(n);
  };

  // LinkedIn ids are snowflakes: id >> 22 = epoch millis.
  const tsFromId = (id) => {
    try {
      const ms = Number(BigInt(id) >> 22n);
      return ms > 1136073600000 && ms < Date.now() + 86400000 ? ms : null;
    } catch (e) {
      return null;
    }
  };

  const relToMs = (label) => {
    const m = String(label || "").match(/(\d+)\s*(mo|yr|[smhdwy])/i);
    if (!m) return null;
    const n = +m[1];
    const u = m[2].toLowerCase();
    const mult =
      u === "s" ? 1e3
      : u === "m" ? 6e4
      : u === "h" ? 36e5
      : u === "d" ? 864e5
      : u === "w" ? 6048e5
      : u === "mo" ? 2592e6
      : 31536e6; // y / yr
    return Date.now() - n * mult;
  };

  window.__lipbActivityCache = window.__lipbActivityCache || {};
  const cache = window.__lipbActivityCache;
  let newCount = 0;

  const nodes = new Set();
  qa("div.feed-shared-update-v2[data-urn]").forEach((n) => nodes.add(n));
  qa("[data-urn*='urn:li:activity']").forEach((n) => nodes.add(n));
  qa("[data-id*='urn:li:activity']").forEach((n) => nodes.add(n));

  nodes.forEach((node) => {
    const urnAttr =
      node.getAttribute("data-urn") || node.getAttribute("data-id") || "";
    const um = urnAttr.match(/urn:li:activity:(\d+)/);
    if (!um) return;
    const id = um[1];

    const header = txt(
      q(".update-components-header, .update-components-header__text-view", node)
    );
    const author =
      txt(
        q(
          ".update-components-actor__title span[aria-hidden='true'], .update-components-actor__title",
          node
        )
      ) || null;
    const body = q(".update-components-text", node);
    const text = body ? clean(body.innerText).slice(0, 3000) : "";

    let kind = "post";
    if (/reposted this/i.test(header)) kind = "repost";
    else if (/(commented on|replied to|likes this|loves this|celebrates|supports|finds this|reacted to)/i.test(header)) kind = "other";

    const rel = txt(
      q(
        ".update-components-actor__sub-description span[aria-hidden='true'], .update-components-actor__sub-description",
        node
      )
    ).split("•")[0].trim();
    const ts = tsFromId(id) || relToMs(rel);

    let reactions = parseCount(
      txt(q(".social-details-social-counts__reactions-count", node))
    );
    if (reactions === null) {
      // Small counts render as a named button: "Jane Doe and 6 others" (= 7).
      const rbtn = q(
        "button[data-reaction-details], .social-details-social-counts__reactions button, button[aria-label*='reaction' i]",
        node
      );
      if (rbtn) {
        const label = rbtn.getAttribute("aria-label") || rbtn.innerText || "";
        const others = label.match(/and ([\d,]+) others?/i);
        if (others) reactions = parseInt(others[1].replace(/,/g, ""), 10) + 1;
        else reactions = parseCount(label) !== null ? parseCount(label) : (label.trim() ? 1 : null);
      }
    }
    let comments = null;
    let shares = null;
    qa(
      ".social-details-social-counts__item, .social-details-social-counts li",
      node
    ).forEach((li) => {
      const t = txt(li);
      if (comments === null && /comment/i.test(t)) comments = parseCount(t);
      if (shares === null && /(repost|share)/i.test(t)) shares = parseCount(t);
    });

    const links = [];
    qa("a[href^='http']", node).forEach((a) => {
      // Strip query strings: tracking params bloat output and can trip
      // browser-tool data-loss filters when the result is returned.
      let h = a.href.split("#")[0].split("?")[0];
      if (/linkedin\.com\/(in|feed|company|posts|pulse|search|school|reactions|signup|login)/.test(h)) return;
      if (/^https?:\/\/(www\.)?linkedin\.com\/?$/.test(h)) return;
      if (!links.includes(h)) links.push(h);
    });

    const item = {
      urn: "urn:li:activity:" + id,
      url: "https://www.linkedin.com/feed/update/urn:li:activity:" + id + "/",
      kind,
      occurred_at: ts ? new Date(ts).toISOString() : null,
      relative_time: rel || null,
      author_name: author,
      is_repost: kind === "repost",
      text,
      link_urls: links.slice(0, 10),
      reaction_count: reactions || 0,
      comment_count: comments || 0,
      share_count: shares || 0,
    };

    const prev = cache[id];
    if (!prev) {
      cache[id] = item;
      newCount += 1;
    } else {
      if ((item.text || "").length > (prev.text || "").length) prev.text = item.text;
      prev.reaction_count = Math.max(prev.reaction_count, item.reaction_count);
      prev.comment_count = Math.max(prev.comment_count, item.comment_count);
      prev.share_count = Math.max(prev.share_count, item.share_count);
      if (!prev.link_urls.length) prev.link_urls = item.link_urls;
      if (prev.kind === "post" && item.kind !== "post") prev.kind = item.kind;
      prev.is_repost = prev.kind === "repost";
    }
  });

  const items = Object.values(cache).sort((a, b) =>
    (b.occurred_at || "").localeCompare(a.occurred_at || "")
  );
  const oldest = items.length ? items[items.length - 1].occurred_at : null;
  return JSON.stringify({
    count: items.length,
    new_count: newCount,
    oldest_occurred_at: oldest,
    items,
  });
}
