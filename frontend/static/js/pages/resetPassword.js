// pages/resetPassword.js — "Şifremi unuttum" akışının 2. adımı: e-postadaki
// linkten gelen uid+token ile yeni şifre belirleme.
import { api } from "../api.js";
import { escapeHtml } from "../format.js";

export async function renderResetPassword(rootEl) {
  document.title = "Yeni Şifre Belirle — Müşavir Asistanı";
  const params = new URLSearchParams(window.location.search);
  const uid = params.get("uid") || "";
  const token = params.get("token") || "";

  if (!uid || !token) {
    rootEl.innerHTML = `
      <div class="auth-shell">
        <div class="auth-card">
          <div class="auth-brand"><span class="logo-badge">MM</span> Mali Müşavir Paneli</div>
          <div class="error-banner">Bağlantı eksik veya geçersiz görünüyor. Şifre sıfırlama işlemini yeniden başlatın.</div>
          <div class="auth-footer"><a href="/sifremi-unuttum" data-link>Şifremi unuttum sayfasına dön</a></div>
        </div>
      </div>
    `;
    return;
  }

  rootEl.innerHTML = `
    <div class="auth-shell">
      <div class="auth-card">
        <div class="auth-brand"><span class="logo-badge">MM</span> Mali Müşavir Paneli</div>
        <div class="auth-sub">Hesabınız için yeni bir şifre belirleyin.</div>
        <div id="reset-msg"></div>
        <form id="reset-form">
          <div class="field">
            <label for="new_password">Yeni Şifre</label>
            <input type="password" id="new_password" name="new_password" required minlength="8" autocomplete="new-password" placeholder="En az 8 karakter" />
          </div>
          <div class="field">
            <label for="new_password_confirm">Yeni Şifre (Tekrar)</label>
            <input type="password" id="new_password_confirm" name="new_password_confirm" required minlength="8" autocomplete="new-password" placeholder="••••••••" />
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="reset-submit">Şifreyi Güncelle</button>
        </form>
        <div class="auth-footer"><a href="/login" data-link>Girişe dön</a></div>
      </div>
    </div>
  `;

  const form = rootEl.querySelector("#reset-form");
  const msgBox = rootEl.querySelector("#reset-msg");
  const submitBtn = rootEl.querySelector("#reset-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgBox.innerHTML = "";
    const newPassword = form.new_password.value;
    const confirmPassword = form.new_password_confirm.value;
    if (newPassword !== confirmPassword) {
      msgBox.innerHTML = `<div class="error-banner">Girdiğiniz şifreler birbiriyle eşleşmiyor.</div>`;
      return;
    }
    submitBtn.disabled = true;
    submitBtn.textContent = "Güncelleniyor...";
    try {
      const res = await api.post("/api/v1/accounts/password-reset-confirm/", {
        uid,
        token,
        new_password: newPassword,
      });
      msgBox.innerHTML = `<div class="success-banner">${escapeHtml(
        res?.detail || "Şifreniz güncellendi."
      )} <a href="/login" data-link>Giriş yap</a></div>`;
      form.reset();
      form.querySelectorAll("input, button").forEach((el) => (el.disabled = true));
    } catch (err) {
      msgBox.innerHTML = `<div class="error-banner">${escapeHtml(err.message || "Şifre güncellenemedi, lütfen tekrar deneyin.")}</div>`;
      submitBtn.disabled = false;
      submitBtn.textContent = "Şifreyi Güncelle";
    }
  });
}
