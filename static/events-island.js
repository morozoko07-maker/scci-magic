/* Events island: React (ESM, no build) renders the season list with scroll reveals.
   Falls back to the server-rendered list if the module fails. */
import React from "https://esm.sh/react@18.3.1";
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client";
import htm from "https://esm.sh/htm@3.1.1";

const html = htm.bind(React.createElement);
const data = window.__EVENTS__ || { events: [], month: "" };

function monthKey(iso) { return iso.slice(0, 7); }

function monthName(key) {
  const [y, m] = key.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleString("en-GB", { month: "long", year: "numeric" });
}

function Reveal({ children }) {
  const ref = React.useRef(null);
  const [seen, setSeen] = React.useState(false);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setSeen(true); return; }
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => { if (e.isIntersecting) { setSeen(true); io.disconnect(); } });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return html`<div ref=${ref} className=${"reveal" + (seen ? " in" : "")}>${children}</div>`;
}

function EventCard({ ev }) {
  const d = new Date(ev.starts_at);
  const day = String(d.getDate()).padStart(2, "0");
  const mon = d.toLocaleString("en-GB", { month: "short" }).toUpperCase();
  const time = d.toLocaleString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return html`
    <a className="ev-card" href=${"/e/" + ev.id} data-kind=${ev.kind} style=${{ "--club-accent": ev.accent }}>
      <div className="ev-date"><strong>${day}</strong><span>${mon}</span></div>
      <div className="ev-body">
        <div className="ev-top">
          <span className=${"badge kind-" + ev.kind}>${ev.kind}</span>
          <span className="mono muted">${time} · ${ev.venue || "Venue TBA"}</span>
        </div>
        <h3>${ev.title}</h3>
        <p className="muted">${ev.club_name}</p>
      </div>
      <span className="ev-go" aria-hidden="true">→</span>
    </a>`;
}

function Season() {
  const groups = React.useMemo(() => {
    const g = new Map();
    for (const ev of data.events) {
      const k = monthKey(ev.starts_at);
      if (!g.has(k)) g.set(k, []);
      g.get(k).push(ev);
    }
    return [...g.entries()];
  }, []);

  return html`
    <div className="season">
      ${groups.map(([k, list]) => html`
        <section className="season-month" key=${k}>
          <${Reveal}>
            <header className="season-head">
              <span className="mono muted">${String(list.length).padStart(2, "0")} events</span>
              <h2>${monthName(k)}</h2>
            </header>
          <//>
          ${list.map((ev) => html`<${Reveal} key=${ev.id}><${EventCard} ev=${ev} /><//>`)}
        </section>`)}
      ${groups.length === 0 && html`<p className="empty">No events yet.</p>`}
    </div>`;
}

const root = document.getElementById("events-app");
if (root) {
  createRoot(root).render(html`<${Season} />`);
  const fallback = document.getElementById("events-fallback");
  if (fallback) fallback.hidden = true;
}
