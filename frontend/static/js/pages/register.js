// pages/register.js — yeni ofis (tenant) + sahip kaydı.
import { api, login } from "../api.js";
import { loadMe } from "../state.js";
import { escapeHtml } from "../format.js";

export async function renderRegister(rootEl) {
  rootEl.innerHTML = `
    <div class="auth-shell">
      <div class="auth-card" style="max-width:440px;">
        <div class="auth-brand"><span class="logo-badge">MM</span> Mali Müşavir Paneli</div>
        <div class="auth-sub">Ofisiniz için ücretsiz bir hesap oluşturun.</div>
        <div id="reg-error"></div>
        <form id="reg-form">
          <div class="field">
            <label for="office_name">Ofis Adı</label>
            <input type="text" id="office_name" required placeholder="Örn: Mercimek Mali Müşavirlik" />
          </div>
          <div class="field">
            <label for="tax_number">Vergi No <span class="text-muted">(opsiyonel)</span></label>
            <input type="text" id="tax_number" placeholder="" />
          </div>
          <div class="field-row">
            <div class="field">
              <label for="owner_first_name">Ad</label>
              <input type="text" id="owner_first_name" />
            </div>
            <div class="field">
              <label for="owner_last_name">Soyad</label>
              <input type="text" id="owner_last_name" />
            </div>
          </div>
          <div class="field">
            <label for="owner_email">E-posta</label>
            <input type="email" id="owner_email" required autocomplete="username" />
          </div>
          <div class="field">
            <label for="owner_password">Şifre <span class="text-muted">(en az 8 karakter)</span></label>
            <input type="password" id="owner_password" required minlength="8" autocomplete="new-password" />
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="reg-submit">Hesap Oluştur</button>
        </form>
        <div class="auth-footer">Zaten hesabınız var mı? <a href="/login" data-link>Giriş yapın</a></div>
      </div>
    </div>
  `;

  const form = rootEl.querySelector("#reg-form");
  const errorBox = rootEl.querySelector("#reg-error");
  const submitBtn = rootEl.querySelector("#reg-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.innerHTML = "";
    submitBtn.disabled = true;
    submitBtn.textContent = "Oluşturuluyor...";
    const payload = {
      office_name: rootEl.querySelector("#office_name").value.trim(),
      tax_number: rootEl.querySelector("#tax_number").value.trim(),
      owner_first_name: rootEl.querySelector("#owner_first_name").value.trim(),
      owner_last_name: rootEl.querySelector("#owner_last_name").value.trim(),
      owner_email: rootEl.querySelector("#owner_email").value.trim(),
      owner_password: rootEl.querySelector("#owner_password").value,
    };
    try {
      await api.post("/api/v1/accounts/register-office/", payload);
      await login(payload.owner_email, payload.owner_password);
      await loadMe();
      window.__mmpRouter.navigate("/", { replace: true });
    } catch (err) {
      errorBox.innerHTML = `<div class="error-banner">${escapeHtml(err.message || "Kayıt başarısız.")}</div>`;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Hesap Oluştur";
    }
  });
}
