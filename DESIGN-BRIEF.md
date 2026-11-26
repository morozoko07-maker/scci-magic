# SCCI Magic — design brief and prompt pack

Living document for anyone — human or AI — designing for SCCI Magic. It records the portal
as it exists and the direction new work must follow. Update the token tables when
`static/style.css` changes.

Stack: Python 3 standard library, SQLite, server-rendered HTML, one stylesheet, small
vanilla JS. No build step, no framework, no accounts, no tracking. Routes live in `SPEC.md`;
templates are f-strings in `app.py`.

## 1. The brief

**Product.** A self-hostable student club portal. Clubs register without an account, get a
private manage link, customise a page and publish events. Students browse, read one
calendar, RSVP and apply. An administrator approves clubs before they go live.

**Audience.** Students aged 17–24, scanning on a phone between lectures; club committees of
one or two unpaid people; a department administrator who wants few surprises.

**Jobs to be done.**
- Student: “Is there a club for this, and what is on this week?” → find it, understand it,
  RSVP or apply in under a minute.
- Club: “Give us a page and a way to collect names.” → register, customise and publish in
  under ten minutes without documentation.
- Admin: “Is this legitimate?” → approve or reject with enough context, safely.

**Tone.** Plain, direct, lightly warm. A competent student explaining something to another
student. Sentence case, short sentences, British English. No exclamation marks, no
“unleash”, “elevate”, “seamless”, no rhetorical questions. Numbers only from the database.

**Success.** A first-time visitor can name three clubs and one event after five seconds. The
paths home → club → apply and home → event → RSVP have no dead end and no account wall. A
club page can be created and published by keyboard alone. Every page works with JavaScript
off. All five palettes feel like one product. No layout shift from video; no horizontal
scroll at 360px.

**Avoid.** Violet or purple as a brand colour. Glassmorphism, frosted panels, backdrop blur.
Gradients, including “subtle” mesh and glow. Emoji as icons or decoration. Invented
statistics, testimonials, member counts, logos or “trusted by” rows. Stock copy
(“empowering the next generation of leaders”). Rounded blobs, pill-shaped cards, large soft
shadows, floating action buttons. Carousels that hide content. Icons where a word is clearer.
Animation that delays reading.

**Direction.** `ascii-magic.com/landing`: near-black ground, white type, 1px borders, square
corners, mono labels, very large display headings, ASCII and dithered imagery, long
marquees, short hover transitions. Restraint is the style; one loud element per screen.

## 2. The design system as it exists

### Colour tokens

Five palettes are the public system. `html[data-theme]` selects one; JS also accepts
`?theme=` and stores the choice under `portal-theme`. Defined in `style.css` lines 545–575.
Legacy `dark`/`light`/`midnight` tokens still exist; do not extend them.

| Token | Variable | Role | Rule |
|---|---|---|---|
| bg | `--bg` | Page ground | Palette-defining; full-bleed. |
| ink | `--ink` | Body and headings | 4.5:1 minimum on bg. |
| muted | `--muted` | Secondary text, meta | Small text still needs 4.5:1. |
| accent | `--accent` | CTA fill, links, focus | See contrast debts. |
| accent ink | `--accent-ink` | Text on accent fill | Pair only with accent. |
| flower | `--flower` | Garden petals | Decorative, never the only signal. |
| stem | `--accent-2` | Garden stems, secondary detail | Decorative; not a UI state. |
| border | `--border` / `--line` (legacy) | 1px hairlines | Exactly 1px. |
| strong | `--strong` / `--line-strong` | Input and hover borders | One step louder than border. |
| surface | `--surface`, `--panel` | Cards, panels, wells | One step from bg, never a gradient. |
| radius | `--radius` | Corners | 5px legacy default; 0 is the target for new work. |

