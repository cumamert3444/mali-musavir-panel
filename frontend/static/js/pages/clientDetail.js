// pages/clientDetail.js — müşteri detay ekranı (sekmeli).
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR, statusBadge, legalTypeLabel } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";
import { openClientForm } from "./clients.js";

let activeTab = "overview";

export async function renderClientDetail(rootEl, params) {
  const clientId = params.id;
  const content = renderShell(rootEl, { pageTitle: "Müşteri Detayı" });
  content.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;

  let client;
  try {
    client = await api.get(`/api/v1/clients/${clientId}/`);
  } catch (err) {
    toastError(err);
    content.innerHTML = `<div class="error-banner">Müşteri bulunamadı.</div>`;
    return;
  }

  activeTab = "overview";
  paint();

  function paint() {
    content.innerHTML = `
      <a href="/clients" data-link class="back-link">${icons.back} Müşterilere Dön</a>
      <div class="detail-header">
        <div>
          <h1>${escapeHtml(client.title)}</h1>
          <div class="meta">${escapeHtml(legalTypeLabel(client.legal_type))} ${client.tax_number ? "· VKN/TCKN: " + escapeHtml(client.tax_number) : ""} ${client.tax_office ? "· " + escapeHtml(client.tax_office) : ""}</div>
        </div>
        <div class="flex gap-8">
          ${statusBadge(client.status)}
          <button class="btn btn-secondary btn-sm" id="edit-client-btn">Düzenle</button>
        </div>
      </div>

      <div class="tabs">
        ${tabBtn("overview", "Genel Bilgiler")}
        ${tabBtn("contacts", "İlgili Kişiler")}
        ${tabBtn("contracts", "Sözleşmeler")}
        ${tabBtn("declarations", "Beyanname Abonelikleri")}
        ${tabBtn("statement", "Cari Hesap Ekstresi")}
      </div>

      <div id="tab-content"><div class="loading-row">Yükleniyor...</div></div>
    `;

    content.querySelector("#edit-client-btn").addEventListener("click", () =>
      openClientForm(client, async () => {
        client = await api.get(`/api/v1/clients/${clientId}/`);
        paint();
      })
    );
    content.querySelectorAll("[data-tab]").forEach((btn) =>
      btn.addEventListener("click", () => {
        activeTab = btn.getAttribute("data-tab");
        paint();
      })
    );

    const tabEl = content.querySelector("#tab-content");
    if (activeTab === "overview") renderOverview(tabEl, client);
    else if (activeTab === "contacts") renderContacts(tabEl, client);
    else if (activeTab === "contracts") renderContracts(tabEl, client);
    else if (activeTab === "declarations") renderDeclarations(tabEl, client);
    else if (activeTab === "statement") renderStatement(tabEl, client);
  }

  function tabBtn(key, label) {
    return `<button data-tab="${key}" class="${activeTab === key ? "active" : ""}" type="button">${label}</button>`;
  }
}

