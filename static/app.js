/* SCCI Magic — themes, video heroes, directory filters. */
(function () {
  "use strict";

  var THEMES = ["rose", "paper", "tomato", "butter", "blush", "garden"];
  var COLOURS = { rose: "#000000", paper: "#F3EEE4", tomato: "#FF1400", butter: "#FFE9A8", blush: "#FAD4D8", garden: "#FAFAFA" };
  var root = document.documentElement;
  var meta = document.querySelector('meta[name="theme-color"]');

  function currentTheme() {
    var t = root.getAttribute("data-theme");
    return THEMES.indexOf(t) >= 0 ? t : "rose";
  }

  function paintTheme() {
    var theme = currentTheme();
    document.querySelectorAll("[data-theme-set]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-theme-set") === theme ? "true" : "false");
    });
    if (meta) meta.setAttribute("content", COLOURS[theme] || "#000000");
    loadVideos(theme);
  }

  function videoUrl(clip, motion, theme) {
    return "/static/media/hero-" + clip + "-" + motion + "-" + theme + ".webm";
  }

  function loadVideos(theme) {
    document.querySelectorAll("video[data-clip]").forEach(function (v) {
      var clip = v.getAttribute("data-clip");
      var motion = v.getAttribute("data-motion") || "grow";
      v.onerror = function () {
        if (motion !== "breathe") {
          motion = "breathe";
          v.src = videoUrl(clip, motion, theme);
          v.play().catch(function () {});
        } else {
          v.setAttribute("data-missing", "1");
        }
      };
      var next = videoUrl(clip, motion, theme);
      if (v.id === "season-bg" && window.__seasonPlayer) {
        try { window.__seasonPlayer.src({ src: next, type: "video/webm" }); window.__seasonPlayer.play(); } catch (e) {}
        return;
      }
      if (v.getAttribute("src") !== next) {
        v.setAttribute("src", next);
        v.load();
        var p = v.play();
        if (p && p.catch) p.catch(function () {});
      }
    });
  }

  // theme buttons
  document.querySelectorAll("[data-theme-set]").forEach(function (b) {
    b.addEventListener("click", function () {
      var next = b.getAttribute("data-theme-set");
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("portal-theme", next); } catch (e) {}
      paintTheme();
    });
  });

  var q = /[?&]theme=([a-z]+)/.exec(location.search);
  if (q && THEMES.indexOf(q[1]) >= 0) {
    root.setAttribute("data-theme", q[1]);
  } else {
    try {
      var saved = localStorage.getItem("portal-theme");
      if (saved && THEMES.indexOf(saved) >= 0) root.setAttribute("data-theme", saved);
    } catch (e) {}
  }
  paintTheme();

  // mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var menu = document.getElementById("mobile-menu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.hasAttribute("hidden");
      if (open) menu.removeAttribute("hidden"); else menu.setAttribute("hidden", "");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a") || e.target.closest("[data-theme-set]")) {
        menu.setAttribute("hidden", "");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      }
    });
  }

  // club directory
  var cards = Array.prototype.slice.call(document.querySelectorAll(".club-row"));
  var filterButtons = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
  var search = document.getElementById("club-search");
  var empty = document.getElementById("club-empty");
  var activeFilter = "all";

  function applyClubs() {
    var q = (search && search.value || "").trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {
      var tags = (card.getAttribute("data-tags") || "").toLowerCase();
      var hay = (card.textContent || "").toLowerCase() + " " + tags;
      var okFilter = activeFilter === "all" || tags.indexOf(activeFilter) >= 0;
      var okSearch = !q || hay.indexOf(q) >= 0;
      var show = okFilter && okSearch;
      card.hidden = !show;
      if (show) shown++;
    });
    if (empty) empty.hidden = shown !== 0 || !cards.length;
  }

  filterButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      activeFilter = b.getAttribute("data-filter");
      filterButtons.forEach(function (x) {
        x.classList.toggle("is-active", x === b);
        x.setAttribute("aria-pressed", x === b ? "true" : "false");
      });
      applyClubs();
    });
  });
  if (search) search.addEventListener("input", applyClubs);

  // event kind filter
  var rows = Array.prototype.slice.call(document.querySelectorAll(".event-row[data-kind]"));
  var kindButtons = Array.prototype.slice.call(document.querySelectorAll("[data-kind-filter]"));
  var eventsEmpty = document.getElementById("events-empty");
  var activeKind = "all";
  function applyKinds() {
    var shown = 0;
    rows.forEach(function (r) {
      var show = activeKind === "all" || r.getAttribute("data-kind") === activeKind;
      r.hidden = !show;
      if (show) shown++;
    });
    if (eventsEmpty) eventsEmpty.hidden = shown !== 0 || activeKind === "all";
  }
  kindButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      activeKind = b.getAttribute("data-kind-filter");
      kindButtons.forEach(function (x) {
        x.classList.toggle("is-active", x === b);
        x.setAttribute("aria-pressed", x === b ? "true" : "false");
      });
      applyKinds();
    });
  });

  // copy buttons
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var text = b.getAttribute("data-copy");
      var done = function () {
        var old = b.textContent;
        b.textContent = "Copied";
        setTimeout(function () { b.textContent = old; }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        ta.remove();
      }
    });
  });

  // "/" focuses search
  document.addEventListener("keydown", function (e) {
    if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
    var t = e.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
    if (search) { e.preventDefault(); search.focus(); }
  });
})();


/* video.js for the seasonal WebM band */
window.addEventListener("load", function () {
  if (!window.videojs) return;
  var el = document.getElementById("season-bg");
  if (!el) return;
  var player = window.videojs(el, { controls: false, autoplay: true, muted: true, loop: true, fill: true });
  window.__seasonPlayer = player;
  var theme = document.documentElement.getAttribute("data-theme") || "rose";
  player.src({ src: "/static/media/hero-events-grow-" + theme + ".webm", type: "video/webm" });
  player.play().catch(function () {});
});
