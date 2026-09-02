// pages/misc.js — Teşekkürler ve Sistem Durumu (herkese açık, küçük sayfalar).
import { escapeHtml } from "../format.js";

export async function renderThankYou(rootEl) {
  rootEl.innerHTML = `
    <div class="landing">
      <div class="auth-shell" style="min-height:100vh;">
        <div class="auth-card" style="max-width:480px;text-align:center;">
          <div class="logo-badge" style="margin:0 auto 18px;width:56px;height:56px;font-size:20px;">MM</div>
          <h1 style="margin:0 0 12px;">Teşekkürler!</h1>
          <p class="text-muted">Talebiniz alındı. Ekibimiz en kısa sürede sizinle iletişime geçecek.</p>
          <a href="/" data-link class="btn btn-primary" style="margin-top:16px;">Ana Sayfaya Dön</a>
        </div>
      </div>
    </div>
  `;
}

export async function renderStatus(rootEl) {
  rootEl.innerHTML = `
    <div class="landing">
      <header class="landing-header">
        <div class="landing-header-inner">
          <a href="/" data-link class="landing-brand"><span class="logo-badge">MM</span> Müşavir Asistanı</a>
          <div class="landing-header-actions">
            <a href="/" data-link class="btn btn-ghost-invert">← Ana Sayfa</a>
          </div>
        </div>
      </header>
      <div class="legal-page" style="max-width:640px;">
        <h1>Sistem Durumu</h1>
        <div id="status-body"><div class="loading-row">Kontrol ediliyor...</div></div>
      </div>
    </div>
  `;

  const body = rootEl.querySelector("#status-body");
  try {
    const res = await fetch(`${window.__API_BASE__ || ""}/api/v1/status/`);
    const data = await res.json();
    const ok = data.status === "operational";
    body.innerHTML = `
      <div class="card" style="padding:20px;">
        <div class="flex" style="align-items:center;gap:10px;margin-bottom:16px;">
          <span style="width:12px;height:12px;border-radius:50%;background:${ok ? "var(--success)" : "var(--danger)"};display:inline-block;"></span>
          <strong style="font-size:16px;">${ok ? "Tüm servisler çalışıyor" : "Bazı servislerde sorun var"}</strong>
        </div>
        <table class="data-table">
          <thead><tr><th>Servis</th><th>Durum</th><th>Detay</th></tr></thead>
          <tbody>
            ${Object.entries(data.checks || {})
              .map(
                ([name, check]) => `<tr>
                  <td>${escapeHtml(name === "database" ? "Veritabanı" : name === "api" ? "API" : name)}</td>
                  <td>${check.status === "ok" ? '<span class="badge badge-green">Çalışıyor</span>' : '<span class="badge badge-red">Hata</span>'}</td>
                  <td class="text-sm text-muted">${check.response_time_ms != null ? `${check.response_time_ms} ms` : escapeHtml(check.detail || "")}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>
        <p class="text-sm text-muted" style="margin-top:14px;">Son kontrol: ${new Date(data.checked_at).toLocaleString("tr-TR")}</p>
      </div>
    `;
  } catch (err) {
    body.innerHTML = `<div class="error-banner">Durum bilgisi alınamadı — API'ye şu anda ulaşılamıyor olabilir.</div>`;
  }
}
