#!/usr/bin/env python3
"""Clubbb — a self-hostable club portal.

Python standard library only. Run:  python3 app.py  → http://localhost:8770
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import secrets
import sqlite3
import traceback
import urllib.parse
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PORTAL_DB", ROOT / "portal.db"))
STATIC = ROOT / "static"
DATA = Path(os.environ.get("PORTAL_DATA", ROOT / "data"))
UPLOADS = DATA / "uploads"
PORT = int(os.environ.get("PORT", "8770"))
HOST = os.environ.get("HOST", "127.0.0.1")

CATEGORIES = ["technical", "cultural", "sports", "social", "academic", "media"]
KINDS = ["hackathon", "talk", "workshop", "interview", "meetup", "sports", "cultural"]
BANNERS = ["solid", "grid", "dots"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS clubs (
  id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  category TEXT NOT NULL, tagline TEXT DEFAULT '', about TEXT DEFAULT '',
  accent TEXT DEFAULT '#8fa68e', banner TEXT DEFAULT 'solid',
  email TEXT DEFAULT '', instagram TEXT DEFAULT '', website TEXT DEFAULT '',
  join_open INTEGER DEFAULT 1, status TEXT DEFAULT 'pending',
  manage_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY, club_id INTEGER NOT NULL, title TEXT NOT NULL,
  kind TEXT NOT NULL, starts_at TEXT NOT NULL, ends_at TEXT DEFAULT '',
  venue TEXT DEFAULT '', description TEXT DEFAULT '', link TEXT DEFAULT '',
  capacity INTEGER DEFAULT 0, cover TEXT DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rsvps (
  id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL, name TEXT NOT NULL,
  email TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(event_id, email)
);
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY, club_id INTEGER NOT NULL, name TEXT NOT NULL,
  email TEXT NOT NULL, year TEXT DEFAULT '', message TEXT DEFAULT '',
  created_at TEXT NOT NULL
);
"""


# --------------------------------------------------------------------------
# storage
# --------------------------------------------------------------------------
def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def admin_key() -> str:
    key = os.environ.get("ADMIN_KEY")
    if key:
        return key
    f = ROOT / ".admin_key"
    if not f.exists():
        f.write_text(secrets.token_urlsafe(18))
        f.chmod(0o600)
    return f.read_text().strip()


def init_db() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    con = connect()
    con.executescript(SCHEMA)
    cols = [r[1] for r in con.execute("pragma table_info(events)")]
    if "cover" not in cols:
        con.execute("ALTER TABLE events ADD COLUMN cover TEXT DEFAULT ''")
    con.commit()
    con.close()


def save_upload(files) -> str:
    item = files.get("cover")
    if not item:
        return ""
    _filename, ctype, data = item
    if len(data) > 5 * 1024 * 1024:
        return ""
    sig = data[:12]
    if sig.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
    elif sig.startswith(b"\x89PNG"):
        ext = ".png"
    elif sig.startswith(b"GIF8"):
        ext = ".gif"
    elif sig[:4] == b"RIFF" and sig[8:12] == b"WEBP":
        ext = ".webp"
    else:
        return ""
    name = secrets.token_hex(10) + ext
    (UPLOADS / name).write_bytes(data)
    return f"/uploads/{name}"


def now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48]
    return s or "club"


def unique_slug(con: sqlite3.Connection, name: str) -> str:
    base = slugify(name)
    slug, n = base, 2
    while con.execute("select 1 from clubs where slug=?", (slug,)).fetchone():
        slug = f"{base}-{n}"
        n += 1
    return slug


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def club_by_slug(con, slug):
    return con.execute("select * from clubs where slug=? and status='approved'", (slug,)).fetchone()


def club_by_token(con, token):
    return con.execute("select * from clubs where manage_hash=?", (token_hash(token),)).fetchone()


def approved_clubs(con):
    return con.execute("select * from clubs where status='approved' order by name").fetchall()


def upcoming_events(con, limit=50, since=None):
    since = since or datetime.now().strftime("%Y-%m-%dT%H:%M")
    return con.execute(
        "select e.*, c.name as club_name, c.slug as club_slug, c.accent as club_accent "
        "from events e join clubs c on c.id=e.club_id "
        "where e.starts_at >= ? and c.status='approved' order by e.starts_at limit ?",
        (since, limit),
    ).fetchall()


def event_by_id(con, eid):
    return con.execute(
        "select e.*, c.name as club_name, c.slug as club_slug, c.accent as club_accent "
        "from events e join clubs c on c.id=e.club_id where e.id=?",
        (eid,),
    ).fetchone()


def rsvp_count(con, eid):
    return con.execute("select count(*) from rsvps where event_id=?", (eid,)).fetchone()[0]


# --------------------------------------------------------------------------
# html helpers
# --------------------------------------------------------------------------
def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def paragraphs(text: str) -> str:
    blocks = [b.strip() for b in (text or "").split("\n\n") if b.strip()]
    return "".join(f"<p>{esc(b)}</p>" for b in blocks) or "<p>No description yet.</p>"


def fmt_dt(value: str, with_time=True) -> str:
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        return esc(value)
    return dt.strftime("%a %d %b · %H:%M") if with_time else dt.strftime("%a %d %b %Y")


def safe_accent(value: str) -> str:
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value or "") else "#8fa68e"


THEMES = [("rose", "Rose"), ("paper", "Paper"), ("tomato", "Tomato"), ("butter", "Butter"), ("blush", "Blush"), ("garden", "Garden")]

THEME_BUTTONS = (
    '<div class="themes" role="group" aria-label="Colour theme">'
    + "".join(f'<button type="button" data-theme-set="{k}">{label}</button>' for k, label in THEMES)
    + "</div>"
)


