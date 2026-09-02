// pages/settings.js — ofis ayarları, API modu ve API anahtarları.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, datetimeTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";
import { state, isOwner } from "../state.js";

let activeTab = "office";

export async function renderSettings(rootEl) {
  const content = renderShell(rootEl, { pageTitle: "Ayarlar" });
  content.innerHTML = `
    <div class="tabs">
      <button data-tab="office" class="active" type="button">Ofis Bilgileri</button>
      <button data-tab="api" type="button">API Modu &amp; Anahtarlar</button>
      <button data-tab="activity" type="button">Aktivite Günlüğü</button>
    </div>
    <div id="settings-tab-content"></div>
  `;
  content.querySelectorAll("[data-tab]").forEach((btn) =>
    btn.addEventListener("click", () => {
      content.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      activeTab = btn.getAttribute("data-tab");
      paintTab();
    })
  );

  function paintTab() {
    const tabEl = content.querySelector("#settings-tab-content");
    if (activeTab === "office") renderOfficeTab(tabEl);
    else if (activeTab === "api") renderApiTab(tabEl);
    else renderActivityTab(tabEl);
  }
  activeTab = "office";
  paintTab();
}

async function renderOfficeTab(el) {
  el.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const office = await api.get("/api/v1/tenants/my-office/");
    const readOnly = !isOwner();
    el.innerHTML = `
      <div class="card" style="max-width:640px;">
        <div class="card-header"><h2>Ofis Bilgileri</h2></div>
        <div class="card-body">
          ${readOnly ? '<div class="error-banner" style="background:var(--warning-light);color:var(--warning);border-color:#fde68a;">Bu ayarları yalnızca ofis sahibi değiştirebilir.</div>' : ""}
          <form id="office-form">
            <div class="field"><label>Ofis Adı</label><input type="text" name="name" value="${escapeHtml(office.name || "")}" ${readOnly ? "disabled" : ""} /></div>
            <div class="field"><label>Ünvan</label><input type="text" name="legal_name" value="${escapeHtml(office.legal_name || "")}" ${readOnly ? "disabled" : ""} /></div>
            <div class="field-row">
              <div class="field"><label>Vergi No</label><input type="text" name="tax_number" value="${escapeHtml(office.tax_number || "")}" ${readOnly ? "disabled" : ""} /></div>
              <div class="field"><label>Vergi Dairesi</label><input type="text" name="tax_office" value="${escapeHtml(office.tax_office || "")}" ${readOnly ? "disabled" : ""} /></div>
            </div>
            <div class="field-row">
              <div class="field"><label>Telefon</label><input type="text" name="phone" value="${escapeHtml(office.phone || "")}" ${readOnly ? "disabled" : ""} /></div>
              <div class="field"><label>E-posta</label><input type="email" name="email" value="${escapeHtml(office.email || "")}" ${readOnly ? "disabled" : ""} /></div>
            </div>
            <div class="field"><label>Adres</label><textarea name="address" ${readOnly ? "disabled" : ""}>${escapeHtml(office.address || "")}</textarea></div>
            ${!readOnly ? '<button type="submit" class="btn btn-primary">Kaydet</button>' : ""}
          </form>
        </div>
      </div>
      ${
        office.subscription
          ? `<div class="card" style="max-width:640px;margin-top:16px;">
              <div class="card-header"><h2>Abonelik</h2></div>
              <div class="card-body">
                <div class="kv-list">
                  <div class="kv-item"><div class="k">Paket</div><div class="v">${escapeHtml(office.subscription.plan.name)}</div></div>
                  <div class="kv-item"><div class="k">Durum</div><div class="v">${escapeHtml(office.subscription.status)}</div></div>
                  <div class="kv-item"><div class="k">Maks. Kullanıcı</div><div class="v">${office.subscription.plan.max_users}</div></div>
                  <div class="kv-item"><div class="k">Maks. Müşteri</div><div class="v">${office.subscription.plan.max_clients}</div></div>
                </div>
              </div>
            </div>`
          : ""
      }
    `;

    const form = el.querySelector("#office-form");
    if (form && !readOnly) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        try {
          await api.patch("/api/v1/tenants/my-office/", {
            name: fd.get("name"),
            legal_name: fd.get("legal_name"),
            tax_number: fd.get("tax_number"),
            tax_office: fd.get("tax_office"),
            phone: fd.get("phone"),
            email: fd.get("email"),
            address: fd.get("address"),
          });
          toast("Ofis bilgileri güncellendi.", "success");
        } catch (err) {
          toastError(err);
        }
      });
    }
  } catch (err) {
    toastError(err);
    el.innerHTML = `<div class="error-banner">Ofis bilgileri yüklenemedi.</div>`;
  }
}

