/* Garden headings: big type that grows vines and roses, then withers and
   regrows when the palette changes. Falls back to plain text. */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var FONT = '"Playfair Display", Georgia, serif';

  function hash(n) { var x = Math.sin(n * 12.9898) * 43758.5453; return x - Math.floor(x); }
  function rng(seed) { var s = seed | 0; return function () { s = (s + 0x6D2B79F5) | 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function easeOut(t) { return 1 - Math.pow(1 - clamp(t, 0, 1), 3); }

  function palette() {
    var cs = getComputedStyle(document.documentElement);
    return {
      ink: cs.getPropertyValue("--ink").trim() || "#fff",
      accent: cs.getPropertyValue("--accent").trim() || "#FF1400",
      flower: cs.getPropertyValue("--flower").trim() || cs.getPropertyValue("--accent").trim() || "#FF1400",
      stem: cs.getPropertyValue("--accent-2").trim() || "#3257FF",
      bg: cs.getPropertyValue("--bg").trim() || "#000"
    };
  }

  function stemPts(base, dir, len, bend, waves, ph, n) {
    var P = [[base[0], base[1]]], x = base[0], y = base[1], step = len / n;
    for (var i = 1; i <= n; i++) {
      var u = i / n, a = dir + bend * u + Math.sin(u * Math.PI * waves + ph) * 0.18 * Math.min(1, u * 3);
      x += Math.cos(a) * step; y += Math.sin(a) * step;
      P.push([x, y]);
    }
    return P;
  }

  function build(word, S, id) {
    var r = rng(id * 7919 + 17);
    var els = [];
    var w = 1;
    var up = 1 + (r() < 0.4 ? 1 : 0);
    for (var i = 0; i < up; i++) {
      var base = [(r() - 0.5) * w * 0.7, -r() * 0.2];
      var dir = -Math.PI / 2 + (r() - 0.5) * 0.7;
      var len = 0.62 + r() * 0.5;
      var pts = stemPts(base, dir, len, (r() - 0.5) * 0.8, 1 + r() * 1.4, r() * 6.28, 30);
      var d0 = 40 + i * 130, dur = 520 + len * 340;
      els.push({ t: "stem", pts: pts, d0: d0, dur: dur });
      var leaves = Math.floor(r() * 3), side = r() < 0.5 ? -1 : 1;
      for (var k = 0; k < leaves; k++) {
        var u = 0.3 + r() * 0.55, idx = Math.min(pts.length - 1, Math.round(u * (pts.length - 1)));
        var p = pts[idx], p2 = pts[Math.min(pts.length - 1, idx + 1)];
        var ang = Math.atan2(p2[1] - p[1], p2[0] - p[0]); side = -side;
        els.push({ t: "leaf", x: p[0], y: p[1], a: ang + side * (0.6 + r() * 0.5), L: 0.15 + r() * 0.18, bend: (r() - 0.5) * 1.2, d0: d0 + dur * u });
      }
      var tip = pts[pts.length - 1];
      if (r() < 0.58) els.push({ t: "rose", x: tip[0], y: tip[1], R: 0.11 + r() * 0.1, rot: (r() - 0.5) * 0.8, seed: r() * 100, d0: d0 + dur * 0.85 });
      else els.push({ t: "leaf", x: tip[0], y: tip[1], a: Math.atan2(tip[1] - pts[pts.length - 3][1], tip[0] - pts[pts.length - 3][0]), L: 0.18 + r() * 0.14, bend: (r() - 0.5), d0: d0 + dur * 0.9 });
    }
    return els;
  }

  function drawStem(g, P, upto, w, col) {
    if (upto <= 0) return;
    var n = P.length - 1, end = upto * n;
    g.beginPath(); g.moveTo(P[0][0], P[0][1]);
    for (var i = 1; i <= n; i++) {
      if (i > end) {
        var f = end - (i - 1);
        g.lineTo(P[i - 1][0] + (P[i][0] - P[i - 1][0]) * f, P[i - 1][1] + (P[i][1] - P[i - 1][1]) * f);
        break;
      }
      g.lineTo(P[i][0], P[i][1]);
    }
    g.strokeStyle = col; g.lineWidth = w; g.lineCap = "round"; g.lineJoin = "round"; g.stroke();
  }

  function drawLeaf(g, x, y, a, L, bend, col, vein) {
    if (L <= 0) return;
    var ca = Math.cos(a), sa = Math.sin(a), px = -sa, py = ca;
    var at = function (u) { var b = Math.sin(Math.PI * u) * bend * 0.15 * L; return [x + ca * u * L + px * b, y + sa * u * L + py * b]; };
    var hw = function (u) { return L * 0.18 * Math.sin(Math.PI * Math.pow(u, 0.8)); };
    var N = 10, s1 = [], s2 = [], i, u, c, wv;
    for (i = 0; i <= N; i++) { u = i / N; c = at(u); wv = hw(u); s1.push([c[0] + px * wv, c[1] + py * wv]); s2.push([c[0] - px * wv, c[1] - py * wv]); }
    var tip = at(1), base = at(0);
    g.beginPath(); g.moveTo(base[0], base[1]);
    for (i = 0; i < s1.length; i++) g.lineTo(s1[i][0], s1[i][1]);
    g.lineTo(tip[0], tip[1]);
    for (i = s2.length - 1; i >= 0; i--) g.lineTo(s2[i][0], s2[i][1]);
    g.closePath(); g.fillStyle = col; g.fill();
    if (L > 7) {
      g.beginPath(); g.moveTo(base[0], base[1]);
      for (i = 1; i <= 6; i++) { c = at(0.1 + 0.7 * i / 6); g.lineTo(c[0], c[1]); }
      g.strokeStyle = vein; g.lineWidth = Math.max(0.7, L * 0.035); g.stroke();
    }
  }

  function drawRose(g, x, y, R, rot, seed, p, C) {
    if (R <= 0.4) return;
    var r = rng(seed * 977 + 3);
    for (var i = 0; i < 6; i++) {
      var pr = easeOut((p - i * 0.08) / 0.55);
      if (pr <= 0) continue;
      var ang = rot + i * 1.05 + r() * 0.2, rr = R * (0.55 + 0.45 * pr);
      g.save(); g.translate(x + Math.cos(ang) * R * 0.32, y + Math.sin(ang) * R * 0.32); g.rotate(ang);
      g.beginPath(); g.ellipse(0, 0, rr, rr * 0.72, 0, 0, Math.PI * 2); g.fillStyle = C.flower; g.fill();
      g.restore();
    }
    g.beginPath();
    for (var k = 0; k <= 40 * p; k++) {
      var u = k / 40, th = u * 2.2 * Math.PI * 2, rr2 = R * (0.05 + 0.3 * u);
      var px = x + Math.cos(th + rot) * rr2, py = y + Math.sin(th + rot) * rr2 * 0.8;
      k ? g.lineTo(px, py) : g.moveTo(px, py);
    }
    g.strokeStyle = C.ink; g.lineWidth = Math.max(0.8, R * 0.06); g.stroke();
  }

  function mount(el) {
    var text = (el.getAttribute("data-garden") || el.textContent || "").trim();
    if (!text) return;
    el.classList.add("garden-heading");
    var canvas = document.createElement("canvas");
    canvas.className = "garden-canvas";
    canvas.setAttribute("aria-hidden", "true");
    el.appendChild(canvas);
    var g = canvas.getContext("2d");
    if (!g) return;

    var letters = [], t0 = performance.now(), witherAt = 0, regrowAt = 0, W = 0, H = 0, S = 0, dpr = 1;
    var mx = null, my = null;

    function measure() {
      g.font = "700 100px " + FONT;
      var total = 0, widths = [];
      for (var i = 0; i < text.length; i++) {
        var w = g.measureText(text[i]).width / 100;
        if (text[i] === " ") w *= 1.35;
        widths.push(w); total += w;
      }
      return { total: total, widths: widths };
    }

    function measure() {
      g.font = "700 100px " + FONT;
      var widths = {};
      for (var i = 0; i < text.length; i++) {
        var ch = text[i];
        if (widths[ch] == null) widths[ch] = g.measureText(ch).width / 100;
      }
      return widths;
    }

    function wrapByWidth(widths, S) {
      var maxUnits = (W * 0.96) / S;
      var words = text.split(/\s+/), lines = [], cur = [], units = 0;
      function unit(w) {
        var u = 0;
        for (var i = 0; i < w.length; i++) u += (widths[w[i]] || 0.5) * (w[i] === " " ? 1.35 : 1);
        return u;
      }
      for (var i = 0; i < words.length; i++) {
        var wu = unit(words[i]), sep = cur.length ? unit(" ") : 0;
        if (cur.length && units + sep + wu > maxUnits) {
          lines.push(cur.join(" ")); cur = [words[i]]; units = wu;
        } else { cur.push(words[i]); units += sep + wu; }
      }
      if (cur.length) lines.push(cur.join(" "));
      return lines;
    }

    function layout() {
      var rect = el.getBoundingClientRect();
      if (!rect.width) return;
      W = rect.width;
      H = Math.max(el.clientHeight || rect.height, 1);
      var widths = measure();
      var lines = [text];
      S = 12;
      for (var test = H * 0.92; test > 10; test -= 1.5) {
        var ls = wrapByWidth(widths, test);
        if (ls.length * 1.16 * test <= H * 0.98) { lines = ls; S = test; break; }
      }
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      letters = [];
      var lh = S * 1.16;
      var firstBase = H / 2 - ((lines.length - 1) * lh) / 2 + S * 0.32;
      var id = 1;
      lines.forEach(function (ln, li) {
        var units = 0, i;
        for (i = 0; i < ln.length; i++) units += (widths[ln[i]] || 0.5) * (ln[i] === " " ? 1.35 : 1);
        var x = 0, baseY = firstBase + li * lh;
        for (i = 0; i < ln.length; i++) {
          var w = (widths[ln[i]] || 0.5) * (ln[i] === " " ? 1.35 : 1) * S;
          if (ln[i] !== " ") {
            var l = { ch: ln[i], x: x + w / 2, y: baseY, w: w, id: id++, seed: id * 1013 + text.length };
            l.els = build(ln[i], S, l.id);
            letters.push(l);
          }
          x += w;
        }
      });
      el.style.textShadow = "none";
    }

    function draw(now) {
      var C = palette();
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, W, H);
      var grow = reduced ? 1 : clamp((now - t0) / 900, 0, 1);
      var wither = 0;
      if (witherAt && now > witherAt) {
        wither = clamp((now - witherAt) / 420, 0, 1);
        if (!reduced && now > witherAt + 460 && !regrowAt) { regrowAt = now; t0 = now; witherAt = 0; }
      }
      var fade = 1 - wither;
      var boil = reduced ? 0 : Math.floor(now / 120);
      var amp = reduced ? 0 : Math.max(0.5, S * 0.008);

      g.textAlign = "center"; g.textBaseline = "alphabetic";
      g.font = "700 " + S + "px " + FONT;

      function layer(layerId) {
        for (var li = 0; li < letters.length; li++) {
          var l = letters[li];
          var ln = [0, 0];
          if (mx != null && !reduced) {
            var dx = mx - l.x, dy = my - (l.y - S * 0.6), d = Math.hypot(dx, dy), reach = Math.max(160, S * 2.4);
            if (d > 1 && d < reach) { var w = 1 - d / reach, s = w * w * (3 - 2 * w); ln = [dx / d * s, dy / d * s]; }
          }
          for (var ei = 0; ei < l.els.length; ei++) {
            var e = l.els[ei], age = now - t0;
            var prog = easeOut((age - e.d0) / e.dur);
            if (prog <= 0) continue;
            var jx = boil ? (hash(l.id * 1.37 + boil * 7.1) - 0.5) * amp : 0;
            var jy = boil ? (hash(l.id * 2.71 + boil * 3.1) - 0.5) * amp : 0;
            if (e.t === "stem") {
              var P = [];
              for (var pi = 0; pi < e.pts.length; pi++) {
                var q = e.pts[pi], hh = clamp(-q[1] / 0.7, 0, 1.5);
                P.push([l.x + q[0] * S + jx + ln[0] * S * 0.08 * hh, l.y + q[1] * S + jy + ln[1] * S * 0.04 * hh]);
              }
              drawStem(g, P, prog * fade, S * 0.02, C.stem);
            } else if (e.t === "leaf") {
              if (layerId !== 1) continue;
              drawLeaf(g, l.x + e.x * S + jx, l.y + e.y * S + jy, e.a, e.L * S * fade, e.bend, C.stem, C.bg);
            } else if (e.t === "rose") {
              if (layerId !== 1) continue;
              drawRose(g, l.x + e.x * S + jx, l.y + e.y * S + jy, e.R * S * fade, e.rot, e.seed, clamp((age - e.d0) / 900, 0, 1), C);
            }
          }
        }
      }

      layer(0);
      g.globalAlpha = fade;
      g.fillStyle = C.ink;
      for (var i = 0; i < letters.length; i++) g.fillText(letters[i].ch, letters[i].x, letters[i].y);
      g.globalAlpha = 1;
      layer(1);
    }

    var raf = 0;
    function loop(now) { draw(now); raf = requestAnimationFrame(loop); }

    layout();
    if (document.fonts) document.fonts.load('700 100px "Playfair Display"').then(layout).catch(function () {});
    window.addEventListener("resize", layout);
    el.addEventListener("pointermove", function (e) { var r = el.getBoundingClientRect(); mx = e.clientX - r.left; my = e.clientY - r.top; });
    el.addEventListener("pointerleave", function () { mx = null; });

    // wither + regrow whenever the palette changes
    new MutationObserver(function () { if (!reduced) { witherAt = performance.now(); regrowAt = 0; } })
      .observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    // rebuild geometry after a theme switch (font metrics unchanged, colours read live)
    if (reduced) draw(performance.now()); else raf = requestAnimationFrame(loop);
  }

  var hosts = document.querySelectorAll("[data-garden]");
  for (var i = 0; i < hosts.length; i++) mount(hosts[i]);
})();
