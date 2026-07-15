# Underground Garden — Site Source

Static site, no framework, no npm — plain HTML/CSS/JS. A small Python build
script keeps the 9 pages DRY so nav/footer edits don't require touching every
file by hand.

Pages: Home, Events, Subtropics, About, Gallery, Merch, Safety &amp; FAQ, Contact, 404.

## Third-party services — all connected and live (as of 2026-07-03)

- **Forms (Web3Forms)** — `WEB3FORMS_ACCESS_KEY` in `assets/js/main.js` is a real key, tested end-to-end with a real submission. All 7 forms (bookings, partnerships, general/press, 4 signup forms — Home, Events, Subtropics presale, Merch) post to Web3Forms, which emails `chris.gomez@ugevents.com` (the Web3Forms account owner; the site's displayed contact `info@ugevents.com` CCs there). Each form sends a different `data-form-subject` so incoming emails are easy to tell apart. If the key ever needs rotating, it's the one constant near the top of the form-handling block in `main.js` — was `"PASTE_YOUR_ACCESS_KEY_HERE"` as a placeholder, now a real UUID.
  - **Spam honeypot (added 2026-07-14):** every form contains a hidden `<input type="checkbox" name="botcheck">` (display:none, aria-hidden, out of tab order). Real visitors never touch it; bots that auto-fill every field check it. `main.js` shows the normal success message but sends nothing when it's checked, and Web3Forms also discards `botcheck`-checked submissions server-side. **When adding a new form, copy the botcheck line along with the rest of the form skeleton.** If spam ever gets past this anyway, Web3Forms supports free hCaptcha — that's the escalation path, not a paid plan.
  - **Form note placement:** the inline signup forms (Home/Events/Subtropics/Merch) keep their `[data-form-note]` status line *outside* the `<form>` tag; `main.js` looks inside the form first, then in the form's parent. (Before 2026-07-14 it only looked inside the form — those forms showed **no** success/failure message at all, a real shipped bug.) The note also carries `role="status"` so screen readers announce the result, and failures get a `.form-note--error` rust-colored treatment instead of the default green success box.
- **SMS signup (not email)** — the 4 "Get On The List" forms (Home, Events, Subtropics presale, Merch — Events added 2026-07-14 so the calendar's "join the list" nudge converts on-page) collect a **phone number** (`type="tel"`, with SMS consent microcopy), not an email address — changed 2026-07-03 to match how DEF (defineeverythingfuture.com) runs their list, since text has better open rates than email for time-sensitive drops. These still submit through Web3Forms same as every other form (into `chris.gomez@ugevents.com` + the submissions Sheet, see below) — **there is no automated texting integration, and none is planned.** Chris uses [ExpertTexting](https://www.experttexting.com/) for actually sending SMS blasts and manually uploads numbers there himself from the collected submissions. Don't build or suggest an ExpertTexting API integration unless he asks — this is intentionally a manual step on his end.
  - **Submissions are also auto-logged to a spreadsheet** — a scheduled agent (`ug-website-form-log`, runs every 30 min, task file at `~/.claude/scheduled-tasks/ug-website-form-log/SKILL.md`) reads new Web3Forms emails from Gmail and appends a row to [Underground Garden — Website Submissions](https://docs.google.com/spreadsheets/d/1JE3g7c6u4SvM4x8UMWqzUXRTk-kwmE7TIwOfQHVDDF8/edit) (Date, Form Type, Name, Email, Message, Gmail Link), then marks the email read so it's not double-logged. Built this way specifically to avoid paid tiers — Web3Forms' native Sheets integration and Zapier's multi-step Zaps both require a paid plan; this doesn't.
- **Google Analytics (GA4)** — live, Measurement ID `G-3M4QYM3MV5` in `partials/layout.html`. Property is under `chris.gomez@ugevents.com` (didn't need Workspace admin rights — GA4 property ownership is independent of that).
- **No live Instagram feed embed** (removed 2026-07-10) — a LightWidget embed was live on the Gallery page ("Live From The Garden" section) until the site went live on `ugevents.com`, when it broke: LightWidget's free tier disables HTTPS, and it started showing an "upgrade required" placeholder instead of the feed instead of the real feed (worked fine in local dev, which runs over plain HTTP). Chris chose to drop the embed rather than pay for LightWidget's paid tier — the Gallery page now ends at the photo grid, and Instagram is still reachable via the social rail (every page) and footer. If a live embed is wanted again later, either upgrade the LightWidget account (same widget ID: `9e8b55dfa3a8572c832e7803d35d8d8f`, same embed code, just needs a paid plan for HTTPS) or switch to a different provider that supports HTTPS on its free tier.
- **`SITE_URL` in `build.py`** — set to `"https://ugevents.com"`.
- **Fonts are self-hosted** (2026-07-14) — the four latin-subset woff2 files live in `assets/fonts/` with `@font-face` rules at the top of `style.css`; there is no Google Fonts request anymore (faster first paint, one less third-party). The two fonts visible at first paint (Anton + Space Mono 400) are preloaded in `partials/layout.html`. If a font file ever needs replacing, rename it — they're cached immutable for a year.

## SEO / social infrastructure (added 2026-07-03)

- Every page carries canonical link, Open Graph, and Twitter Card meta tags (see `partials/layout.html`), plus `theme-color` and `apple-touch-icon`. They're driven by `SITE_URL` in `build.py` (see above) — if the domain ever changes, update it there and rerun the build, or the canonical/OG/sitemap URLs will point at the wrong place.
- **The homepage's canonical URL is `https://ugevents.com/` (bare root), not `/index.html`** — `build.py` special-cases `index.html` when filling `{{PAGE_FILE}}` and in the sitemap, and `netlify.toml` 301-redirects `/index.html` → `/`. Without this, search engines see the same page at two URLs and split ranking signal between them. Internal links can keep pointing at `index.html`; the redirect catches them on the live site.
- `assets/img/brand/og-image.jpg` (1200x630) is the social-share preview image — since 2026-07-14 it's a real event photo (the warehouse DJ/crowd shot from `warehouse-skypbr.jpg`) with the bone wordmark overlaid, generated by `python3 scripts/make_og_image.py`. To swap the photo later, edit the source path/crop in that script and rerun it, then rerun `scripts/build_press_kit.py` (the press kit bundles the og image). It stays a JPG on purpose — social scrapers are pickier about formats than browsers.
- `robots.txt` and `sitemap.xml` are now generated by `build.py` (see `write_robots_and_sitemap`) every time you run the build — don't hand-edit them, they'll get overwritten.
- **`llms.txt`** (root, added 2026-07-14 from the SEO audit) — a plain-text brand summary + page map for AI answer engines (ChatGPT, Perplexity, AI Overviews), copied into `dist/` by build.py like `_headers`. Update it when pages are added/removed or the brand blurb changes. The per-event `image` in events.html's JSON-LD currently points at the og-image as an interim — swap each to its real flyer once that event's artwork exists.
- `pages/404.html` renders through the same layout/nav/footer as every other page and is excluded from the sitemap. Most static hosts (Netlify, GitHub Pages, etc.) auto-serve a root `404.html` for unmatched routes with no extra config.

## How it's structured

```
partials/layout.html   the ONE shared page shell — nav, mobile menu, social rail, footer
pages/*.html            per-page source: front-matter + body content only
build.py                 stitches partials + pages -> the root-level HTML files
scripts/                 reusable CLIs: image prep, press kit, site health check (see below)
assets/                  css, js, images, video (unchanged, edited directly)
index.html, events.html, ...   GENERATED — don't hand-edit, run build.py instead
```

## Running the site while editing

`python3 build.py --serve` rebuilds automatically on every save (watches
`pages/*.html`, `partials/layout.html`, `style.css`, `main.js`) and serves the
result on `http://localhost:8743` in one process — no separate "rebuild, then
restart the server" step. `--serve 8800` picks a different port. Plain
`python3 build.py` still does a one-shot build if you just want to check the
output without a server. CSS/JS cache-busting (`?v=...`) is a content hash
computed automatically at build time — nothing to bump by hand anymore.

The project's `.claude/launch.json` (at the `Claude/` root, one level up from
this folder) has two preview configs pointed at this: `underground-garden`
(port 8743) and `underground-garden-alt` (port 8744) — use the `-alt` one if
another session already has 8743 running, instead of hand-editing the launch
config each time.

## Making changes

**Nav, footer, mobile menu, social links (site-wide):**
Edit `partials/layout.html` once, then run the build.

**Page content, copy, sections:**
Edit the matching file in `pages/`. Each page source looks like:

```
---
title: Events — Underground Garden
description: ...
active: events              <- must match a key in build.py's NAV_ITEMS
nav_cta_label: Get Tickets
nav_cta_href: #calendar
---
<!-- head -->
<style> ...page-specific CSS, optional... </style>
<!-- body -->
  ...everything that goes inside <main>...
<!-- scripts -->
<script> ...page-specific JS, optional... </script>
```

`<!-- head -->` and `<!-- scripts -->` are optional; `<!-- body -->` is required.

**Styling / animation / design tokens (site-wide):**
Edit `assets/css/style.css` directly — colors, type, spacing, the `.type-break`
and `.social-rail` components, etc. all live there.

**Page rhythm — `.type-break` placement is deliberate, not uniform (2026-07-06):**
Every page used to open `hero → type-break → content`, identically, site-wide — flagged in a design review as making every page feel like the same template reskinned. Fixed by splitting pages into two rhythms on purpose:
- **Manifesto pages** (Home, About, Subtropics) keep `hero → type-break → content` — these are brand/story pages where the oversized duplicated-text statement earns its place emotionally.
- **Utility pages** (Events, Merch, Contact, FAQ) go straight from `hero → content`, no type-break — these are pages people land on to *do* something (buy a ticket, find an answer), so getting to the content fast matters more than the ceremony.
- **Gallery** is a hybrid: type-break is repositioned *mid-page*, between the recap video and the photo grid, functioning as a browsing break rather than a gate before any content.

**When adding a new page, decide which bucket it's in before copying another page as a starting template** — don't reflexively add a type-break after the hero just because most examples have one; check whether the new page is manifesto-like (keep it) or utility-like (skip it), per the above.

**Adding a new page:**
1. Add a line to `NAV_ITEMS` in `build.py` (label, filename, active-key).
2. Create `pages/newpage.html` with front-matter + body.
3. Add a link to it in the footer's "Explore" list in `partials/layout.html` if it should show up there too.
4. Run the build.

**Section-break divider (`.vine-divider`, identical markup on every page except 404):**
- Renders as `<div class="vine-divider" aria-hidden="true"><img src="assets/img/brand/ug-wordmark-vine.png" alt="" loading="lazy" width="640" height="334" /></div>`, flanked by two bone-dim lines drawn via CSS `::before`/`::after` (see `.vine-divider` in `style.css`).
- The image is the real "UNDERGROUND GARDEN" wordmark + vine flourish from `UG SHIRT FRONT LOGO.psd` (Chris's shirt design), trimmed to its content bounding box and downsized to 640px wide — not a generated graphic. If it ever needs re-exporting from a new PSD, run `python3 scripts/prep_image.py trim "source.psd" assets/img/brand/out.png --max-width 640`.
- Don't try to isolate just the vine tendril without the wordmark text — in the source art the vine is drawn threading behind/through the "GARDEN" letterforms, so it can't be cropped out cleanly without redrawing the stub-lines where it meets the letters.

**Merch page (`pages/merch.html`) — teaser mode as of 2026-07-10:**
- **The page is intentionally a teaser right now, not a live store** — Chris's call, to keep it simple until there's real stock/fulfillment ready to sell against. The "Featured" section shows the tee photos + copy but ends in "Exclusive drops coming soon. Be the first to find out." + a "Join The List" button (anchors to the `#signup` section at the bottom), not a real buy button.
- **The real Square checkout still exists, just commented out** — see the `<!-- STORE CHECKOUT ... -->` HTML comment right after the Featured section. To go live again: delete the teaser `<p class="lede mt-2">`/`<a class="btn btn--primary">` pair and uncomment that block in their place. The `.square-buy-btn`/`.square-buy-btn__link` CSS it depends on was left untouched in the page's own `<style>` block, so nothing else needs restoring. The Square Buy Button link itself (`https://square.link/u/rPpHr7tH?src=embed`) is the same one from before — Square Dashboard → Payments & orders → Payment links → Share → Buy Button is where to generate a new one if this item's listing ever needs to change.
- **"Future Drops" is also commented out** (see the `<!-- FUTURE DROPS ... -->` block) since there was nothing queued up behind the featured tee to tease — an empty "Coming Soon" grid was just noise. Uncomment the whole section once a next drop is confirmed enough to preview, then replace `<div class="placeholder-tile placeholder-tile--merch">...</div>` tiles with `<img src="assets/img/yourphoto.jpg" alt="..." loading="lazy" width="W" height="H" />` as each photo is ready (same pattern used everywhere else on the site — see Gallery page for lots of examples).
- To add a second featured product (once selling again), duplicate the whole `<div class="grid grid--2 reveal-group">...</div>` block (the one with the section-head "Coming Soon"/product name above it) and give it its own heading. Each product needs its own Square payment link + Buy Button — they're one-item-at-a-time, not a shared cart. If UG ever needs a real multi-item cart (buy a tee + a hat in one checkout), that's a Shopify-tier decision, not a Square one — flagged, not built, since it's a real monthly cost and only worth it once there are enough simultaneous live drops to matter.

**Images are WebP on the page, JPG on disk (2026-07-14):**
- Every content photo/flyer `<img>` (and the Gallery video poster) references a `.webp` file — typically 50-70% smaller than the JPG at the same visual quality. **The original `.jpg` files stay in `assets/img/` as the editing source of truth** — don't delete them; they're what you re-crop/re-process from, and they're never downloaded by visitors.
- **When adding any new photo or flyer:** process the JPG as usual (stretch/crop/compress), then run `python3 scripts/prep_image.py webp assets/img/newphoto.jpg` — it writes `newphoto.webp` next to it (plus `newphoto-800w.webp` if the source is wider than 1000px), and the `<img>` should reference the `.webp`.
- Photos wider than 1000px that sit in the standard grids also carry `srcset`/`sizes` so phones download the 800px variant instead of the full 1400px file — copy the pattern off any existing grid image on the same kind of grid (`grid--2` vs `grid--4` use different `sizes` values). Flyers are all under 1000px wide and skip srcset entirely.
- Brand marks and sponsor logos stay PNG (transparency + tiny files already); `og-image.jpg` stays JPG (see the SEO section).

**Past Events flyers (`pages/events.html`, "Archive" section) — how to add/reorder:**
- Order is newest-first, left-to-right / top-to-bottom (grid is `grid--4`, wraps automatically — any number of flyers works, no fixed slot count).
- Every slot is the same uniform size — `<div class="media-card media-card--flyer tilt-a|b reveal"><img src="assets/img/events/FILE.webp" alt="..." loading="lazy" width="W" height="H" /></div>` — alternate `tilt-a`/`tilt-b` for the subtle stagger look. **(Changed 2026-07-10, Chris's call:** this grid used to feature every 3rd flyer at 2x size via `media-card--featured` + a `.media-card-pair` wrapper for its neighbors — removed for a simpler, uniform grid. If you see either of those classes referenced anywhere, that pattern is gone; don't reintroduce it without Chris asking.)
- **Flyers render with `object-fit: contain`, not `cover`** (see `.media-card--flyer img` in `style.css`) — guarantees the full flyer is always visible with zero cropping, since a flyer carries text/lineup info edge-to-edge and any cropping can clip it. Any small letterboxing (when a flyer's aspect ratio isn't an exact 4:5 match) shows the card's own dark background, not a hard edge.
- Flyers should still be reasonably close to a 4:5 canvas for a consistent look (not required to be exact anymore, since `contain` no longer depends on it) — `python3 scripts/prep_image.py stretch assets/img/events/newflyer.jpg` still works for de-padding/normalizing a new flyer to 4:5 if you want that consistency.
  After processing, set the `<img>` `width`/`height` attributes to the file's actual pixel dimensions (`sips -g pixelWidth -g pixelHeight file.jpg` to check).
- Filename convention so far: `assets/img/events/event-archive-NN-shortname.jpg`, `NN` zero-padded and ordered oldest→newest (so slot order in the HTML is the reverse of the filename numbers — newest file number goes in the first grid slot).

**Subtropics timeline scroll motion (`pages/subtropics.html`, added 2026-07-15):**
- The "Road to Subtropics" timeline has a scroll-scrubbed turquoise progress line (`.timeline-progress`) that travels down the static gradient line as you scroll, plus chapter dots that scale up (`.is-lit`) as the 70%-viewport "read line" passes them. Plain vanilla JS — deliberately NOT GSAP (CSP is `script-src 'self'`, and one scrub effect doesn't justify vendoring a library).
- It lives in exactly 3 places, all in `pages/subtropics.html`: the `.timeline-progress` CSS block in the page `<style>` (find `scroll-scrubbed`), the `<div class="timeline-progress">` element (kept as the LAST child of `.timeline` on purpose — putting it first would shift the `.reveal-group` nth-child stagger delays), and the `<script>` block at the bottom (find `Road to Subtropics`). **To remove the effect entirely, delete those 3 blocks — nothing else references them.** Honors `prefers-reduced-motion` (bar hidden via CSS + script exits early).

**FAQPage structured data (`pages/safety.html`, added 2026-07-15):**
- The FAQ page carries `FAQPage` JSON-LD in its `<!-- head -->` block mirroring the 10 visible Q&As. **If a question/answer is edited in the visible `<details>` accordion, update the matching JSON-LD entry too** (plain text only there — links/HTML aren't allowed in schema text fields).

**FAQ page (`pages/safety.html`, added 2026-07-03, content confirmed by Chris):**
- Combined "Ground Rules" (community values) + FAQ accordion (native `<details>/<summary>`, no JS — see `.faq-item` in `style.css`) on one page, per Chris's call to keep both together rather than splitting them.
- Nav label is "FAQ" (`NAV_ITEMS` in `build.py`, key `"safety"` — filename stayed `safety.html`, only the label changed) and the H1 is "Frequently Asked Questions." Also in the footer Explore list.
- **Ground Rules** is 6 cards: See Something Say Something, Respect, Consent Forward, Stay Hydrated, All Are Welcome, Leave It Better. To add a 7th, duplicate a `<div class="card reveal"><h3>...</h3><p class="lede mt-1" style="font-size:1rem;">...</p></div>` block in the `grid grid--3` — it wraps automatically, no fixed slot count.
- **FAQ** content (age policy, ID requirements, refunds, entry/re-entry, parking, tickets, accessibility, photo timing) was adapted from a BLNK CNVS-style FAQ template with Underground Garden's own info swapped in (contact email, Shotgun as the ticketing platform, real social links) — Chris has read through and confirmed it's accurate. To add a question, duplicate a `<details class="faq-item reveal"><summary>Question?</summary><p>Answer.</p></details>` block.

**Press kit (`assets/press/ug-press-kit.zip`, linked from the General & Press tab on Contact):**
- Contains `ug-mark.png`, `wordmark.png`, `og-image.jpg`, and a `brand-boilerplate.txt` (About blurb, contact email, brand colors, fonts). Run `python3 scripts/build_press_kit.py` to regenerate it after swapping any of those source files — edit the `BOILERPLATE` string at the top of that script if the blurb/colors/contact info ever changes.
- Deliberately folded into the existing Contact page rather than a separate nav page/section — keeps the 8-item nav from growing to 9 for something press/sponsors already had a landing spot for.

**Venue map (Contact page, "Direct Lines" card):**
- An OpenStreetMap `export/embed.html?bbox=...&marker=...` iframe — no API key, no account. Tried Google's classic no-key `maps.google.com/maps?q=...&output=embed` trick first; Google now blocks that embed (`ERR_ABORTED`) without a Maps Embed API key, so this uses OSM instead. Currently a general Miami/Fort Lauderdale-area bbox with one marker since venues rotate per event — to point it at a specific address later, get a bbox/marker from openstreetmap.org's own "Share" panel (search the address there, click Share, copy the embed HTML's bbox and marker values into the `src`).

**Sponsors & Collaborators carousel (`pages/contact.html`):**
- It's a horizontal scroll-snap carousel (`.carousel` / `.carousel-track` / `.carousel-item`), not a static grid — swipeable on touch, prev/next arrow buttons on desktop (hidden under 620px). Logic lives in `assets/js/main.js` under `[data-carousel]`.
- To add a sponsor: duplicate one `<div class="card carousel-item text-center" style="display:flex; align-items:center; justify-content:center;"><img src="assets/img/logos/NAME.png" alt="..." /></div>` block. No inline sizing needed — `.carousel-item img` (in style.css) auto-scales any logo to fit the fixed-size card via `object-fit: contain`.
- Logo ink color matters: dark/black-ink logos need a light backdrop to read against the dark card — wrap the `<img>` in `<span style="background:var(--bone); border-radius:4px; padding:10px 14px; display:inline-flex;">`. Light/colored-ink logos (red, blue, white — e.g. Shotgun, which is white ink) can sit directly on the card with no wrapper. Check the actual file's ink color before assuming; don't guess from the brand name.

**Brand mark / nav logo (`assets/img/brand/`):**
- The nav wordmark is a real PNG (`wordmark.png`), not text/SVG — it's black ink on transparent, so `.brand-mark img` applies `filter: invert(1)` in CSS to flip it to bone/white for the dark nav. If the logo file is ever replaced, keep that in mind (a light-ink source logo would go invisible after the invert).
- `ug-mark.png` is the circular "U" mark used as the favicon.

## Tooling scripts (`scripts/`)

- **`prep_image.py`** — image prep CLI, run `python3 scripts/prep_image.py -h` for the full list:
  - `stretch FILE` — de-pad + stretch a flyer to fill its 4:5 canvas (see "Past Events flyers" above).
  - `trim SRC OUT --max-width N` — trim transparent margins off a logo/PSD export and downsize it.
  - `crop-bars FILE` — crop off solid-color letterbox bars from a photo (e.g. a phone screenshot with black bars), in place. Unlike `stretch`, this doesn't resize back afterward — use for cover-fit photos, not flyers.
  - `poster VIDEO OUT --at 20 --ratio 16:9` — grab a frame from a video at a timestamp and crop it to a target ratio, for use as a `<video poster="...">`. Requires `pip3 install opencv-python-headless` if not already present.
  - `compress FILE --quality 82` — recompress a JPG in place to shrink file size; use on anything that's grown past ~500KB.
  - `webp FILE` — write `FILE.webp` (+ `FILE-800w.webp` if wide) next to a JPG; run on every new photo/flyer (see "Images are WebP" above).
- **`make_og_image.py`** — regenerates `assets/img/brand/og-image.jpg` (real event photo + bone wordmark, see the SEO section). Rerun `build_press_kit.py` after.
- **`build_press_kit.py`** — regenerates `assets/press/ug-press-kit.zip` (see "Press kit" above).
- **`check_site.py`** — rebuilds the site and verifies every internal link/image/asset reference across every page actually resolves (HTTP HEAD check against a running local server). Run this after any batch of edits instead of manually curling files one at a time:
  ```
  python3 scripts/check_site.py --port 8743
  ```
- **`prep_video.py compress IN OUT --width 640 --crf 30`** — re-encodes a video smaller (H.264/AAC). No system `ffmpeg` exists in this environment; this uses the `imageio-ffmpeg` pip package instead (`pip3 install imageio-ffmpeg`), which bundles a static binary. Used to take the Gallery recap video from 17MB down to 7.8MB at 640px wide with no visible quality loss — that same recap video will need re-compressing again once Chris uploads the real edited aftermovie (see Gallery section below).

## Legal pages (`pages/privacy.html`, `pages/terms.html`, added 2026-07-06)

- Footer-only links (not main nav — see `partials/layout.html`'s `.footer-bottom`), same pattern as skipping a NAV_ITEMS entry that 404.html already used (`active: none` in front-matter).
- Added because the site collects real PII (name, email, phone number) across 7 forms for email/SMS marketing — SMS platforms and ad/analytics platforms generally expect a linked privacy policy, and it's a baseline credibility/trust signal regardless.
- **These are a reasonable baseline, not a substitute for actual legal review** — if Underground Garden wants airtight TCPA/CCPA compliance, an actual lawyer should look at the SMS consent language and data-handling sections before leaning on this in a dispute.

## Event structured data (`pages/events.html`, added 2026-07-06)

- JSON-LD `Event` schema (one entry per calendar card) in the page's `<!-- head -->` block, for Google's event rich results in search.
- Dates are intentionally reduced-precision (`"2026-07"`, not a fake specific day) since exact dates aren't announced yet — update each `startDate` to a full ISO date once it's confirmed, and consider adding a `price` to the `offers` block once ticket prices are announced. Uses `{{SITE_URL}}` like everything else, so it'll silently stay relative until a domain is set (already is: `ugevents.com`).

**⚠️ Same event, data lives in 3 places on purpose — keep the facts in sync:**
The same 4 events appear in `pages/events.html`'s calendar cards, the JSON-LD block above, and `pages/subtropics.html`'s timeline. **As of 2026-07-10, the visible calendar cards and timeline items are intentionally description-free** (title/tag/date/button only, no descriptive lede paragraph, per Chris's call to simplify both) — the JSON-LD block still carries a `description` per event for Google's rich results, since that's not user-visible UI copy. What has to match across all 3 places is just the **facts** — the month/year and the ticket URL. Reference table:

| Event | Date | Ticket URL |
|---|---|---|
| Chapter One | Late Aug 2026 | shotgun.live/en/venues/underground-garden-events |
| Chapter Two | Oct 2026 | shotgun.live/en/venues/underground-garden-events |
| Give Back Bass Night | Nov 2026 | *(no ticket link — donation event, CTA goes to Contact)* |
| Chapter Three | Dec 2026 | shotgun.live/en/venues/underground-garden-events |

If any of these change, update: the `event-date` badge + JSON-LD `startDate` in `events.html`, and the timeline eyebrow date in `subtropics.html`.

## Building & previewing

`python3 build.py --serve` (or the `.claude/launch.json` configs, which run
exactly this) rebuilds automatically on every save and serves the result —
**there is no separate "run build.py after editing" step while a `--serve`
process is running.** Just edit `pages/*.html`, `partials/layout.html`,
`style.css`, or `main.js` and refresh the browser.

The one exception: **editing `build.py` itself** (e.g. `NAV_ITEMS`,
`SITE_URL`, adding a new page's build wiring) requires the running server
process to restart, since Python can't hot-reload its own already-loaded
source. `watch_loop` detects this and restarts itself automatically
(`os.execv`) within about a second — you don't need to manually kill/restart
the preview server, just give it a moment after saving `build.py`.

CSS/JS cache-busting (`?v=...`) is a content hash computed automatically at
build time (see `file_hash()` in `build.py`) — nothing to bump by hand.

Plain `python3 build.py` (no `--serve`/`--watch`) still does a one-shot build
if you just want to check the generated output without running a server.

## Deploying (GitHub + Netlify continuous deploy, live at ugevents.com since 2026-07-10)

This repo is connected to Netlify via GitHub — **push to the repo's main
branch and Netlify builds + deploys automatically.** No manual upload step.

> ⚠️ **Unverified as of 2026-07-14:** the deploy that went out that day had
> new content but none of netlify.toml's header/redirect rules, which is
> the signature of a *manual* deploy (drag-and-drop or CLI upload of
> `dist/`), not a git-triggered CI build. Check the Netlify dashboard →
> Deploys tab: if the latest deploys say "manual deploy" rather than
> naming a git commit, the GitHub connection isn't actually building on
> push and needs reconnecting (Site configuration → Build & deploy →
> Link repository). The `_headers`/`_redirects`-in-dist setup (see above)
> makes headers work either way, but CI should still be fixed so future
> pushes deploy without a manual step.

- `netlify.toml` (repo root) tells Netlify everything it needs: build
  command `python3 build.py`, publish directory `dist`. Netlify runs the
  build itself on its own servers on every push — `build.py` only needs
  Python's standard library, no `pip install` step required.
- `netlify.toml` also carries (added 2026-07-14, live only on Netlify — the
  local Python server ignores all of it):
  - **Security headers** on every path (X-Frame-Options, nosniff,
    Referrer-Policy, Permissions-Policy, HSTS), plus a
    **Content-Security-Policy** (added later on 2026-07-14) that allowlists
    exactly the third parties in use: GA4, Web3Forms, and the OpenStreetMap
    iframe. ⚠️ **If a new third-party embed/script/service is ever added to
    the site, its host must be added to the CSP too** — it will work fine in
    local preview (which has no CSP) and silently fail in production
    otherwise. `unsafe-inline` is allowed on purpose (pages carry inline
    page-scoped `<script>`/`<style>` blocks by design).
  - **Headers/redirects live in the root `_headers` and `_redirects` files,
    NOT in netlify.toml** — build.py copies them into `dist/` so they apply
    on every deploy type. Rules in netlify.toml only work for git-triggered
    CI builds; the 2026-07-14 deploy turned out to be a manual deploy of
    `dist/` (see below) and shipped with no headers at all until these
    files existed. Edit `_headers`/`_redirects` at the repo root, never in
    `dist/` (generated), and never move the rules back into netlify.toml.
  - **Cache headers**: CSS/JS cache for a year + `immutable` (safe because
    the `?v=<content-hash>` query param from `build.py` changes the URL on
    every edit); images/video cache for one week only, because this
    project's workflow swaps image files in place under the same filename.
  - **A 301 redirect `/index.html` → `/`** matching the homepage's
    canonical URL (see the SEO section above).
- `dist/` is 100% generated (see `build.py`'s `DIST_DIR` / `build_all()`) —
  it's git-ignored, never committed. Netlify creates its own copy during
  each build. Locally, `python3 build.py --serve` also serves straight out
  of `dist/`, so what you preview locally is exactly what Netlify publishes
  — nothing from `pages/`, `partials/`, `scripts/`, or `README.md` is ever
  publicly reachable on the live site.
- **To ship an update:** just `git add`, `git commit`, `git push` from this
  project folder like normal — no separate build/upload dance. Netlify
  picks up the push, runs `python3 build.py`, and publishes the fresh
  `dist/` within a minute or two. Check the Netlify dashboard's Deploys tab
  if you want to watch it happen or see build logs.
- If a deploy ever fails on Netlify's side, the build log there will show
  the same output `python3 build.py` prints locally (e.g. a page missing
  required front-matter) — reproduce it locally first with a plain
  `python3 build.py` before debugging on Netlify's end.