async function renderApiTab(el) {
  el.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const office = await api.get("/api/v1/tenants/my-office/");
    const readOnly = !isOwner();
    let keys = [];
    try {
      const data = await api.get("/api/v1/apikeys/keys/", { page_size: 100 });
      keys = data.results || data;
    } catch (e) {
      /* API modu kapalıyken de anahtar listesi görülebilmeli; hata olursa sessiz geç */
    }

    el.innerHTML = `
      <div class="card" style="max-width:720px;">
        <div class="card-header"><h2>API Modu</h2></div>
        <div class="card-body">
          <p class="text-sm text-muted" style="margin-top:0;">API modu açıldığında dış sistemler (muhasebe programı, entegrasyonlar) <code>X-API-Key</code> başlığıyla bu ofisin verilerine erişebilir.</p>
          <div class="checkbox-row">
            <input type="checkbox" id="api-enabled-toggle" ${office.api_enabled ? "checked" : ""} ${readOnly ? "disabled" : ""} />
            <label for="api-enabled-toggle" style="margin:0;">API modu aktif</label>
          </div>
        </div>
      </div>

      <div class="card" style="max-width:720px;margin-top:16px;">
        <div class="card-header">
          <h2>API Anahtarları</h2>
          ${!readOnly ? `<button class="btn btn-primary btn-sm" id="new-key-btn">${icons.plus} Yeni Anahtar</button>` : ""}
        </div>
        <div class="table-wrap">
          ${
            keys.length
              ? `<table class="data-table">
                  <thead><tr><th>Ad</th><th>Önek</th><th>Durum</th><th>Son Kullanım</th>${!readOnly ? "<th></th>" : ""}</tr></thead>
                  <tbody>
                    ${keys
                      .map(
                        (k) => `<tr>
                          <td>${escapeHtml(k.name)}</td>
                          <td><code>${escapeHtml(k.prefix)}...</code></td>
                          <td>${k.is_active ? '<span class="badge badge-green">Aktif</span>' : '<span class="badge badge-gray">İptal</span>'}</td>
                          <td>${k.last_used_at ? datetimeTR(k.last_used_at) : "Hiç kullanılmadı"}</td>
                          ${!readOnly ? `<td>${k.is_active ? `<button class="btn btn-ghost btn-sm" data-revoke="${k.id}">İptal Et</button>` : ""}</td>` : ""}
                        </tr>`
                      )
                      .join("")}
                  </tbody>
                </table>`
              : `<div class="empty-state"><div class="empty-icon">${icons.key}</div><h3>Henüz API anahtarı yok</h3></div>`
          }
        </div>
      </div>
    `;

    const toggle = el.querySelector("#api-enabled-toggle");
    if (toggle && !readOnly) {
      toggle.addEventListener("change", async () => {
        try {
          await api.patch("/api/v1/tenants/my-office/", { api_enabled: toggle.checked });
          toast(toggle.checked ? "API modu açıldı." : "API modu kapatıldı.", "success");
        } catch (err) {
          toastError(err);
          toggle.checked = !toggle.checked;
        }
      });
    }

    const newKeyBtn = el.querySelector("#new-key-btn");
    if (newKeyBtn) {
      newKeyBtn.addEventListener("click", () => {
        openModal({
          title: "Yeni API Anahtarı",
          bodyHtml: `
            <form id="key-form">
              <div class="field"><label>Anahtar Adı *</label><input type="text" name="name" required placeholder="Örn: Logo Entegrasyonu" /></div>
            </form>
          `,
          footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="key-form">Oluştur</button>`,
          onMount: (modal) => {
            modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
            modal.querySelector("#key-form").addEventListener("submit", async (e) => {
              e.preventDefault();
              const fd = new FormData(e.target);
              try {
                const created = await api.post("/api/v1/apikeys/keys/", { name: fd.get("name") });
                closeModal();
                showRawKey(created.key);
                renderApiTab(el);
              } catch (err) {
                toastError(err);
              }
            });
          },
        });
      });
    }

    el.querySelectorAll("[data-revoke]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu API anahtarını iptal etmek istediğinize emin misiniz? Bu işlem geri alınamaz."))) return;
        try {
          await api.post(`/api/v1/apikeys/keys/${btn.getAttribute("data-revoke")}/revoke/`, {});
          toast("Anahtar iptal edildi.", "success");
          renderApiTab(el);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    el.innerHTML = `<div class="error-banner">Yüklenemedi.</div>`;
  }
}

const ACTION_LABELS = {
  create: "Oluşturuldu",
  update: "Güncellendi",
  delete: "Silindi",
  login: "Giriş yapıldı",
  login_failed: "Başarısız giriş",
  api_access: "API erişimi",
  other: "Diğer",
};

const ACTION_BADGE_COLOR = {
  create: "green",
  update: "blue",
  delete: "red",
  login: "green",
  login_failed: "red",
  api_access: "gray",
  other: "gray",
};

let activityFilter = "";

async function renderActivityTab(el) {
  el.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const params = { page_size: 50, ordering: "-created_at" };
    if (activityFilter) params.action = activityFilter;
    const data = await api.get("/api/v1/audit-logs/", params);
    const entries = data.results || data;

    el.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h2>Aktivite Günlüğü</h2>
          <select id="activity-filter" style="max-width:220px;">
            <option value="">Tüm işlemler</option>
            ${Object.entries(ACTION_LABELS)
              .map(([val, label]) => `<option value="${val}" ${activityFilter === val ? "selected" : ""}>${escapeHtml(label)}</option>`)
              .join("")}
          </select>
        </div>
        <p class="text-sm text-muted" style="padding:0 20px;">
          Ofisinizde kim, ne zaman, hangi kaydı oluşturdu/güncelledi/sildi — en yeniler üstte, son 50 kayıt.
        </p>
        <div class="table-wrap">
          ${
            entries.length
              ? `<table class="data-table">
                  <thead><tr><th>Tarih</th><th>Kullanıcı</th><th>İşlem</th><th>Kayıt Türü</th><th>Yol</th></tr></thead>
                  <tbody>
                    ${entries
                      .map(
                        (e) => `<tr>
                          <td>${datetimeTR(e.created_at)}</td>
                          <td>${escapeHtml(e.actor_label || "—")}</td>
                          <td><span class="badge badge-${ACTION_BADGE_COLOR[e.action] || "gray"}">${escapeHtml(e.action_display || ACTION_LABELS[e.action] || e.action)}</span></td>
                          <td>${escapeHtml(e.model_name || "—")}</td>
                          <td class="text-muted text-sm">${escapeHtml(e.method || "")} ${escapeHtml(e.path || "")}</td>
                        </tr>`
                      )
                      .join("")}
                  </tbody>
                </table>`
              : `<div class="empty-state"><h3>Henüz kayıtlı bir aktivite yok</h3></div>`
          }
        </div>
      </div>
    `;

    el.querySelector("#activity-filter").addEventListener("change", (e) => {
      activityFilter = e.target.value;
      renderActivityTab(el);
    });
  } catch (err) {
    toastError(err);
    el.innerHTML = `<div class="error-banner">Aktivite günlüğü yüklenemedi.</div>`;
  }
}

function showRawKey(key) {
  openModal({
    title: "API Anahtarı Oluşturuldu",
    bodyHtml: `
      <p>Bu anahtarı şimdi kopyalayın — güvenlik nedeniyle bir daha gösterilmeyecek.</p>
      <div class="field">
        <input type="text" readonly value="${escapeHtml(key)}" id="raw-key-input" style="font-family:monospace;width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;" />
      </div>
    `,
    footerHtml: `<button class="btn btn-secondary" id="copy-btn" type="button">Kopyala</button><button class="btn btn-primary" id="ok-btn" type="button">Anladım</button>`,
    onMount: (modal) => {
      modal.querySelector("#ok-btn").addEventListener("click", closeModal);
      modal.querySelector("#copy-btn").addEventListener("click", async () => {
        const input = modal.querySelector("#raw-key-input");
        input.select();
        try {
          await navigator.clipboard.writeText(key);
          toast("Panoya kopyalandı.", "success");
        } catch (e) {
          document.execCommand("copy");
        }
      });
    },
  });
}
