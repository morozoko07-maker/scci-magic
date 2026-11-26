# Campus Clubs — build spec

A self-hostable club portal: clubs register, get a page they can customise, post
events; students browse clubs, see a calendar, RSVP and apply to join.

Stack: Python 3 standard library only (`http.server`, `sqlite3`), server-rendered
HTML, one stylesheet, one small JS file. No build step, no npm, no accounts.

Run: `python3 app.py` → http://localhost:8770

## Data model (SQLite, `portal.db`)

clubs
- id INTEGER pk
- slug TEXT unique
- name TEXT
- category TEXT            (technical, cultural, sports, social, academic, media)
- tagline TEXT
- about TEXT               (plain text, paragraphs on blank lines)
- accent TEXT              (hex colour chosen by the club)
- banner TEXT              (solid | grid | dots)
- email TEXT
- instagram TEXT
- website TEXT
- join_open INTEGER       (1 = show the application form)
- status TEXT             (pending | approved)
- manage_hash TEXT        (sha256 of the manage token)
- created_at TEXT

events
- id INTEGER pk
- club_id INTEGER fk
- title TEXT
- kind TEXT               (hackathon, talk, workshop, interview, meetup, sports, cultural)
- starts_at TEXT          (ISO 'YYYY-MM-DDTHH:MM')
- ends_at TEXT
- venue TEXT
- description TEXT
- link TEXT
- capacity INTEGER        (0 = unlimited)
- created_at TEXT

rsvps (event_id, name, email, created_at)  unique(event_id, email)
applications (club_id, name, email, year, message, created_at)

## Routes

GET  /                          home: featured clubs, this week, next events
GET  /clubs                     directory (?q=&cat=)
GET  /c/<slug>                  club page
GET  /events                    list + month calendar (?m=YYYY-MM&kind=)
GET  /e/<id>                    event page + RSVP form
GET  /calendar.ics              all upcoming events as ICS
GET  /register                  form  |  POST /register
GET  /manage/<token>            club dashboard
POST /manage/<token>/profile    update profile + customisation
POST /manage/<token>/event      create event
GET  /manage/<token>/people     applications + RSVPs
GET  /admin?key=KEY             pending clubs | POST /admin/approve
POST /c/<slug>/apply            join application
POST /e/<id>/rsvp               RSVP

POSTs redirect (303) after success. Errors re-render with a message.

## HTML contract (for CSS/JS agents)

- `<html data-theme="dark|light|midnight">`
- theme buttons: `[data-theme-set]`
- club filter buttons: `[data-filter="all|technical|..."]`
- club cards: `.club-card[data-tags="..."]`
- search input: `#club-search`
- calendar: `.cal`, `.cal-grid`, `.cal-day[data-date]`, `.cal-day.is-today`,
  `.cal-day.has-event`, `.cal-day.is-outside`; prev/next are plain links `?m=`
- copy button: `[data-copy="text"]`
- class names available: `.shell`, `.bar`, `.brand`, `.mark`, `.btn`, `.btn-ghost`,
  `.pill`, `.card`, `.club-card`, `.event-row`, `.badge`, `.empty`, `.notice`,
  `.field`, `.grid`, `.section`, `.muted`, `.mono`

## Design

Same family as OpenCSE: matte charcoal default, warm paper light, true-black
midnight; Funnel Display headings, Geist body, Geist Mono labels; flat grounds,
1px borders, 5px radius, sage accent, quiet hover. No violet, no gradients,
no glass, no emoji. Body text 60–75 characters per line.

## Seed data

`seed.json` with 8 clubs and 14 events (relative to today, ISO datetime), used by
`python3 seed.py` when the database is empty.
