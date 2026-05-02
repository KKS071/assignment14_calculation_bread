// File: static/js/auth.js
// Purpose: Shared auth helpers — navbar state, logout, and authFetch wrapper.

(function updateNav() {
  const token = localStorage.getItem("access_token");
  const show  = id => { const el = document.getElementById(id); if (el) el.style.display = "inline"; };
  const hide  = id => { const el = document.getElementById(id); if (el) el.style.display = "none";   };

  if (token) {
    show("nav-dashboard");
    hide("nav-login");
    hide("nav-register");
    show("nav-logout");
  }
})();

function logout() {
  ["access_token","refresh_token","user_id","username"].forEach(k => localStorage.removeItem(k));
  window.location.href = "/login";
}

/**
 * Authenticated fetch — injects Bearer token and redirects on 401.
 */
async function authFetch(url, options = {}) {
  const token = localStorage.getItem("access_token");
  if (!token) { window.location.href = "/login"; return; }

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (res.status === 401) { logout(); return; }
  return res;
}

/**
 * Parse a comma-separated string into an array of numbers.
 * Returns null if any token is not a finite number.
 */
function parseInputs(raw) {
  const parts = String(raw).split(",").map(s => s.trim()).filter(Boolean);
  if (parts.length < 2) return null;
  const nums = parts.map(Number);
  if (nums.some(n => !isFinite(n) || isNaN(n))) return null;
  return nums;
}

/** Render a comma-separated string as blue pills below the input. */
function renderPills(containerId, rawValue) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const parts = String(rawValue).split(",").map(s => s.trim()).filter(Boolean);
  container.innerHTML = parts
    .map(p => `<span class="input-pill">${p}</span>`)
    .join("");
}

/** Show an element with a text message; hide if message is falsy. */
function showMsg(id, msg, visible = true) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg || "";
  el.style.display = visible && msg ? "block" : "none";
}

/** Badge HTML for an operation type. */
function typeBadge(type) {
  return `<span class="badge badge-${type}">${type}</span>`;
}

/** Operation symbol for display in tables. */
function opSymbol(type) {
  return { addition: "+", subtraction: "−", multiplication: "×", division: "÷" }[type] || "?";
}