def layout(title: str, body: str, active: str = "", description: str = "") -> str:
    nav = [
        ("/", "Home", "home"),
        ("/clubs", "Clubs", "clubs"),
        ("/events", "Events", "events"),
        ("/register", "Register a club", "register"),
    ]
    links = "".join(
        f'<a class="navlink{" is-active" if key == active else ""}" href="{href}">{label}</a>'
        for href, label, key in nav
    )
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="rose">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Clubbb</title>
<meta name="description" content="{esc(description or "Every club on campus, in one place. Register a club, post events, and find what is happening this week.")}">
<meta name="theme-color" content="#000000">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@400;500;600&family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&family=Libre+Caslon+Display&display=swap" rel="stylesheet">
<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/static/style.css">
<link rel="stylesheet" href="https://unpkg.com/video.js@8.10.0/dist/video-js.min.css">
<script src="https://unpkg.com/video.js@8.10.0/dist/video.min.js" defer></script>
<script>
(function(){{try{{var t=localStorage.getItem("portal-theme")||"dark";document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();
</script>
</head>
<body>
<header class="bar">
  <a class="brand" href="/"><span class="mark">CB</span><span>Clubbb</span></a>
  <nav class="nav">{links}</nav>
  {THEME_BUTTONS}
  <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="mobile-menu" aria-label="Open menu">
    <span></span><span></span><span></span>
  </button>
</header>
<main class="shell">
{body}
</main>
<footer class="foot">
  <p><strong>Clubbb</strong> · a student-run portal. Not affiliated with any institution.
     No accounts, no tracking, no ads.</p>
  <p class="muted">Clubs register themselves; an administrator approves before a page goes live.</p>
</footer>
<script src="/static/app.js"></script>
<script src="/static/shaders.js"></script>
<script src="/static/garden-heading.js"></script>
<script src="/static/motion.js"></script>

</body>
</html>"""


def club_card(club) -> str:
    return f"""<a class="club-card" href="/c/{esc(club['slug'])}" data-tags="{esc(club['category'])}" style="--club-accent:{safe_accent(club['accent'])}">
  <span class="club-stripe"></span>
  <span class="club-mono" aria-hidden="true">{''.join(w[0] for w in club['name'].split()[:2]).upper()}</span>
  <span class="pill">{esc(club['category'])}</span>
  <h3>{esc(club['name'])}</h3>
  <p>{esc(club['tagline'] or 'A student club on campus.')}</p>
  <span class="card-go">View club →</span>
</a>"""


def shader_panel(ev) -> str:
    cover = ev["cover"] or ""
    return f"""<a class="panel" href="/e/{ev['id']}" style="--club-accent:{safe_accent(ev['club_accent'])}">
  {f'<img class="panel-img" src="{esc(cover)}" alt="" loading="lazy">' if cover else ''}
  <canvas class="panel-canvas" data-shader data-src="{esc(cover)}" data-seed="{ev['id']}" data-accent="{safe_accent(ev['club_accent'])}"></canvas>
  <span class="panel-body">
    <span class="badge kind-{esc(ev['kind'])}">{esc(ev['kind'])}</span>
    <strong class="panel-title">{esc(ev['title'])}</strong>
    <span class="panel-meta mono">{fmt_dt(ev['starts_at'])} · {esc(ev['venue'] or 'Venue TBA')}</span>
    <span class="panel-club">{esc(ev['club_name'])}</span>
  </span>
</a>"""


def event_row(ev, show_club=True) -> str:
    try:
        dt = datetime.fromisoformat(ev["starts_at"])
        day, mon = dt.strftime("%d"), dt.strftime("%b").upper()
    except Exception:
        day, mon = "--", ""
    club = (
        f'<a href="/c/{esc(ev["club_slug"])}">{esc(ev["club_name"])}</a>'
        if show_club
        else ""
    )
    return f"""<a class="event-row" href="/e/{ev['id']}" data-kind="{esc(ev['kind'])}" style="--club-accent:{safe_accent(ev['club_accent'])}">
  <span class="date-block"><strong>{day}</strong><span>{mon}</span></span>
  <span class="event-body">
    <span class="event-top"><span class="badge kind-{esc(ev['kind'])}">{esc(ev['kind'])}</span>
      <span class="mono muted">{fmt_dt(ev['starts_at'])}</span></span>
    <strong>{esc(ev['title'])}</strong>
    <span class="muted">{esc(ev['venue'] or 'Venue to be announced')}{(' · ' + club) if club else ''}</span>
  </span>
</a>"""


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------
def page_home(con):
    clubs = approved_clubs(con)
    events = upcoming_events(con, 40)
    now_dt = datetime.now()
    week = [e for e in events if datetime.fromisoformat(e["starts_at"]) <= now_dt + timedelta(days=7)]
    body = f"""
<div class="vpage">
  <section class="v-section v-hero" id="top">
    <section class="hero hero-split">
      <div class="hero-copy">
        <p class="eyebrow">Student clubs · one portal</p>
        <h1>Every club on campus, <em>in one place.</em></h1>
        <p class="lede">Find a club, see what it does, apply to join. Clubs get a page they control and a shared calendar for hackathons, talks, interviews and meets.</p>
        <div class="hero-actions">
          <a class="btn" href="/clubs">Browse clubs</a>
          <a class="btn btn-ghost" href="/register">Register your club</a>
        </div>
        <div class="stats">
          <div><strong>{len(clubs)}</strong><span>clubs</span></div>
          <div><strong>{len(events)}</strong><span>upcoming events</span></div>
          <div><strong>{len(week)}</strong><span>this week</span></div>
        </div>
      </div>
      <div class="ascii-stage">
        <video class="stage-video" data-clip="events" muted loop playsinline autoplay preload="metadata" aria-hidden="true"></video>
        <span class="stage-tag">EVENTS · LIVE</span>
        <span class="stage-idx">CB/01</span>
      </div>
    </section>
  </section>

  <section class="v-section" id="clubs">
    <div class="v-head"><span class="v-num">01</span><h2>Clubs</h2><a class="mono" href="/clubs">All {len(clubs)} clubs →</a></div>
    <div class="club-showcase">{club_showcase(con, clubs[:3])}</div>
  </section>

  <section class="v-section" id="events">
    <div class="v-head"><span class="v-num">02</span><h2>Events</h2><a class="mono" href="/events">Full calendar →</a></div>
    {''.join(event_row(e) for e in events[:4]) or '<p class="empty">No events yet.</p>'}
  </section>

  <section class="v-section v-join" id="join">
    <p class="eyebrow">03 · For clubs</p>
    <h2>Start something<br>worth joining.</h2>
    <p class="lede">Register your club, get a page you control, and put your events on the same calendar every student already reads.</p>
    <div class="hero-actions">
      <a class="btn" href="/register">Register a club</a>
      <a class="btn btn-ghost" href="/clubs">See the directory</a>
    </div>
  </section>
</div>
<nav class="v-dots" aria-label="Page sections">
  <a href="#top" aria-label="Top"></a>
  <a href="#clubs" aria-label="Clubs"></a>
  <a href="#events" aria-label="Events"></a>
  <a href="#join" aria-label="Join"></a>
</nav>
"""
    return 200, layout("Home", body, "home")


def club_showcase(con, clubs):
    rows = []
    for c in clubs:
        n = con.execute("select count(*) from events where club_id=?", (c["id"],)).fetchone()[0]
        initials = "".join(w[0] for w in c["name"].split()[:2]).upper()
        about = (c["about"] or "").replace("\n", " ").strip()
        excerpt = about[:220] + ("…" if len(about) > 220 else "")
        rows.append(f"""<article class="club-row" data-tags="{esc(c['category'])}" style="--club-accent:{safe_accent(c['accent'])}">
  <a class="club-visual" href="/c/{esc(c['slug'])}" aria-hidden="true" tabindex="-1"><span class="club-initials">{esc(initials)}</span></a>
  <div class="club-copy">
    <p class="club-meta">{esc(c['category'])} · {n} event{'s' if n != 1 else ''}</p>
    <h2><a href="/c/{esc(c['slug'])}">{esc(c['name'])}</a></h2>
    <p class="club-tag">{esc(c['tagline'] or 'A student club on campus.')}</p>
    <p class="club-about">{esc(excerpt)}</p>
    <div class="club-actions"><a class="btn" href="/c/{esc(c['slug'])}">View club</a></div>
  </div>
</article>""")
    return "".join(rows)


def page_clubs(con, query):
    q = (query.get("q", [""])[0] or "").strip()
    cat = (query.get("cat", [""])[0] or "").strip()
    clubs = approved_clubs(con)
    if cat and cat in CATEGORIES:
        clubs = [c for c in clubs if c["category"] == cat]
    if q:
        needle = q.lower()
        clubs = [
            c for c in clubs
            if needle in (c["name"] + " " + c["tagline"] + " " + c["category"]).lower()
        ]
    filters = ['<button class="pill filter is-active" data-filter="all" aria-pressed="true">All</button>']
    filters += [
        f'<button class="pill filter" data-filter="{c}" aria-pressed="false">{c}</button>'
        for c in CATEGORIES
    ]
    body = f"""
<section class="hero compact">
  <p class="eyebrow">Directory</p>
  <h1>Clubs</h1>
  <p class="lede">{len(clubs)} approved club{'s' if len(clubs) != 1 else ''}. Filter by category or search by name.</p>
</section>
<div class="toolbar">
  <div class="filters">{''.join(filters)}</div>
  <input id="club-search" class="search" type="search" placeholder="Search clubs (press /)" value="{esc(q)}" aria-label="Search clubs">
</div>
<div class="club-showcase" id="club-grid">{club_showcase(con, clubs)}</div>
<p class="empty" id="club-empty" hidden>No clubs match that search.</p>
"""
    return 200, layout("Clubs", body, "clubs")


def page_club(con, slug, notice=""):
    club = club_by_slug(con, slug)
    if not club:
        return 404, layout("Not found", '<h1>Club not found</h1><p class="empty">This page does not exist or is awaiting approval.</p>')
    events = con.execute(
        "select e.*, c.name as club_name, c.slug as club_slug, c.accent as club_accent "
        "from events e join clubs c on c.id=e.club_id where e.club_id=? and e.starts_at>=? "
        "order by e.starts_at",
        (club["id"], datetime.now().strftime("%Y-%m-%dT%H:%M")),
    ).fetchall()
    links = []
    if club["website"]:
        links.append(f'<a class="btn btn-ghost" href="{esc(club["website"])}" rel="noopener">Website</a>')
    if club["instagram"]:
        handle = club["instagram"].lstrip("@")
        links.append(f'<a class="btn btn-ghost" href="https://instagram.com/{esc(handle)}" rel="noopener">@{esc(handle)}</a>')
    if club["email"]:
        links.append(f'<a class="btn btn-ghost" href="mailto:{esc(club["email"])}">Email</a>')
    join = ""
    if club["join_open"]:
        join = f"""
<section class="section" id="join">
  <h2>Join {esc(club['name'])}</h2>
  <form class="form card" method="post" action="/c/{esc(club['slug'])}/apply">
    <div class="grid two">
      <label class="field"><span>Name</span><input name="name" required maxlength="80"></label>
      <label class="field"><span>Email</span><input name="email" type="email" required maxlength="120"></label>
      <label class="field"><span>Year</span>
        <select name="year"><option>1st</option><option>2nd</option><option>3rd</option><option>4th</option></select>
      </label>
    </div>
    <label class="field"><span>Why do you want to join?</span><textarea name="message" rows="4" maxlength="800"></textarea></label>
    <button class="btn" type="submit">Send application</button>
  </form>
</section>"""
    else:
        join = '<p class="notice">This club is not taking applications right now.</p>'
    body = f"""
<div class="club-page" style="--accent:{safe_accent(club['accent'])};--accent-ink:#ffffff">
<section class="club-hero banner-{esc(club['banner'])}" style="--club-accent:{safe_accent(club['accent'])}">
  <p class="pill">{esc(club['category'])}</p>
  <h1 data-garden="{esc(club['name'])}">{esc(club['name'])}</h1>
  <p class="lede">{esc(club['tagline'] or '')}</p>
  <div class="hero-actions">{''.join(links)}</div>
</section>
{notice}
<section class="section prose">{paragraphs(club['about'])}</section>
<section class="section">
  <div class="section-head"><h2>Events</h2><a class="mono" href="/events">All events →</a></div>
  {''.join(event_row(e, show_club=False) for e in events) or '<p class="empty">No upcoming events.</p>'}
</section>
{join}
</div>
"""
    return 200, layout(club["name"], body, "clubs", description=club["tagline"] or "")


def build_calendar(con, year: int, month: int) -> str:
    first = date(year, month, 1)
    start = first - timedelta(days=first.weekday())
    end_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    rows = con.execute(
        "select e.*, c.accent as club_accent from events e join clubs c on c.id=e.club_id "
        "where c.status='approved' and e.starts_at >= ? and e.starts_at < ? order by e.starts_at",
        (f"{year:04d}-{month:02d}-01", f"{end_month:%Y-%m-%d}"),
    ).fetchall()
    by_day: dict[str, list] = {}
    for e in rows:
        by_day.setdefault(e["starts_at"][:10], []).append(e)
    today = date.today().isoformat()
    cells = []
    for week in range(6):
        for i in range(7):
            day = start + timedelta(days=week * 7 + i)
            key = day.isoformat()
            classes = ["cal-day"]
            if day.month != month:
                classes.append("is-outside")
            if key == today:
                classes.append("is-today")
            evs = by_day.get(key, [])
            if evs:
                classes.append("has-event")
            chips = "".join(
                f'<span class="ev" style="--club-accent:{safe_accent(e["club_accent"])}" title="{esc(e["title"])}">{esc(e["title"])}</span>'
                for e in evs[:2]
            )
            cells.append(f'<div class="{" ".join(classes)}" data-date="{key}"><span class="dnum">{day.day}</span>{chips}</div>')
    return f'<div class="cal-grid">{"".join(cells)}</div>'


def page_events(con, query):
    today = date.today()
    m = (query.get("m", [""])[0] or "").strip()
    try:
        year, month = (int(x) for x in m.split("-"))
        if not (1 <= month <= 12):
            raise ValueError
    except Exception:
        year, month = today.year, today.month
    first = date(year, month, 1)
    kind = (query.get("kind", [""])[0] or "").strip()
    prev_m = (date(year, month, 1) - timedelta(days=1)).strftime("%Y-%m")
    next_m = (date(year, month, 28) + timedelta(days=7)).strftime("%Y-%m")
    month_start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        month_end = f"{year + 1:04d}-01-01"
    else:
        month_end = f"{year:04d}-{month + 1:02d}-01"
    rows = con.execute(
        "select e.*, c.name as club_name, c.slug as club_slug, c.accent as club_accent "
        "from events e join clubs c on c.id=e.club_id "
        "where c.status='approved' and e.starts_at>=? and e.starts_at<? order by e.starts_at",
        (month_start, month_end),
    ).fetchall()
    visible = [e for e in rows if not kind or e["kind"] == kind]
    kinds = ['<button class="pill filter is-active" data-kind-filter="all" aria-pressed="true">All</button>']
    kinds += [f'<button class="pill filter" data-kind-filter="{k}" aria-pressed="false">{k}</button>' for k in KINDS]
    body = f"""
<div class="events-page">
<section class="hero compact">
  <p class="eyebrow">What is happening</p>
  <h1 data-garden="Events">Events</h1>
  <p class="lede">Everything approved clubs are running, in one calendar. {len(rows)} event{'s' if len(rows) != 1 else ''} in {first.strftime('%B %Y')}.</p>
</section>
<div class="toolbar"><div class="filters">{''.join(kinds)}</div>
  <a class="btn btn-ghost" href="/calendar.ics">Subscribe (.ics)</a></div>
<section class="cal card">
  <div class="cal-head">
    <a class="btn btn-ghost" href="/events?m={prev_m}&kind={esc(kind)}" aria-label="Previous month">←</a>
    <strong>{first.strftime('%B %Y')}</strong>
    <a class="btn btn-ghost" href="/events?m={next_m}&kind={esc(kind)}" aria-label="Next month">→</a>
  </div>
  <div class="cal-week"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div>
  {build_calendar(con, year, month)}
</section>
<div class="season-media">
  <video id="season-bg" class="video-js" muted loop autoplay playsinline preload="auto" data-clip="events" aria-hidden="true"></video>
</div>
<section class="section season-wrap">
  <div id="events-app"></div>
  <div id="events-fallback">
    {''.join(event_row(e) for e in visible) or '<p class="empty">No events this month.</p>'}
    <p class="empty" id="events-empty" hidden>No events of that kind this month.</p>
  </div>
</section>
<script>window.CAL_MONTH = "{year:04d}-{month:02d}";
window.__EVENTS__ = {{"month": "{year:04d}-{month:02d}", "events": {json.dumps([
    {"id": e["id"], "title": e["title"], "kind": e["kind"], "starts_at": e["starts_at"],
     "venue": e["venue"], "club_name": e["club_name"], "accent": e["club_accent"]}
    for e in visible])}}};</script>
<script type="module" src="/static/events-island.js"></script>
</div>
"""
    return 200, layout("Events", body, "events")


def page_event(con, eid, notice=""):
    ev = event_by_id(con, eid)
    if not ev or ev["club_name"] is None:
        return 404, layout("Not found", '<h1>Event not found</h1>')
    count = rsvp_count(con, eid)
    cap = ev["capacity"] or 0
    capacity_line = f"{count}/{cap} seats" if cap else f"{count} going"
    full = bool(cap and count >= cap)
    body = f"""
<p class="crumb"><a href="/events">Events</a> / <a href="/c/{esc(ev['club_slug'])}">{esc(ev['club_name'])}</a></p>
<section class="hero compact" style="--club-accent:{safe_accent(ev['club_accent'])}">
  <p><span class="badge kind-{esc(ev['kind'])}">{esc(ev['kind'])}</span></p>
  <h1>{esc(ev['title'])}</h1>
  <p class="lede">{fmt_dt(ev['starts_at'])}{' – ' + fmt_dt(ev['ends_at'])[-5:] if ev['ends_at'] else ''} · {esc(ev['venue'] or 'Venue TBA')}</p>
  <p class="mono muted">{capacity_line}</p>
</section>
<section class="prose">{paragraphs(ev['description'])}</section>
{f'<p><a class="btn btn-ghost" href="{esc(ev["link"])}" rel="noopener">Registration link</a></p>' if ev['link'] else ''}
{notice}
<section class="section" id="rsvp">
  <h2>RSVP</h2>
  {'<p class="notice">This event is full.</p>' if full else f'''
  <form class="form card" method="post" action="/e/{eid}/rsvp">
    <div class="grid two">
      <label class="field"><span>Name</span><input name="name" required maxlength="80"></label>
      <label class="field"><span>Email</span><input name="email" type="email" required maxlength="120"></label>
    </div>
    <button class="btn" type="submit">Save my seat</button>
  </form>'''}
</section>
"""
    return 200, layout(ev["title"], body, "events")


def page_register(con, error=""):
    body = f"""
<section class="hero compact">
  <p class="eyebrow">For clubs</p>
  <h1 data-garden="Register your club.">Register your club.</h1>
  <p class="lede">One form, one page of your own. An administrator approves it before it appears in the directory.</p>
</section>
{error}
<form class="form card" method="post" action="/register">
  <div class="grid two">
    <label class="field"><span>Club name</span><input name="name" required maxlength="80" placeholder="Robotics Club"></label>
    <label class="field"><span>Category</span>
      <select name="category">{''.join(f'<option>{c}</option>' for c in CATEGORIES)}</select></label>
  </div>
  <label class="field"><span>Tagline</span><input name="tagline" maxlength="120" placeholder="One line students will remember"></label>
  <label class="field"><span>About</span><textarea name="about" rows="6" maxlength="2000" placeholder="Two short paragraphs. Leave a blank line between them."></textarea></label>
  <div class="grid two">
    <label class="field"><span>Accent colour</span><input name="accent" type="color" value="#8fa68e"></label>
    <label class="field"><span>Page style</span>
      <select name="banner"><option value="solid">Solid</option><option value="grid">Grid</option><option value="dots">Dots</option></select></label>
    <label class="field"><span>Email</span><input name="email" type="email" maxlength="120" placeholder="club@example.com"></label>
    <label class="field"><span>Instagram handle</span><input name="instagram" maxlength="60" placeholder="@club"></label>
    <label class="field"><span>Website</span><input name="website" type="url" maxlength="160" placeholder="https://example.com"></label>
  </div>
  <label class="check"><input type="checkbox" name="join_open" value="1" checked> Show an application form on my page</label>
  <button class="btn" type="submit">Create club page</button>
</form>
"""
    return 200, layout("Register a club", body, "register")


def page_registered(con, club, token):
    body = f"""
<section class="hero compact">
  <p class="eyebrow">Saved</p>
  <h1>{esc(club['name'])} is registered.</h1>
  <p class="lede">It is pending administrator approval. Keep this private link — it is the only way to
     edit the page, and it will not be shown again.</p>
</section>
<section class="card">
  <p class="mono muted">Manage link</p>
  <p class="copyline"><code id="manage-url">/manage/{esc(token)}</code>
     <button class="btn btn-ghost" type="button" data-copy="/manage/{esc(token)}">Copy</button></p>
  <p class="muted">Open it on this device now so you do not lose it.</p>
  <p><a class="btn" href="/manage/{esc(token)}">Open dashboard</a></p>
</section>
"""
    return 201, layout("Registered", body)


def page_manage(con, token, notice="", error=""):
    club = club_by_token(con, token)
    if not club:
        return 404, layout("Not found", '<h1>Invalid manage link</h1>')
    apps = con.execute("select count(*) from applications where club_id=?", (club["id"],)).fetchone()[0]
    evs = con.execute("select count(*) from events where club_id=?", (club["id"],)).fetchone()[0]
    status = (
        '<p class="notice ok">Live in the directory.</p>'
        if club["status"] == "approved"
        else '<p class="notice">Pending approval. The page is not public yet.</p>'
    )
    body = f"""
<section class="hero compact">
  <p class="eyebrow">Dashboard</p>
  <h1 data-garden="{esc(club['name'])}">{esc(club['name'])}</h1>
  <p class="lede">Edit the page, add events, and read applications. {evs} events · {apps} applications.</p>
  {status}{notice}{error}
</section>

<section class="section">
  <h2>Page</h2>
  <form class="form card" method="post" action="/manage/{esc(token)}/profile">
    <div class="grid two">
      <label class="field"><span>Name</span><input name="name" value="{esc(club['name'])}" required maxlength="80"></label>
      <label class="field"><span>Category</span>
        <select name="category">{''.join(f'<option{" selected" if c == club["category"] else ""}>{c}</option>' for c in CATEGORIES)}</select></label>
    </div>
    <label class="field"><span>Tagline</span><input name="tagline" value="{esc(club['tagline'])}" maxlength="120"></label>
    <label class="field"><span>About</span><textarea name="about" rows="7" maxlength="2000">{esc(club['about'])}</textarea></label>
    <div class="grid two">
      <label class="field"><span>Accent colour</span><input name="accent" type="color" value="{safe_accent(club['accent'])}"></label>
      <label class="field"><span>Page style</span>
        <select name="banner">{''.join(f'<option value="{b}"{" selected" if b == club["banner"] else ""}>{b}</option>' for b in BANNERS)}</select></label>
      <label class="field"><span>Email</span><input name="email" value="{esc(club['email'])}" maxlength="120"></label>
      <label class="field"><span>Instagram</span><input name="instagram" value="{esc(club['instagram'])}" maxlength="60"></label>
      <label class="field"><span>Website</span><input name="website" value="{esc(club['website'])}" maxlength="160"></label>
    </div>
    <label class="check"><input type="checkbox" name="join_open" value="1" {"checked" if club["join_open"] else ""}> Accept applications</label>
    <button class="btn" type="submit">Save page</button>
  </form>
</section>

<section class="section">
  <h2>Add an event</h2>
  <form class="form card" method="post" action="/manage/{esc(token)}/event" enctype="multipart/form-data">
    <div class="grid two">
      <label class="field"><span>Title</span><input name="title" required maxlength="120"></label>
      <label class="field"><span>Kind</span><select name="kind">{''.join(f'<option>{k}</option>' for k in KINDS)}</select></label>
      <label class="field"><span>Starts</span><input name="starts_at" type="datetime-local" required></label>
      <label class="field"><span>Ends</span><input name="ends_at" type="datetime-local"></label>
      <label class="field"><span>Venue</span><input name="venue" maxlength="120"></label>
      <label class="field"><span>Capacity (0 = unlimited)</span><input name="capacity" type="number" min="0" value="0"></label>
    </div>
    <label class="field"><span>Description</span><textarea name="description" rows="4" maxlength="1500"></textarea></label>
    <label class="field"><span>Registration link</span><input name="link" maxlength="200" placeholder="https://"></label>
    <label class="field"><span>Cover image (JPG, PNG, WEBP · 5 MB)</span><input name="cover" type="file" accept="image/jpeg,image/png,image/webp,image/gif"></label>
    <p class="muted small">The cover is rendered as a dithered, animated panel on the home page. Without one, the panel uses your club colour.</p>
    <button class="btn" type="submit">Publish event</button>
  </form>
</section>

<section class="section">
  <div class="section-head"><h2>People</h2><a class="mono" href="/manage/{esc(token)}/people">Applications and RSVPs →</a></div>
</section>
"""
    return 200, layout("Dashboard", body)


def page_people(con, token):
    club = club_by_token(con, token)
    if not club:
        return 404, layout("Not found", '<h1>Invalid manage link</h1>')
    apps = con.execute("select * from applications where club_id=? order by created_at desc", (club["id"],)).fetchall()
    rsvps = con.execute(
        "select r.*, e.title from rsvps r join events e on e.id=r.event_id "
        "where e.club_id=? order by r.created_at desc", (club["id"],)
    ).fetchall()
    app_rows = "".join(
        f"<tr><td>{esc(a['name'])}</td><td>{esc(a['email'])}</td><td>{esc(a['year'])}</td>"
        f"<td>{esc(a['message'])}</td><td class=mono>{esc(a['created_at'][:10])}</td></tr>"
        for a in apps
    ) or '<tr><td colspan="5" class="muted">No applications yet.</td></tr>'
    rsvp_rows = "".join(
        f"<tr><td>{esc(r['title'])}</td><td>{esc(r['name'])}</td><td>{esc(r['email'])}</td>"
        f"<td class=mono>{esc(r['created_at'][:10])}</td></tr>"
        for r in rsvps
    ) or '<tr><td colspan="4" class="muted">No RSVPs yet.</td></tr>'
    body = f"""
<p class="crumb"><a href="/manage/{esc(token)}">Dashboard</a> / People</p>
<h1>{esc(club['name'])} · people</h1>
<section class="section"><h2>Applications</h2>
<div class="tablewrap"><table><thead><tr><th>Name</th><th>Email</th><th>Year</th><th>Message</th><th>Date</th></tr></thead>
<tbody>{app_rows}</tbody></table></div></section>
<section class="section"><h2>RSVPs</h2>
<div class="tablewrap"><table><thead><tr><th>Event</th><th>Name</th><th>Email</th><th>Date</th></tr></thead>
<tbody>{rsvp_rows}</tbody></table></div></section>
"""
    return 200, layout("People", body)


def page_admin(con, key, notice=""):
    if key != admin_key():
        return 403, layout("Admin", '<h1>Admin</h1><p class="empty">Add <code>?key=…</code> with the admin key.</p>')
    pending = con.execute("select * from clubs where status='pending' order by created_at").fetchall()
    live = con.execute("select count(*) from clubs where status='approved'").fetchone()[0]
    rows = "".join(
        f"<tr><td><strong>{esc(c['name'])}</strong><br><span class=muted>{esc(c['category'])} · {esc(c['email'])}</span></td>"
        f"<td>{esc(c['tagline'])}</td><td class=mono>{esc(c['created_at'][:10])}</td>"
        f'<td><form method="post" action="/admin/approve"><input type="hidden" name="key" value="{esc(key)}">'
        f'<input type="hidden" name="id" value="{c["id"]}"><button class="btn" type="submit">Approve</button></form></td></tr>'
        for c in pending
    ) or '<tr><td colspan="4" class="muted">Nothing pending.</td></tr>'
    body = f"""
<p class="eyebrow">Admin</p>
<h1>Approvals</h1>
<p class="lede">{len(pending)} pending · {live} live.</p>
{notice}
<div class="tablewrap"><table><thead><tr><th>Club</th><th>Tagline</th><th>Registered</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    return 200, layout("Admin", body)


# --------------------------------------------------------------------------
# POST handlers
# --------------------------------------------------------------------------
def read_form(handler):
    ctype = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length)
    if "multipart/form-data" not in ctype:
        parsed = urllib.parse.parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}, {}
    m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', ctype)
    if not m:
        return {}, {}
    boundary = (m.group(1) or m.group(2)).strip().encode()
    fields, files = {}, {}
    for part in raw.split(b"--" + boundary):
        part = part.strip(b"\r\n")
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue
        head, data = part.split(b"\r\n\r\n", 1)
        head_s = head.decode("utf-8", "replace")
        nm = re.search(r'name="([^"]+)"', head_s)
        if not nm:
            continue
        fn = re.search(r'filename="([^"]*)"', head_s)
        data = data.rstrip(b"\r\n")
        if fn and fn.group(1):
            ct = re.search(r"Content-Type:\s*([^\r\n]+)", head_s, re.I)
            files[nm.group(1)] = (fn.group(1), (ct.group(1) if ct else "").strip(), data)
        else:
            fields[nm.group(1)] = data.decode("utf-8", "replace")
    return fields, files


def clean(value: str, limit: int = 500) -> str:
    return (value or "").strip()[:limit]


def handle_register(con, form):
    name = clean(form.get("name", ""), 80)
    if len(name) < 2:
        return 400, page_register(con, '<p class="notice err">A club name is required.</p>')
    category = form.get("category", "technical")
    if category not in CATEGORIES:
        category = "technical"
    token = secrets.token_urlsafe(18)
    slug = unique_slug(con, name)
    con.execute(
        "insert into clubs(slug,name,category,tagline,about,accent,banner,email,instagram,website,join_open,status,manage_hash,created_at) "
        "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            slug, name, category, clean(form.get("tagline", ""), 120),
            clean(form.get("about", ""), 2000), safe_accent(form.get("accent", "")),
            form.get("banner") if form.get("banner") in BANNERS else "solid",
            clean(form.get("email", ""), 120), clean(form.get("instagram", ""), 60),
            clean(form.get("website", ""), 160), 1 if form.get("join_open") else 0,
            "pending", token_hash(token), now(),
        ),
    )
    con.commit()
    club = con.execute("select * from clubs where slug=?", (slug,)).fetchone()
    return page_registered(con, club, token)


def handle_profile(con, token, form):
    club = club_by_token(con, token)
    if not club:
        return 404, layout("Not found", "<h1>Invalid manage link</h1>")
    con.execute(
        "update clubs set name=?,category=?,tagline=?,about=?,accent=?,banner=?,email=?,instagram=?,website=?,join_open=? where id=?",
        (
            clean(form.get("name", club["name"]), 80), form.get("category") if form.get("category") in CATEGORIES else club["category"],
            clean(form.get("tagline", ""), 120), clean(form.get("about", ""), 2000),
            safe_accent(form.get("accent", "")), form.get("banner") if form.get("banner") in BANNERS else club["banner"],
            clean(form.get("email", ""), 120), clean(form.get("instagram", ""), 60),
            clean(form.get("website", ""), 160), 1 if form.get("join_open") else 0, club["id"],
        ),
    )
    con.commit()
    return page_manage(con, token, notice='<p class="notice ok">Page saved.</p>')


def handle_event(con, token, form, files=None):
    club = club_by_token(con, token)
    if not club:
        return 404, layout("Not found", "<h1>Invalid manage link</h1>")
    title = clean(form.get("title", ""), 120)
    starts = clean(form.get("starts_at", ""), 20)
    if not title or not starts:
        return 400, page_manage(con, token, error='<p class="notice err">A title and start time are required.</p>')
    kind = form.get("kind") if form.get("kind") in KINDS else "meetup"
    ends = clean(form.get("ends_at", ""), 20) or starts
    clash = con.execute(
        "select title from events where club_id=? and starts_at < ? and (case when ends_at='' then starts_at else ends_at end) > ?",
        (club["id"], ends, starts),
    ).fetchone()
    cover = save_upload(files or {})
    con.execute(
        "insert into events(club_id,title,kind,starts_at,ends_at,venue,description,link,capacity,cover,created_at) values(?,?,?,?,?,?,?,?,?,?,?)",
        (club["id"], title, kind, starts, ends or starts, clean(form.get("venue", ""), 120),
         clean(form.get("description", ""), 1500), clean(form.get("link", ""), 200),
         max(0, int(form.get("capacity") or 0)), cover, now()),
    )
    con.commit()
    if clash:
        return page_manage(con, token, notice=(
            '<p class="notice ok">Event published.</p>'
            f'<p class="notice">Heads up: it overlaps with “{esc(clash["title"])}”.</p>'))
    return page_manage(con, token, notice='<p class="notice ok">Event published.</p>')


def handle_apply(con, slug, form):
    club = club_by_slug(con, slug)
    if not club:
        return 404, layout("Not found", "<h1>Club not found</h1>")
    name, email = clean(form.get("name", ""), 80), clean(form.get("email", ""), 120)
    if not name or "@" not in email:
        return 400, page_club(con, slug, '<p class="notice err">Name and a valid email are required.</p>')
    con.execute(
        "insert into applications(club_id,name,email,year,message,created_at) values(?,?,?,?,?,?)",
        (club["id"], name, email, clean(form.get("year", ""), 10), clean(form.get("message", ""), 800), now()),
    )
    con.commit()
    return page_club(con, slug, '<p class="notice ok">Application sent. The club will reach out by email.</p>')


def handle_rsvp(con, eid, form):
    ev = event_by_id(con, eid)
    if not ev:
        return 404, layout("Not found", "<h1>Event not found</h1>")
    name, email = clean(form.get("name", ""), 80), clean(form.get("email", ""), 120)
    if not name or "@" not in email:
        return 400, page_event(con, eid, '<p class="notice err">Name and a valid email are required.</p>')
    if ev["capacity"] and rsvp_count(con, eid) >= ev["capacity"]:
        return 400, page_event(con, eid, '<p class="notice err">This event just filled up.</p>')
    try:
        con.execute("insert into rsvps(event_id,name,email,created_at) values(?,?,?,?)", (eid, name, email, now()))
        con.commit()
        msg = '<p class="notice ok">You are on the list. Add it to your calendar from the events page.</p>'
    except sqlite3.IntegrityError:
        msg = '<p class="notice">That email is already on the list.</p>'
    return page_event(con, eid, msg)


def handle_approve(con, form):
    key = form.get("key", "")
    if key != admin_key():
        return 403, layout("Admin", "<h1>Forbidden</h1>")
    con.execute("update clubs set status='approved' where id=?", (form.get("id"),))
    con.commit()
    return page_admin(con, key, '<p class="notice ok">Club approved.</p>')


# --------------------------------------------------------------------------
# ICS
# --------------------------------------------------------------------------
def ics_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def ics_calendar(con) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Clubbb//EN", "CALSCALE:GREGORIAN"]
    for ev in upcoming_events(con, 200):
        start = ev["starts_at"].replace("-", "").replace(":", "")
        end = (ev["ends_at"] or ev["starts_at"]).replace("-", "").replace(":", "")
        if len(start) == 13:
            start += "00"
        if len(end) == 13:
            end += "00"
        lines += [
            "BEGIN:VEVENT", f"UID:event-{ev['id']}@sccimagic", f"DTSTART:{start}", f"DTEND:{end}",
            f"SUMMARY:{ics_escape(ev['title'])}", f"LOCATION:{ics_escape(ev['venue'])}",
            f"DESCRIPTION:{ics_escape(ev['description'])}", "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


# --------------------------------------------------------------------------
# server
# --------------------------------------------------------------------------
class App(BaseHTTPRequestHandler):
    server_version = "SCCIMagic/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send(self, status, body, ctype="text/html; charset=utf-8", extra=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send(303, "", extra={"Location": location})

    def do_GET(self):
        try:
            parts = urllib.parse.urlsplit(self.path)
            path, query = parts.path, urllib.parse.parse_qs(parts.query, keep_blank_values=True)
            con = connect()
            try:
                if path.startswith("/static/"):
                    return self.serve_static(path)
                if path.startswith("/uploads/"):
                    name = path[len("/uploads/"):]
                    target = (UPLOADS / name).resolve()
                    if str(target).startswith(str(UPLOADS.resolve())) and target.is_file():
                        ext = target.suffix.lower()
                        return self.send(200, target.read_bytes(), {".jpg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}.get(ext, "application/octet-stream"))
                    return self.send(404, "not found", "text/plain")
                if path == "/":
                    return self.send(*page_home(con))
                if path == "/clubs":
                    return self.send(*page_clubs(con, query))
                if path == "/events":
                    return self.send(*page_events(con, query))
                if path == "/register":
                    return self.send(*page_register(con))
                if path == "/admin":
                    return self.send(*page_admin(con, (query.get("key", [""])[0] or "")))
                if path == "/calendar.ics":
                    return self.send(200, ics_calendar(con), "text/calendar; charset=utf-8")
                m = re.fullmatch(r"/c/([a-z0-9-]+)", path)
                if m:
                    return self.send(*page_club(con, m.group(1)))
                m = re.fullmatch(r"/e/(\d+)", path)
                if m:
                    return self.send(*page_event(con, int(m.group(1))))
                m = re.fullmatch(r"/manage/([A-Za-z0-9_-]+)", path)
                if m:
                    return self.send(*page_manage(con, m.group(1)))
                m = re.fullmatch(r"/manage/([A-Za-z0-9_-]+)/people", path)
                if m:
                    return self.send(*page_people(con, m.group(1)))
                return self.send(404, layout("Not found", "<h1>Page not found</h1>"))
            finally:
                con.close()
        except Exception:
            traceback.print_exc()
            self.send(500, layout("Error", "<h1>Something broke</h1><p>The error was logged in the terminal.</p>"))

    def do_POST(self):
        try:
            path = urllib.parse.urlsplit(self.path).path
            form, files = read_form(self)
            con = connect()
            try:
                if path == "/register":
                    status, body = handle_register(con, form)
                    return self.send(status, body)
                if path == "/admin/approve":
                    return self.send(*handle_approve(con, form))
                m = re.fullmatch(r"/manage/([A-Za-z0-9_-]+)/profile", path)
                if m:
                    return self.send(*handle_profile(con, m.group(1), form))
                m = re.fullmatch(r"/manage/([A-Za-z0-9_-]+)/event", path)
                if m:
                    return self.send(*handle_event(con, m.group(1), form, files))
                m = re.fullmatch(r"/c/([a-z0-9-]+)/apply", path)
                if m:
                    return self.send(*handle_apply(con, m.group(1), form))
                m = re.fullmatch(r"/e/(\d+)/rsvp", path)
                if m:
                    return self.send(*handle_rsvp(con, int(m.group(1)), form))
                return self.send(404, layout("Not found", "<h1>Page not found</h1>"))
            finally:
                con.close()
        except Exception:
            traceback.print_exc()
            self.send(500, layout("Error", "<h1>Something broke</h1>"))

    def serve_static(self, path):
        name = path[len("/static/"):]
        target = (STATIC / name).resolve()
        if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
            return self.send(404, "not found", "text/plain")
        types = {".css": "text/css", ".js": "application/javascript", ".svg": "image/svg+xml", ".png": "image/png"}
        return self.send(200, target.read_bytes(), types.get(target.suffix, "application/octet-stream"))


def main() -> int:
    init_db()
    print(f"Clubbb on http://{HOST}:{PORT}")
    print(f"Admin: http://{HOST}:{PORT}/admin?key={admin_key()}")
    ThreadingHTTPServer((HOST, PORT), App).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
