/**
 * DigitalKart Hero Slider
 * - Vanilla JS, no dependencies
 * - Autoplay, pause on hover, touch swipe, keyboard nav
 */

(function () {
  "use strict";

  const SELECTOR = ".dk-slider";
  const AUTOPLAY_INTERVAL = 4000;

  class HeroSlider {
    constructor(root) {
      this.root = root;
      this.viewport = root.querySelector(".dk-slider__viewport");
      this.slides = Array.from(root.querySelectorAll(".dk-slide"));
      this.prevBtn = root.querySelector(".dk-slider__arrow--prev");
      this.nextBtn = root.querySelector(".dk-slider__arrow--next");
      this.dotsContainer = root.querySelector(".dk-slider__dots");
      this.currentIndex = 0;
      this.autoplayTimer = null;
      this.isPaused = false;
      this.touchStartX = 0;
      this.touchEndX = 0;

      if (!this.viewport || this.slides.length === 0) return;

      this.init();
    }

    init() {
      this.buildDots();
      this.bindEvents();
      this.goTo(0, false);
      this.startAutoplay();
    }

    buildDots() {
      if (!this.dotsContainer) return;
      this.slides.forEach((_, index) => {
        const dot = document.createElement("button");
        dot.className = "dk-slider__dot";
        dot.setAttribute("aria-label", `Go to slide ${index + 1}`);
        dot.type = "button";
        dot.addEventListener("click", () => {
          this.goTo(index);
          this.resetAutoplay();
        });
        this.dotsContainer.appendChild(dot);
      });
      this.dots = Array.from(this.dotsContainer.querySelectorAll(".dk-slider__dot"));
    }

    bindEvents() {
      // Arrows
      if (this.prevBtn) {
        this.prevBtn.addEventListener("click", () => {
          this.prev();
          this.resetAutoplay();
        });
      }

      if (this.nextBtn) {
        this.nextBtn.addEventListener("click", () => {
          this.next();
          this.resetAutoplay();
        });
      }

      // Pause on hover
      this.root.addEventListener("mouseenter", () => this.pause());
      this.root.addEventListener("mouseleave", () => this.resume());

      // Touch swipe
      this.viewport.addEventListener("touchstart", (e) => {
        this.touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });

      this.viewport.addEventListener("touchend", (e) => {
        this.touchEndX = e.changedTouches[0].screenX;
        this.handleSwipe();
      }, { passive: true });

      // Keyboard navigation
      this.root.setAttribute("tabindex", "0");
      this.root.addEventListener("keydown", (e) => {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          this.prev();
          this.resetAutoplay();
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          this.next();
          this.resetAutoplay();
        }
      });
    }

    handleSwipe() {
      const threshold = 50;
      const diff = this.touchStartX - this.touchEndX;
      if (Math.abs(diff) > threshold) {
        if (diff > 0) {
          this.next();
        } else {
          this.prev();
        }
        this.resetAutoplay();
      }
    }

    goTo(index, animate = true) {
      const prevIndex = this.currentIndex;
      this.currentIndex = (index + this.slides.length) % this.slides.length;

      // Remove active from previous
      this.slides[prevIndex].classList.remove("is-active");

      // Add active to current
      this.slides[this.currentIndex].classList.add("is-active");

      // Update dots
      if (this.dots) {
        this.dots.forEach((dot, i) => {
          dot.classList.toggle("is-active", i === this.currentIndex);
        });
      }

      // Update aria
      this.slides.forEach((slide, i) => {
        slide.setAttribute("aria-hidden", i !== this.currentIndex);
      });
    }

    next() {
      this.goTo(this.currentIndex + 1);
    }

    prev() {
      this.goTo(this.currentIndex - 1);
    }

    startAutoplay() {
      this.stopAutoplay();
      this.autoplayTimer = setInterval(() => {
        if (!this.isPaused) {
          this.next();
        }
      }, AUTOPLAY_INTERVAL);
    }

    stopAutoplay() {
      if (this.autoplayTimer) {
        clearInterval(this.autoplayTimer);
        this.autoplayTimer = null;
      }
    }

    resetAutoplay() {
      this.startAutoplay();
    }

    pause() {
      this.isPaused = true;
    }

    resume() {
      this.isPaused = false;
    }
  }

  // Initialize all sliders on the page
  function initSliders() {
    const sliders = document.querySelectorAll(SELECTOR);
    sliders.forEach((slider) => new HeroSlider(slider));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSliders);
  } else {
    initSliders();
  }
})();
