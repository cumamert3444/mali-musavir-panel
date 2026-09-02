// layout.js — giriş yapılmış kullanıcı için ortak kabuk (sidebar + topbar).
import { icons } from "./icons.js";
import { escapeHtml } from "./format.js";
import { state, roleLabel, switchOffice } from "./state.js";
import { logout } from "./api.js";
import { toastError } from "./toast.js";

const NAV_ITEMS = [
  { path: "/", label: "Panel", icon: "dashboard" },
  { path: "/clients", label: "Müşteriler", icon: "clients" },
  { path: "/invoices", label: "Faturalar", icon: "invoice" },
  { path: "/tasks", label: "Görevler", icon: "task" },
  { path: "/declarations", label: "Beyannameler", icon: "declaration" },
  { path: "/team", label: "Ekip", icon: "team" },
  { path: "/settings", label: "Ayarlar", icon: "settings" },
];

function initials(me) {
  if (!me) return "?";
  const a = (me.first_name || "")[0] || "";
  const b = (me.last_name || "")[0] || "";
  return (a + b).toUpperCase() || (me.email || "?")[0].toUpperCase();
}

export function renderShell(rootEl, { pageTitle = "", headerActionsHtml = "" } = {}) {
  const me = state.me;
  const memberships = (me && me.memberships || []).filter((m) => m.is_active);
  const activeMembership = memberships.find((m) => String(m.office) === String(localStorage.getItem("mmp_active_office_id"))) || memberships[0];

  const officeSwitcherHtml =
    memberships.length > 1
      ? `<select id="office-switch" class="office-switch" style="margin-left:10px;padding:4px 8px;border-radius:6px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.06);color:#e2e8f0;font-size:11.5px;max-width:100%;">
          ${memberships.map((m) => `<option value="${m.office}" ${activeMembership && m.office === activeMembership.office ? "selected" : ""}>${escapeHtml(m.office_name)}</option>`).join("")}
        </select>`
      : "";

  rootEl.innerHTML = `
    <div class="shell">
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-brand">
          <span class="logo-badge">MM</span>
          <span>Mali Müşavir Paneli</span>
        </div>
        <div class="sidebar-office">
          <strong>${escapeHtml((state.office && state.office.name) || (activeMembership && activeMembership.office_name) || "Ofis")}</strong>
          ${officeSwitcherHtml}
        </div>
        <nav class="sidebar-nav">
          ${NAV_ITEMS.map(
            (item) => `
            <a href="${item.path}" data-link data-nav="${item.path}">
              <span class="nav-icon">${icons[item.icon]}</span>
              <span>${item.label}</span>
            </a>`
          ).join("")}
        </nav>
        <div class="sidebar-footer">
          <div class="sidebar-user">
            <div class="avatar">${initials(me)}</div>
            <div class="who">
              <div class="name">${escapeHtml(me ? (me.first_name || me.email) : "")}</div>
              <div class="role">${escapeHtml(activeMembership ? roleLabel(activeMembership.role) : "")}</div>
            </div>
          </div>
          <button class="btn btn-ghost btn-sm btn-block" id="logout-btn" type="button">
            ${icons.logout} Çıkış Yap
          </button>
        </div>
      </aside>
      <div class="main">
        <div class="topbar">
          <div class="flex gap-8" style="align-items:center;">
            <button class="btn btn-ghost mobile-menu-btn" id="mobile-menu-btn" type="button" aria-label="Menü">${icons.menu}</button>
            <h1>${escapeHtml(pageTitle)}</h1>
          </div>
          <div class="topbar-actions">${headerActionsHtml}</div>
        </div>
        <div class="content" id="page-content"></div>
      </div>
    </div>
  `;

  rootEl.querySelector("#logout-btn").addEventListener("click", () => {
    logout();
    window.location.href = "/login";
  });

  const menuBtn = rootEl.querySelector("#mobile-menu-btn");
  const sidebar = rootEl.querySelector("#sidebar");
  if (menuBtn) {
    menuBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
  }

  const officeSwitch = rootEl.querySelector("#office-switch");
  if (officeSwitch) {
    officeSwitch.addEventListener("change", async (e) => {
      try {
        await switchOffice(e.target.value);
        window.location.reload();
      } catch (err) {
        toastError(err);
      }
    });
  }

  return rootEl.querySelector("#page-content");
}
