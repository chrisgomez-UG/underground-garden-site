// Underground Garden — shared site behavior
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- sticky nav ---------------- */
  var nav = document.querySelector(".site-nav");
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------------- mobile menu ---------------- */
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.querySelector(".mobile-menu");
  var closeBtn = document.querySelector(".mobile-menu-close");

  function openMenu() {
    menu.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Close menu");
    document.body.style.overflow = "hidden";
    var firstLink = menu.querySelector("a");
    if (firstLink) firstLink.focus();
  }
  function closeMenu() {
    menu.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Open menu");
    document.body.style.overflow = "";
    toggle.focus();
  }
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var expanded = toggle.getAttribute("aria-expanded") === "true";
      expanded ? closeMenu() : openMenu();
    });
    if (closeBtn) closeBtn.addEventListener("click", closeMenu);
    menu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", closeMenu);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.classList.contains("is-open")) closeMenu();
    });
    // Keep Tab focus cycling inside the open menu — it's a full-screen
    // overlay, so tabbing out would land focus on content you can't see.
    menu.addEventListener("keydown", function (e) {
      if (e.key !== "Tab" || !menu.classList.contains("is-open")) return;
      var focusables = menu.querySelectorAll("a, button");
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    });
  }

  /* ---------------- scroll reveal ---------------- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      revealEls.forEach(function (el) { el.classList.add("is-visible"); });
    } else {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
      );
      revealEls.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------------- hero: word-by-word title reveal ---------------- */
  document.querySelectorAll(".hero h1").forEach(function (h1) {
    if (h1.dataset.split) return;
    h1.dataset.split = "true";

    var frag = document.createDocumentFragment();
    var wordIndex = 0;
    Array.prototype.slice.call(h1.childNodes).forEach(function (node) {
      if (node.nodeType === Node.TEXT_NODE) {
        node.textContent.split(/(\s+)/).forEach(function (chunk) {
          if (chunk === "") return;
          if (chunk.trim() === "") {
            frag.appendChild(document.createTextNode(chunk));
            return;
          }
          var span = document.createElement("span");
          span.className = "word";
          span.textContent = chunk;
          if (!reduceMotion) span.style.transitionDelay = (120 + wordIndex * 70) + "ms";
          frag.appendChild(span);
          wordIndex++;
        });
      } else {
        frag.appendChild(node.cloneNode(true));
      }
    });
    h1.textContent = "";
    h1.appendChild(frag);

    if (reduceMotion) {
      h1.classList.add("is-split-visible");
    } else {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          h1.classList.add("is-split-visible");
        });
      });
    }
  });

  /* ---------------- hero: cursor-reactive glow (desktop only) ---------------- */
  if (!reduceMotion && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.querySelectorAll(".hero").forEach(function (hero) {
      var raf = null;
      hero.addEventListener("mousemove", function (e) {
        if (raf) return;
        raf = requestAnimationFrame(function () {
          var rect = hero.getBoundingClientRect();
          hero.style.setProperty("--mx", ((e.clientX - rect.left) / rect.width) * 100 + "%");
          hero.style.setProperty("--my", ((e.clientY - rect.top) / rect.height) * 100 + "%");
          raf = null;
        });
      });
    });
  }

  /* ---------------- carousel (prev/next + edge-aware disabled state) ---------------- */
  document.querySelectorAll("[data-carousel]").forEach(function (carousel) {
    var track = carousel.querySelector("[data-carousel-track]");
    var prevBtn = carousel.querySelector("[data-carousel-prev]");
    var nextBtn = carousel.querySelector("[data-carousel-next]");
    if (!track) return;

    function scrollByCards(dir) {
      var card = track.querySelector(".carousel-item");
      var amount = card ? card.getBoundingClientRect().width + 24 : track.clientWidth * 0.8;
      track.scrollBy({ left: dir * amount, behavior: reduceMotion ? "auto" : "smooth" });
    }

    function updateArrows() {
      var max = track.scrollWidth - track.clientWidth - 2;
      if (prevBtn) prevBtn.disabled = track.scrollLeft <= 0;
      if (nextBtn) nextBtn.disabled = track.scrollLeft >= max;
    }

    if (prevBtn) prevBtn.addEventListener("click", function () { scrollByCards(-1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { scrollByCards(1); });
    track.addEventListener("scroll", updateArrows, { passive: true });
    window.addEventListener("resize", updateArrows);
    updateArrows();
  });

  /* ---------------- marquee duplication (seamless loop) ---------------- */
  document.querySelectorAll(".marquee-track, .type-break-track").forEach(function (track) {
    if (track.dataset.doubled) return;
    var originalCount = track.children.length;
    track.innerHTML += track.innerHTML;
    // The second half is a visual-only copy for the seamless loop — hide it
    // from screen readers and keep its links out of the Tab order so
    // keyboard/AT users don't hit every item twice.
    Array.prototype.slice.call(track.children, originalCount).forEach(function (clone) {
      clone.setAttribute("aria-hidden", "true");
      clone.querySelectorAll("a").forEach(function (a) { a.tabIndex = -1; });
      if (clone.tagName === "A") clone.tabIndex = -1;
    });
    track.dataset.doubled = "true";
  });

  /* ---------------- countdown ---------------- */
  document.querySelectorAll("[data-countdown]").forEach(function (root) {
    var target = new Date(root.getAttribute("data-countdown")).getTime();
    var dEl = root.querySelector("[data-days]");
    var hEl = root.querySelector("[data-hours]");
    var mEl = root.querySelector("[data-mins]");
    var sEl = root.querySelector("[data-secs]");

    function pad(n) { return String(n).padStart(2, "0"); }

    function tick() {
      var diff = Math.max(0, target - Date.now());
      var days = Math.floor(diff / 86400000);
      var hours = Math.floor((diff % 86400000) / 3600000);
      var mins = Math.floor((diff % 3600000) / 60000);
      var secs = Math.floor((diff % 60000) / 1000);
      if (dEl) dEl.textContent = days;
      if (hEl) hEl.textContent = pad(hours);
      if (mEl) mEl.textContent = pad(mins);
      if (sEl) sEl.textContent = pad(secs);
    }
    tick();
    setInterval(tick, 1000);
  });

  /* ---------------- form handling (Web3Forms — https://web3forms.com) ----------------
     Get a free access key at web3forms.com (just enter an email, no account/dashboard
     needed) and paste it below. Every form on the site emails to that same inbox with
     a different "subject" so you can tell them apart. Until a real key is pasted in,
     submissions will fail silently past validation — see the console warning. */
  var WEB3FORMS_ACCESS_KEY = "629b9e59-9146-4b16-b12c-71fe467e41cf";

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var valid = true;
      form.querySelectorAll("[required]").forEach(function (input) {
        var field = input.closest(".field");
        var ok = input.value.trim().length > 0
          && (input.type !== "email" || /.+@.+\..+/.test(input.value))
          && (input.type !== "tel" || input.value.replace(/\D/g, "").length >= 10);
        if (field) field.classList.toggle("has-error", !ok);
        if (ok) {
          input.removeAttribute("aria-invalid");
        } else {
          input.setAttribute("aria-invalid", "true");
        }
        if (!ok) valid = false;
      });
      if (!valid) {
        var firstError = form.querySelector(".has-error input, .has-error textarea");
        if (firstError) firstError.focus();
        return;
      }

      var note = form.querySelector("[data-form-note]");
      if (!note) {
        // Inline-signup forms keep their note outside the <form> tag.
        var wrap = form.parentElement;
        note = wrap ? wrap.querySelector("[data-form-note]") : null;
      }
      var submitBtn = form.querySelector('button[type="submit"]');

      // Honeypot: the hidden "botcheck" box is invisible to real visitors —
      // if it's checked, a bot filled the form. Show the normal success
      // message (don't tip the bot off) and send nothing.
      var honeypot = form.querySelector('input[name="botcheck"]');
      if (honeypot && honeypot.checked) {
        if (note) {
          note.hidden = false;
          note.classList.remove("form-note--error");
          note.textContent = form.dataset.formSuccess || "Thanks — we'll be in touch shortly.";
        }
        form.reset();
        return;
      }

      var data = new FormData(form);
      data.append("access_key", WEB3FORMS_ACCESS_KEY);
      data.append("subject", form.dataset.formSubject || "Underground Garden — website submission");
      data.append("from_name", "Underground Garden Website");

      if (submitBtn) submitBtn.disabled = true;

      fetch("https://api.web3forms.com/submit", {
        method: "POST",
        headers: { Accept: "application/json" },
        body: data,
      })
        .then(function (res) { return res.json(); })
        .then(function (result) {
          if (note) {
            note.hidden = false;
            note.classList.toggle("form-note--error", !result.success);
            note.textContent = result.success
              ? (form.dataset.formSuccess || "Thanks — we'll be in touch shortly.")
              : "Something went wrong sending that — mind trying again, or email info@ugevents.com?";
          }
          if (result.success) form.reset();
        })
        .catch(function () {
          if (note) {
            note.hidden = false;
            note.classList.add("form-note--error");
            note.textContent = "Something went wrong sending that — mind trying again, or email info@ugevents.com?";
          }
        })
        .finally(function () {
          if (submitBtn) submitBtn.disabled = false;
        });
    });
  });

  /* ---------------- current year ---------------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  /* ---------------- back to top ---------------- */
  var backToTop = document.querySelector(".back-to-top");
  if (backToTop) {
    var toggleBackToTop = function () {
      backToTop.classList.toggle("is-visible", window.scrollY > 800);
    };
    toggleBackToTop();
    window.addEventListener("scroll", toggleBackToTop, { passive: true });
    backToTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
  }
})();