function renderOverview(el, client) {
  el.innerHTML = `
    <div class="two-col">
      <div class="card">
        <div class="card-header"><h2>Firma Bilgileri</h2></div>
        <div class="card-body">
          <div class="kv-list">
            <div class="kv-item"><div class="k">Ünvan</div><div class="v">${escapeHtml(client.title)}</div></div>
            <div class="kv-item"><div class="k">Tür</div><div class="v">${escapeHtml(legalTypeLabel(client.legal_type))}</div></div>
            <div class="kv-item"><div class="k">Vergi No</div><div class="v">${escapeHtml(client.tax_number || "—")}</div></div>
            <div class="kv-item"><div class="k">Vergi Dairesi</div><div class="v">${escapeHtml(client.tax_office || "—")}</div></div>
            <div class="kv-item"><div class="k">Mersis No</div><div class="v">${escapeHtml(client.mersis_no || "—")}</div></div>
            <div class="kv-item"><div class="k">Ticaret Sicil No</div><div class="v">${escapeHtml(client.trade_registry_no || "—")}</div></div>
            <div class="kv-item"><div class="k">Telefon</div><div class="v">${escapeHtml(client.phone || "—")}</div></div>
            <div class="kv-item"><div class="k">E-posta</div><div class="v">${escapeHtml(client.email || "—")}</div></div>
            <div class="kv-item"><div class="k">Şehir</div><div class="v">${escapeHtml(client.city || "—")}</div></div>
            <div class="kv-item"><div class="k">Adres</div><div class="v">${escapeHtml(client.address || "—")}</div></div>
          </div>
          ${client.notes ? `<div class="section-title">Notlar</div><p class="text-sm">${escapeHtml(client.notes)}</p>` : ""}
        </div>
      </div>
      <div class="card">
        <div class="card-header"><h2>Hizmet Bilgileri</h2></div>
        <div class="card-body">
          <div class="kv-list">
            <div class="kv-item"><div class="k">Paket</div><div class="v">${escapeHtml(client.package_name || "—")}</div></div>
            <div class="kv-item"><div class="k">Aylık Ücret</div><div class="v">${money(client.monthly_fee)}</div></div>
            <div class="kv-item"><div class="k">Personel Sayısı</div><div class="v">${client.employee_count ?? 0}</div></div>
            <div class="kv-item"><div class="k">Muhasebe Programı</div><div class="v">${escapeHtml(client.accounting_software || "—")}</div></div>
            <div class="kv-item"><div class="k">e-Fatura</div><div class="v">${client.e_invoice_enabled ? "Mükellef" : "—"}</div></div>
            <div class="kv-item"><div class="k">e-Defter</div><div class="v">${client.e_ledger_enabled ? "Mükellef" : "—"}</div></div>
            <div class="kv-item"><div class="k">Başlangıç</div><div class="v">${dateTR(client.start_date)}</div></div>
          </div>
          ${
            (client.groups || []).length
              ? `<div class="section-title">Gruplar</div><div class="flex gap-8" style="flex-wrap:wrap;">${client.groups
                  .map((g) => `<span class="badge badge-blue">${escapeHtml(g.name)}</span>`)
                  .join("")}</div>`
              : ""
          }
        </div>
      </div>
    </div>
  `;
}

function renderContacts(el, client) {
  const contacts = client.contacts || [];
  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>İlgili Kişiler</h2>
        <button class="btn btn-primary btn-sm" id="add-contact-btn">${icons.plus} Ekle</button>
      </div>
      <div class="table-wrap">
        ${
          contacts.length
            ? `<table class="data-table">
                <thead><tr><th>Ad Soyad</th><th>Görev</th><th>Telefon</th><th>E-posta</th><th></th></tr></thead>
                <tbody>
                  ${contacts
                    .map(
                      (c) => `<tr>
                        <td>${escapeHtml(c.full_name)} ${c.is_primary ? '<span class="badge badge-blue">Birincil</span>' : ""}</td>
                        <td>${escapeHtml(c.role || "—")}</td>
                        <td>${escapeHtml(c.phone || "—")}</td>
                        <td>${escapeHtml(c.email || "—")}</td>
                        <td><button class="btn btn-ghost btn-sm" data-del="${c.id}">Sil</button></td>
                      </tr>`
                    )
                    .join("")}
                </tbody>
              </table>`
            : `<div class="empty-state"><h3>Henüz ilgili kişi eklenmemiş</h3></div>`
        }
      </div>
    </div>
  `;

  el.querySelector("#add-contact-btn").addEventListener("click", () => {
    openModal({
      title: "Yeni İlgili Kişi",
      bodyHtml: `
        <form id="contact-form">
          <div class="field"><label>Ad Soyad *</label><input type="text" name="full_name" required /></div>
          <div class="field"><label>Görev</label><input type="text" name="role" placeholder="Genel Müdür, Muhasebe Sorumlusu..." /></div>
          <div class="field-row">
            <div class="field"><label>Telefon</label><input type="text" name="phone" /></div>
            <div class="field"><label>E-posta</label><input type="email" name="email" /></div>
          </div>
          <div class="checkbox-row"><input type="checkbox" id="is-primary" name="is_primary" /><label for="is-primary" style="margin:0;">Birincil yetkili</label></div>
        </form>
      `,
      footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="contact-form">Ekle</button>`,
      onMount: (modal) => {
        modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
        modal.querySelector("#contact-form").addEventListener("submit", async (e) => {
          e.preventDefault();
          const fd = new FormData(e.target);
          try {
            await api.post(`/api/v1/clients/${client.id}/contacts/`, {
              full_name: fd.get("full_name"),
              role: fd.get("role"),
              phone: fd.get("phone"),
              email: fd.get("email"),
              is_primary: fd.get("is_primary") === "on",
            });
            const fresh = await api.get(`/api/v1/clients/${client.id}/`);
            Object.assign(client, fresh);
            closeModal();
            toast("İlgili kişi eklendi.", "success");
            renderContacts(el, client);
          } catch (err) {
            toastError(err);
          }
        });
      },
    });
  });

  el.querySelectorAll("[data-del]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      if (!(await confirmDialog("Bu ilgili kişiyi silmek istediğinize emin misiniz?"))) return;
      try {
        await api.del(`/api/v1/clients/${client.id}/contacts/${btn.getAttribute("data-del")}/`);
        client.contacts = client.contacts.filter((c) => String(c.id) !== btn.getAttribute("data-del"));
        toast("Silindi.", "success");
        renderContacts(el, client);
      } catch (err) {
        toastError(err);
      }
    })
  );
}

