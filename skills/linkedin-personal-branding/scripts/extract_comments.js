// LinkedIn comments extractor.
// A single arrow-function expression returning a JSON string.
// chrome-devtools MCP: pass this file's contents as `function` to evaluate_script.
// Raw JS eval tools (Claude in Chrome javascript_tool): evaluate `(<file contents>)()`.
//
// Run on https://www.linkedin.com/in/<username>/recent-activity/comments/ in a
// scroll loop. Results ACCUMULATE across runs in window.__lipbCommentCache.
// Items are the profile owner's comments on posts (theirs or others').
() => {
  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
  const txt = (el) => clean(el && (el.innerText || el.textContent));
  const q = (sel, root) => (root || document).querySelector(sel);
  const qa = (sel, root) => Array.from((root || document).querySelectorAll(sel));

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
      : 31536e6;
    return Date.now() - n * mult;
  };

  window.__lipbCommentCache = window.__lipbCommentCache || {};
  const cache = window.__lipbCommentCache;
  let newCount = 0;

  const nodes = new Set();
  qa("article.comments-comment-entity").forEach((n) => nodes.add(n));
  qa(".comments-comment-item").forEach((n) => nodes.add(n));
  qa("[data-id*='urn:li:comment']").forEach((n) => nodes.add(n));

  nodes.forEach((node) => {
    const idAttr =
      node.getAttribute("data-id") || node.getAttribute("data-urn") || "";
    // urn:li:comment:(urn:li:activity:712...,7123456789012345678)
    const cm = idAttr.match(/urn:li:comment:\(([^,]+),(\d+)\)/);
    const activityId = cm ? (cm[1].match(/(\d{10,})/) || [])[1] || null : null;
    const commentId = cm ? cm[2] : null;

    const text = txt(
      q(
        ".comments-comment-item__main-content, .comments-comment-entity__content, .comments-comment-item-content-body",
        node
      )
    ).slice(0, 1500);
    const key = commentId || (activityId ? activityId + ":" + text.slice(0, 40) : text.slice(0, 80));
    if (!key || (!text && !commentId)) return;

    const rel =
      txt(q("time", node)) ||
      txt(q(".comments-comment-meta__data", node)) ||
      null;
    const ts = (commentId ? tsFromId(commentId) : null) || relToMs(rel);

    // Comment author: threads on the comments tab include OTHER people's
    // replies. Capture the author so the agent can filter to the profile
    // owner (drop items whose comment_author is clearly someone else).
    const commentAuthor =
      txt(
        q(
          ".comments-comment-meta__description-title, .comments-post-meta__name-text, .comments-comment-meta__actor",
          node
        )
      ).replace(/\s*•.*$/, "") || null;

    const update = node.closest(
      "[data-urn*='urn:li:activity'], div.feed-shared-update-v2"
    );
    let postUrn = null;
    if (update) {
      const um = (update.getAttribute("data-urn") || update.getAttribute("data-id") || "").match(/urn:li:activity:\d+/);
      postUrn = um ? um[0] : null;
    }
    if (!postUrn && activityId) postUrn = "urn:li:activity:" + activityId;
    const postUrl = postUrn
      ? "https://www.linkedin.com/feed/update/" + postUrn + "/"
      : null;
    const postAuthor = update
      ? txt(
          q(
            ".update-components-actor__title span[aria-hidden='true'], .update-components-actor__title",
            update
          )
        ) || null
      : null;

    const item = {
      url: postUrl || location.href.split("?")[0] + "#" + key,
      occurred_at: ts ? new Date(ts).toISOString() : null,
      relative_time: rel,
      text,
      comment_author: commentAuthor,
      post_url: postUrl,
      post_author: postAuthor,
    };

    const prev = cache[key];
    if (!prev) {
      cache[key] = item;
      newCount += 1;
    } else if ((item.text || "").length > (prev.text || "").length) {
      prev.text = item.text;
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
