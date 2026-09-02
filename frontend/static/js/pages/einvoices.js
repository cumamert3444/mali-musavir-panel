// pages/einvoices.js — e-Fatura Kayıtları (dürüst kapsam: CSV/Excel içe aktarma,
// gerçek zamanlı GİB/TÜRMOB API entegrasyonu değil — bkz. apps.einvoices.models docstring'i).
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

let clientsCache = [];
let currentClient = "";
let currentDocType = "";
let currentDirection = "";

const DOC_TYPE_LABELS = {
  e_fatura: "e-Fatura",
  e_arsiv: "e-Arşiv Fatura",
  e_irsaliye: "e-İrsaliye",
  e_mm: "e-Müstahsil Makbuzu",
  e_smm: "e-Serbest Meslek Makbuzu",
};
const DIRECTION_LABELS = { incoming: "Gelen (Alış)", outgoing: "Giden (Satış)" };
const STATUS_LABELS = {
  approved: ["Onaylandı", "green"],
  pending: ["Beklemede", "amber"],
  rejected: ["Reddedildi", "red"],
  cancelled: ["İptal Edildi", "gray"],
};

export async function renderEInvoices(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "e-Fatura Kayıtları",
    headerActionsHtml: `
      <button class="btn btn-secondary" id="import-csv-btn">${icons.document} CSV İçe Aktar</button>
      <button class="btn btn-primary" id="new-einvoice-btn">${icons.plus} Yeni Kayıt</button>
    `,
  });

  content.innerHTML = `
    <div class="card" style="margin-bottom:16px;">
      <div class="card-body">
        <p class="text-sm text-muted" style="margin:0 0 10px;">
          Bu liste, mükelleflerinizin e-Fatura/e-Arşiv/e-İrsaliye kayıtlarının Luca e-Belge Portalı
          (veya kullandığınız entegratör) üzerinden alınıp buraya işlenen (elle veya CSV/Excel toplu
          içe aktarma ile) konsolide görünümüdür — gerçek zamanlı, otomatik bir GİB/TÜRMOB API
          entegrasyonu değildir (TÜRMOB Luca'nın üçüncü parti yazılımlara açık genel bir API'si
          bulunmuyor).
        </p>
        <div id="einvoice-summary" class="stat-grid"><div class="loading-row">Yükleniyor...</div></div>
      </div>
    </div>

    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <select id="einvoice-client-filter"><option value="">Tüm Müşteriler</option></select>
          <select id="einvoice-doctype-filter">
            <option value="">Tüm Belge Türleri</option>
            ${Object.entries(DOC_TYPE_LABELS).map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}
          </select>
          <select id="einvoice-direction-filter">
            <option value="">Gelen + Giden</option>
            ${Object.entries(DIRECTION_LABELS).map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}
          </select>
        </div>
      </div>
      <div class="table-wrap" id="einvoice-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;

  try {
    const clientsData = await api.get("/api/v1/clients/", { page_size: 200, ordering: "title" });
    clientsCache = clientsData.results || clientsData;
    const sel = content.querySelector("#einvoice-client-filter");
    sel.innerHTML += clientsCache.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("");
  } catch (e) {
    /* müşteri filtresi olmadan da devam edilebilir */
  }

  content.querySelector("#einvoice-client-filter").addEventListener("change", (e) => {
    currentClient = e.target.value;
    loadEInvoices(content);
  });
  content.querySelector("#einvoice-doctype-filter").addEventListener("change", (e) => {
    currentDocType = e.target.value;
    loadEInvoices(content);
  });
  content.querySelector("#einvoice-direction-filter").addEventListener("change", (e) => {
    currentDirection = e.target.value;
    loadEInvoices(content);
    loadSummary(content);
  });
  content.querySelector("#new-einvoice-btn").addEventListener("click", () => openEInvoiceForm(null, () => { loadEInvoices(content); loadSummary(content); }));
  content.querySelector("#import-csv-btn").addEventListener("click", () => openImportModal(() => { loadEInvoices(content); loadSummary(content); }));

  await Promise.all([loadSummary(content), loadEInvoices(content)]);
}

async function loadSummary(content) {
  const wrap = content.querySelector("#einvoice-summary");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/einvoices/summary/");
    wrap.innerHTML = `
      <div class="stat-card accent-success">
        <div class="stat-label">Giden (Satış) Toplamı</div>
        <div class="stat-value" style="font-size:20px;">${money(data.outgoing_total)}</div>
      </div>
      <div class="stat-card accent-warning">
        <div class="stat-label">Gelen (Alış) Toplamı</div>
        <div class="stat-value" style="font-size:20px;">${money(data.incoming_total)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Toplam Kayıt</div>
        <div class="stat-value" style="font-size:20px;">${data.count}</div>
      </div>
    `;
  } catch (err) {
    wrap.innerHTML = `<div class="error-banner">Özet yüklenemedi.</div>`;
  }
}

async function loadEInvoices(content) {
  const wrap = content.querySelector("#einvoice-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/einvoices/", {
      client: currentClient || undefined,
      doc_type: currentDocType || undefined,
      direction: currentDirection || undefined,
      page_size: 200,
      ordering: "-issue_date",
    });
    const items = data.results || data;
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.invoice}</div><h3>e-Fatura kaydı bulunamadı</h3><p>Yeni kayıt ekleyin veya CSV/Excel ile toplu içe aktarın.</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Müşteri</th><th>Tür</th><th>Yön</th><th>Fatura No</th><th>Karşı Taraf</th><th>Tarih</th><th>Tutar</th><th>Durum</th><th></th></tr></thead>
        <tbody>
          ${items
            .map((r) => {
              const [label, color] = STATUS_LABELS[r.status] || [r.status, "gray"];
              return `<tr>
                <td><a href="/clients/${r.client}" data-link>${escapeHtml(r.client_title)}</a></td>
                <td>${escapeHtml(DOC_TYPE_LABELS[r.doc_type] || r.doc_type)}</td>
                <td>${escapeHtml(DIRECTION_LABELS[r.direction] || r.direction)}</td>
                <td>${escapeHtml(r.invoice_number || "—")}</td>
                <td>${escapeHtml(r.counterparty_title || "—")}</td>
                <td>${dateTR(r.issue_date)}</td>
                <td>${money(r.amount)}</td>
                <td><span class="badge badge-${color}">${escapeHtml(label)}</span></td>
                <td>
                  <button class="btn btn-ghost btn-sm" data-edit="${r.id}">Düzenle</button>
                  <button class="btn btn-ghost btn-sm" data-delete="${r.id}">Sil</button>
                </td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;
    const itemsById = Object.fromEntries(items.map((r) => [String(r.id), r]));
    wrap.querySelectorAll("[data-edit]").forEach((btn) =>
      btn.addEventListener("click", () => openEInvoiceForm(itemsById[btn.getAttribute("data-edit")], () => { loadEInvoices(content); loadSummary(content); }))
    );
    wrap.querySelectorAll("[data-delete]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu e-Fatura kaydını silmek istediğinize emin misiniz?"))) return;
        try {
          await api.del(`/api/v1/einvoices/${btn.getAttribute("data-delete")}/`);
          toast("Kayıt silindi.", "success");
          loadEInvoices(content);
          loadSummary(content);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">e-Fatura kayıtları yüklenemedi.</div>`;
  }
}

