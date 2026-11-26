/* Scroll motion: quiet reveals, cover parallax, press states. */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) return;

  var revealTargets = document.querySelectorAll(".v-section, .club-row, .panel, .event-row, .card");
  revealTargets.forEach(function (el) { el.classList.add("will-reveal"); });

  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("is-in");
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.08 });
    revealTargets.forEach(function (el) { io.observe(el); });
  } else {
    revealTargets.forEach(function (el) { el.classList.add("is-in"); });
  }

  // cover parallax
  var covers = Array.prototype.slice.call(document.querySelectorAll(".club-visual, .ascii-stage"));
  var ticking = false;
  function move() {
    ticking = false;
    var vh = window.innerHeight;
    covers.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) return;
      var centre = r.top + r.height / 2;
      var delta = (centre - vh / 2) / vh;          // -1 … 1
      var shift = Math.max(-14, Math.min(14, -delta * 18));
      el.style.setProperty("--parallax", shift.toFixed(1) + "px");
    });
  }
  function onScroll() {
    if (!ticking) { ticking = true; requestAnimationFrame(move); }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  move();
})();
