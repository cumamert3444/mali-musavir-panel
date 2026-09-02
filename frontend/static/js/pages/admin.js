// pages/admin.js — Süper Admin (SaaS sahibi) paneli: tüm ofisler, kullanıcılar, paketler.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

let activeTab = "overview";

export async function renderAdmin(rootEl) {
  const content = renderShell(rootEl, { pageTitle: "Süper Admin Paneli" });
  content.innerHTML = `
    <div class="tabs">
      <button data-tab="overview" class="active" type="button">Genel Bakış</button>
      <button data-tab="offices" type="button">Ofisler</button>
      <button data-tab="users" type="button">Kullanıcılar</button>
      <button data-tab="plans" type="button">Paketler</button>
    </div>
    <div id="admin-tab-content"></div>
  `;
  content.querySelectorAll("[data-tab]").forEach((btn) =>
    btn.addEventListener("click", () => {
      content.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      activeTab = btn.getAttribute("data-tab");
      paintTab();
    })
  );

  function paintTab() {
    const tabEl = content.querySelector("#admin-tab-content");
    if (activeTab === "overview") renderOverviewTab(tabEl);
    else if (activeTab === "offices") renderOfficesTab(tabEl);
    else if (activeTab === "users") renderUsersTab(tabEl);
    else renderPlansTab(tabEl);
  }
  activeTab = "overview";
  paintTab();
}

async function renderOverviewTab(el) {
  el.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const stats = await api.get("/api/v1/tenants/admin/stats/");
    el.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card accent-primary">
          <div class="stat-label">Toplam Ofis</div>
          <div class="stat-value">${stats.total_offices}</div>
          <div class="stat-sub">${stats.active_offices} aktif · ${stats.inactive_offices} pasif</div>
        </div>
        <div class="stat-card accent-success">
          <div class="stat-label">Toplam Kullanıcı</div>
          <div class="stat-value">${stats.total_users}</div>
        </div>
        <div class="stat-card accent-warning">
          <div class="stat-label">Toplam Müşteri (Mükellef)</div>
          <div class="stat-value">${stats.total_clients}</div>
        </div>
      </div>

      <div class="two-col">
        <div class="card">
          <div class="card-header"><h2>Pakete Göre Dağılım</h2></div>
          <div class="table-wrap">
            ${
              stats.plan_breakdown.length
                ? `<table class="data-table">
                    <thead><tr><th>Paket</th><th>Ofis Sayısı</th></tr></thead>
                    <tbody>
                      ${stats.plan_breakdown
                        .map((p) => `<tr><td>${escapeHtml(p.plan__name || "—")}</td><td>${p.office_count}</td></tr>`)
                        .join("")}
                    </tbody>
                  </table>`
                : `<div class="empty-state"><h3>Kayıt yok</h3></div>`
            }
          </div>
        </div>
        <div class="card">
          <div class="card-header"><h2>Abonelik Durumuna Göre</h2></div>
          <div class="table-wrap">
            ${
              stats.status_breakdown.length
                ? `<table class="data-table">
                    <thead><tr><th>Durum</th><th>Adet</th></tr></thead>
                    <tbody>
                      ${stats.status_breakdown
                        .map((s) => `<tr><td>${escapeHtml(s.status)}</td><td>${s.count}</td></tr>`)
                        .join("")}
                    </tbody>
                  </table>`
                : `<div class="empty-state"><h3>Kayıt yok</h3></div>`
            }
          </div>
        </div>
      </div>

      <div class="card" style="margin-top:18px;">
        <div class="card-header"><h2>Son Kayıt Olan Ofisler</h2></div>
        <div class="table-wrap">
          ${renderOfficeTable(stats.recent_offices)}
        </div>
      </div>
    `;
  } catch (err) {
    toastError(err);
    el.innerHTML = `<div class="error-banner">Platform istatistikleri yüklenemedi: ${escapeHtml(err.message)}</div>`;
  }
}

function renderOfficeTable(offices, { withActions = false } = {}) {
  if (!offices.length) {
    return `<div class="empty-state"><div class="empty-icon">${icons.building}</div><h3>Ofis bulunamadı</h3></div>`;
  }
  return `
    <table class="data-table">
      <thead><tr><th>Ofis</th><th>Vergi No</th><th>Paket</th><th>Kullanıcı</th><th>Müşteri</th><th>Durum</th><th>Kayıt Tarihi</th>${withActions ? "<th></th>" : ""}</tr></thead>
      <tbody>
        ${offices
          .map(
            (o) => `<tr>
              <td><strong>${escapeHtml(o.name)}</strong></td>
              <td>${escapeHtml(o.tax_number || "—")}</td>
              <td>${escapeHtml((o.subscription && o.subscription.plan && o.subscription.plan.name) || "—")}</td>
              <td>${o.user_count}</td>
              <td>${o.client_count}</td>
              <td>${o.is_active ? '<span class="badge badge-green">Aktif</span>' : '<span class="badge badge-red">Pasif</span>'}</td>
              <td>${dateTR(o.created_at)}</td>
              ${
                withActions
                  ? `<td><button class="btn btn-ghost btn-sm" data-toggle-office="${o.id}">${o.is_active ? "Pasife Al" : "Aktive Et"}</button></td>`
                  : ""
              }
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

async function renderOfficesTab(el) {
  el.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="office-search" class="search-input" placeholder="Ofis adı veya vergi no ara..." />
        </div>
      </div>
      <div class="table-wrap" id="office-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;
  let searchTimer;
  el.querySelector("#office-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadOffices(el, e.target.value), 350);
  });
  await loadOffices(el, "");
}

async function loadOffices(el, search) {
  const wrap = el.querySelector("#office-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/tenants/admin/offices/", { search: search || undefined, page_size: 100 });
    const offices = data.results || data;
    wrap.innerHTML = renderOfficeTable(offices, { withActions: true });
    wrap.querySelectorAll("[data-toggle-office]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-toggle-office");
        if (!(await confirmDialog("Bu ofisin durumunu değiştirmek istediğinize emin misiniz?"))) return;
        try {
          await api.post(`/api/v1/tenants/admin/offices/${id}/toggle_active/`, {});
          toast("Ofis durumu güncellendi.", "success");
          loadOffices(el, search);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Ofisler yüklenemedi.</div>`;
  }
}

async function renderUsersTab(el) {
  el.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="user-search" class="search-input" placeholder="E-posta veya isim ara..." />
        </div>
      </div>
      <div class="table-wrap" id="user-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;
  let searchTimer;
  el.querySelector("#user-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadUsers(el, e.target.value), 350);
  });
  await loadUsers(el, "");
}

