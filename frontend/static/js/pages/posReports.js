// pages/posReports.js — POS & ÖKC gün sonu senkronizasyon takibi.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

let clientsCache = [];
let currentClient = "";

export async function renderPosReports(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "POS / ÖKC Gün Sonu Raporları",
    headerActionsHtml: `
      <button class="btn btn-secondary" id="import-csv-btn">${icons.document} CSV İçe Aktar</button>
      <button class="btn btn-primary" id="new-report-btn">${icons.plus} Yeni Gün Sonu Raporu</button>
    `,
  });

  const now = new Date();
  content.innerHTML = `
    <div class="card" style="margin-bottom:16px;">
      <div class="card-body">
        <p class="text-sm text-muted" style="margin:0 0 10px;">
          Banka POS ve ÖKC gün sonu (Z raporu) tutarlarını burada özetleyin. Bu, gerçek bir muhasebe
          defteri değildir — rakamları kendi muhasebe yazılımınıza (Logo/Mikro/Luca) ayrıca işlemeniz gerekir.
        </p>
        <div class="toolbar">
          <select id="pos-month-select"></select>
          <select id="pos-client-filter"><option value="">Tüm Müşteriler</option></select>
        </div>
        <div id="pos-summary" class="stat-grid" style="margin-top:14px;"><div class="loading-row">Yükleniyor...</div></div>
      </div>
    </div>

    <div class="card">
      <div class="table-wrap" id="pos-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;

  const monthSelect = content.querySelector("#pos-month-select");
  const months = [];
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push({ year: d.getFullYear(), month: d.getMonth() + 1, label: d.toLocaleDateString("tr-TR", { month: "long", year: "numeric" }) });
  }
  monthSelect.innerHTML = months.map((m) => `<option value="${m.year}-${m.month}">${m.label}</option>`).join("");

  try {
    const clientsData = await api.get("/api/v1/clients/", { page_size: 200, ordering: "title" });
    clientsCache = clientsData.results || clientsData;
    content.querySelector("#pos-client-filter").innerHTML += clientsCache
      .map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`)
      .join("");
  } catch (e) {
    /* devam et */
  }

  monthSelect.addEventListener("change", () => { loadSummary(content); loadReports(content); });
  content.querySelector("#pos-client-filter").addEventListener("change", (e) => {
    currentClient = e.target.value;
    loadReports(content);
  });
  content.querySelector("#new-report-btn").addEventListener("click", () => openReportForm(null, () => { loadReports(content); loadSummary(content); }));
  content.querySelector("#import-csv-btn").addEventListener("click", () => openImportModal(() => { loadReports(content); loadSummary(content); }));

  await Promise.all([loadSummary(content), loadReports(content)]);
}

function getSelectedMonth(content) {
  const [year, month] = content.querySelector("#pos-month-select").value.split("-").map(Number);
  return { year, month };
}

async function loadSummary(content) {
  const wrap = content.querySelector("#pos-summary");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const { year, month } = getSelectedMonth(content);
    const data = await api.get("/api/v1/pos-reports/monthly_summary/", { year, month });
    const totalSales = data.rows.reduce((s, r) => s + r.gross_sales, 0);
    const totalVat = data.rows.reduce((s, r) => s + r.vat_amount, 0);
    const totalPos = data.rows.reduce((s, r) => s + r.pos_collection, 0);
    wrap.innerHTML = `
      <div class="stat-card accent-primary"><div class="stat-label">Toplam Net Satış (600)</div><div class="stat-value" style="font-size:19px;">${money(totalSales)}</div></div>
      <div class="stat-card accent-warning"><div class="stat-label">Toplam Hesaplanan KDV (391)</div><div class="stat-value" style="font-size:19px;">${money(totalVat)}</div></div>
      <div class="stat-card accent-success"><div class="stat-label">Toplam POS Tahsilatı (108)</div><div class="stat-value" style="font-size:19px;">${money(totalPos)}</div></div>
    `;
  } catch (err) {
    wrap.innerHTML = `<div class="error-banner">Özet yüklenemedi.</div>`;
  }
}

