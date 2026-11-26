# Literature Survey and Technical Review

**Project:** Clubbb — a student club portal, plus the course-material site (OpenCSE) and
the Type Garden typographic experiment built alongside it.

**Scope of this survey.** There is very little academic literature on "a college club
portal", so this review covers the systems and sources the work actually draws on:
open course-material repositories, student-club platforms, generative typography,
real-time graphics on the web, design systems, and the tooling used to build and
evaluate the result. Each source is cited with a URL and a note on what was taken
from it, if anything.

---

## 1. Introduction

Two problems motivated the work.

The first is **institutional memory loss**. Course notes, model question papers and
revision advice circulate in messaging groups and personal drives; they disappear
when a cohort graduates, and each new cohort repeats the collection work. Open
course-material repositories attempt to fix this with version control and a static
site.

The second is **fragmented student life**. Clubs each maintain a separate presence —
a group chat, a form that circulates once a year, a poster for an event. Students
cannot see what exists, and clubs cannot see who applied. A shared portal addresses
discovery, application and event visibility in one place.

The work therefore produced three artefacts:

1. **OpenCSE** — a course-material repository and static site for a CSE syllabus
   (first year to semester 8, 49 courses, 1,300+ files, 47 revision sheets).
2. **Clubbb** — a self-hostable club portal: registration, custom club pages,
   events, calendar, RSVP and applications.
3. **Type Garden** — a standalone generative-typography toy in which stems and roses
   grow out of typed letters.

The survey below records the references that shaped them, the methods used, and the
limits of the evaluation.

---

## 2. Related work

### 2.1 Open course-material repositories

**OpenISE** (`github.com/changyicheng1234/OpenISE`) is the direct model for OpenCSE.
It collects Sun Yat-sen University course material as a 4 GB tree of per-course
folders, each with a `README.md` carrying revision strategy and grade breakdown.
Its site is generated from the repository and served as static HTML. Two design
decisions were adopted: material is grouped **by course, then by semester and
contributor**, and every course page ends with a written strategy rather than a file
dump. Two were rejected: committing multi-gigabyte binaries to Git (no Git LFS), and
unstructured folder names.

**HITSZ Course Sharing** (`hoa.moe`) is cited by OpenISE as its own inspiration and
follows the same pattern: one page per course, contributions by pull request,
Creative Commons licensing. It confirms the model generalises across institutions.

**MIT OpenCourseWare** (`ocw.mit.edu`) and **awesome-courses**
(`github.com/prakhar1989/awesome-courses`) were reviewed as contrast: they are
curated catalogues, not student-maintained archives. Their strength is metadata
quality; their weakness is that they do not capture assessment patterns or local
teaching quirks, which is exactly what a student-run archive does well.

### 2.2 Club and event platforms

**Presence in commercial products.** CampusGroups, Engage (Anthology) and
Microsoft Teams-based club sites all offer club directories and event calendars,
but they are institution-licensed and require single sign-on. The requirement here
was the opposite: a small, unlicensed, self-hostable system that a student can run
on a department server.

**Static-first alternatives.** GitHub-based club sites (for example the many
`awesome-club` repositories and Jekyll/Hugo club pages) are simple but put
registration and RSVP out of reach: every change becomes a pull request.

Clubbb takes a middle path — a single Python process with SQLite, no framework and
no accounts. Club identity is a random manage token whose hash is stored; this is
the minimum viable substitute for authentication and is discussed in §4.4.

### 2.3 Generative typography

**Type Garden** (`type-garden.vercel.app`, by Akshat Agarwal) is the origin of the
third artefact. Its idea: typed letters grow botanical stems and roses, space cuts
the growth, backspace withers, enter clears. The original is a React component
written for a design tool and uses a commercial typeface. Our port reimplements the
behaviour in plain canvas JavaScript — letter layout with wrapping, per-letter
seeded growth, bezier stems, petal blobs, partial-stroke growth animation, boil
jitter, pointer-reactive lean and multi-palette rendering — as one self-contained
HTML file, replacing the typeface with Playfair Display and the interface with
DM Mono, both open fonts.

