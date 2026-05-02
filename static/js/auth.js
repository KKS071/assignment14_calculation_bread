// File: static/js/auth.js
// Purpose: Navbar state update only. All other helpers (authFetch, parseInputs, etc.)
//          are defined inline in each template so no cross-file dependency can break them.

document.addEventListener("DOMContentLoaded", function () {
  var token = localStorage.getItem("access_token");

  function show(id) {
    var el = document.getElementById(id);
    if (el) el.style.display = "inline";
  }
  function hide(id) {
    var el = document.getElementById(id);
    if (el) el.style.display = "none";
  }

  if (token) {
    show("nav-dashboard");
    hide("nav-login");
    hide("nav-register");
    show("nav-logout");
  } else {
    hide("nav-dashboard");
    show("nav-login");
    show("nav-register");
    hide("nav-logout");
  }
});

function logout() {
  ["access_token", "refresh_token", "user_id", "username"].forEach(function (k) {
    localStorage.removeItem(k);
  });
  window.location.href = "/login";
}
