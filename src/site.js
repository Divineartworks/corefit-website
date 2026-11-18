(function () {
  var d = document, h = d.documentElement;
  h.classList.add("js");
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var sda = window.CSS && CSS.supports && CSS.supports("animation-timeline: view()");
  var io = "IntersectionObserver" in window;
  if (!sda || reduce) {
    // Without scroll-driven animations (or with reduced motion) the phone swaps screens by step,
    // and the top bar turns solid after the first screen.
    h.classList.add("no-sda");
    var top = d.getElementById("top");
    var solid = function () { top.classList.toggle("is-solid", scrollY > 120); };
    addEventListener("scroll", solid, { passive: true }); solid();
    var screens = d.querySelectorAll(".screen");
    if (io && screens.length) {
      var steps = d.querySelectorAll(".step");
      var so = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!e.isIntersecting) return;
          var n = Array.prototype.indexOf.call(steps, e.target);
          screens.forEach(function (s, i) { s.classList.toggle("on", i <= n); });
        });
      }, { rootMargin: "-45% 0px -45% 0px" });
      steps.forEach(function (s) { so.observe(s); });
    }
  }
  // Phone dock: shows once the hero buttons have scrolled away, hides again at the closing section.
  var dock = d.getElementById("dock"), cta = d.getElementById("hero-cta"), end = d.getElementById("kontakt");
  if (dock && io) {
    var seen = { cta: true, end: false };
    var dx = new IntersectionObserver(function (es) {
      es.forEach(function (e) { seen[e.target === cta ? "cta" : "end"] = e.isIntersecting; });
      dock.classList.toggle("on", !seen.cta && !seen.end);
    });
    dx.observe(cta); dx.observe(end);
  } else if (dock) { dock.classList.add("on"); }
})();
