// pages/team.js — ofis ekibi (üyeler) yönetimi.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, dateTR } from "../format.js";
import { toast, toastError } from "../toast.js";
import { icons } from "../icons.js";
import { openModal, closeModal, confirmDialog } from "../modal.js";
import { roleLabel, isOwner } from "../state.js";

export async function renderTeam(rootEl) {
  const content = renderShell(rootEl, {
    pageTitle: "Ekip",
    headerActionsHtml: isOwner() ? `<button class="btn btn-primary" id="invite-btn">${icons.plus} Üye Davet Et</button>` : "",
  });

  content.innerHTML = `<div class="card"><div class="table-wrap" id="team-table-wrap"><div class="loading-row">Yükleniyor...</div></div></div>`;

  const inviteBtn = content.querySelector("#invite-btn");
  if (inviteBtn) inviteBtn.addEventListener("click", () => openInviteForm(() => loadMembers(content)));

  await loadMembers(content);
}

async function loadMembers(content) {
  const wrap = content.querySelector("#team-table-wrap");
  wrap.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;
  try {
    const data = await api.get("/api/v1/accounts/members/", { page_size: 100 });
    const items = data.results || data;
    if (!items.length) {
      wrap.innerHTML = `<div class="empty-state"><h3>Ekip üyesi bulunamadı</h3></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Ad Soyad</th><th>E-posta</th><th>Rol</th><th>Durum</th><th>Katılım</th>${isOwner() ? "<th></th>" : ""}</tr></thead>
        <tbody>
          ${items
            .map(
              (m) => `<tr>
                <td>${escapeHtml(m.user.full_name || "—")}</td>
                <td>${escapeHtml(m.user.email)}</td>
                <td><span class="badge badge-blue">${escapeHtml(roleLabel(m.role))}</span></td>
                <td>${m.is_active ? '<span class="badge badge-green">Aktif</span>' : '<span class="badge badge-gray">Pasif</span>'}</td>
                <td>${dateTR(m.created_at)}</td>
                ${isOwner() ? `<td>${m.is_active ? `<button class="btn btn-ghost btn-sm" data-deactivate="${m.id}">Pasife Al</button>` : ""}</td>` : ""}
              </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    wrap.querySelectorAll("[data-deactivate]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!(await confirmDialog("Bu ekip üyesini pasife almak istediğinize emin misiniz?"))) return;
        try {
          await api.post(`/api/v1/accounts/members/${btn.getAttribute("data-deactivate")}/deactivate/`, {});
          toast("Üye pasife alındı.", "success");
          loadMembers(content);
        } catch (err) {
          toastError(err);
        }
      })
    );
  } catch (err) {
    toastError(err);
    wrap.innerHTML = `<div class="error-banner">Ekip listesi yüklenemedi.</div>`;
  }
}

function openInviteForm(onSaved) {
  openModal({
    title: "Ekip Üyesi Davet Et",
    bodyHtml: `
      <form id="invite-form">
        <div class="field"><label>E-posta *</label><input type="email" name="email" required /></div>
        <div class="field-row">
          <div class="field"><label>Ad</label><input type="text" name="first_name" /></div>
          <div class="field"><label>Soyad</label><input type="text" name="last_name" /></div>
        </div>
        <div class="field">
          <label>Rol</label>
          <select name="role">
            <option value="accountant">Mali Müşavir</option>
            <option value="bookkeeper" selected>Muhasebeci</option>
            <option value="intern">Stajyer / Yardımcı Personel</option>
            <option value="owner">Ofis Sahibi</option>
          </select>
        </div>
        <p class="text-sm text-muted" style="margin-top:8px;">Kullanıcı sistemde yoksa otomatik oluşturulur; giriş bilgisi için ayrıca bilgilendirmeniz gerekir.</p>
      </form>
    `,
    footerHtml: `<button class="btn btn-secondary" id="cancel-btn" type="button">Vazgeç</button><button class="btn btn-primary" type="submit" form="invite-form">Davet Et</button>`,
    onMount: (modal) => {
      modal.querySelector("#cancel-btn").addEventListener("click", closeModal);
      modal.querySelector("#invite-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await api.post("/api/v1/accounts/members/", {
            email: fd.get("email"),
            first_name: fd.get("first_name"),
            last_name: fd.get("last_name"),
            role: fd.get("role"),
          });
          closeModal();
          toast("Üye eklendi.", "success");
          if (onSaved) onSaved();
        } catch (err) {
          toastError(err);
        }
      });
    },
  });
}