function renderContracts(el, client) {
  const contracts = client.contracts || [];
  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>Sözleşmeler</h2>
        <button class="btn btn-primary btn-sm" id="add-contract-btn">${icons.plus} Ekle</button>
      </div>
      <div class="table-wrap">
        ${
          contracts.length
            ? `<table class="data-table">
                <thead><tr><th>Başlık</th><th>Başlangıç</th><th>Bitiş</th><th>Aylık Ücret</th><th>Durum</th></tr></thead>
                <tbody>
                  ${contracts
                    .map(
                      (c) => `<tr>
                        <td>${escapeHtml(c.title)}</td>
                        <td>${dateTR(c.start_date)}</td>
                        <td>${dateTR(c.end_date)}</td>
                        <td>${money(c.monthly_fee)}</td>
                        <td><span class="badge badge-gray">${escapeHtml(c.status)}</span></td>
                      </tr>`
                    )
                    .join("")}
                </tbody>
              </table>`
            : `<div class="empty-state"><h3>Henüz sözleşme eklenmemiş</h3></div>`
        }
      </div>
    </div>
  `;

  el.querySelector("#add-contract-btn").addEventListener("click", () => {
    openModal({
      title: "Yeni Sözleşme",
      bodyHtml: `
        <form id="contract-form">
          <div class="field"><label>Başlık</label><input type="text" name="title" value="Hizmet Sözleşmesi" /></div>
          <div class="field-row">
            <div class="field"><label>Başlangıç *</label><input type="date" name="start_date" required /></div>
            <div class="field"><label>Bitiş</label><input type="date" name="end_date" /></div>
          </div>
          <div class="field"><label>Aylık Ücret (₺)</label><input type="number" step="0.01" name="monthly_fee" value="${client.monthly_fee || 0}" /></div>
          <div class="field"><label>Kapsam</label><textarea name="scope_description"></textarea></div>
        </form>
      `,
      footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="contract-form">Ekle</button>`,
      onMount: (modal) => {
        modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
        modal.querySelector("#contract-form").addEventListener("submit", async (e) => {
          e.preventDefault();
          const fd = new FormData(e.target);
          try {
            await api.post(`/api/v1/clients/${client.id}/contracts/`, {
              title: fd.get("title"),
              start_date: fd.get("start_date"),
              end_date: fd.get("end_date") || null,
              monthly_fee: fd.get("monthly_fee") || 0,
              scope_description: fd.get("scope_description"),
            });
            const fresh = await api.get(`/api/v1/clients/${client.id}/`);
            Object.assign(client, fresh);
            closeModal();
            toast("Sözleşme eklendi.", "success");
            renderContracts(el, client);
          } catch (err) {
            toastError(err);
          }
        });
      },
    });
  });
}

