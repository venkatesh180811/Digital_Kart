// DigitalKart front-end interactions
function getCookie(name) {
  const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return v ? v.pop() : "";
}

function toggleWishlist(event) {
  const btn = event.target.closest("[data-wishlist-url]");
  if (!btn) return;
  event.preventDefault();

  const url = btn.getAttribute("data-wishlist-url");
  const inWishlist = btn.getAttribute("data-in-wishlist") === "true";
  const icon = btn.querySelector(".wishlist-icon");

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok" && icon) {
        if (data.in_wishlist) {
          icon.classList.remove("fa-regular");
          icon.classList.add("fa-solid");
          btn.setAttribute("data-in-wishlist", "true");
        } else {
          icon.classList.remove("fa-solid");
          icon.classList.add("fa-regular");
          btn.setAttribute("data-in-wishlist", "false");
        }
        showToast(data.message || "Wishlist updated.", "success");
      }
    })
    .catch(() => {
      showToast("Something went wrong. Please try again.", "error");
    });
}

function showToast(message, type = "success") {
  let toast = document.querySelector(".toast-wishlist");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast toast-wishlist toast-" + type;
    toast.style.cssText =
      "position:fixed;bottom:20px;right:20px;background:var(--teal-500);color:white;padding:12px 24px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:1000;font-size:14px;font-weight:600;opacity:0;transform:translateY(20px);transition:all 0.3s ease;";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(20px)";
  }, 2500);
}

document.addEventListener("DOMContentLoaded", () => {
  // Flash sale countdown demo — resets to 4 hours from page load
  const timerEl = document.getElementById("flash-timer");
  if (timerEl) {
    let secondsLeft = 4 * 60 * 60;
    setInterval(() => {
      if (secondsLeft <= 0) return;
      secondsLeft--;
      const h = String(Math.floor(secondsLeft / 3600)).padStart(2, "0");
      const m = String(Math.floor((secondsLeft % 3600) / 60)).padStart(2, "0");
      const s = String(secondsLeft % 60).padStart(2, "0");
      timerEl.textContent = `${h}:${m}:${s}`;
    }, 1000);
  }

  // Live search autocomplete
  const searchInput = document.querySelector(".search-form input[name='q']");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        if (searchInput.value.length < 2) return;
        fetch(`/search/autocomplete/?q=${encodeURIComponent(searchInput.value)}`)
          .then((res) => res.json())
          .catch(() => null);
      }, 300);
    });
  }

  // Wishlist heart buttons
  document.querySelectorAll("[data-wishlist-url]").forEach((btn) => {
    btn.addEventListener("click", toggleWishlist);
  });
});
