// pages/invoiceDetail.js
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR, statusBadge } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

export async function renderInvoiceDetail(rootEl, params) {
  const invoiceId = params.id;
  const content = renderShell(rootEl, { pageTitle: "Fatura Detayı" });
  content.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;

  let invoice;
  try {
    invoice = await api.get(`/api/v1/invoices/${invoiceId}/`);
  } catch (err) {
    toastError(err);
    content.innerHTML = `<div class="error-banner">Fatura bulunamadı.</div>`;
    return;
  }

  paint();

  function paint() {
    content.innerHTML = `
      <a href="/invoices" data-link class="back-link">${icons.back} Faturalara Dön</a>
      <div class="detail-header">
        <div>
          <h1>${escapeHtml(invoice.invoice_number)}</h1>
          <div class="meta">${escapeHtml(invoice.client_title)} ${invoice.period_label ? "· " + escapeHtml(invoice.period_label) : ""}</div>
        </div>
        <div class="flex gap-8" style="align-items:center;">
          ${statusBadge(invoice.status)}
          <select id="status-select" class="btn-sm" style="padding:6px 10px;border-radius:8px;border:1px solid var(--border);">
            ${["draft", "sent", "partially_paid", "paid", "overdue", "canceled"]
              .map((s) => `<option value="${s}" ${invoice.status === s ? "selected" : ""}>${s}</option>`)
              .join("")}
          </select>
          <button class="btn btn-danger btn-sm" id="delete-invoice-btn">Sil</button>
        </div>
      </div>

      <div class="two-col">
        <div class="card">
          <div class="card-header"><h2>Kalemler</h2></div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Açıklama</th><th>Miktar</th><th>Birim Fiyat</th><th>Tutar</th></tr></thead>
              <tbody>
                ${(invoice.lines || [])
                  .map(
                    (l) => `<tr>
                      <td>${escapeHtml(l.description)}</td>
                      <td>${l.quantity}</td>
                      <td>${money(l.unit_price)}</td>
                      <td>${money(l.amount)}</td>
                    </tr>`
                  )
                  .join("")}
              </tbody>
              <tfoot>
                <tr><td colspan="3">Toplam</td><td>${money(invoice.total_amount)}</td></tr>
                <tr><td colspan="3">Tahsil Edilen</td><td>${money(invoice.paid_amount)}</td></tr>
                <tr><td colspan="3">Kalan</td><td style="color:${Number(invoice.balance_due) > 0 ? "var(--danger)" : "var(--success)"}">${money(invoice.balance_due)}</td></tr>
              </tfoot>
            </table>
          </div>
          <div class="card-body" style="border-top:1px solid var(--border);">
            <div class="kv-list">
              <div class="kv-item"><div class="k">Kesim Tarihi</div><div class="v">${dateTR(invoice.issue_date)}</div></div>
              <div class="kv-item"><div class="k">Vade Tarihi</div><div class="v">${dateTR(invoice.due_date)}</div></div>
            </div>
            ${invoice.notes ? `<div class="section-title">Notlar</div><p class="text-sm">${escapeHtml(invoice.notes)}</p>` : ""}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2>Tahsilatlar</h2>
            <button class="btn btn-primary btn-sm" id="add-payment-btn">${icons.plus} Ödeme Ekle</button>
          </div>
          <div class="table-wrap">
            ${
              (invoice.payments || []).length
                ? `<table class="data-table">
                    <thead><tr><th>Tarih</th><th>Tutar</th><th>Yöntem</th></tr></thead>
                    <tbody>
                      ${invoice.payments
                        .map(
                          (p) => `<tr>
                            <td>${dateTR(p.paid_at)}</td>
                            <td>${money(p.amount)}</td>
                            <td>${escapeHtml(p.method)}</td>
                          </tr>`
                        )
                        .join("")}
                    </tbody>
                  </table>`
                : `<div class="empty-state"><h3>Henüz tahsilat yok</h3></div>`
            }
          </div>
        </div>
      </div>
    `;

    content.querySelector("#status-select").addEventListener("change", async (e) => {
      try {
        await api.patch(`/api/v1/invoices/${invoiceId}/`, { status: e.target.value });
        toast("Durum güncellendi.", "success");
        invoice = await api.get(`/api/v1/invoices/${invoiceId}/`);
        paint();
      } catch (err) {
        toastError(err);
      }
    });

    content.querySelector("#delete-invoice-btn").addEventListener("click", async () => {
      if (!(await confirmDialog(`"${invoice.invoice_number}" numaralı faturayı silmek istediğinize emin misiniz?`))) return;
      try {
        await api.del(`/api/v1/invoices/${invoiceId}/`);
        toast("Fatura silindi.", "success");
        window.__mmpRouter.navigate("/invoices");
      } catch (err) {
        toastError(err);
      }
    });

    content.querySelector("#add-payment-btn").addEventListener("click", () => {
      const today = new Date().toISOString().slice(0, 10);
      openModal({
        title: "Ödeme Ekle",
        bodyHtml: `
          <form id="payment-form">
            <div class="field"><label>Tutar (₺) *</label><input type="number" step="0.01" name="amount" required value="${invoice.balance_due}" /></div>
            <div class="field-row">
              <div class="field"><label>Tarih *</label><input type="date" name="paid_at" required value="${today}" /></div>
              <div class="field">
                <label>Yöntem</label>
                <select name="method">
                  <option value="bank_transfer">Havale/EFT</option>
                  <option value="cash">Nakit</option>
                  <option value="credit_card">Kredi Kartı</option>
                  <option value="other">Diğer</option>
                </select>
              </div>
            </div>
            <div class="field"><label>Referans</label><input type="text" name="reference" /></div>
          </form>
        `,
        footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="payment-form">Kaydet</button>`,
        onMount: (modal) => {
          modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
          modal.querySelector("#payment-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await api.post(`/api/v1/invoices/${invoiceId}/payments/`, {
                amount: fd.get("amount"),
                paid_at: fd.get("paid_at"),
                method: fd.get("method"),
                reference: fd.get("reference"),
              });
              closeModal();
              toast("Ödeme kaydedildi.", "success");
              invoice = await api.get(`/api/v1/invoices/${invoiceId}/`);
              paint();
            } catch (err) {
              toastError(err);
            }
          });
        },
      });
    });
  }
}
