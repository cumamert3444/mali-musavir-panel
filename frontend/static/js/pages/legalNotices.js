// pages/legalNotices.js — e-Tebligat / resmi bildirim takibi.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, dateTR, daysUntil } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal } from "../modal.js";

let currentStatus = "";
let currentSearch = "";
let clientsCache = [];

const SOURCE_LABELS = {
  gib: "GİB (e-Tebligat)",
  sgk: "SGK",
  court_enforcement: "Mahkeme / İcra Dairesi",
  municipality: "Belediye",
  other: "Diğer",
};
const STATUS_LABELS = {
  new: ["Yeni", "amber"],
  reviewed: ["İncelendi", "blue"],
  responded: ["Cevaplandı", "green"],
  expired: ["Süresi Geçti", "red"],
  not_applicable: ["İşlem Gerekmiyor", "gray"],
};

export async function renderLegalNotices(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "e-Tebligatlar",
    headerActionsHtml: `
      <button class="btn btn-secondary" id="import-csv-btn">${icons.document} CSV İçe Aktar (Toplu)</button>
      <button class="btn btn-primary" id="new-notice-btn">${icons.plus} Yeni Kayıt</button>
    `,
  });

  content.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="notice-search" class="search-input" placeholder="Başlık veya müşteri ara..." />
          <select id="notice-status-filter">
            <option value="">Tüm Durumlar</option>
            <option value="new">Yeni</option>
            <option value="reviewed">İncelendi</option>
            <option value="responded">Cevaplandı</option>
            <option value="expired">Süresi Geçti</option>
            <option value="not_applicable">İşlem Gerekmiyor</option>
          </select>
        </div>
      </div>
      <div class="table-wrap" id="notice-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;

  try {
    const clientsData = await api.get("/api/v1/clients/", { page_size: 200, ordering: "title" });
    clientsCache = clientsData.results || clientsData;
  } catch (e) {
    /* müşteri listesi olmadan da liste görüntülenebilir */
  }

  content.querySelector("#notice-status-filter").addEventListener("change", (e) => {
    currentStatus = e.target.value;
    loadNotices(content);
  });
  let searchTimer;
  content.querySelector("#notice-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      currentSearch = e.target.value;
      loadNotices(content);
    }, 350);
  });
  content.querySelector("#new-notice-btn").addEventListener("click", () => openNoticeForm(null, () => loadNotices(content)));
  content.querySelector("#import-csv-btn").addEventListener("click", () => openImportModal(() => loadNotices(content)));

  await loadNotices(content);
}