function openEInvoiceForm(record, onSaved) {
  const isEdit = !!record;
  const r = record || {};
  openModal({
    title: isEdit ? "e-Fatura Kaydını Düzenle" : "Yeni e-Fatura Kaydı",
    bodyHtml: `
      <form id="einvoice-form">
        <div class="field">
          <label>Müşteri *</label>
          <select name="client" required ${isEdit ? "disabled" : ""}>
            ${clientsCache.map((c) => `<option value="${c.id}" ${r.client === c.id ? "selected" : ""}>${escapeHtml(c.title)}</option>`).join("")}
          </select>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Belge Türü</label>
            <select name="doc_type">
              ${Object.entries(DOC_TYPE_LABELS).map(([v, l]) => `<option value="${v}" ${(r.doc_type || "e_fatura") === v ? "selected" : ""}>${l}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label>Yön</label>
            <select name="direction">
              ${Object.entries(DIRECTION_LABELS).map(([v, l]) => `<option value="${v}" ${(r.direction || "outgoing") === v ? "selected" : ""}>${l}</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="field"><label>Fatura No / ETTN</label><input type="text" name="invoice_number" value="${escapeHtml(r.invoice_number || "")}" /></div>
        <div class="field-row">
          <div class="field"><label>Karşı Taraf Unvanı</label><input type="text" name="counterparty_title" value="${escapeHtml(r.counterparty_title || "")}" /></div>
          <div class="field"><label>Karşı Taraf VKN/TCKN</label><input type="text" name="counterparty_tax_number" value="${escapeHtml(r.counterparty_tax_number || "")}" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Tutar (₺) *</label><input type="number" step="0.01" name="amount" required value="${r.amount ?? ""}" /></div>
          <div class="field"><label>Belge Tarihi</label><input type="date" name="issue_date" value="${r.issue_date || ""}" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Dönem</label><input type="text" name="period_label" placeholder="2026-08" value="${escapeHtml(r.period_label || "")}" /></div>
          <div class="field">
            <label>Durum</label>
            <select name="status">
              ${Object.entries(STATUS_LABELS).map(([v, [l]]) => `<option value="${v}" ${(r.status || "approved") === v ? "selected" : ""}>${l}</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="field"><label>Notlar</label><textarea name="notes">${escapeHtml(r.notes || "")}</textarea></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="einvoice-form">${isEdit ? "Kaydet" : "Oluştur"}</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#einvoice-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          doc_type: fd.get("doc_type"),
          direction: fd.get("direction"),
          invoice_number: fd.get("invoice_number"),
          counterparty_title: fd.get("counterparty_title"),
          counterparty_tax_number: fd.get("counterparty_tax_number"),
          amount: fd.get("amount"),
          issue_date: fd.get("issue_date") || null,
          period_label: fd.get("period_label"),
          status: fd.get("status"),
          notes: fd.get("notes"),
        };
        if (!isEdit) payload.client = fd.get("client");
        try {
          if (isEdit) await api.patch(`/api/v1/einvoices/${r.id}/`, payload);
          else await api.post("/api/v1/einvoices/", payload);
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

function openImportModal(onSaved) {
  openModal({
    title: "CSV ile Toplu e-Fatura İçe Aktarma",
    bodyHtml: `
      <p class="text-sm text-muted" style="margin-top:0;">
        Luca e-Belge Portalı'ndan (veya entegratörünüzden) Excel olarak indirdiğiniz fatura listesini
        aşağıdaki kolon isimleriyle CSV'ye çevirip yükleyin:
        <br/><code>client_tax_number, doc_type, direction, invoice_number, counterparty_title,
        counterparty_tax_number, amount, currency, issue_date, period_label, status, notes</code>
        <br/><code>client_tax_number</code> bu ofisteki bir müşterinin vergi numarasıyla eşleşmelidir.
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
          const result = await api.postForm("/api/v1/einvoices/import-csv/", fd);
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