| Palette | bg | ink | muted | accent | flower | stem |
|---|---|---|---|---|---|---|
| rose | `#000000` | `#FFFFFF` | `#9A9A9A` | `#FF1400` | `#FF1400` | `#3257FF` |
| paper | `#F3EEE4` | `#111111` | `#5F5E58` | `#FF3B1F` | `#FF3B1F` | `#1C2B8F` |
| tomato | `#FF1400` | `#000000` | `#5A0D00` | `#000000` | `#FFF1E0` | `#0B0B0B` |
| butter | `#FFE9A8` | `#1A1A1A` | `#6B5A20` | `#E4002B` | `#E4002B` | `#0F5132` |
| blush | `#FAD4D8` | `#1A1A1A` | `#6B4A50` | `#C8102E` | `#C8102E` | `#274690` |

**Contrast debts.** Against each palette's bg: paper accent 3.08:1, tomato muted 3.59:1,
butter accent 4.03:1, blush accent 4.34:1. Use accent as a fill or large-text colour there
and `--ink` for small text. Do not add new failures.

### Type

| Role | Family | Weight | Size and spacing |
|---|---|---|---|
| Display XL (new work) | Funnel Display | 500–600 | `clamp(3.25rem, 9vw, 8rem)`, line 0.95–1.02, −0.04em |
| H1 (current) | Funnel Display | 600 | `clamp(2rem, 1.6vw + 1.6rem, 3.2rem)`, line 1.12, −0.035em |
| H2 / H3 | Funnel Display | 600 | `clamp(1.4rem…1.9rem)` / `clamp(1.08rem…1.25rem)` |
| Body | Geist | 300–500 | `clamp(16px, 0.25vw + 12.6px, 18px)`, line 1.62, measure 60–68ch |
| Label, eyebrow, table head | Geist Mono | 400–500 | 10–11px, uppercase, tracking 0.06–0.14em |
| Garden heading | Playfair Display | 500–600 | Inherits H1; only via `data-garden` |

Funnel Display, Geist and Geist Mono load from Google Fonts in `app.py`. Playfair Display is
referenced by `garden-heading.js` but is not in the font link, so it falls back to Georgia.
Add it (self-hosted WOFF2 preferred) before treating garden headings as finished.

### Spacing, grid, shape

Base unit 4px: 4, 8, 12, 16, 24, 32, 48, 64, 96. Round to the nearest step rather than add a
token. Shell `clamp(980px, 86vw, 1240px)`; gutter 28px, 20px below 600px; section rhythm
`clamp(32px, 4vw, 56px)`; card padding 18–24px; grid gap 14–16px. Borders 1px. New components
use radius 0; 5px exists on cards, inputs and badges; pills use 999px. No new intermediate
radii. Shadows: none, or the 8px offset block on media bands. No soft elevation, no glass.

### Motion

| Event | Duration and easing |
|---|---|
| Hover, colour, border | 150ms ease |
| Press | `translateY(1px)`, 150ms |
| Marquee | 32s linear, infinite, exact 50% loop |
| Garden grow | 520–860ms per element, ease-out, 40–130ms stagger |
| Hero video | 3–6s seamless loop, no visible cut |
| Theme switch | Immediate; swap palette and video, no crossfade |
| Reduced motion | 0.01ms, one iteration, transforms removed, marquee stopped |

Animate only transform, opacity, background, border and colour. No springs, bounce or text
parallax. Nothing may block reading or input.

## 3. Component inventory and markup contract

Class names are public API. Keep them and the `data-*` hooks that `app.js` uses.

### Nav
```html
<header class="bar">
  <a class="brand" href="/"><span class="mark">SM</span>SCCI Magic</a>
  <nav class="nav" aria-label="Primary"><a class="navlink is-active" href="/" aria-current="page">Home</a>…</nav>
  <div class="themes" role="group" aria-label="Colour theme">…</div>
</header>
```
Sticky, 64px minimum, 1px bottom border, no shadow. Mark 28×28; links 44px; one
`aria-current="page"`. Wrap below 900px; never hide links behind a hamburger.

### Palette switch
```html
<button type="button" data-theme-set="rose" aria-pressed="true">Rose</button>
```
Exactly five: rose, paper, tomato, butter, blush. JS owns `aria-pressed`, `<html data-theme>`,
`theme-color` and the hero video source. No-JS default is rose. Word labels, not swatches alone.