Related generative-typography practice includes **p5.js** sketches
(`p5js.org`) and the **Processing** community's text-as-geometry work. The common
technique is the same: sample glyph geometry, attach parametric growth to anchor
points, and animate a progress parameter. Type Garden's addition is the
space/backspace/enter grammar, which makes the output feel like writing rather than
generating.

### 2.4 Real-time graphics on the web

**Active Theory** (`activetheory.net`) was reviewed as the high-water mark for
WebGL-driven marketing sites: a persistent 3D scene, scroll-linked camera movement
and pointer parallax. Only the *technique* was adopted — a particle field with
depth fog, additive blending and camera reaction — not assets, code or trade dress.
The same technique appears in Three.js examples (`threejs.org/examples`) and in the
WebGL fundamentals literature (`webglfundamentals.org`).

**ASCII Magic** (`ascii-magic.com`) converts images and video into animated ASCII
art in the browser. From it we took the rendering idea (luminance-to-character
mapping, ordered dithering, scanlines) and the visual language (near-black ground,
one accent, uppercase mono labels, long marquees), not the product.
The relevant technical background is **ordered dithering / Bayer matrices**
(Ulichney, *Digital Halftoning*, MIT Press, 1987) and character-ramp rendering as
used in terminal image viewers.

### 2.5 Design systems and reference extraction

Two Figma files were used as formal references:

- a cyberpunk poster frame (`figma.com/design/19ex4KQCnvtNSW84REr9Ko`) — 2212×1045,
  9 px border, 46 px radius, a 200 px display face, cut-out figures;
- **Langard**, a landscaping template (`figma.com/design/BFOBRtiHFjOzVG1ep9G3xd`) —
  deep teal `#033040`, mint `#A9FFCA`, 120 px section padding, 128–266 px display
  sizes.

Both were read through the Figma API rather than eyeballed, which produced exact
tokens (colours, font families, sizes, radii, shadows). A third reference, the
**Spotify Wrapped** community file, turned out to be flat raster posters with no
tokens, and was used only for colour and motif.

Background on design tokens: the **W3C Design Tokens Community Group** format and
Salesforce's Lightning Design System papers on tokenised theming. The shade-family
approach used here — deriving wash, line, tint and deep variants from one palette
colour with `color-mix()` — follows the same principle at a much smaller scale.

### 2.6 Accessibility and evaluation

The evaluation checklist follows **WCAG 2.2** (`w3.org/TR/WCAG22`): 4.5:1 contrast
for body text, 3:1 for large text and UI boundaries, 44×44 CSS-pixel targets,
visible focus, reduced-motion support. Heuristic review follows Nielsen's ten
usability heuristics (visibility of system status, consistency, error prevention),
narrowed to what applies to a content site.

---

## 3. Method

### 3.1 Repository analysis

OpenISE was cloned and measured (files, extensions, per-folder sizes, Git history,
generator scripts, CI workflow) before anything was built. This produced the
structural model reused by OpenCSE: `courses/<group>/<course>/` with per-course
notes, past papers and generated pages.

### 3.2 Reference extraction

Design references were queried through the **Figma MCP server**
(`figma-developer-mcp`) with a personal access token. The tool returns a parsed node
tree: fills, gradients, strokes, effects, text styles and image references. Images
were exported with `download_figma_images`. Tokens were then mapped onto CSS custom
properties rather than copied as pixel values.

### 3.3 Implementation

- **OpenCSE:** a standard-library Python generator (Markdown subset → HTML), no
  build step, deployed by GitHub Actions to Pages.
- **Clubbb:** Python `http.server` + `sqlite3`, server-rendered HTML, one stylesheet,
  one small JS file. Club registration issues a manage token (SHA-256 stored);
  admin approval gates publication; events, RSVPs and applications are relational
  tables; a `.ics` feed exposes the calendar.
- **Type Garden:** canvas 2D, seeded RNG per letter, partial-stroke growth.

### 3.4 Evaluation

Three layers:

