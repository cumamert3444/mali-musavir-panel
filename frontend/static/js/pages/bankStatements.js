// pages/bankStatements.js — Banka Ekstresi İşleme (dürüst kapsam: Excel/CSV/PDF
// dosyasını okuyup işlem satırlarına ayrıştırır; gerçek zamanlı bir bankacılık
// API'sine (açık bankacılık/PSD2) bağlanmaz ve gerçek bir muhasebe fişi kesmez —
// bkz. apps.bank_statements.models modül docstring'i).
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

let clientsCache = [];
let currentClient = "";
let currentStatus = "";

const SOURCE_FORMAT_LABELS = { excel: "Excel (.xlsx)", csv: "CSV", pdf: "PDF" };
const IMPORT_STATUS_LABELS = {
  pending: ["İşleniyor", "gray"],
  parsed: ["Ayrıştırıldı", "green"],
  partial: ["Kısmen Ayrıştırıldı", "amber"],
  failed: ["Başarısız", "red"],
};
const TX_STATUS_LABELS = {
  draft: ["Taslak", "gray"],
  matched: ["Hesap Kodu Atandı", "amber"],
  confirmed: ["Onaylandı", "green"],
};
const DIRECTION_LABELS = { credit: "Giren", debit: "Çıkan" };

export async function renderBankStatements(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Banka Ekstresi İşleme",
    headerActionsHtml: `<button class="btn btn-primary" id="new-import-btn">${icons.document} Ekstre Yükle</button>`,
  });

  content.innerHTML = `
    <div class="card" style="margin-bottom:16px;">
      <div class="card-body">
        <p class="text-sm text-muted" style="margin:0;">
          Bankadan indirdiğiniz ekstre dosyasını (Excel, CSV veya PDF) buraya yükleyin;
          sistem işlem satırlarını otomatik olarak ayrıştırmaya çalışır. Bu, bankanıza
          gerçek zamanlı bağlanan bir "açık bankacılık" entegrasyonu DEĞİLDİR ve
          otomatik bir muhasebe fişi kesmez — her satır önce <strong>taslak</strong>
          olarak gelir, siz karşı hesap kodunu atayıp gözden geçirdikten sonra
          "Muhasebe Fişi Olarak Dışa Aktar" ile kendi muhasebe programınıza
          aktarabileceğiniz bir CSV üretebilirsiniz. PDF ayrıştırma, banka ekstresi
          düzenlerinin çok farklı olması nedeniyle "en iyi çaba" esasına dayanır;
          sonuçları mutlaka kontrol edin.
        </p>
      </div>
    </div>

    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <select id="stmt-client-filter"><option value="">Tüm Müşteriler</option></select>
          <select id="stmt-status-filter">
            <option value="">Tüm Durumlar</option>
            ${Object.entries(IMPORT_STATUS_LABELS).map(([v, [l]]) => `<option value="${v}">${l}</option>`).join("")}
          </select>
        </div>
      </div>
      <div class="table-wrap" id="stmt-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;

  try {
    const clientsData = await api.get("/api/v1/clients/", { page_size: 200, ordering: "title" });
    clientsCache = clientsData.results || clientsData;
    const sel = content.querySelector("#stmt-client-filter");
    sel.innerHTML += clientsCache.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("");
  } catch (e) {
    /* müşteri filtresi olmadan da devam edilebilir */
  }

  content.querySelector("#stmt-client-filter").addEventListener("change", (e) => {
    currentClient = e.target.value;
    loadImports(content);
  });
  content.querySelector("#stmt-status-filter").addEventListener("change", (e) => {
    currentStatus = e.target.value;
    loadImports(content);
  });
  content.querySelector("#new-import-btn").addEventListener("click", () => openImportModal(() => loadImports(content)));

  await loadImports(content);
}

async function loadImports(content) {
  const wrap = content.querySelector("#stmt-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/bank-statements/", {
      client: currentClient || undefined,
      status: currentStatus || undefined,
      page_size: 100,
      ordering: "-created_at",
    });
    const items = data.results || data;
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">${icons.bank}</div><h3>Henüz ekstre yüklenmedi</h3><p>Bir banka ekstresi (Excel/CSV/PDF) yükleyerek başlayın.</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Müşteri</th><th>Banka</th><th>Dönem</th><th>Format</th><th>Satır</th><th>Durum</th><th></th></tr></thead>
        <tbody>
          ${items
            .map((r) => {
              const [label, color] = IMPORT_STATUS_LABELS[r.status] || [r.status, "gray"];
              return `<tr>
                <td><a href="/clients/${r.client}" data-link>${escapeHtml(r.client_title)}</a></td>
                <td>${escapeHtml(r.bank_name || "—")}</td>
                <td>${escapeHtml(r.period_label || "—")}</td>
                <td>${escapeHtml(SOURCE_FORMAT_LABELS[r.source_format] || r.source_format)}</td>
                <td>${r.parsed_count}/${r.row_count}</td>
                <td><span class="badge badge-${color}">${escapeHtml(label)}</span></td>
                <td>
                  <button class="btn btn-ghost btn-sm" data-review="${r.id}">İncele</button>
                  <button class="btn btn-ghost btn-sm" data-delete="${r.id}">Sil</button>
                </td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;
    const itemsById = Object.fromEntries(items.map((r) => [String(r.id), r]));
    wrap.querySelectorAll("[data-review]").forEach((btn) =>
      btn.addEventListener("click", () => openReviewModal(itemsById[btn.getAttribute("data-review")].id, () => loadImports(content)))
    );
    wrap.querySelectorAll("[data-delete]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu ekstre içe aktarımını ve tüm işlem satırlarını silmek istediğinize emin misiniz?"))) return;
        try {
          await api.del(`/api/v1/bank-statements/${btn.getAttribute("data-delete")}/`);
          toast("Ekstre silindi.", "success");
          loadImports(content);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Ekstre listesi yüklenemedi.</div>`;
  }
}

function openImportModal(onSaved) {
  openModal({
    title: "Banka Ekstresi Yükle",
    bodyHtml: `
      <form id="stmt-import-form">
        <div class="field">
          <label>Müşteri *</label>
          <select name="client" required>
            <option value="">Seçin...</option>
            ${clientsCache.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("")}
          </select>
        </div>
        <div class="field-row">
          <div class="field"><label>Banka</label><input type="text" name="bank_name" placeholder="Örn. Ziraat Bankası" /></div>
          <div class="field"><label>Banka Hesap Kodu</label><input type="text" name="bank_account_code" placeholder="Örn. 102.01" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Hesap Açıklaması</label><input type="text" name="account_label" placeholder="Örn. TL Vadesiz Hesap" /></div>
          <div class="field"><label>Dönem</label><input type="text" name="period_label" placeholder="2026-08" /></div>
        </div>
        <div class="field">
          <label>Dosya Türü *</label>
          <select name="source_format" id="stmt-format-select" required>
            <option value="excel">Excel (.xlsx)</option>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
          </select>
        </div>
        <div class="field">
          <label>Ekstre Dosyası *</label>
          <input type="file" name="file" id="stmt-file-input" accept=".xlsx,.csv,.pdf" required />
        </div>
      </form>
      <div id="stmt-import-result"></div>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="stmt-import-form">Yükle ve Ayrıştır</button>`,
    onMount: (modal) => {
      const formatSelect = modal.querySelector("#stmt-format-select");
      const fileInput = modal.querySelector("#stmt-file-input");
      const extToFormat = { xlsx: "excel", xls: "excel", csv: "csv", pdf: "pdf" };
      fileInput.addEventListener("change", () => {
        const name = fileInput.files[0]?.name || "";
        const ext = name.split(".").pop().toLowerCase();
        if (extToFormat[ext]) formatSelect.value = extToFormat[ext];
      });
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#stmt-import-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = e.target;
        const file = fileInput.files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append("client", form.client.value);
        fd.append("bank_name", form.bank_name.value);
        fd.append("bank_account_code", form.bank_account_code.value);
        fd.append("account_label", form.account_label.value);
        fd.append("period_label", form.period_label.value);
        fd.append("source_format", form.source_format.value);
        fd.append("file", file);
        const submitBtn = modal.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = "Yükleniyor...";
        try {
          const result = await api.postForm("/api/v1/bank-statements/", fd);
          const [label] = IMPORT_STATUS_LABELS[result.status] || [result.status];
          modal.querySelector("#stmt-import-result").innerHTML = `
            <div class="${result.status === "failed" ? "error-banner" : ""}" style="margin-top:12px;">
              Ayrıştırma sonucu: <strong>${escapeHtml(label)}</strong> —
              ${result.parsed_count}/${result.row_count} satır ayrıştırıldı.
              ${result.error_message ? `<pre style="white-space:pre-wrap;font-size:12px;margin-top:8px;">${escapeHtml(result.error_message)}</pre>` : ""}
            </div>`;
          toast("Ekstre yüklendi ve ayrıştırıldı.", "success");
          if (onSaved) onSaved();
          submitBtn.textContent = "Kapat";
          submitBtn.disabled = false;
          submitBtn.setAttribute("type", "button");
          submitBtn.addEventListener("click", () => {
            closeModal();
            openReviewModal(result.id, onSaved);
          });
        } catch (err) {
          toastError(err);
          submitBtn.disabled = false;
          submitBtn.textContent = "Yükle ve Ayrıştır";
        }
      });
    },
  });
}

async function openReviewModal(statementId, onSaved) {
  let statement;
  try {
    statement = await api.get(`/api/v1/bank-statements/${statementId}/`);
  } catch (err) {
    toastError(err);
    return;
  }

  const renderRows = (transactions) => `
    <table class="data-table" style="margin-top:12px;">
      <thead><tr><th>Tarih</th><th>Açıklama</th><th>Yön</th><th>Tutar</th><th>Karşı Hesap Kodu</th><th>Durum</th></tr></thead>
      <tbody>
        ${transactions
          .map((tx) => {
            const [label, color] = TX_STATUS_LABELS[tx.status] || [tx.status, "gray"];
            return `<tr data-tx-row="${tx.id}">
              <td>${tx.transaction_date ? dateTR(tx.transaction_date) : "—"}</td>
              <td>${escapeHtml(tx.description || "—")}</td>
              <td>${DIRECTION_LABELS[tx.direction] || tx.direction}</td>
              <td>${money(tx.amount)}</td>
              <td>
                <input type="text" class="tx-account-code" data-tx-id="${tx.id}" value="${escapeHtml(tx.account_code || "")}" placeholder="Örn. 770" style="width:90px;" />
                ${tx.suggested_by_ai ? `<span class="badge badge-gray" style="margin-left:4px;" title="Bu kod, ofisinizin daha önce onayladığı benzer işlemlerden öğrenilerek otomatik önerildi. Doğruysa aynen bırakıp onaylayın, yanlışsa değiştirin.">🤖 önerildi</span>` : ""}
              </td>
              <td><span class="badge badge-${color}" data-tx-status="${tx.id}">${escapeHtml(label)}</span></td>
            </tr>`;
          })
          .join("")}
      </tbody>
    </table>
  `;

  openModal({
    title: `${statement.client_title} — Ekstre İnceleme`,
    bodyHtml: `
      <p class="text-sm text-muted" style="margin-top:0;">
        ${statement.bank_name ? escapeHtml(statement.bank_name) + " · " : ""}${escapeHtml(statement.period_label || "")}
        — Her satıra bir karşı hesap kodu yazıp alandan çıkın (otomatik kaydedilir).
        Gözden geçirmeyi bitirdikten sonra "Muhasebe Fişi Olarak Dışa Aktar" ile CSV indirebilirsiniz.
      </p>
      <div id="stmt-review-rows">${renderRows(statement.transactions || [])}</div>
    `,
    footerHtml: `
      <button class="btn btn-secondary" id="reparse-btn" type="button">Yeniden Ayrıştır</button>
      <button class="btn btn-secondary" id="export-btn" type="button">${icons.document} Muhasebe Fişi Olarak Dışa Aktar</button>
      <button class="btn btn-primary" id="close-btn" type="button">Kapat</button>
    `,
    onMount: (modal) => {
      modal.querySelector("#close-btn").addEventListener("click", () => {
        closeModal();
        if (onSaved) onSaved();
      });

      modal.querySelectorAll(".tx-account-code").forEach((input) => {
        input.addEventListener("change", async () => {
          const txId = input.getAttribute("data-tx-id");
          try {
            const updated = await api.patch(`/api/v1/bank-transactions/${txId}/`, {
              account_code: input.value,
              status: input.value.trim() ? "matched" : "draft",
            });
            const badge = modal.querySelector(`[data-tx-status="${txId}"]`);
            const [label, color] = TX_STATUS_LABELS[updated.status] || [updated.status, "gray"];
            badge.className = `badge badge-${color}`;
            badge.textContent = label;
          } catch (err) {
            toastError(err);
          }
        });
      });

      modal.querySelector("#reparse-btn").addEventListener("click", async () => {
        if (!(await confirmDialog("Dosya yeniden ayrıştırılsın mı? Elle eklediğiniz satırlar korunur, dosyadan gelen satırlar yeniden oluşturulur (hesap kodu atamaları sıfırlanır)."))) return;
        try {
          const updated = await api.post(`/api/v1/bank-statements/${statementId}/reparse/`, {});
          modal.querySelector("#stmt-review-rows").innerHTML = renderRows(updated.transactions || []);
          rebindRowHandlers(modal, statementId, onSaved);
          toast("Ekstre yeniden ayrıştırıldı.", "success");
        } catch (err) {
          toastError(err);
        }
      });

      modal.querySelector("#export-btn").addEventListener("click", async () => {
        try {
          const csvText = await api.get(`/api/v1/bank-statements/${statementId}/export-journal/`);
          const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `muhasebe-fisi-${statement.client_title.replace(/\s+/g, "_")}-${statement.period_label || statement.id}.csv`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}

function rebindRowHandlers(modal, statementId, onSaved) {
  modal.querySelectorAll(".tx-account-code").forEach((input) => {
    input.addEventListener("change", async () => {
      const txId = input.getAttribute("data-tx-id");
      try {
        const updated = await api.patch(`/api/v1/bank-transactions/${txId}/`, {
          account_code: input.value,
          status: input.value.trim() ? "matched" : "draft",
        });
        const badge = modal.querySelector(`[data-tx-status="${txId}"]`);
        const [label, color] = TX_STATUS_LABELS[updated.status] || [updated.status, "gray"];
        badge.className = `badge badge-${color}`;
        badge.textContent = label;
      } catch (err) {
        toastError(err);
      }
    });
  });
}
