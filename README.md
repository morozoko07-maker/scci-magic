# Campus Clubs

A self-hostable portal for college clubs: clubs register, get a page they can
customise, post events; students browse clubs, see one calendar, RSVP and apply.

Python 3 standard library only. No npm, no build step, no accounts, no tracking.

```bash
python3 seed.py     # demo clubs + events (optional)
python3 app.py      # http://localhost:8770
```

The admin key is printed on start, or set `ADMIN_KEY` yourself.

## What it does

**Students**
- club directory with category filters and search
- one calendar per month plus a list view
- event pages with RSVP, capacity and a `calendar.ics` feed
- apply to join a club directly from its page

**Clubs**
- register without an account, receive a private manage link
- customise name, category, tagline, about, accent colour, page style, links
- choose whether applications are open
- publish events (hackathon, talk, workshop, interview, meetup, sports, cultural)
- read applications and RSVPs in one place

**Admin**
- `/admin?key=…` lists pending clubs and approves them

## Design decisions

- **No accounts.** A club gets a random manage token once; only its hash is stored.
  Lose the link and the page is orphaned — the trade for not running auth.
- **Approval before publication.** A club exists as `pending` until an admin approves.
- **Server-rendered.** Every page is HTML from Python; JavaScript is only theme,
  filters and copy-to-clipboard. Works without JS.
- **SQLite.** One file (`portal.db`), easy to back up, easy to move.

## Hosting

The only real requirement is a machine that can run Python 3.8+ and stay up.

```bash
PORT=8080 HOST=0.0.0.0 ADMIN_KEY='something-long' python3 app.py
```

Put nginx or Caddy in front for TLS. A department subdomain pointing at a lab
server is enough. Docker:

```bash
docker build -t campus-clubs .
docker run -p 8770:8770 -v "$PWD/data:/data" -e ADMIN_KEY=change-me campus-clubs
```

## Files

```
app.py          server, database, views
seed.py         demo data loader
seed.json       8 clubs, 14 events
static/style.css  one stylesheet, three themes
static/app.js     theme, filters, search, copy
```

## Known limits (on purpose)

- No email sending: applications and RSVPs are visible in the club dashboard.
- No password reset, because no passwords.
- No file uploads yet; logos are an accent colour and a page style.
- No multi-admin roles; one key.

These are the next things to add, in that order.
