// contactWidgets.js — WhatsApp kabarcık butonu + mobil hızlı iletişim çubuğu.
// Sadece window.__WHATSAPP_NUMBER__ (Django ayarından, boşsa gizli) yapılandırılmışsa görünür.
import { icons } from "./icons.js";

const WIDGET_ID = "mmp-contact-widgets";

export function mountContactWidgets() {
  // SPA sayfa değişiminde tekrar tekrar eklenmesin diye önce temizle.
  const existing = document.getElementById(WIDGET_ID);
  if (existing) existing.remove();

  const number = (window.__WHATSAPP_NUMBER__ || "").replace(/[^0-9]/g, "");
  if (!number) return; // yapılandırılmamışsa sessizce hiçbir şey göstermiyoruz (sahte/kırık buton yok)

  const wrap = document.createElement("div");
  wrap.id = WIDGET_ID;

  const fab = document.createElement("a");
  fab.href = `https://wa.me/${number}`;
  fab.target = "_blank";
  fab.rel = "noopener";
  fab.className = "floating-whatsapp";
  fab.setAttribute("aria-label", "WhatsApp ile iletişime geçin");
  fab.innerHTML = icons.chat;
  wrap.appendChild(fab);

  const mobileBar = document.createElement("div");
  mobileBar.className = "mobile-contact-bar";
  mobileBar.innerHTML = `
    <a href="https://wa.me/${number}" target="_blank" rel="noopener">${icons.chat} WhatsApp</a>
    <a href="tel:+${number}">${icons.bell} Ara</a>
  `;
  wrap.appendChild(mobileBar);

  document.body.appendChild(wrap);
}

export function unmountContactWidgets() {
  const existing = document.getElementById(WIDGET_ID);
  if (existing) existing.remove();
}