1. **Automated browser QA** with **Playwright**: every page × six palettes ×
   1440/768/390, checking console errors, failed requests, horizontal overflow,
   video readiness, canvas pixels painted, contrast ratios computed from rendered
   colours, and touch-target sizes.
2. **Heuristic design review** against the ASCII-Magic reference: hierarchy, type
   scale, spacing rhythm, edge alignment, colour count, motion.
3. **Functional tests**: register → approve → publish event → RSVP → read people
   page, plus duplicate-RSVP and capacity guards.

---

## 4. Findings

### 4.1 Theming is a token problem, not a colour problem

The first implementation changed background and accent per palette and left every
other token at its dark-theme value. The result was measurable breakage: hairlines
at 1.48:1 on black, search fields with dark text on dark backgrounds, calendar cells
that were black-on-black in two palettes. Completing the token set (line, field,
card, tint, deep accent) fixed all of them at once. **A palette is a family of
shades, not a background colour.**

### 4.2 Reference fidelity needs extraction, not imitation

Reading the Figma frames produced exact values (9 px border, 46 px radius, 200 px
display) that no screenshot estimate would have given. Conversely, the community
"Wrapped" file offered no tokens at all, and treating it as a design system produced
incoherent results. The lesson: a reference is useful in proportion to how much of
it can be read structurally.

### 4.3 Motion must be scroll-aware but not scroll-dependent

Reveal and parallax were added with `IntersectionObserver` and passive scroll
listeners, disabled under `prefers-reduced-motion`. The site remains fully usable
with JavaScript disabled. Scroll-linked animation that gates content is the common
failure mode in reference-driven redesigns.

### 4.4 Token-based club identity has a real cost

Without accounts, a lost manage link orphans a club page. This is documented in the
README rather than hidden. For a campus deployment, an SSO hand-off or an emailed
recovery link would be the next step.

### 4.5 Automated QA caught what visual review missed

The design review flagged taste; Playwright flagged that the hamburger menu had no
menu behind it, that ghost buttons were filled by a late CSS rule, and that the
seasonal video wrapper was 0 px tall. Neither review alone would have found both.

---

## 5. Limitations

- No user study. Evaluation is automated plus heuristic; no students used the portal.
- The dataset is one institution's syllabus; course codes vary between schemes.
- Some source papers in the archive are image-only scans, so a few question banks
  are thinner and say so on the page.
- The portal is not deployed publicly; it is a local/self-hosted artefact with a
  Dockerfile and a systemd unit.
- Figma community files cannot be read through the API (404); only files owned by
  the token holder are accessible.

---

## 6. References

1. OpenISE — https://github.com/changyicheng1234/OpenISE
2. HITSZ Course Sharing — https://hoa.moe/
3. MIT OpenCourseWare — https://ocw.mit.edu/
4. awesome-courses — https://github.com/prakhar1989/awesome-courses
5. Type Garden — https://type-garden.vercel.app/
6. ASCII Magic — https://www.ascii-magic.com/landing
7. Active Theory — https://activetheory.net/
8. Langard template — https://www.figma.com/design/BFOBRtiHFjOzVG1ep9G3xd
9. Cyberpunk poster frame — https://www.figma.com/design/19ex4KQCnvtNSW84REr9Ko
10. Spotify Wrapped community file — https://www.figma.com/design/nE7lgr2UIC4vLfouNDQsI6
11. Figma REST API — https://www.figma.com/developers/api
12. Model Context Protocol — https://modelcontextprotocol.io/
13. Playwright — https://playwright.dev/
14. WCAG 2.2 — https://www.w3.org/TR/WCAG22/
15. Ulichney, R. *Digital Halftoning*. MIT Press, 1987.
16. Nielsen, J. *Usability Engineering*. Morgan Kaufmann, 1993.
17. p5.js — https://p5js.org/
18. three.js — https://threejs.org/examples/
19. WebGL Fundamentals — https://webglfundamentals.org/
20. Creative Commons BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/
21. MIT License — https://opensource.org/license/mit

---

*Prepared alongside the code; last updated with commit `b89b6c5` of the Clubbb
repository.*
