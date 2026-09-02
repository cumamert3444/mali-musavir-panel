// pages/clients.js — müşteri listesi + yeni müşteri ekleme.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, statusBadge, legalTypeLabel } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal } from "../modal.js";

let currentPage = 1;
let currentSearch = "";
let currentStatus = "";

export async function renderClients(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Müşteriler",
    headerActionsHtml: `<button class="btn btn-primary" id="new-client-btn">${icons.plus} Yeni Müşteri</button>`,
  });

  currentPage = 1;
  content.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="client-search" class="search-input" placeholder="Ünvan veya vergi no ile ara..." value="${escapeHtml(currentSearch)}" />
          <select id="client-status-filter">
            <option value="">Tüm Durumlar</option>
            <option value="active">Aktif</option>
            <option value="prospect">Potansiyel</option>
            <option value="passive">Pasif</option>
            <option value="former">Eski Müşteri</option>
          </select>
        </div>
      </div>
      <div class="table-wrap" id="clients-table-wrap">
        <div class="loading-row">Yükleniyor...</div>
      </div>
      <div class="pagination" id="clients-pagination" style="display:none;"></div>
    </div>
  `;

  const searchInput = content.querySelector("#client-search");
  const statusFilter = content.querySelector("#client-status-filter");
  statusFilter.value = currentStatus;

  let searchTimer;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      currentSearch = searchInput.value;
      currentPage = 1;
      loadClients(content);
    }, 350);
  });
  statusFilter.addEventListener("change", () => {
    currentStatus = statusFilter.value;
    currentPage = 1;
    loadClients(content);
  });

  content.querySelector("#new-client-btn").addEventListener("click", () => openClientForm(null, () => loadClients(content)));

  await loadClients(content);
}

async function loadClients(content) {
  const tableWrap = content.querySelector("#clients-table-wrap");
  const pagination = content.querySelector("#clients-pagination");
  tableWrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/clients/", {
      search: currentSearch || undefined,
      status: currentStatus || undefined,
      page: currentPage,
    });
    const items = data.results || data;
    if (!items.length) {
      tableWrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.clients}</div><h3>Müşteri bulunamadı</h3><p>Arama kriterlerinizi değiştirin ya da yeni bir müşteri ekleyin.</p></div>`;
      pagination.style.display = "none";
      return;
    }
    tableWrap.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Ünvan</th><th>Tür</th><th>Vergi No</th><th>Paket</th><th>Aylık Ücret</th><th>e-Fatura</th><th>Durum</th>
          </tr>
        </thead>
        <tbody>
          ${items
            .map(
              (c) => `
            <tr class="clickable" data-id="${c.id}">
              <td><strong>${escapeHtml(c.title)}</strong>${c.city ? ` <span class="text-muted text-sm">· ${escapeHtml(c.city)}</span>` : ""}</td>
              <td>${escapeHtml(legalTypeLabel(c.legal_type))}</td>
              <td>${escapeHtml(c.tax_number || "—")}</td>
              <td>${escapeHtml(c.package_name || "—")}</td>
              <td>${money(c.monthly_fee)}</td>
              <td>${c.e_invoice_enabled ? "✓" : "—"}</td>
              <td>${statusBadge(c.status)}</td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    tableWrap.querySelectorAll("tr[data-id]").forEach((row) => {
      row.addEventListener("click", () => window.__mmpRouter.navigate(`/clients/${row.getAttribute("data-id")}`));
    });

    if (data.count !== undefined) {
      const pageSize = items.length && data.results ? Math.ceil(data.count / Math.max(1, Math.ceil(data.count / (data.results.length || 1)))) : 25;
      pagination.style.display = "flex";
      const totalPages = Math.max(1, Math.ceil(data.count / 25));
      pagination.innerHTML = `
        <span>${data.count} kayıt · Sayfa ${currentPage}/${totalPages}</span>
        <div class="pager-btns">
          <button class="btn btn-secondary btn-sm" id="prev-page" ${!data.previous ? "disabled" : ""}>← Önceki</button>
          <button class="btn btn-secondary btn-sm" id="next-page" ${!data.next ? "disabled" : ""}>Sonraki →</button>
        </div>
      `;
      const prevBtn = pagination.querySelector("#prev-page");
      const nextBtn = pagination.querySelector("#next-page");
      if (prevBtn) prevBtn.addEventListener("click", () => { currentPage--; loadClients(content); });
      if (nextBtn) nextBtn.addEventListener("click", () => { currentPage++; loadClients(content); });
    } else {
      pagination.style.display = "none";
    }
  } catch (err) {
    toastError(err);
    tableWrap.innerHTML = `<div class="error-banner">Müşteriler yüklenemedi.</div>`;
  }
}

export function openClientForm(client, onSaved) {
  const isEdit = !!client;
  const c = client || {};
  openModal({
    title: isEdit ? "Müşteriyi Düzenle" : "Yeni Müşteri",
    bodyHtml: `
      <form id="client-form">
        <div class="field">
          <label>Ünvan *</label>
          <input type="text" name="title" required value="${escapeHtml(c.title || "")}" />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Tür</label>
            <select name="legal_type">
              ${["sahis", "ltd", "as", "adi_ortaklik", "kooperatif", "dernek_vakif", "serbest_meslek", "diger"]
                .map((v) => `<option value="${v}" ${c.legal_type === v ? "selected" : ""}>${escapeHtml(legalTypeLabel(v))}</option>`)
                .join("")}
            </select>
          </div>
          <div class="field">
            <label>Durum</label>
            <select name="status">
              ${["prospect", "active", "passive", "former"]
                .map((v) => `<option value="${v}" ${(c.status || "active") === v ? "selected" : ""}>${v}</option>`)
                .join("")}
            </select>
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Vergi/TC No</label>
            <input type="text" name="tax_number" value="${escapeHtml(c.tax_number || "")}" />
          </div>
          <div class="field">
            <label>Vergi Dairesi</label>
            <input type="text" name="tax_office" value="${escapeHtml(c.tax_office || "")}" />
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Telefon</label>
            <input type="text" name="phone" value="${escapeHtml(c.phone || "")}" />
          </div>
          <div class="field">
            <label>E-posta</label>
            <input type="email" name="email" value="${escapeHtml(c.email || "")}" />
          </div>
        </div>
        <div class="field">
          <label>Şehir</label>
          <input type="text" name="city" value="${escapeHtml(c.city || "")}" />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Aylık Ücret (₺)</label>
            <input type="number" step="0.01" name="monthly_fee" value="${c.monthly_fee || 0}" />
          </div>
          <div class="field">
            <label>Personel Sayısı</label>
            <input type="number" name="employee_count" value="${c.employee_count || 0}" />
          </div>
        </div>
        <div class="field-row">
          <div class="checkbox-row"><input type="checkbox" name="e_invoice_enabled" id="e-inv" ${c.e_invoice_enabled ? "checked" : ""} /><label for="e-inv" style="margin:0;">e-Fatura Mükellefi</label></div>
          <div class="checkbox-row"><input type="checkbox" name="e_ledger_enabled" id="e-ledg" ${c.e_ledger_enabled ? "checked" : ""} /><label for="e-ledg" style="margin:0;">e-Defter Mükellefi</label></div>
        </div>
        <div class="field">
          <label>Notlar</label>
          <textarea name="notes">${escapeHtml(c.notes || "")}</textarea>
        </div>
      </form>
    `,
    footerHtml: `
      <button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button>
      <button class="btn btn-primary" id="save-btn" type="submit" form="client-form">${isEdit ? "Kaydet" : "Oluştur"}</button>
    `,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      const form = modal.querySelector("#client-form");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const payload = {
          title: fd.get("title"),
          legal_type: fd.get("legal_type"),
          status: fd.get("status"),
          tax_number: fd.get("tax_number"),
          tax_office: fd.get("tax_office"),
          phone: fd.get("phone"),
          email: fd.get("email"),
          city: fd.get("city"),
          monthly_fee: fd.get("monthly_fee") || 0,
          employee_count: fd.get("employee_count") || 0,
          e_invoice_enabled: fd.get("e_invoice_enabled") === "on",
          e_ledger_enabled: fd.get("e_ledger_enabled") === "on",
          notes: fd.get("notes"),
        };
        const saveBtn = modal.querySelector("#save-btn");
        saveBtn.disabled = true;
        try {
          if (isEdit) {
            await api.patch(`/api/v1/clients/${c.id}/`, payload);
            toast("Müşteri güncellendi.", "success");
          } else {
            await api.post("/api/v1/clients/", payload);
            toast("Müşteri oluşturuldu.", "success");
          }
          closeModal();
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
          saveBtn.disabled = false;
        }
      });
    },
  });
}