function openImportModal(onSaved) {
  openModal({
    title: "CSV ile Toplu e-Tebligat İçe Aktarma",
    bodyHtml: `
      <p class="text-sm text-muted" style="margin-top:0;">
        Beklenen kolonlar: <code>client_tax_number, source, title, notification_number, received_at, response_due_date, body_summary, notes</code>.
        <br/><code>client_tax_number</code> boş bırakılırsa kayıt ofis geneli olarak eklenir.
        Bu, GİB/SGK'nın e-Tebligat sistemine gerçek zamanlı bağlanan bir servis değildir — portaldan
        indirdiğiniz listeyi buraya toplu yüklersiniz.
      </p>
      <form id="import-form">
        <div class="field"><label>CSV Dosyası *</label><input type="file" name="file" accept=".csv,text/csv" required /></div>
      </form>
      <div id="import-result"></div>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Kapat</button><button class="btn btn-primary" type="submit" form="import-form">Yükle</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#import-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const file = modal.querySelector('input[name="file"]').files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append("file", file);
        try {
          const result = await api.postForm("/api/v1/legal-notifications/import-csv/", fd);
          modal.querySelector("#import-result").innerHTML = `
            <div class="${result.error_count ? "error-banner" : ""}" style="margin-top:12px;">
              ${result.created_count} kayıt oluşturuldu${result.error_count ? `, ${result.error_count} satırda hata:` : "."}
              ${result.errors && result.errors.length ? `<ul>${result.errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("")}</ul>` : ""}
            </div>`;
          if (result.created_count) {
            toast(`${result.created_count} kayıt içe aktarıldı.`, "success");
            if (onSaved) onSaved();
          }
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}

async function loadNotices(content) {
  const wrap = content.querySelector("#notice-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/legal-notifications/", {
      status: currentStatus || undefined,
      search: currentSearch || undefined,
      page_size: 100,
      ordering: "-received_at",
    });
    const items = data.results || data;
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.alert}</div><h3>Kayıt bulunamadı</h3><p>Gelen bir e-Tebligat/resmi bildirimi manuel kaydedin.</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Başlık</th><th>Müşteri</th><th>Kaynak</th><th>Alınma Tarihi</th><th>Cevap Vadesi</th><th>Durum</th></tr></thead>
        <tbody>
          ${items
            .map((n) => {
              const [label, color] = STATUS_LABELS[n.status] || [n.status, "gray"];
              const days = n.response_due_date ? daysUntil(n.response_due_date) : null;
              return `<tr class="clickable" data-id="${n.id}" ${days !== null && days < 0 && !["responded", "not_applicable"].includes(n.status) ? 'style="background:var(--danger-light);"' : ""}>
                <td><strong>${escapeHtml(n.title)}</strong></td>
                <td>${escapeHtml(n.client_title || "—")}</td>
                <td>${escapeHtml(SOURCE_LABELS[n.source] || n.source)}</td>
                <td>${dateTR(n.received_at)}</td>
                <td>${n.response_due_date ? dateTR(n.response_due_date) + (days !== null ? ` <span class="text-muted text-sm">(${days < 0 ? Math.abs(days) + " gün geçti" : days + " gün kaldı"})</span>` : "") : "—"}</td>
                <td><span class="badge badge-${color}">${escapeHtml(label)}</span></td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;
    wrap.querySelectorAll("tr[data-id]").forEach((row) => {
      const notice = items.find((n) => String(n.id) === row.getAttribute("data-id"));
      row.addEventListener("click", () => openNoticeForm(notice, () => loadNotices(content)));
    });
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Kayıtlar yüklenemedi.</div>`;
  }
}

function openNoticeForm(notice, onSaved) {
  const isEdit = !!notice;
  const n = notice || {};
  openModal({
    title: isEdit ? "Kaydı Düzenle" : "Yeni e-Tebligat Kaydı",
    bodyHtml: `
      <form id="notice-form">
        <div class="field"><label>Başlık *</label><input type="text" name="title" required value="${escapeHtml(n.title || "")}" /></div>
        <div class="field-row">
          <div class="field">
            <label>Müşteri</label>
            <select name="client">
              <option value="">— Ofis Geneli —</option>
              ${clientsCache.map((c) => `<option value="${c.id}" ${n.client === c.id ? "selected" : ""}>${escapeHtml(c.title)}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label>Kaynak</label>
            <select name="source">
              ${Object.entries(SOURCE_LABELS)
                .map(([v, label]) => `<option value="${v}" ${(n.source || "gib") === v ? "selected" : ""}>${label}</option>`)
                .join("")}
            </select>
          </div>
        </div>
        <div class="field-row">
          <div class="field"><label>Alınma Tarihi *</label><input type="date" name="received_at" required value="${n.received_at || new Date().toISOString().slice(0, 10)}" /></div>
          <div class="field"><label>Cevap/İtiraz Vadesi</label><input type="date" name="response_due_date" value="${n.response_due_date || ""}" /></div>
        </div>
        <div class="field"><label>Tebligat/İleti No</label><input type="text" name="notification_number" value="${escapeHtml(n.notification_number || "")}" /></div>
        <div class="field"><label>Özet</label><textarea name="body_summary">${escapeHtml(n.body_summary || "")}</textarea></div>
        <div class="field">
          <label>Durum</label>
          <select name="status">
            ${Object.entries(STATUS_LABELS)
              .map(([v, [label]]) => `<option value="${v}" ${(n.status || "new") === v ? "selected" : ""}>${label}</option>`)
              .join("")}
          </select>
        </div>
        <div class="field"><label>Notlar</label><textarea name="notes">${escapeHtml(n.notes || "")}</textarea></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="notice-form">${isEdit ? "Kaydet" : "Oluştur"}</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#notice-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          title: fd.get("title"),
          client: fd.get("client") || null,
          source: fd.get("source"),
          received_at: fd.get("received_at"),
          response_due_date: fd.get("response_due_date") || null,
          notification_number: fd.get("notification_number"),
          body_summary: fd.get("body_summary"),
          status: fd.get("status"),
          notes: fd.get("notes"),
        };
        try {
          if (isEdit) await api.patch(`/api/v1/legal-notifications/${n.id}/`, payload);
          else await api.post("/api/v1/legal-notifications/", payload);
          closeModal();
          toast(isEdit ? "Kayıt güncellendi." : "Kayıt oluşturuldu.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}