### Hero and video stage
```html
<section class="hero hero-split">
  <div class="hero-copy">
    <p class="eyebrow">Student clubs · one portal</p>
    <h1 data-garden="Every club on campus, in one place.">Every club on campus, <em>in one place.</em></h1>
    <p class="lede">One sentence of orientation.</p>
    <div class="hero-actions"><a class="btn" href="/clubs">Browse clubs</a></div>
    <div class="stats"><div><strong>12</strong><span>clubs</span></div></div>
  </div>
  <div class="ascii-stage"><video class="stage-video" data-clip="events" data-motion="grow" muted
    loop playsinline autoplay preload="metadata" aria-hidden="true" poster="/static/media/poster-events-rose.webp"></video>
    <span class="stage-tag">EVENTS · LIVE</span><span class="stage-idx">SM/01</span></div>
</section>
```
`data-clip` is `events` or `clubs`; `data-motion` is `grow` or `breathe`. Video is decorative:
muted, no controls, `aria-hidden`, poster required. Fallback: grow → breathe → poster → flat
accent. Stats only from database counts. Media band: `<div class="media-band"><video data-clip="clubs" …></video></div>`.

### ASCII banner
```html
<pre class="ascii" aria-hidden="true">{{ ascii_banner("SCCI MAGIC") }}</pre>
```
Generated server-side; decorative. Mono, 3–7px, line-height 1.05, `overflow: hidden`, max one
per page. Never the only page title.

### Marquee
```html
<div class="ticker" aria-hidden="true"><div class="ticker-track">
  <span>HACKATHONS</span><i>/</i><span>TALKS</span><i>/</i>
  <span>HACKATHONS</span><i>/</i><span>TALKS</span><i>/</i>
</div></div>
```
Duplicate the track exactly twice for a seamless −50% loop. Uppercase mono, 10.5px, 0.1em,
32s. No links, buttons or essential text inside. Stop under reduced motion.

### Club card
```html
<a class="club-card" href="/c/robotics" data-tags="technical" style="--club-accent:#FF1400">
  <span class="club-stripe"></span><span class="club-mono" aria-hidden="true">RC</span>
  <span class="pill">technical</span><h3>Robotics Club</h3>
  <p>One line students will remember.</p><span class="card-go">View club →</span>
</a>
```
Whole card is the link; no nested controls. 4px left accent bar via `::before`. `data-tags`
drives the filter and must match the category. Hover lifts 2px and changes border only.

### Event row
```html
<a class="event-row" href="/e/42" data-kind="workshop" style="--club-accent:#FF1400">
  <span class="date-block"><strong>14</strong><span>MAR</span></span>
  <span class="event-body">
    <span class="event-top"><span class="badge kind-workshop">workshop</span><span class="mono muted">Thu 14 Mar · 18:00</span></span>
    <strong>Intro to soldering</strong><span class="muted">Lab 2 · Robotics Club</span>
  </span>
</a>
```
Grid 76px + 1fr, 52px on mobile. Day is display type; month and time are mono. `data-kind` is
one of hackathon, talk, workshop, interview, meetup, sports, cultural.

### Event panel
```html
<a class="panel" href="/e/42" style="--club-accent:#FF1400">
  <img class="panel-img" src="/media/cover.jpg" alt="" loading="lazy">
  <canvas class="panel-canvas" data-shader data-src="/media/cover.jpg" data-seed="42" data-accent="#FF1400"></canvas>
  <span class="panel-body"><span class="badge kind-workshop">workshop</span>
    <strong class="panel-title">Intro to soldering</strong>
    <span class="panel-meta mono">Thu 14 Mar · 18:00</span><span class="panel-club">Robotics Club</span></span>
</a>
```
Minimum 220px tall; image cropped; caption on a solid surface. No cover means flat club
accent, not a placeholder illustration. Canvas is decorative; img is the fallback.

### Calendar
```html
<section class="cal card">
  <div class="cal-head">
    <a class="btn btn-ghost" href="/events?m=2026-02" aria-label="Previous month">←</a>
    <strong>March 2026</strong>
    <a class="btn btn-ghost" href="/events?m=2026-04" aria-label="Next month">→</a>
  </div>
  <div class="cal-week"><span>Mon</span>…<span>Sun</span></div>
  <div class="cal-grid"><div class="cal-day has-event" data-date="2026-03-14">
    <span class="dnum">14</span><a class="ev" href="/e/42">Intro to soldering</a></div></div>
</section>
```
Month links use `?m=YYYY-MM`; filters append `&kind=`. Cells expose `.is-today`,
`.has-event`, `.is-outside`. Today is an inset outline, not a fill. Below 900px event titles
hide and the dot remains; the list below carries detail. Gaps are the 1px border colour.

