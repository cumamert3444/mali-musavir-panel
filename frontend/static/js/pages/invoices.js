// pages/invoices.js — hizmet faturaları listesi + yeni fatura oluşturma.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR, statusBadge } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal } from "../modal.js";

let currentPage = 1;
let currentStatus = "";
let currentSearch = "";

export async function renderInvoices(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Faturalar",
    headerActionsHtml: `<button class="btn btn-primary" id="new-invoice-btn">${icons.plus} Yeni Fatura</button>`,
  });

  currentPage = 1;
  content.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="invoice-search" class="search-input" placeholder="Fatura no veya müşteri ara..." />
          <select id="invoice-status-filter">
            <option value="">Tüm Durumlar</option>
            <option value="draft">Taslak</option>
            <option value="sent">Gönderildi</option>
            <option value="partially_paid">Kısmen Ödendi</option>
            <option value="paid">Ödendi</option>
            <option value="overdue">Gecikti</option>
            <option value="canceled">İptal</option>
          </select>
        </div>
      </div>
      <div class="table-wrap" id="invoices-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
      <div class="pagination" id="invoices-pagination" style="display:none;"></div>
    </div>
  `;

  const searchInput = content.querySelector("#invoice-search");
  const statusFilter = content.querySelector("#invoice-status-filter");
  let searchTimer;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      currentSearch = searchInput.value;
      currentPage = 1;
      loadInvoices(content);
    }, 350);
  });
  statusFilter.addEventListener("change", () => {
    currentStatus = statusFilter.value;
    currentPage = 1;
    loadInvoices(content);
  });

  content.querySelector("#new-invoice-btn").addEventListener("click", () => openInvoiceForm(() => loadInvoices(content)));

  await loadInvoices(content);
}

async function loadInvoices(content) {
  const tableWrap = content.querySelector("#invoices-table-wrap");
  const pagination = content.querySelector("#invoices-pagination");
  tableWrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/invoices/", {
      status: currentStatus || undefined,
      search: currentSearch || undefined,
      page: currentPage,
      ordering: "-issue_date",
    });
    const items = data.results || data;
    if (!items.length) {
      tableWrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.invoice}</div><h3>Fatura bulunamadı</h3><p>Yeni bir hizmet faturası oluşturun.</p></div>`;
      pagination.style.display = "none";
      return;
    }
    tableWrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Fatura No</th><th>Müşteri</th><th>Dönem</th><th>Kesim</th><th>Vade</th><th>Toplam</th><th>Kalan</th><th>Durum</th></tr></thead>
        <tbody>
          ${items
            .map(
              (i) => `<tr class="clickable" data-id="${i.id}">
                <td><strong>${escapeHtml(i.invoice_number)}</strong></td>
                <td>${escapeHtml(i.client_title)}</td>
                <td>${escapeHtml(i.period_label || "—")}</td>
                <td>${dateTR(i.issue_date)}</td>
                <td>${dateTR(i.due_date)}</td>
                <td>${money(i.total_amount)}</td>
                <td>${Number(i.balance_due) > 0 ? `<strong style="color:var(--danger)">${money(i.balance_due)}</strong>` : money(0)}</td>
                <td>${statusBadge(i.status)}</td>
              </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    tableWrap.querySelectorAll("tr[data-id]").forEach((row) =>
      row.addEventListener("click", () => window.__mmpRouter.navigate(`/invoices/${row.getAttribute("data-id")}`))
    );

    if (data.count !== undefined) {
      const totalPages = Math.max(1, Math.ceil(data.count / 25));
      pagination.style.display = "flex";
      pagination.innerHTML = `
        <span>${data.count} kayıt · Sayfa ${currentPage}/${totalPages}</span>
        <div class="pager-btns">
          <button class="btn btn-secondary btn-sm" id="prev-page" ${!data.previous ? "disabled" : ""}>← Önceki</button>
          <button class="btn btn-secondary btn-sm" id="next-page" ${!data.next ? "disabled" : ""}>Sonraki →</button>
        </div>`;
      const p = pagination.querySelector("#prev-page");
      const n = pagination.querySelector("#next-page");
      if (p) p.addEventListener("click", () => { currentPage--; loadInvoices(content); });
      if (n) n.addEventListener("click", () => { currentPage++; loadInvoices(content); });
    } else {
      pagination.style.display = "none";
    }
  } catch (err) {
    toastError(err);
    tableWrap.innerHTML = `<div class="error-banner">Faturalar yüklenemedi.</div>`;
  }
}

async function openInvoiceForm(onSaved) {
  let clients = [];
  try {
    const data = await api.get("/api/v1/clients/", { page_size: 200, status: "active", ordering: "title" });
    clients = data.results || data;
  } catch (err) {
    toastError(err);
    return;
  }

  const today = new Date().toISOString().slice(0, 10);
  const dueDefault = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10);

  openModal({
    title: "Yeni Fatura",
    bodyHtml: `
      <form id="invoice-form">
        <div class="field-row">
          <div class="field">
            <label>Müşteri *</label>
            <select name="client" required>
              <option value="">Seçin...</option>
              ${clients.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label>Fatura No *</label>
            <input type="text" name="invoice_number" required placeholder="2026-0001" />
          </div>
        </div>
        <div class="field-row">
          <div class="field"><label>Dönem</label><input type="text" name="period_label" placeholder="2026-08" /></div>
          <div class="field"><label>Kesim Tarihi *</label><input type="date" name="issue_date" required value="${today}" /></div>
        </div>
        <div class="field"><label>Vade Tarihi *</label><input type="date" name="due_date" required value="${dueDefault}" /></div>

        <div class="section-title">Kalemler</div>
        <table class="line-items" id="line-items">
          <thead><tr><th style="width:50%">Açıklama</th><th>Miktar</th><th>Birim Fiyat</th><th></th></tr></thead>
          <tbody id="line-items-body"></tbody>
        </table>
        <button type="button" class="btn btn-secondary btn-sm" id="add-line-btn">${icons.plus} Kalem Ekle</button>

        <div class="field" style="margin-top:16px;"><label>Notlar</label><textarea name="notes"></textarea></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="invoice-form">Oluştur</button>`,
    onMount: (modal) => {
      const tbody = modal.querySelector("#line-items-body");
      const addLine = (desc = "", qty = 1, price = 0) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td><input type="text" class="line-desc" value="${escapeHtml(desc)}" placeholder="Aylık muhasebe hizmeti" required /></td>
          <td><input type="number" step="0.01" class="line-qty" value="${qty}" style="width:70px;" /></td>
          <td><input type="number" step="0.01" class="line-price" value="${price}" style="width:100px;" /></td>
          <td><button type="button" class="btn btn-ghost btn-sm remove-line">✕</button></td>
        `;
        row.querySelector(".remove-line").addEventListener("click", () => row.remove());
        tbody.appendChild(row);
      };
      addLine("Aylık muhasebe hizmet bedeli", 1, 0);
      modal.querySelector("#add-line-btn").addEventListener("click", () => addLine());
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);

      modal.querySelector("#invoice-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const lines = Array.from(tbody.querySelectorAll("tr")).map((row) => ({
          description: row.querySelector(".line-desc").value,
          quantity: row.querySelector(".line-qty").value || 1,
          unit_price: row.querySelector(".line-price").value || 0,
        }));
        try {
          await api.post("/api/v1/invoices/", {
            client: fd.get("client"),
            invoice_number: fd.get("invoice_number"),
            period_label: fd.get("period_label"),
            issue_date: fd.get("issue_date"),
            due_date: fd.get("due_date"),
            notes: fd.get("notes"),
            lines,
          });
          closeModal();
          toast("Fatura oluşturuldu.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}
