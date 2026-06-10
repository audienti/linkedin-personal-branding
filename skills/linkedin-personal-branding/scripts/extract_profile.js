// LinkedIn profile extractor.
// A single arrow-function expression returning a JSON string.
// chrome-devtools MCP: pass this file's contents as `function` to evaluate_script.
// Raw JS eval tools (Claude in Chrome javascript_tool): evaluate `(<file contents>)()`.
//
// Run on https://www.linkedin.com/in/<username>/ after scrolling 2-3 times so
// lazy sections mount. Run again on .../overlay/contact-info/ to get `contact`.
// Selectors are best-effort with fallbacks; missing fields land in `warnings`
// and must be filled manually by reading the page.
() => {
  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
  const txt = (el) => clean(el && (el.innerText || el.textContent));
  const q = (sel, root) => (root || document).querySelector(sel);
  const qa = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const warnings = [];

  const parseCount = (s) => {
    const m = String(s || "").replace(/,/g, "").match(/([\d.]+)\s*([KkMm]?)\+?/);
    if (!m) return null;
    let n = parseFloat(m[1]);
    if (/k/i.test(m[2])) n *= 1000;
    if (/m/i.test(m[2])) n *= 1000000;
    return Math.round(n);
  };

  // Profile cards are sections anchored by an empty div with a stable id.
  const sectionFor = (id) => {
    const a = document.getElementById(id);
    return a ? a.closest("section") : null;
  };
  const visibleSpans = (root) =>
    qa('span[aria-hidden="true"]', root).map(txt).filter(Boolean);

  const out = { warnings };

  // --- Contact-info overlay mode -------------------------------------------
  const overlayOpen = location.pathname.includes("overlay/contact-info");
  const overlay =
    q("section.pv-contact-info") ||
    (overlayOpen ? q(".artdeco-modal, div[role='dialog']") : null);
  if (overlay) {
    const links = qa("a[href]", overlay).map((a) => ({
      url: a.href,
      label: txt(a),
    }));
    out.contact = {
      websites: links.filter(
        (l) =>
          /^https?:/.test(l.url) &&
          !/linkedin\.com/.test(l.url)
      ),
      emails: links
        .filter((l) => l.url.startsWith("mailto:"))
        .map((l) => l.url.replace("mailto:", "")),
    };
    return JSON.stringify(out);
  }

  // --- New React profile shell detection -----------------------------------
  // Some accounts get a rebuilt profile page (main#workspace, hashed CSS
  // classes, no h1/#about/#experience anchors). Legacy selectors below will
  // find nothing there. Signal it clearly: the caller should fall back to
  // reading the page text (get_page_text / snapshot) and the
  // /details/experience/ and /overlay/contact-info/ pages, per the
  // collection guide.
  const workspace = document.getElementById("workspace");
  if (workspace && !q("h1") && !document.getElementById("about")) {
    out.new_dom = true;
    warnings.push(
      "new React profile DOM detected (main#workspace, no legacy anchors) — extract from page text instead"
    );
    return JSON.stringify(out);
  }

  // --- Top card --------------------------------------------------------------
  const h1 = q("h1");
  out.name = txt(h1) || null;
  if (!out.name) warnings.push("name");

  const topCard = (h1 && h1.closest("section")) || document;
  out.headline = txt(q("div.text-body-medium.break-words", topCard)) || null;
  if (!out.headline) warnings.push("headline");

  out.location =
    txt(q("span.text-body-small.inline.t-black--light.break-words", topCard)) ||
    null;
  if (!out.location) warnings.push("location");

  let connections = null;
  let followers = null;
  qa("li, p, span", topCard).forEach((el) => {
    const t = txt(el);
    if (!t || t.length > 60) return;
    if (connections === null && /connection/i.test(t)) connections = parseCount(t);
    if (followers === null && /follower/i.test(t)) followers = parseCount(t);
  });
  out.connections = connections;
  out.followers = followers;

  const photo = q(
    "img.pv-top-card-profile-picture__image--show, .pv-top-card-profile-picture img, .pv-top-card__photo img"
  );
  out.profile_photo = photo ? photo.src : null;
  const banner = q(
    ".profile-background-image img, img.profile-background-image__image, #profile-background-image-target-image"
  );
  out.banner_image = banner ? banner.src : null;

  const compBtn = q('button[aria-label^="Current company" i]');
  out.company = compBtn
    ? clean(
        (compBtn.getAttribute("aria-label") || "")
          .replace(/Current company:?\s*/i, "")
          .replace(/\.\s*Click.*$/i, "")
      ) || null
    : null;

  // --- About -------------------------------------------------------------------
  const aboutSec = sectionFor("about");
  if (aboutSec) {
    const candidates = qa(
      'div[class*="inline-show-more-text"] span[aria-hidden="true"]',
      aboutSec
    )
      .map(txt)
      .filter(Boolean);
    out.about =
      candidates.sort((a, b) => b.length - a.length)[0] ||
      clean(txt(aboutSec).replace(/^About\s*/i, "")) ||
      null;
  } else {
    out.about = null;
  }
  if (!out.about) warnings.push("about");

  // --- Experience ---------------------------------------------------------------
  const expSec = sectionFor("experience");
  out.experience = [];
  if (expSec) {
    let items = qa("li.artdeco-list__item", expSec);
    if (!items.length) items = qa("ul > li", expSec);
    // keep only top-level entries (drop nested li of grouped roles)
    items = items.filter(
      (li) => !items.some((other) => other !== li && other.contains(li))
    );
    items.slice(0, 8).forEach((li) => {
      const lines = visibleSpans(li);
      if (!lines.length) return;
      const desc = lines
        .slice(2)
        .filter((l) => l.length > 60)
        .sort((a, b) => b.length - a.length)[0];
      out.experience.push({
        title: lines[0] || null,
        company: (lines[1] || "").split("·")[0].trim() || null,
        date_range:
          lines.find((l) => /\d{4}|present|\bmos?\b|\byrs?\b/i.test(l)) || null,
        description: desc ? desc.slice(0, 600) : null,
      });
    });
  }
  if (!out.experience.length) warnings.push("experience");
  out.job_title = out.experience[0] ? out.experience[0].title : null;

  // --- Featured -------------------------------------------------------------------
  const featSec = sectionFor("featured");
  out.featured_links = [];
  if (featSec) {
    qa("a[href]", featSec).forEach((a) => {
      if (!/^https?:/.test(a.href) || /\/overlay\//.test(a.href)) return;
      if (out.featured_links.some((f) => f.url === a.href)) return;
      const title = clean((a.innerText || "").split("\n")[0]).slice(0, 120);
      out.featured_links.push({ title: title || "Featured", url: a.href });
    });
    out.featured_links = out.featured_links.slice(0, 6);
  }

  out.linkedin_url = location.href.split("?")[0];
  return JSON.stringify(out);
}