### Form
```html
<form class="form card" method="post" action="/e/42/rsvp">
  <div class="grid two">
    <label class="field"><span>Name</span><input name="name" required maxlength="80"></label>
    <label class="field"><span>Email</span><input name="email" type="email" required maxlength="120"></label>
  </div>
  <button class="btn" type="submit">Save my seat</button>
</form>
```
Visible mono labels wrapped around controls; never placeholder-only. Inputs 44px, 1px border,
2px accent focus. Errors in `.notice.error` above the form, linked with `aria-describedby`.
Keep field `name`s stable; handlers depend on them.

### Table
```html
<div class="tablewrap"><table>
  <caption>Applications</caption>
  <thead><tr><th scope="col">Name</th><th scope="col">Email</th></tr></thead>
  <tbody><tr><td>Sam Lee</td><td class="mono">sam@example.com</td></tr></tbody>
</table></div>
```
The wrapper scrolls horizontally; the page must not. Dates, emails and IDs use `.mono`. Empty
state is one row with `colspan` and `.muted`. Never remove headers on mobile.

### Notice
```html
<p class="notice error" role="alert">That email has already RSVP’d.</p>
```
One message each. 3px left border in accent, success or danger, with the matching soft tint.
`role="status"` for confirmation, `role="alert"` for errors. Do not stack more than two.

### Footer
```html
<footer class="foot">
  <p><strong>SCCI Magic</strong> · a student-run portal. Not affiliated with any institution.
     No accounts, no tracking, no ads.</p>
  <p class="muted">Clubs register themselves; an administrator approves before a page goes live.</p>
</footer>
```
Top border, mono 11px, muted. Two short paragraphs maximum. No link farm, social icons or
newsletter form. Keep the non-affiliation and privacy lines.

## 4. Five ready-to-paste prompts

Replace every `<PLACEHOLDER>`; keep the constraints. Each prompt is self-contained and
assumes the repository at `/home/miz/Projects/clubportal`.

### a. Redesign a page section
```text
Redesign one section of SCCI Magic: Python stdlib + SQLite, server-rendered HTML, one
stylesheet (static/style.css), templates in app.py, no build step. Read DESIGN-BRIEF.md.

Section: <NAME> on <ROUTE>. Current HTML: <PASTE>. Relevant CSS: <PASTE>.
Job: <ONE SENTENCE — what a student must understand or do here>. Mostly mobile, 360–430px.

Constraints: ascii-magic.com/landing direction; tokens only (DESIGN-BRIEF.md §2); 1px
borders; radius 0 for new work; Funnel Display/Geist/Geist Mono; no gradients, glass, violet,
emoji, stock copy or invented numbers. Keep class names, data-* hooks, routes and field names.
Work without JS; 360–1440; no horizontal scroll; 44px targets; focus-visible; reduced motion.

Deliver: section HTML; CSS under a new numbered section; four lines on changes, removals,
risks, tests. If it already meets the job, say so and propose at most two changes. Do not
rewrite the page or add dependencies.
```

### b. Build a new component
```text
Build one component for SCCI Magic: Python stdlib + SQLite, server-rendered HTML,
static/style.css, vanilla JS, no build step. Read DESIGN-BRIEF.md.

Component: <NAME>. Purpose: <WHAT IT LETS A USER DO>. Used on: <ROUTES>.
Data: <FIELDS AND TYPES, OR "static">. States: default, hover, focus-visible, active,
disabled, empty, error, loading if it submits.

Constraints: semantic HTML that works without JS; enhance only if unavoidable. Reuse
.shell, .section, .card, .btn, .badge, .pill, .field, .notice, .mono, .muted; prefix new
classes. 1px borders, radius 0, no shadows except an 8px offset block; no gradients, glass,
violet, emoji, icon fonts or UI libraries. Funnel Display/Geist/Geist Mono. Mobile-first at
360, 390, 768, 1440; 44px targets; 4.5:1 contrast; reduced motion shows the final state. All
five palettes via html[data-theme] must work.

Deliver: a one-paragraph contract (root, classes, attributes, slots, states); HTML; CSS under
a numbered section; minimal JS with no-JS fallback, if justified; a demo with realistic seed
data and a five-item test list. Do not invent endpoints, fields, copy or statistics.
```