async function renderDeclarations(el, client) {
  el.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const [subs, types] = await Promise.all([
      api.get(`/api/v1/clients/${client.id}/declaration-subscriptions/`),
      api.get("/api/v1/declaration-types/", { page_size: 100 }),
    ]);
    const subsList = subs.results || subs;
    const typesList = types.results || types;
    el.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h2>Beyanname Abonelikleri</h2>
          <button class="btn btn-primary btn-sm" id="add-sub-btn">${icons.plus} Tür Ekle</button>
        </div>
        <div class="table-wrap">
          ${
            subsList.length
              ? `<table class="data-table">
                  <thead><tr><th>Beyanname Türü</th><th>Periyot</th><th>Aktif mi</th></tr></thead>
                  <tbody>
                    ${subsList
                      .map(
                        (s) => `<tr>
                          <td>${escapeHtml(s.declaration_type_detail.name)}</td>
                          <td>${escapeHtml(s.declaration_type_detail.period)}</td>
                          <td>${s.is_active ? '<span class="badge badge-green">Aktif</span>' : '<span class="badge badge-gray">Pasif</span>'}</td>
                        </tr>`
                      )
                      .join("")}
                  </tbody>
                </table>`
              : `<div class="empty-state"><h3>Bu müşteri henüz bir beyanname türüne abone değil</h3><p>Aktif olduğu vergi/bildirim türlerini ekleyin ki takvim otomatik oluşsun.</p></div>`
          }
        </div>
      </div>
    `;

    el.querySelector("#add-sub-btn").addEventListener("click", () => {
      const available = typesList.filter((t) => !subsList.some((s) => s.declaration_type === t.id));
      if (!available.length) {
        toast("Eklenebilecek başka beyanname türü yok.", "default");
        return;
      }
      openModal({
        title: "Beyanname Türü Ekle",
        bodyHtml: `
          <form id="sub-form">
            <div class="field">
              <label>Beyanname Türü *</label>
              <select name="declaration_type" required>
                ${available.map((t) => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join("")}
              </select>
            </div>
          </form>
        `,
        footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="sub-form">Ekle</button>`,
        onMount: (modal) => {
          modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
          modal.querySelector("#sub-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await api.post(`/api/v1/clients/${client.id}/declaration-subscriptions/`, {
                declaration_type: fd.get("declaration_type"),
              });
              closeModal();
              toast("Beyanname türü eklendi; ilk dönemler otomatik oluşturuldu.", "success");
              renderDeclarations(el, client);
            } catch (err) {
              toastError(err);
            }
          });
        },
      });
    });
  } catch (err) {
    toastError(err);
    el.innerHTML = `<div class="error-banner">Yüklenemedi.</div>`;
  }
}

async function renderStatement(el, client) {
  el.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get(`/api/v1/clients/${client.id}/account-statement/`);
    el.innerHTML = `
      <div class="stat-grid" style="margin-bottom:16px;">
        <div class="stat-card accent-primary"><div class="stat-label">Toplam Faturalanan</div><div class="stat-value" style="font-size:19px;">${money(data.summary.total_invoiced)}</div></div>
        <div class="stat-card accent-success"><div class="stat-label">Toplam Tahsil Edilen</div><div class="stat-value" style="font-size:19px;">${money(data.summary.total_paid)}</div></div>
        <div class="stat-card ${data.summary.balance_due > 0 ? "accent-danger" : "accent-success"}"><div class="stat-label">Bakiye</div><div class="stat-value" style="font-size:19px;">${money(data.summary.balance_due)}</div></div>
      </div>
      <div class="card">
        <div class="card-header"><h2>Hareketler</h2></div>
        <div class="table-wrap">
          ${
            data.entries.length
              ? `<table class="data-table">
                  <thead><tr><th>Tarih</th><th>Tür</th><th>Referans</th><th>Açıklama</th><th>Borç</th><th>Alacak</th><th>Bakiye</th></tr></thead>
                  <tbody>
                    ${data.entries
                      .map(
                        (e) => `<tr>
                          <td>${dateTR(e.date)}</td>
                          <td>${e.type === "invoice" ? '<span class="badge badge-blue">Fatura</span>' : '<span class="badge badge-green">Tahsilat</span>'}</td>
                          <td>${escapeHtml(e.reference)}</td>
                          <td>${escapeHtml(e.description)}</td>
                          <td>${e.debit ? money(e.debit) : "—"}</td>
                          <td>${e.credit ? money(e.credit) : "—"}</td>
                          <td><strong>${money(e.balance)}</strong></td>
                        </tr>`
                      )
                      .join("")}
                  </tbody>
                </table>`
              : `<div class="empty-state"><h3>Henüz hareket yok</h3></div>`
          }
        </div>
      </div>
    `;
  } catch (err) {
    toastError(err);
    el.innerHTML = `<div class="error-banner">Ekstre yüklenemedi.</div>`;
  }
}
