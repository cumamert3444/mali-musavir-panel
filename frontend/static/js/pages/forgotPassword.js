// pages/forgotPassword.js — "Şifremi unuttum" akışının 1. adımı: e-posta iste.
import { api } from "../api.js";
import { escapeHtml } from "../format.js";

export async function renderForgotPassword(rootEl) {
  document.title = "Şifremi Unuttum — Müşavir Asistanı";
  rootEl.innerHTML = `
    <div class="auth-shell">
      <div class="auth-card">
        <div class="auth-brand"><span class="logo-badge">MM</span> Mali Müşavir Paneli</div>
        <div class="auth-sub">Hesabınızın e-posta adresini girin, şifre sıfırlama bağlantısını gönderelim.</div>
        <div id="forgot-msg"></div>
        <form id="forgot-form">
          <div class="field">
            <label for="email">E-posta</label>
            <input type="email" id="email" name="email" required autocomplete="username" placeholder="ornek@ofis.com" />
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="forgot-submit">Sıfırlama Bağlantısı Gönder</button>
        </form>
        <div class="auth-footer"><a href="/login" data-link>Girişe dön</a></div>
      </div>
    </div>
  `;

  const form = rootEl.querySelector("#forgot-form");
  const msgBox = rootEl.querySelector("#forgot-msg");
  const submitBtn = rootEl.querySelector("#forgot-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgBox.innerHTML = "";
    submitBtn.disabled = true;
    submitBtn.textContent = "Gönderiliyor...";
    try {
      const email = form.email.value.trim();
      const res = await api.post("/api/v1/accounts/password-reset/", { email });
      msgBox.innerHTML = `<div class="success-banner">${escapeHtml(
        res?.detail || "Bu e-posta adresi sistemde kayıtlıysa, şifre sıfırlama bağlantısı gönderildi."
      )}</div>`;
      form.reset();
    } catch (err) {
      msgBox.innerHTML = `<div class="error-banner">${escapeHtml(err.message || "İstek başarısız oldu, lütfen tekrar deneyin.")}</div>`;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Sıfırlama Bağlantısı Gönder";
    }
  });
}
