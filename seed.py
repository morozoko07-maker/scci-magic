#!/usr/bin/env python3
"""Load demo clubs and events from seed.json. Safe to run twice."""
import json
import sys
from pathlib import Path

from app import BANNERS, CATEGORIES, KINDS, connect, init_db, now, token_hash

ROOT = Path(__file__).resolve().parent


def main() -> int:
    init_db()
    data = json.loads((ROOT / "seed.json").read_text(encoding="utf-8"))
    con = connect()
    if con.execute("select count(*) from clubs").fetchone()[0]:
        print("Database already has clubs; nothing to do.")
        return 0

    ids = {}
    links = []
    for club in data["clubs"]:
        slug = club["slug"]
        token = f"demo-{slug}"
        con.execute(
            "insert into clubs(slug,name,category,tagline,about,accent,banner,email,instagram,"
            "website,join_open,status,manage_hash,created_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                slug, club["name"], club.get("category", "technical"),
                club.get("tagline", ""), club.get("about", ""),
                club.get("accent", "#8fa68e"),
                club.get("banner") if club.get("banner") in BANNERS else "solid",
                club.get("email", ""), club.get("instagram", ""), club.get("website", ""),
                1 if club.get("join_open", True) else 0,
                "approved", token_hash(token), now(),
            ),
        )
        ids[slug] = con.execute("select id from clubs where slug=?", (slug,)).fetchone()[0]
        links.append(f"/manage/{token}")

    for ev in data["events"]:
        con.execute(
            "insert into events(club_id,title,kind,starts_at,ends_at,venue,description,link,"
            "capacity,created_at) values(?,?,?,?,?,?,?,?,?,?)",
            (
                ids[ev["club_slug"]], ev["title"],
                ev.get("kind") if ev.get("kind") in KINDS else "meetup",
                ev["starts_at"], ev.get("ends_at", ""), ev.get("venue", ""),
                ev.get("description", ""), ev.get("link", ""),
                int(ev.get("capacity") or 0), now(),
            ),
        )
    con.commit()
    print(f"Seeded {len(data['clubs'])} clubs and {len(data['events'])} events.")
    print("Demo manage links:")
    for link in links:
        print("  http://localhost:8770" + link)
    return 0


if __name__ == "__main__":
    sys.exit(main())
