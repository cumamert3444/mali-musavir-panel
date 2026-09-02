// pages/tasks.js — görev panosu (kanban tarzı, sürüklemesiz).
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, dateTR, statusBadge } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal } from "../modal.js";
import { state } from "../state.js";

const COLUMNS = [
  { key: "todo", label: "Yapılacak" },
  { key: "in_progress", label: "Devam Ediyor" },
  { key: "review", label: "Kontrol Bekliyor" },
  { key: "done", label: "Tamamlandı" },
];

let onlyMine = false;

export async function renderTasks(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Görevler",
    headerActionsHtml: `<button class="btn btn-primary" id="new-task-btn">${icons.plus} Yeni Görev</button>`,
  });

  content.innerHTML = `
    <div class="toolbar">
      <div class="checkbox-row">
        <input type="checkbox" id="only-mine" ${onlyMine ? "checked" : ""} />
        <label for="only-mine" style="margin:0;">Sadece bana atananlar</label>
      </div>
    </div>
    <div class="kanban" id="kanban-wrap" style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;align-items:start;">
      ${COLUMNS.map(
        (col) => `
        <div class="card" data-col="${col.key}">
          <div class="card-header"><h2>${col.label}</h2><span class="badge badge-gray" data-count="${col.key}">0</span></div>
          <div class="card-body" style="padding:10px;display:flex;flex-direction:column;gap:8px;min-height:60px;" data-list="${col.key}"></div>
        </div>`
      ).join("")}
    </div>
  `;

  content.querySelector("#only-mine").addEventListener("change", (e) => {
    onlyMine = e.target.checked;
    loadTasks(content);
  });
  content.querySelector("#new-task-btn").addEventListener("click", () => openTaskForm(null, () => loadTasks(content)));

  const style = document.createElement("style");
  style.textContent = "@media (max-width: 1100px){ #kanban-wrap{ grid-template-columns:1fr 1fr !important; } } @media (max-width: 640px){ #kanban-wrap{ grid-template-columns:1fr !important; } }";
  content.appendChild(style);

  await loadTasks(content);
}

async function loadTasks(content) {
  const wrap = content.querySelector("#kanban-wrap");
  COLUMNS.forEach((col) => {
    wrap.querySelector(`[data-list="${col.key}"]`).innerHTML = `<div class="loading-row" style="padding:16px;">…</div>`;
  });
  try {
    const params = { page_size: 200, ordering: "due_date" };
    if (onlyMine && state.me) params.assigned_to = state.me.id;
    const data = await api.get("/api/v1/tasks/", params);
    const items = data.results || data;

    COLUMNS.forEach((col) => {
      const list = wrap.querySelector(`[data-list="${col.key}"]`);
      const colItems = items.filter((t) => t.status === col.key);
      wrap.querySelector(`[data-count="${col.key}"]`).textContent = colItems.length;
      if (!colItems.length) {
        list.innerHTML = `<div class="text-muted text-sm" style="padding:8px;">Görev yok</div>`;
        return;
      }
      list.innerHTML = colItems
        .map(
          (t) => `
        <div class="card" style="box-shadow:none;border:1px solid var(--border);padding:12px;cursor:pointer;" data-task="${t.id}">
          <div class="flex-between" style="margin-bottom:6px;">
            <strong style="font-size:13px;">${escapeHtml(t.title)}</strong>
            ${statusBadge(t.priority)}
          </div>
          ${t.client_title ? `<div class="text-muted text-sm" style="margin-bottom:4px;">${escapeHtml(t.client_title)}</div>` : ""}
          <div class="text-muted text-sm">${t.due_date ? "Vade: " + dateTR(t.due_date) : "Vade yok"}</div>
          ${t.assigned_to_detail ? `<div class="text-sm" style="margin-top:6px;">👤 ${escapeHtml(t.assigned_to_detail.full_name || t.assigned_to_detail.email)}</div>` : ""}
        </div>`
        )
        .join("");
      list.querySelectorAll("[data-task]").forEach((card) => {
        const task = items.find((t) => String(t.id) === card.getAttribute("data-task"));
        card.addEventListener("click", () => openTaskForm(task, () => loadTasks(content)));
      });
    });
  } catch (err) {
    toastError(err);
  }
}

async function openTaskForm(task, onSaved) {
  const isEdit = !!task;
  let clients = [];
  try {
    const data = await api.get("/api/v1/clients/", { page_size: 200, status: "active", ordering: "title" });
    clients = data.results || data;
  } catch (e) {
    /* müşteri listesi olmadan da devam edilebilir */
  }

  openModal({
    title: isEdit ? "Görevi Düzenle" : "Yeni Görev",
    bodyHtml: `
      <form id="task-form">
        <div class="field"><label>Başlık *</label><input type="text" name="title" required value="${escapeHtml(task?.title || "")}" /></div>
        <div class="field"><label>Açıklama</label><textarea name="description">${escapeHtml(task?.description || "")}</textarea></div>
        <div class="field-row">
          <div class="field">
            <label>Müşteri</label>
            <select name="client">
              <option value="">— Yok —</option>
              ${clients.map((c) => `<option value="${c.id}" ${task?.client === c.id ? "selected" : ""}>${escapeHtml(c.title)}</option>`).join("")}
            </select>
          </div>
          <div class="field"><label>Vade Tarihi</label><input type="date" name="due_date" value="${task?.due_date || ""}" /></div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Durum</label>
            <select name="status">
              ${COLUMNS.map((c) => `<option value="${c.key}" ${(task?.status || "todo") === c.key ? "selected" : ""}>${c.label}</option>`).join("")}
            </select>
          </div>
          <div class="field">
            <label>Öncelik</label>
            <select name="priority">
              ${["low", "normal", "high", "urgent"].map((p) => `<option value="${p}" ${(task?.priority || "normal") === p ? "selected" : ""}>${p}</option>`).join("")}
            </select>
          </div>
        </div>
      </form>
    `,
    footerHtml: `
      <button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button>
      ${isEdit ? '<button class="btn btn-danger" id="delete-btn" type="button">Sil</button>' : ""}
      <button class="btn btn-primary" type="submit" form="task-form">${isEdit ? "Kaydet" : "Oluştur"}</button>
    `,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      const deleteBtn = modal.querySelector("#delete-btn");
      if (deleteBtn) {
        deleteBtn.addEventListener("click", async () => {
          try {
            await api.del(`/api/v1/tasks/${task.id}/`);
            closeModal();
            toast("Görev silindi.", "success");
            if (onSaved) onSaved();
          } catch (err) {
            toastError(err);
          }
        });
      }
      modal.querySelector("#task-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          title: fd.get("title"),
          description: fd.get("description"),
          client: fd.get("client") || null,
          due_date: fd.get("due_date") || null,
          status: fd.get("status"),
          priority: fd.get("priority"),
        };
        try {
          if (isEdit) await api.patch(`/api/v1/tasks/${task.id}/`, payload);
          else await api.post("/api/v1/tasks/", payload);
          closeModal();
          toast(isEdit ? "Görev güncellendi." : "Görev oluşturuldu.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}
