// pages/documents.js — evrak (belge) yönetimi.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";

let currentClient = "";
let currentCategory = "";
let currentSearch = "";
let clientsCache = [];
let categoriesCache = [];

export async function renderDocuments(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Evraklar",
    headerActionsHtml: `<button class="btn btn-primary" id="upload-doc-btn">${icons.plus} Evrak Yükle</button>`,
  });

  content.innerHTML = `
    <div class="card">
      <div class="card-body" style="padding-bottom:0;">
        <div class="toolbar">
          <input type="text" id="doc-search" class="search-input" placeholder="Başlık veya açıklamada ara..." />
          <select id="doc-client-filter"><option value="">Tüm Müşteriler</option></select>
          <select id="doc-category-filter"><option value="">Tüm Kategoriler</option></select>
        </div>
      </div>
      <div class="table-wrap" id="doc-table-wrap"><div class="loading-row">Yükleniyor...</div></div>
    </div>
  `;

  try {
    const [clientsData, categoriesData] = await Promise.all([
      api.get("/api/v1/clients/", { page_size: 200, ordering: "title" }),
      api.get("/api/v1/document-categories/", { page_size: 200 }),
    ]);
    clientsCache = clientsData.results || clientsData;
    categoriesCache = categoriesData.results || categoriesData;
    const clientSelect = content.querySelector("#doc-client-filter");
    clientSelect.insertAdjacentHTML(
      "beforeend",
      clientsCache.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("")
    );
    const catSelect = content.querySelector("#doc-category-filter");
    catSelect.insertAdjacentHTML(
      "beforeend",
      categoriesCache.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("")
    );
  } catch (err) {
    toastError(err);
  }

  content.querySelector("#doc-client-filter").addEventListener("change", (e) => {
    currentClient = e.target.value;
    loadDocuments(content);
  });
  content.querySelector("#doc-category-filter").addEventListener("change", (e) => {
    currentCategory = e.target.value;
    loadDocuments(content);
  });
  let searchTimer;
  content.querySelector("#doc-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      currentSearch = e.target.value;
      loadDocuments(content);
    }, 350);
  });

  content.querySelector("#upload-doc-btn").addEventListener("click", () => openUploadForm(() => loadDocuments(content)));

  await loadDocuments(content);
}

async function loadDocuments(content) {
  const wrap = content.querySelector("#doc-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/documents/", {
      client: currentClient || undefined,
      category: currentCategory || undefined,
      search: currentSearch || undefined,
      page_size: 100,
    });
    const items = data.results || data;
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><h3>Evrak bulunamadı</h3><p>Yeni bir evrak yükleyin.</p></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Başlık</th><th>Müşteri</th><th>Kategori</th><th>Yükleyen</th><th>Tarih</th><th></th></tr></thead>
        <tbody>
          ${items
            .map((d) => {
              const client = clientsCache.find((c) => c.id === d.client);
              return `<tr>
                <td><a href="${escapeHtml(d.file)}" target="_blank" rel="noopener">${escapeHtml(d.title)}</a></td>
                <td>${client ? escapeHtml(client.title) : '<span class="text-muted">Ofis geneli</span>'}</td>
                <td>${escapeHtml(d.category_name || "—")}</td>
                <td>${escapeHtml(d.uploaded_by_email || "—")}</td>
                <td>${dateTR(d.created_at)}</td>
                <td><button class="btn btn-ghost btn-sm" data-del="${d.id}">Sil</button></td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;
    wrap.querySelectorAll("[data-del]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu evrakı silmek istediğinize emin misiniz?"))) return;
        try {
          await api.del(`/api/v1/documents/${btn.getAttribute("data-del")}/`);
          toast("Evrak silindi.", "success");
          loadDocuments(content);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Evraklar yüklenemedi.</div>`;
  }
}

function openUploadForm(onSaved) {
  openModal({
    title: "Evrak Yükle",
    bodyHtml: `
      <form id="doc-form">
        <div class="field"><label>Başlık *</label><input type="text" name="title" required /></div>
        <div class="field-row">
          <div class="field">
            <label>Müşteri</label>
            <select name="client">
              <option value="">— Ofis Geneli —</option>
              ${clientsCache.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label>Kategori</label>
            <select name="category" id="doc-category-select">
              <option value="">— Yok —</option>
              ${categoriesCache.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("")}
              <option value="__new__">+ Yeni kategori...</option>
            </select>
          </div>
        </div>
        <div class="field"><label>Dosya *</label><input type="file" name="file" required /></div>
        <div class="field"><label>Açıklama</label><textarea name="description"></textarea></div>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="doc-form">Yükle</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      const catSelect = modal.querySelector("#doc-category-select");
      catSelect.addEventListener("change", async () => {
        if (catSelect.value !== "__new__") return;
        const name = window.prompt("Yeni kategori adı:");
        catSelect.value = "";
        if (!name || !name.trim()) return;
        try {
          const created = await api.post("/api/v1/document-categories/", { name: name.trim() });
          categoriesCache.push(created);
          catSelect.insertAdjacentHTML("beforeend", `<option value="${created.id}">${escapeHtml(created.name)}</option>`);
          catSelect.value = created.id;
        } catch (err) {
          toastError(err);
        }
      });

      modal.querySelector("#doc-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = e.target;
        const fileInput = form.querySelector('input[name="file"]');
        if (!fileInput.files.length) {
          toast("Lütfen bir dosya seçin.", "error");
          return;
        }
        const fd = new FormData();
        fd.append("title", form.title.value);
        if (form.client.value) fd.append("client", form.client.value);
        if (form.category.value && form.category.value !== "__new__") fd.append("category", form.category.value);
        fd.append("description", form.description.value);
        fd.append("file", fileInput.files[0]);
        try {
          await api.postForm("/api/v1/documents/", fd);
          closeModal();
          toast("Evrak yüklendi.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}
