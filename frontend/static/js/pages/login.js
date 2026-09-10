// pages/login.js
import { login } from "../api.js";
import { loadMe } from "../state.js";
import { escapeHtml } from "../format.js";

export async function renderLogin(rootEl) {
  rootEl.innerHTML = `
    <div class="auth-shell">
      <div class="auth-card">
        <div class="auth-brand"><span class="logo-badge">MM</span> Mali Müşavir Paneli</div>
        <div class="auth-sub">Ofis hesabınızla giriş yapın.</div>
        <div id="login-error"></div>
        <form id="login-form">
          <div class="field">
            <label for="email">E-posta</label>
            <input type="email" id="email" name="email" required autocomplete="username" placeholder="ornek@ofis.com" />
          </div>
          <div class="field">
            <label for="password">Şifre</label>
            <input type="password" id="password" name="password" required autocomplete="current-password" placeholder="••••••••" />
          </div>
          <div class="auth-inline-link"><a href="/sifremi-unuttum" data-link>Şifremi unuttum</a></div>
          <button type="submit" class="btn btn-primary btn-block" id="login-submit">Giriş Yap</button>
        </form>
        <div class="auth-footer">Henüz hesabınız yok mu? <a href="/register" data-link>Ofisinizi kaydedin</a></div>
      </div>
    </div>
  `;

  const form = rootEl.querySelector("#login-form");
  const errorBox = rootEl.querySelector("#login-error");
  const submitBtn = rootEl.querySelector("#login-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.innerHTML = "";
    submitBtn.disabled = true;
    submitBtn.textContent = "Giriş yapılıyor...";
    try {
      const email = form.email.value.trim();
      const password = form.password.value;
      await login(email, password);
      await loadMe();
      window.__mmpRouter.navigate("/", { replace: true });
    } catch (err) {
      errorBox.innerHTML = `<div class="error-banner">${escapeHtml(err.message || "Giriş başarısız.")}</div>`;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Giriş Yap";
    }
  });
}
