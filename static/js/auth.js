// File: static/js/auth.js
// Purpose: Shared auth helper — updates navbar links based on login state.

(function () {
  const token    = localStorage.getItem("access_token");
  const username = localStorage.getItem("username");

  const navDashboard = document.getElementById("nav-dashboard");
  const navLogin     = document.getElementById("nav-login");
  const navRegister  = document.getElementById("nav-register");
  const navLogout    = document.getElementById("nav-logout");

  if (token) {
    if (navDashboard) navDashboard.style.display = "inline";
    if (navLogin)     navLogin.style.display     = "none";
    if (navRegister)  navRegister.style.display  = "none";
    if (navLogout)    navLogout.style.display     = "inline";
  }
})();

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
  window.location.href = "/login";
}

/**
 * Convenience wrapper for authenticated fetch calls.
 * Automatically attaches the Authorization header.
 */
async function authFetch(url, options = {}) {
  const token = localStorage.getItem("access_token");
  if (!token) {
    window.location.href = "/login";
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(options.headers || {}),
  };

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    logout();
    return;
  }

  return res;
}