async function loadUsers(el, search) {
  const wrap = el.querySelector("#user-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/tenants/admin/users/", { search: search || undefined, page_size: 100 });
    const users = data.results || data;
    if (!users.length) {
      wrap.innerHTML = `<div class="empty-state"><h3>Kullanıcı bulunamadı</h3></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>E-posta</th><th>Ad Soyad</th><th>Ofis(ler)</th><th>Yetki</th><th>Durum</th><th>Kayıt</th><th></th></tr></thead>
        <tbody>
          ${users
            .map(
              (u) => `<tr>
                <td>${escapeHtml(u.email)}</td>
                <td>${escapeHtml(`${u.first_name} ${u.last_name}`.trim() || "—")}</td>
                <td>${u.memberships.map((m) => escapeHtml(m.office_name)).join(", ") || "—"}</td>
                <td>${u.is_superuser ? '<span class="badge badge-amber">Süper Admin</span>' : u.is_staff ? '<span class="badge badge-blue">Personel</span>' : "—"}</td>
                <td>${u.is_active ? '<span class="badge badge-green">Aktif</span>' : '<span class="badge badge-red">Pasif</span>'}</td>
                <td>${dateTR(u.date_joined)}</td>
                <td><button class="btn btn-ghost btn-sm" data-toggle-user="${u.id}">${u.is_active ? "Pasife Al" : "Aktive Et"}</button></td>
              </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    wrap.querySelectorAll("[data-toggle-user]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-toggle-user");
        if (!(await confirmDialog("Bu kullanıcının durumunu değiştirmek istediğinize emin misiniz?"))) return;
        try {
          await api.post(`/api/v1/tenants/admin/users/${id}/toggle_active/`, {});
          toast("Kullanıcı durumu güncellendi.", "success");
          loadUsers(el, search);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Kullanıcılar yüklenemedi.</div>`;
  }
}

async function renderPlansTab(el) {
  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>Abonelik Paketleri</h2>
        <button class="btn btn-primary btn-sm" id="new-plan-btn">${icons.plus} Yeni Paket</button>
      </div>
      <div class="table-wrap" id="plan-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;
  el.querySelector("#new-plan-btn").addEventListener("click", () => openPlanForm(null, () => loadPlans(el)));
  await loadPlans(el);
}

async function loadPlans(el) {
  const wrap = el.querySelector("#plan-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/tenants/admin/plans/", { page_size: 100 });
    const plans = data.results || data;
    if (!plans.length) {
      wrap.innerHTML = `<div class="empty-state"><h3>Henüz paket tanımlı değil</h3></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Paket</th><th>Kod</th><th>Aylık Ücret</th><th>Maks. Kullanıcı</th><th>Maks. Müşteri</th><th>Kullanan Ofis</th><th>Durum</th><th></th></tr></thead>
        <tbody>
          ${plans
            .map(
              (p) => `<tr class="clickable" data-id="${p.id}">
                <td><strong>${escapeHtml(p.name)}</strong></td>
                <td><code>${escapeHtml(p.code)}</code></td>
                <td>${money(p.price_monthly)}</td>
                <td>${p.max_users}</td>
                <td>${p.max_clients}</td>
                <td>${p.office_count}</td>
                <td>${p.is_active ? '<span class="badge badge-green">Aktif</span>' : '<span class="badge badge-gray">Pasif</span>'}</td>
                <td><button class="btn btn-ghost btn-sm" data-edit="${p.id}">Düzenle</button></td>
              </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    const plansById = Object.fromEntries(plans.map((p) => [String(p.id), p]));
    wrap.querySelectorAll("[data-edit]").forEach((btn) =>
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        openPlanForm(plansById[btn.getAttribute("data-edit")], () => loadPlans(el));
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Paketler yüklenemedi.</div>`;
  }
}

function openPlanForm(plan, onSaved) {
  const isEdit = !!plan;
  const p = plan || {};
  openModal({
    title: isEdit ? "Paketi Düzenle" : "Yeni Paket",
    bodyHtml: `
      <form id="plan-form">
        <div class="field-row">
          <div class="field"><label>Paket Adı *</label><input type="text" name="name" required value="${escapeHtml(p.name || "")}" /></div>
          <div class="field"><label>Kod *</label><input type="text" name="code" required value="${escapeHtml(p.code || "")}" ${isEdit ? "readonly" : ""} /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Aylık Ücret (₺)</label><input type="number" step="0.01" name="price_monthly" value="${p.price_monthly ?? 0}" /></div>
          <div class="field"><label>Maks. Kullanıcı</label><input type="number" name="max_users" value="${p.max_users ?? 3}" /></div>
        </div>
        <div class="field"><label>Maks. Müşteri</label><input type="number" name="max_clients" value="${p.max_clients ?? 25}" /></div>
        <div class="checkbox-row"><input type="checkbox" id="plan-active" name="is_active" ${p.is_active !== false ? "checked" : ""} /><label for="plan-active" style="margin:0;">Aktif (yeni ofis kaydında seçilebilir)</label></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="plan-form">${isEdit ? "Kaydet" : "Oluştur"}</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#plan-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          name: fd.get("name"),
          code: fd.get("code"),
          price_monthly: fd.get("price_monthly") || 0,
          max_users: fd.get("max_users") || 1,
          max_clients: fd.get("max_clients") || 1,
          is_active: fd.get("is_active") === "on",
        };
        try {
          if (isEdit) await api.patch(`/api/v1/tenants/admin/plans/${p.id}/`, payload);
          else await api.post("/api/v1/tenants/admin/plans/", payload);
          closeModal();
          toast(isEdit ? "Paket güncellendi." : "Paket oluşturuldu.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}
