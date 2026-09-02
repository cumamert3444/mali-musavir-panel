// pages/declarations.js — beyanname takvimi + risk motoru (çapraz eşleştirme).
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, dateTR, daysUntil, statusBadge, money } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal } from "../modal.js";

let currentStatus = "";
let currentSearch = "";
let currentPage = 1;

export async function renderDeclarations(rootEl) {
  const content = renderShell(rootEl, { pageTitle: "Beyannameler" });

  currentPage = 1;
  content.innerHTML = `
    <div class="card" id="risk-panel">
      <div class="card-header">
        <h2>${icons.alert} Risk Uyarıları — Çapraz Eşleştirme Motoru</h2>
        <button class="btn btn-ghost btn-sm" id="risk-toggle" type="button">Göster/Gizle</button>
      </div>
      <div class="card-body" id="risk-body" style="display:none;">
        <div class="loading-row">Yükleniyor...</div>
      </div>
    </div>

    <div class="card" style="margin-top:16px;">
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

  let riskLoaded = false;
  content.querySelector("#risk-toggle").addEventListener("click", async () => {
    const body = content.querySelector("#risk-body");
    const visible = body.style.display !== "none";
    body.style.display = visible ? "none" : "block";
    if (!visible && !riskLoaded) {
      riskLoaded = true;
      await loadRiskReport(content);
    }
  });

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

function openAmountModal(instance, onSaved) {
  openModal({
    title: `${instance.declaration_type_name} — ${instance.period_label}`,
    bodyHtml: `
      <form id="amount-form">
        <p class="text-sm text-muted" style="margin-top:0;">
          Bu beyannamede fiilen beyan edilen tutarları girin. Bu bilgi, risk motorunun
          (Muhtasar–SGK karşılaştırması ve matrah dalgalanması) çalışabilmesi için gereklidir.
        </p>
        <div class="field"><label>Beyan Edilen Matrah/Tutar (₺)</label><input type="number" step="0.01" name="declared_amount" value="${instance.declared_amount ?? ""}" /></div>
        <div class="field"><label>Hesaplanan/Ödenecek Vergi Tutarı (₺)</label><input type="number" step="0.01" name="declared_tax_amount" value="${instance.declared_tax_amount ?? ""}" /></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="amount-form">Kaydet</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#amount-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await api.patch(`/api/v1/declaration-instances/${instance.id}/`, {
            declared_amount: fd.get("declared_amount") || null,
            declared_tax_amount: fd.get("declared_tax_amount") || null,
          });
          closeModal();
          toast("Tutar kaydedildi.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}

const RISK_LABELS = {
  muhtasar_sgk_mismatch: "Muhtasar–SGK Uyumsuzluğu",
  matrah_volatility: "Matrah Dalgalanması",
  missing_declared_amount: "Tutar Girilmemiş",
};

async function loadRiskReport(content) {
  const body = content.querySelector("#risk-body");
  body.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const report = await api.get("/api/v1/declaration-instances/risk-report/");
    if (!report.total_flags) {
      body.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.declaration}</div><h3>Risk tespit edilmedi</h3><p>Şu anda beyan edilen tutarlar arasında bir tutarsızlık bulunmuyor.</p></div>`;
      return;
    }
    body.innerHTML = `
      <p class="text-sm text-muted" style="margin-top:0;">
        ${report.risky_client_count} müşteride toplam ${report.total_flags} uyarı bulundu. Bu motor, beyanname
        onaylanırken girilen <strong>"Beyan Edilen Tutar"</strong> alanını bordro kayıtları ve önceki dönemlerle
        karşılaştırır (gerçek zamanlı GİB/SGK sorgulaması değildir).
      </p>
      <table class="data-table">
        <thead><tr><th>Müşteri</th><th>Dönem</th><th>Uyarı Türü</th><th>Önem</th><th>Açıklama</th></tr></thead>
        <tbody>
          ${report.flags
            .map(
              (f) => `<tr>
                <td><a href="/clients/${f.client_id}" data-link>${escapeHtml(f.client_title)}</a></td>
                <td>${escapeHtml(f.period_label)}</td>
                <td>${escapeHtml(RISK_LABELS[f.risk_type] || f.risk_type)}</td>
                <td><span class="badge badge-${f.severity === "high" ? "red" : "amber"}">${f.severity === "high" ? "Yüksek" : "Orta"}</span></td>
                <td class="text-sm">${escapeHtml(f.message)}</td>
              </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    toastError(err);
    body.innerHTML = `<div class="error-banner">Risk raporu yüklenemedi.</div>`;
  }
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
        <thead><tr><th>Müşteri</th><th>Beyanname</th><th>Dönem</th><th>Vade</th><th>Beyan Edilen Tutar</th><th>Durum</th><th></th></tr></thead>
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
                <td>
                  <button class="btn btn-ghost btn-sm" data-amount-btn="${d.id}">
                    ${d.declared_amount != null ? money(d.declared_amount) : "Tutar Gir"}
                  </button>
                </td>
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

    tableWrap.querySelectorAll("[data-amount-btn]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-amount-btn");
        const item = items.find((d) => String(d.id) === id);
        openAmountModal(item, () => loadDeclarations(content));
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
