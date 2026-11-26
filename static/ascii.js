/* ASCII stage — procedural character field with a 3D tilt. */
(function () {
  "use strict";
  var RAMP = " .,:;i1tfLCG08@";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function mount(stage) {
    var canvas = document.createElement("canvas");
    canvas.className = "ascii-canvas";
    canvas.setAttribute("aria-hidden", "true");
    stage.appendChild(canvas);
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var cell = 9, cols = 0, rows = 0, dpr = 1, running = false, last = 0;
    var accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#8fa68e";

    function size() {
      var r = stage.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(r.width * dpr));
      canvas.height = Math.max(1, Math.floor(r.height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cell = r.width > 900 ? 10 : r.width > 520 ? 8 : 6;
      cols = Math.max(10, Math.floor(r.width / cell));
      rows = Math.max(8, Math.floor(r.height / (cell * 1.25)));
    }

    function rgb(hex) {
      var m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
      return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [143, 166, 142];
    }
    var c = rgb(accent);

    function draw(t) {
      var w = cols * cell, h = rows * cell * 1.25;
      ctx.clearRect(0, 0, w, h);
      ctx.font = cell + "px 'Geist Mono', ui-monospace, monospace";
      ctx.textBaseline = "top";
      for (var y = 0; y < rows; y++) {
        for (var x = 0; x < cols; x++) {
          var nx = x / cols, ny = y / rows;
          var v = 0.5
            + 0.42 * Math.sin(nx * 7.2 + t * 0.00035)
            + 0.34 * Math.cos(ny * 5.4 - t * 0.00027)
            + 0.22 * Math.sin((nx + ny) * 15.0 + t * 0.0009);
          var n = Math.max(0, Math.min(1, (v + 0.55) / 1.9));
          var ch = RAMP[Math.floor(n * (RAMP.length - 1))];
          if (ch === " ") continue;
          var a = 0.18 + n * 0.75;
          ctx.fillStyle = "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a.toFixed(3) + ")";
          ctx.fillText(ch, x * cell, y * cell * 1.25);
        }
      }
    }

    function loop(now) {
      if (!running) return;
      if (now - last > 55) { draw(now); last = now; }
      requestAnimationFrame(loop);
    }
    function start() { if (running) return; running = true; requestAnimationFrame(loop); }
    function stop() { running = false; }

    size();
    draw(reduced ? 0 : performance.now());

    if (!reduced) {
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (es) {
          es.forEach(function (e) { e.isIntersecting ? start() : stop(); });
        }, { threshold: 0.1 }).observe(stage);
      } else { start(); }
    }

    window.addEventListener("resize", function () { size(); draw(0); });

    if (reduced) return;
    var raf = 0, tx = 0, ty = 0;
    stage.addEventListener("pointermove", function (e) {
      var r = stage.getBoundingClientRect();
      tx = ((e.clientX - r.left) / r.width - 0.5) * 7;
      ty = ((e.clientY - r.top) / r.height - 0.5) * -7;
      if (!raf) raf = requestAnimationFrame(function () {
        stage.style.transform = "perspective(900px) rotateX(" + ty.toFixed(2) + "deg) rotateY(" + tx.toFixed(2) + "deg)";
        raf = 0;
      });
    });
    stage.addEventListener("pointerleave", function () {
      stage.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)";
    });
  }

  var stages = document.querySelectorAll("[data-ascii]");
  for (var i = 0; i < stages.length; i++) mount(stages[i]);
})();