### c. Figma → code
```text
Translate a Figma design into production code for SCCI Magic: Python stdlib + SQLite,
server-rendered HTML, static/style.css, no build step. Read DESIGN-BRIEF.md.

Figma: <FILE KEY OR URL>. Node: <NODE ID, e.g. 1234:5678>. Target: <ROUTE / COMPONENT>.
Breakpoints: 1440, 768, 390.

Extract before coding, using the Figma MCP tools (get_figma_data; download_figma_images only
for assets CSS cannot recreate). Report: palette — every fill and stroke mapped to --bg, --ink,
--muted, --accent, --flower, --accent-2, --border, with contrast pass/fail; type — family,
weight, size, line-height, tracking; spacing — padding, gaps, widths, snapped to the 4px
scale; motion — prototype durations and easing; assets — export size and format; deltas —
anything without a token or component equivalent.

If Figma conflicts with the brief, the brief wins; list the conflict. Reject gradients, glass,
blur, violet, emoji and radii other than 0/5/999px; replace with flat token equivalents.

Build: semantic HTML using existing classes and data-* hooks; CSS under a numbered section;
no absolute positioning for layout; no off-scale pixels except type and borders. Must work at
360 without horizontal scroll, 44px targets, focus-visible, reduced motion, all five palettes.
Deliver the token mapping, contract, HTML, CSS, asset specs and open questions.
```

### d. Visual QA with Playwright
```text
Run visual QA on SCCI Magic at http://localhost:8770. Do not change code during capture.
Save to /tmp/qa/<YYYY-MM-DD>/.

Capture full page at 1440×900, 768×1024, 390×844 and 360×800 for /, /clubs, /events,
/register, one /c/<slug> and one /e/<id>. At 1440, every route in all five themes via
?theme=rose|paper|tomato|butter|blush. At 390, home and events in rose, tomato and paper.
One keyboard pass, screenshotting the third and eighth focus stops. One pass with
prefers-reduced-motion: reduce.

Example:
npx playwright screenshot --viewport-size="1440,900" --full-page \
  "http://localhost:8770/events?theme=paper" /tmp/qa/2026-11-26/events-1440-paper.png

Check every shot: (1) no horizontal scroll at 360, no clipped text; (2) one clear H1 and sane
heading order; (3) 44×44 targets; (4) 2px accent focus ring, 2px offset, never obscured;
(5) text ≥4.5:1 and UI ≥3:1 in all palettes; (6) no gradients, glass, violet, emoji, blobs or
fake stats; (7) 1px borders, new radii 0, no soft shadows; (8) video poster, no layout shift,
visible fallback; (9) marquee legible and static under reduced motion; (10) visible form
labels and announced errors; (11) calendar states distinct without colour alone; (12) tables
scroll inside their wrapper; (13) no console errors or 404s; (14) British English, sentence
case, no exclamation marks or invented numbers.

Report: Route | Viewport | Theme | Issue | Severity P0/P1/P2 | Selector or screenshot.
P0 = broken task, accessibility failure or horizontal scroll. P1 = unclear or inconsistent.
P2 = polish. End with the three fixes worth doing first. No praise.
```

