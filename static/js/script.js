/* ==========================================================================
   JK Classes Barnagar - public site behaviour
   Plain JavaScript, no libraries.
   1. Mobile hamburger menu
   2. Gallery category filter
   3. Gallery lightbox (click a photo to see it bigger)
   4. Gentle fade-in as sections scroll into view
   ========================================================================== */

(function () {
  "use strict";

  /* ----------------------------------------------- 1. mobile menu ------- */
  var toggle = document.getElementById("navToggle");
  var mobileMenu = document.getElementById("navMobile");

  if (toggle && mobileMenu) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      toggle.setAttribute("aria-label", open ? "Open menu" : "Close menu");
      mobileMenu.hidden = open;
    });

    // Close the menu when the screen becomes wide enough for the desktop nav.
    window.addEventListener("resize", function () {
      if (window.innerWidth >= 992) {
        toggle.setAttribute("aria-expanded", "false");
        mobileMenu.hidden = true;
      }
    });
  }

  /* --------------------------------- 1b. navbar shadow once scrolled --- */
  var siteNav = document.getElementById("siteNav");

  if (siteNav) {
    var onScroll = function () {
      siteNav.classList.toggle("is-stuck", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ------------------------------------------- 2. gallery filtering ----- */
  var filters = document.querySelectorAll(".filter");
  var grid = document.getElementById("galleryGrid");
  var emptyNote = document.getElementById("galleryEmpty");

  if (filters.length && grid) {
    var items = Array.prototype.slice.call(grid.querySelectorAll(".gallery-item"));

    filters.forEach(function (button) {
      button.addEventListener("click", function () {
        var wanted = button.getAttribute("data-filter");

        filters.forEach(function (b) { b.classList.remove("is-active"); });
        button.classList.add("is-active");

        var shown = 0;
        items.forEach(function (item) {
          var match = wanted === "all" || item.getAttribute("data-category") === wanted;
          item.hidden = !match;
          if (match) { shown++; }
        });

        if (emptyNote) { emptyNote.hidden = shown !== 0; }
      });
    });
  }

  /* ------------------------------------------------- 3. lightbox -------- */
  var photos = Array.prototype.slice.call(document.querySelectorAll(".gallery-item"));

  if (photos.length) {
    var box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Photo preview");
    box.innerHTML =
      '<button class="lightbox__close" type="button" aria-label="Close preview">&times;</button>' +
      '<button class="lightbox__nav lightbox__nav--prev" type="button" aria-label="Previous photo">&#8249;</button>' +
      '<button class="lightbox__nav lightbox__nav--next" type="button" aria-label="Next photo">&#8250;</button>' +
      '<div><img alt="" hidden><p class="lightbox__caption"></p></div>';
    document.body.appendChild(box);

    var boxImage = box.querySelector("img");
    var boxCaption = box.querySelector(".lightbox__caption");
    var current = 0;

    function visiblePhotos() {
      return photos.filter(function (p) { return !p.hidden; });
    }

    function show(index) {
      var list = visiblePhotos();
      if (!list.length) { return; }
      current = (index + list.length) % list.length;
      var item = list[current];
      boxImage.src = item.getAttribute("data-full");
      boxImage.alt = item.getAttribute("data-caption") || "Photo";
      boxImage.hidden = false;
      boxCaption.textContent = item.getAttribute("data-caption") || "";
    }

    function open(item) {
      show(visiblePhotos().indexOf(item));
      box.classList.add("is-open");
      document.body.style.overflow = "hidden";
    }

    function close() {
      box.classList.remove("is-open");
      document.body.style.overflow = "";
      boxImage.removeAttribute("src");
      boxImage.hidden = true;
    }

    photos.forEach(function (item) {
      item.addEventListener("click", function () { open(item); });
      item.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open(item);
        }
      });
    });

    box.querySelector(".lightbox__close").addEventListener("click", close);
    box.querySelector(".lightbox__nav--prev").addEventListener("click", function () { show(current - 1); });
    box.querySelector(".lightbox__nav--next").addEventListener("click", function () { show(current + 1); });
    box.addEventListener("click", function (event) { if (event.target === box) { close(); } });

    document.addEventListener("keydown", function (event) {
      if (!box.classList.contains("is-open")) { return; }
      if (event.key === "Escape") { close(); }
      if (event.key === "ArrowLeft") { show(current - 1); }
      if (event.key === "ArrowRight") { show(current + 1); }
    });
  }

  /* --------------------------------------------- 4. fade-in on scroll --- */
  var revealables = document.querySelectorAll(".reveal");

  if (!("IntersectionObserver" in window)) {
    revealables.forEach(function (el) { el.classList.add("is-visible"); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: "0px 0px -40px 0px" });

  revealables.forEach(function (el) { observer.observe(el); });
})();