async function loadReports(content) {
  const wrap = content.querySelector("#pos-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const { year, month } = getSelectedMonth(content);
    const data = await api.get("/api/v1/pos-reports/", {
      client: currentClient || undefined,
      page_size: 200,
      ordering: "-report_date",
    });
    let items = data.results || data;
    items = items.filter((r) => {
      const d = new Date(r.report_date + "T00:00:00");
      return d.getFullYear() === year && d.getMonth() + 1 === month;
    });
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.bank}</div><h3>Bu ay için kayıt yok</h3><p>Yeni gün sonu raporu ekleyin veya CSV ile toplu içe aktarın.</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Tarih</th><th>Müşteri</th><th>ÖKC No</th><th>Net Satış</th><th>KDV</th><th>POS Tahsilat</th><th>Nakit</th><th></th></tr></thead>
        <tbody>
          ${items
            .map(
              (r) => `<tr>
                <td>${dateTR(r.report_date)}</td>
                <td><a href="/clients/${r.client}" data-link>${escapeHtml(r.client_title)}</a></td>
                <td>${escapeHtml(r.okc_no || "—")}</td>
                <td>${money(r.gross_sales)}</td>
                <td>${money(r.vat_amount)}</td>
                <td>${money(r.pos_collection)}</td>
                <td>${money(r.cash_collection)}</td>
                <td>
                  <button class="btn btn-ghost btn-sm" data-edit="${r.id}">Düzenle</button>
                  <button class="btn btn-ghost btn-sm" data-delete="${r.id}">Sil</button>
                </td>
              </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    const itemsById = Object.fromEntries(items.map((r) => [String(r.id), r]));
    wrap.querySelectorAll("[data-edit]").forEach((btn) =>
      btn.addEventListener("click", () => openReportForm(itemsById[btn.getAttribute("data-edit")], () => { loadReports(content); loadSummary(content); }))
    );
    wrap.querySelectorAll("[data-delete]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu raporu silmek istediğinize emin misiniz?"))) return;
        try {
          await api.del(`/api/v1/pos-reports/${btn.getAttribute("data-delete")}/`);
          toast("Rapor silindi.", "success");
          loadReports(content);
          loadSummary(content);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Raporlar yüklenemedi.</div>`;
  }
}

function openReportForm(report, onSaved) {
  const isEdit = !!report;
  const r = report || {};
  openModal({
    title: isEdit ? "Gün Sonu Raporunu Düzenle" : "Yeni Gün Sonu Raporu",
    bodyHtml: `
      <form id="pos-form">
        <div class="field">
          <label>Müşteri *</label>
          <select name="client" required ${isEdit ? "disabled" : ""}>
            ${clientsCache.map((c) => `<option value="${c.id}" ${r.client === c.id ? "selected" : ""}>${escapeHtml(c.title)}</option>`).join("")}
          </select>
        </div>
        <div class="field-row">
          <div class="field"><label>Tarih *</label><input type="date" name="report_date" required value="${r.report_date || new Date().toISOString().slice(0, 10)}" /></div>
          <div class="field"><label>ÖKC No</label><input type="text" name="okc_no" value="${escapeHtml(r.okc_no || "")}" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Net Satış (₺)</label><input type="number" step="0.01" name="gross_sales" value="${r.gross_sales ?? 0}" /></div>
          <div class="field"><label>Hesaplanan KDV (₺)</label><input type="number" step="0.01" name="vat_amount" value="${r.vat_amount ?? 0}" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>POS Tahsilatı (₺)</label><input type="number" step="0.01" name="pos_collection" value="${r.pos_collection ?? 0}" /></div>
          <div class="field"><label>Nakit Tahsilat (₺)</label><input type="number" step="0.01" name="cash_collection" value="${r.cash_collection ?? 0}" /></div>
        </div>
        <div class="field"><label>Notlar</label><textarea name="notes">${escapeHtml(r.notes || "")}</textarea></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="pos-form">${isEdit ? "Kaydet" : "Oluştur"}</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#pos-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          report_date: fd.get("report_date"),
          okc_no: fd.get("okc_no"),
          gross_sales: fd.get("gross_sales") || 0,
          vat_amount: fd.get("vat_amount") || 0,
          pos_collection: fd.get("pos_collection") || 0,
          cash_collection: fd.get("cash_collection") || 0,
          notes: fd.get("notes"),
        };
        if (!isEdit) payload.client = fd.get("client");
        try {
          if (isEdit) await api.patch(`/api/v1/pos-reports/${r.id}/`, payload);
          else await api.post("/api/v1/pos-reports/", payload);
          closeModal();
          toast(isEdit ? "Rapor güncellendi." : "Rapor oluşturuldu.", "success");
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
    title: "CSV ile Toplu Gün Sonu Raporu İçe Aktarma",
    bodyHtml: `
      <p class="text-sm text-muted" style="margin-top:0;">
        Beklenen kolonlar: <code>client_tax_number, report_date, okc_no, gross_sales, vat_amount, pos_collection, cash_collection, notes</code>.
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
          const result = await api.postForm("/api/v1/pos-reports/import-csv/", fd);
          modal.querySelector("#import-result").innerHTML = `
            <div class="${result.error_count ? "error-banner" : ""}" style="margin-top:12px;">
              ${result.created_count} kayıt işlendi${result.error_count ? `, ${result.error_count} satırda hata:` : "."}
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