### e. Critique like a senior designer
```text
Critique this SCCI Magic screen as a senior product designer. Be specific and unsentimental.
Input: <URL, SCREENSHOT PATH, OR CODE>. Context: student club portal; students on phones and
unpaid club committees; direction is ascii-magic.com/landing — near-black ground, white type,
1px borders, 0 radii, mono labels, huge display type, ASCII imagery, long marquees, short
hovers; five palettes: rose, paper, tomato, butter, blush.

Judge in order: (1) five-second read — what is this, who is it for, what can I do, what did you
see first; (2) job — does the primary action match the page purpose, is anything competing;
(3) hierarchy — type scale, one H1, scan path, density, quote inferred sizes; (4) rhythm —
alignment, 4px spacing, border consistency, optical balance; (5) type — family roles, measure,
leading, tracking, wraps; (6) colour — tokens, contrast, accent discipline, coherence across
all five; (7) states — hover, focus, disabled, empty, error, loading, what is missing;
(8) content — plain British English, specificity, invented claims; (9) accessibility — targets,
focus order, semantics, reduced motion, alt text, contrast; (10) character — the most
distinctive element and the most generic, and whether it looks like this brief or a SaaS
template.

Score each dimension 1–5 with one sentence of evidence. Rank issues P0 (blocks a task or fails
accessibility), P1 (weakens comprehension or trust), P2 (polish). For each P0/P1 give the
smallest concrete fix: element, property, value. Do not redesign the page. End with three
fixes in order, one thing to keep, and a one-line verdict against the brief's success criteria.
```

## 5. Definition of done

- [ ] No horizontal scroll at 360, 390, 768 or 1440px.
- [ ] Interactive targets at least 44×44px, including icon-only links and theme buttons.
- [ ] `:focus-visible` is a 2px accent outline at 2px offset; never `outline: none` without a replacement.
- [ ] Body text ≥4.5:1; large text and meaningful UI boundaries ≥3:1, in all five palettes.
- [ ] `prefers-reduced-motion: reduce` stops marquee, garden growth, video motion and hover transforms.
- [ ] Informative images have useful alt text; decorative images use `alt=""` and `aria-hidden`.
- [ ] No console errors or warnings; no 404s for CSS, JS, fonts, video or posters.
- [ ] Hero videos have a poster, explicit aspect ratio and a working fallback chain.
- [ ] Keyboard: logical tab order, visible focus, no traps, forms submit with Enter.
- [ ] Semantics: one H1, landmarks, labelled nav, `scope` on table headers, labels tied to inputs.
- [ ] Works with JavaScript off: content readable, navigation and filters reachable, forms submit.
- [ ] British English, sentence case, specific copy, no invented numbers.
- [ ] No gradients, glass, violet, emoji, soft shadows, or radii outside 0/5/999px.
- [ ] Counts and names come from the database; empty states are honest.
- [ ] All five palettes checked at desktop and mobile, including tomato and paper accents.

## 6. Assets needed

| Asset | Spec | Naming | Status |
|---|---|---|---|
| Hero loop, per clip per palette | 1080×1080, VP9 WebM, 3–6s seamless, 24–30fps, sRGB, no audio, <8MB | `hero-<clip>-<motion>-<palette>.webm`; clip `events|clubs`, motion `grow|breathe` | 20 files exist but are VP8 at ~60KB; re-encode to VP9 and verify duration |
| Poster fallback | WebP, 1080×1080, quality 80, first frame, <120KB, no text | `poster-<clip>-<palette>.webp` | Missing; required before launch |
| Fonts | WOFF2, latin subset: Funnel Display 400/500/600, Geist 300–600, Geist Mono 400/500, Playfair Display 500/600 | `funnel-display-<weight>.woff2` etc. | Google Fonts link exists; Playfair not loaded; self-host with `font-display: swap` |
| Favicon | SVG, 32×32 viewBox, 1px strokes, works on all grounds | `favicon.svg` | Present |
| Theme colour | One `theme-color` per palette, matching `--bg` | in `app.py` and JS | Present; keep in sync |
| ASCII art | Generated by `ascii.js` / `ascii_banner()`; no bitmaps | n/a | Present |
| Copy deck | All UI strings, British English, sentence case, no placeholders | n/a | Scattered in `app.py`; consolidate only when touched |

Video direction: one slow “type garden” loop per palette — stems, leaves and petals growing
and breathing against the ground, accent as the flower. No camera moves, cuts or loop-point
fades; first and last frame must match. Encode with
`ffmpeg -c:v libvpx-vp9 -b:v 0 -crf 34 -an`; check with `ffprobe -show_entries format=duration`
(the current VP8 files report `N/A`).
