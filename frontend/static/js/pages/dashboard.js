// pages/dashboard.js — ofis genel bakış panosu.
import { api } from "../api.js";
import { renderShell } from "../layout.js";
import { escapeHtml, money, dateTR, daysUntil, statusBadge } from "../format.js";
import { toastError } from "../toast.js";
import { icons } from "../icons.js";

export async function renderDashboard(rootEl) {
  const content = renderShell(rootEl, { pageTitle: "Panel" });
  content.innerHTML = `<div class="loading-row">Yükleniyor...</div>`;

  try {
    const [upcomingDecl, myTasks, clientsPage, invoicesPage] = await Promise.all([
      api.get("/api/v1/declaration-instances/upcoming/", { days: 14, page_size: 8 }),
      api.get("/api/v1/tasks/my_tasks/", { page_size: 50 }),
      api.get("/api/v1/clients/", { status: "active", page_size: 1 }),
      api.get("/api/v1/invoices/", { page_size: 50, ordering: "due_date" }),
    ]);

    const declResults = upcomingDecl.results || upcomingDecl;
    const overdueCount = (declResults || []).filter((d) => d.is_overdue).length;

    const tasksList = (myTasks.results || myTasks).filter((t) => t.status !== "done");
    const invoicesList = (invoicesPage.results || invoicesPage).filter((i) =>
      ["sent", "partially_paid", "overdue"].includes(i.status)
    );
    const totalDue = invoicesList.reduce((sum, inv) => sum + Number(inv.balance_due || 0), 0);
    const overdueInvoices = invoicesList
      .filter((i) => i.status === "overdue" || (i.due_date && daysUntil(i.due_date) < 0))
      .sort((a, b) => (a.due_date > b.due_date ? 1 : -1));

    content.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card accent-primary">
          <div class="stat-label">Aktif Müşteri</div>
          <div class="stat-value">${clientsPage.count ?? "—"}</div>
          <div class="stat-sub"><a href="/clients" data-link>Tüm müşterileri gör →</a></div>
        </div>
        <div class="stat-card ${overdueCount ? "accent-danger" : "accent-warning"}">
          <div class="stat-label">Yaklaşan / Geciken Beyanname</div>
          <div class="stat-value">${(declResults || []).length}</div>
          <div class="stat-sub">${overdueCount ? `${overdueCount} tanesi gecikti` : "önümüzdeki 14 gün"}</div>
        </div>
        <div class="stat-card accent-warning">
          <div class="stat-label">Açık Görevlerim</div>
          <div class="stat-value">${tasksList.length}</div>
          <div class="stat-sub"><a href="/tasks" data-link>Görev listesi →</a></div>
        </div>
        <div class="stat-card ${overdueInvoices.length ? "accent-danger" : "accent-success"}">
          <div class="stat-label">Tahsil Edilmemiş Tutar</div>
          <div class="stat-value" style="font-size:20px;">${money(totalDue)}</div>
          <div class="stat-sub">${overdueInvoices.length} gecikmiş fatura</div>
        </div>
      </div>

      <div class="two-col">
        <div class="card">
          <div class="card-header">
            <h2>Yaklaşan Beyannameler</h2>
            <a href="/declarations" data-link class="text-sm">Tümünü gör →</a>
          </div>
          <div class="table-wrap">
            ${renderDeclTable(declResults || [])}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2>Görevlerim</h2>
            <a href="/tasks" data-link class="text-sm">Tümünü gör →</a>
          </div>
          <div class="table-wrap">
            ${renderTaskList(tasksList.slice(0, 8))}
          </div>
        </div>
      </div>

      <div class="card" style="margin-top:18px;">
        <div class="card-header">
          <h2>Gecikmiş Tahsilatlar</h2>
          <a href="/invoices" data-link class="text-sm">Tüm faturalar →</a>
        </div>
        <div class="table-wrap">
          ${renderOverdueInvoices(overdueInvoices.slice(0, 8))}
        </div>
      </div>
    `;

    content.querySelectorAll("[data-goto]").forEach((el) => {
      el.addEventListener("click", () => window.__mmpRouter.navigate(el.getAttribute("data-goto")));
    });
  } catch (err) {
    toastError(err);
    content.innerHTML = `<div class="error-banner">Panel verileri yüklenemedi: ${escapeHtml(err.message)}</div>`;
  }
}

function renderDeclTable(items) {
  if (!items.length) {
    return `<div class="empty-state"><div class="empty-icon">${icons.declaration}</div><h3>Yaklaşan beyanname yok</h3><p>Önümüzdeki 14 gün içinde vadesi gelen kayıt bulunmuyor.</p></div>`;
  }
  return `
    <table class="data-table">
      <thead><tr><th>Müşteri</th><th>Beyanname</th><th>Dönem</th><th>Vade</th><th>Durum</th></tr></thead>
      <tbody>
        ${items
          .map((d) => {
            const days = daysUntil(d.due_date);
            const dayLabel = days < 0 ? `${Math.abs(days)} gün gecikti` : days === 0 ? "bugün" : `${days} gün kaldı`;
            return `<tr class="clickable" data-goto="/clients/${d.client}">
              <td>${escapeHtml(d.client_title)}</td>
              <td>${escapeHtml(d.declaration_type_name)}</td>
              <td>${escapeHtml(d.period_label)}</td>
              <td>${dateTR(d.due_date)} <span class="text-muted text-sm">(${dayLabel})</span></td>
              <td>${statusBadge(d.is_overdue ? "overdue" : d.status)}</td>
            </tr>`;
          })
          .join("")}
      </tbody>
    </table>
  `;
}

function renderTaskList(items) {
  if (!items.length) {
    return `<div class="empty-state"><div class="empty-icon">${icons.task}</div><h3>Açık göreviniz yok</h3><p>Size atanmış bekleyen bir görev bulunmuyor.</p></div>`;
  }
  return `
    <table class="data-table">
      <thead><tr><th>Görev</th><th>Müşteri</th><th>Vade</th><th>Öncelik</th></tr></thead>
      <tbody>
        ${items
          .map(
            (t) => `<tr class="clickable" data-goto="/tasks">
              <td>${escapeHtml(t.title)}</td>
              <td>${escapeHtml(t.client_title || "—")}</td>
              <td>${dateTR(t.due_date)}</td>
              <td>${statusBadge(t.priority)}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderOverdueInvoices(items) {
  if (!items.length) {
    return `<div class="empty-state"><div class="empty-icon">${icons.invoice}</div><h3>Gecikmiş tahsilat yok</h3><p>Tüm faturalar zamanında ya da vadesinde.</p></div>`;
  }
  return `
    <table class="data-table">
      <thead><tr><th>Fatura No</th><th>Müşteri</th><th>Vade</th><th>Kalan Tutar</th><th>Durum</th></tr></thead>
      <tbody>
        ${items
          .map(
            (i) => `<tr class="clickable" data-goto="/invoices/${i.id}">
              <td>${escapeHtml(i.invoice_number)}</td>
              <td>${escapeHtml(i.client_title)}</td>
              <td>${dateTR(i.due_date)}</td>
              <td>${money(i.balance_due)}</td>
              <td>${statusBadge(i.status)}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}
