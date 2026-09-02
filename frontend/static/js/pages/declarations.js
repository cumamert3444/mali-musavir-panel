// pages/declarations.js — beyanname takvimi.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, dateTR, daysUntil, statusBadge } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";

let currentStatus = "";
let currentSearch = "";
let currentPage = 1;

export async function renderDeclarations(rootEl) {
  const content = renderShell(rootEl, { pageTitle: "Beyannameler" });

  currentPage = 1;
  content.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="decl-search" class="search-input" placeholder="Müşteri veya dönem ara..." />
          <select id="decl-status-filter">
            <option value="">Tüm Durumlar</option>
            <option value="pending">Bekliyor</option>
            <option value="in_progress">Hazırlanıyor</option>
            <option value="submitted">Beyan Edildi</option>
            <option value="paid">Ödendi/Kapandı</option>
            <option value="overdue">Gecikti</option>
            <option value="not_applicable">Geçersiz</option>
          </select>
        </div>
      </div>
      <div class="table-wrap" id="decl-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
      <div class="pagination" id="decl-pagination" style="display:none;"></div>
    </div>
  `;

  content.querySelector("#decl-status-filter").addEventListener("change", (e) => {
    currentStatus = e.target.value;
    currentPage = 1;
    loadDeclarations(content);
  });
  let searchTimer;
  content.querySelector("#decl-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      currentSearch = e.target.value;
      currentPage = 1;
      loadDeclarations(content);
    }, 350);
  });

  await loadDeclarations(content);
}

async function loadDeclarations(content) {
  const tableWrap = content.querySelector("#decl-table-wrap");
  const pagination = content.querySelector("#decl-pagination");
  tableWrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/declaration-instances/", {
      status: currentStatus || undefined,
      search: currentSearch || undefined,
      page: currentPage,
      ordering: "due_date",
    });
    const items = data.results || data;
    if (!items.length) {
      tableWrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.declaration}</div><h3>Kayıt bulunamadı</h3><p>Müşteri detayından beyanname türü aboneliği ekleyerek takvim oluşturabilirsiniz.</p></div>`;
      pagination.style.display = "none";
      return;
    }
    tableWrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Müşteri</th><th>Beyanname</th><th>Dönem</th><th>Vade</th><th>Durum</th><th></th></tr></thead>
        <tbody>
          ${items
            .map((d) => {
              const days = daysUntil(d.due_date);
              const overdue = d.is_overdue;
              return `<tr ${overdue ? 'style="background:var(--danger-light);"' : ""}>
                <td><a href="/clients/${d.client}" data-link>${escapeHtml(d.client_title)}</a></td>
                <td>${escapeHtml(d.declaration_type_name)}</td>
                <td>${escapeHtml(d.period_label)}</td>
                <td>${dateTR(d.due_date)} ${days !== null ? `<span class="text-muted text-sm">(${days < 0 ? Math.abs(days) + " gün gecikti" : days + " gün kaldı"})</span>` : ""}</td>
                <td>${statusBadge(d.status)}</td>
                <td>
                  <select data-status-select="${d.id}" class="btn-sm" style="padding:5px 8px;border-radius:6px;border:1px solid var(--border);">
                    ${["pending", "in_progress", "submitted", "paid", "overdue", "not_applicable"]
                      .map((s) => `<option value="${s}" ${d.status === s ? "selected" : ""}>${s}</option>`)
                      .join("")}
                  </select>
                </td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;

    tableWrap.querySelectorAll("[data-status-select]").forEach((sel) => {
      sel.addEventListener("change", async () => {
        const id = sel.getAttribute("data-status-select");
        try {
          await api.patch(`/api/v1/declaration-instances/${id}/`, { status: sel.value });
          toast("Durum güncellendi.", "success");
          loadDeclarations(content);
        } catch (err) {
          toastError(err);
        }
      });
    });

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
      if (p) p.addEventListener("click", () => { currentPage--; loadDeclarations(content); });
      if (n) n.addEventListener("click", () => { currentPage++; loadDeclarations(content); });
    } else {
      pagination.style.display = "none";
    }
  } catch (err) {
    toastError(err);
    tableWrap.innerHTML = `<div class="error-banner">Beyannameler yüklenemedi.</div>`;
  }
}
