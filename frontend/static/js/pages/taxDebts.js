// pages/taxDebts.js — Vergi/SGK Borç Matrisi (Tek Hamle tarzı konsolide görünüm).
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

let clientsCache = [];
let currentClient = "";
let currentStatus = "";

const DEBT_TYPE_LABELS = { vergi: "Vergi (GİB)", sgk: "SGK Prim Borcu", belediye: "Belediye", diger: "Diğer" };
const STATUS_LABELS = {
  unpaid: ["Ödenmedi", "red"],
  partially_paid: ["Kısmen Ödendi", "amber"],
  paid: ["Ödendi", "green"],
  disputed: ["İtiraz Edildi", "blue"],
};

export async function renderTaxDebts(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Vergi / SGK Borç Matrisi",
    headerActionsHtml: `
      <button class="btn btn-secondary" id="import-csv-btn">${icons.document} CSV İçe Aktar</button>
      <button class="btn btn-primary" id="new-debt-btn">${icons.plus} Yeni Borç Kaydı</button>
    `,
  });

  content.innerHTML = `
    <div class="card" style="margin-bottom:16px;">
      <div class="card-body">
        <p class="text-sm text-muted" style="margin:0 0 10px;">
          Bu matris, mükelleflerinizin vergi/SGK borçlarının GİB/e-Devlet üzerinden kontrol edilip
          buraya işlenen (elle veya CSV toplu içe aktarma ile) konsolide görünümüdür — gerçek zamanlı
          resmi bir borç sorgulama entegrasyonu değildir.
        </p>
        <div id="matrix-summary" class="stat-grid"><div class="loading-row">Yükleniyor...</div></div>
      </div>
    </div>

    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <select id="debt-client-filter"><option value="">Tüm Müşteriler</option></select>
          <select id="debt-status-filter">
            <option value="">Ödenmemiş Tümü</option>
            <option value="unpaid">Ödenmedi</option>
            <option value="partially_paid">Kısmen Ödendi</option>
            <option value="disputed">İtiraz Edildi</option>
            <option value="paid">Ödendi</option>
          </select>
        </div>
      </div>
      <div class="table-wrap" id="debt-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;

  try {
    const clientsData = await api.get("/api/v1/clients/", { page_size: 200, ordering: "title" });
    clientsCache = clientsData.results || clientsData;
    const sel = content.querySelector("#debt-client-filter");
    sel.innerHTML += clientsCache.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("");
  } catch (e) {
    /* müşteri filtresi olmadan da devam edilebilir */
  }

  content.querySelector("#debt-client-filter").addEventListener("change", (e) => {
    currentClient = e.target.value;
    loadDebts(content);
  });
  content.querySelector("#debt-status-filter").addEventListener("change", (e) => {
    currentStatus = e.target.value;
    loadDebts(content);
    loadMatrix(content);
  });
  content.querySelector("#new-debt-btn").addEventListener("click", () => openDebtForm(null, () => { loadDebts(content); loadMatrix(content); }));
  content.querySelector("#import-csv-btn").addEventListener("click", () => openImportModal(() => { loadDebts(content); loadMatrix(content); }));

  await Promise.all([loadMatrix(content), loadDebts(content)]);
}

async function loadMatrix(content) {
  const wrap = content.querySelector("#matrix-summary");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/tax-debts/matrix/", { status: currentStatus || undefined });
    wrap.innerHTML = `
      <div class="stat-card accent-danger">
        <div class="stat-label">Toplam Borç</div>
        <div class="stat-value" style="font-size:20px;">${money(data.grand_total)}</div>
        <div class="stat-sub">${data.client_count} müşteride borç kaydı</div>
      </div>
      <div class="stat-card accent-warning">
        <div class="stat-label">En Yüksek Borçlu</div>
        <div class="stat-value" style="font-size:16px;">${data.rows[0] ? escapeHtml(data.rows[0].client_title) : "—"}</div>
        <div class="stat-sub">${data.rows[0] ? money(data.rows[0].total) : ""}</div>
      </div>
    `;
  } catch (err) {
    wrap.innerHTML = `<div class="error-banner">Özet yüklenemedi.</div>`;
  }
}

async function loadDebts(content) {
  const wrap = content.querySelector("#debt-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/tax-debts/", {
      client: currentClient || undefined,
      status: currentStatus || undefined,
      page_size: 200,
      ordering: "-due_date",
    });
    const items = data.results || data;
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.alert}</div><h3>Borç kaydı bulunamadı</h3><p>Yeni kayıt ekleyin veya CSV ile toplu içe aktarın.</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Müşteri</th><th>Tür</th><th>Açıklama</th><th>Dönem</th><th>Vade</th><th>Tutar</th><th>Durum</th><th></th></tr></thead>
        <tbody>
          ${items
            .map((d) => {
              const [label, color] = STATUS_LABELS[d.status] || [d.status, "gray"];
              return `<tr>
                <td><a href="/clients/${d.client}" data-link>${escapeHtml(d.client_title)}</a></td>
                <td>${escapeHtml(DEBT_TYPE_LABELS[d.debt_type] || d.debt_type)}</td>
                <td>${escapeHtml(d.description || "—")}</td>
                <td>${escapeHtml(d.period_label || "—")}</td>
                <td>${dateTR(d.due_date)}</td>
                <td>${money(d.amount)}</td>
                <td><span class="badge badge-${color}">${escapeHtml(label)}</span></td>
                <td>
                  <button class="btn btn-ghost btn-sm" data-edit="${d.id}">Düzenle</button>
                  <button class="btn btn-ghost btn-sm" data-delete="${d.id}">Sil</button>
                </td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;
    const itemsById = Object.fromEntries(items.map((d) => [String(d.id), d]));
    wrap.querySelectorAll("[data-edit]").forEach((btn) =>
      btn.addEventListener("click", () => openDebtForm(itemsById[btn.getAttribute("data-edit")], () => { loadDebts(content); loadMatrix(content); }))
    );
    wrap.querySelectorAll("[data-delete]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu borç kaydını silmek istediğinize emin misiniz?"))) return;
        try {
          await api.del(`/api/v1/tax-debts/${btn.getAttribute("data-delete")}/`);
          toast("Kayıt silindi.", "success");
          loadDebts(content);
          loadMatrix(content);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Borç kayıtları yüklenemedi.</div>`;
  }
}

function openDebtForm(debt, onSaved) {
  const isEdit = !!debt;
  const d = debt || {};
  openModal({
    title: isEdit ? "Borç Kaydını Düzenle" : "Yeni Borç Kaydı",
    bodyHtml: `
      <form id="debt-form">
        <div class="field">
          <label>Müşteri *</label>
          <select name="client" required ${isEdit ? "disabled" : ""}>
            ${clientsCache.map((c) => `<option value="${c.id}" ${d.client === c.id ? "selected" : ""}>${escapeHtml(c.title)}</option>`).join("")}
          </select>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Borç Türü</label>
            <select name="debt_type">
              ${Object.entries(DEBT_TYPE_LABELS).map(([v, l]) => `<option value="${v}" ${(d.debt_type || "vergi") === v ? "selected" : ""}>${l}</option>`).join("")}
            </select>
          </div>
          <div class="field"><label>Dönem</label><input type="text" name="period_label" placeholder="2026-08" value="${escapeHtml(d.period_label || "")}" /></div>
        </div>
        <div class="field"><label>Açıklama</label><input type="text" name="description" value="${escapeHtml(d.description || "")}" /></div>
        <div class="field-row">
          <div class="field"><label>Tutar (₺) *</label><input type="number" step="0.01" name="amount" required value="${d.amount ?? ""}" /></div>
          <div class="field"><label>Vade Tarihi</label><input type="date" name="due_date" value="${d.due_date || ""}" /></div>
        </div>
        <div class="field">
          <label>Durum</label>
          <select name="status">
            ${Object.entries(STATUS_LABELS).map(([v, [l]]) => `<option value="${v}" ${(d.status || "unpaid") === v ? "selected" : ""}>${l}</option>`).join("")}
          </select>
        </div>
        <div class="field"><label>Notlar</label><textarea name="notes">${escapeHtml(d.notes || "")}</textarea></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="debt-form">${isEdit ? "Kaydet" : "Oluştur"}</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#debt-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          debt_type: fd.get("debt_type"),
          period_label: fd.get("period_label"),
          description: fd.get("description"),
          amount: fd.get("amount"),
          due_date: fd.get("due_date") || null,
          status: fd.get("status"),
          notes: fd.get("notes"),
        };
        if (!isEdit) payload.client = fd.get("client");
        try {
          if (isEdit) await api.patch(`/api/v1/tax-debts/${d.id}/`, payload);
          else await api.post("/api/v1/tax-debts/", payload);
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
    title: "CSV ile Toplu Borç İçe Aktarma",
    bodyHtml: `
      <p class="text-sm text-muted" style="margin-top:0;">
        Beklenen kolonlar: <code>client_tax_number, debt_type, period_label, description, amount, due_date, status, notes</code>.
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
          const result = await api.postForm("/api/v1/tax-debts/import-csv/", fd);
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
