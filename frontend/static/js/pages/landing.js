// pages/landing.js — herkese açık karşılama (marketing) sayfası, "/" kökünde.
import { isAuthenticated } from "../api.js";
import { icons } from "../icons.js";
import { toast, toastError } from "../toast.js";

const FEATURES = [
  {
    icon: "scan",
    title: "OCR Fatura Okuma",
    desc: "Gelen/giden faturaları ve fişleri tarayın; tutar, tarih ve müşteri bilgisi otomatik olarak kayıt altına alınsın.",
  },
  {
    icon: "bank",
    title: "Banka Ekstresi Otomasyonu",
    desc: "Banka ve POS/ÖKC gün sonu raporlarını içe aktarın, tahsilatları müşteri bazında otomatik eşleştirin.",
  },
  {
    icon: "building",
    title: "LUCA / Logo / Mikro Entegrasyonu",
    desc: "API anahtarı ile kullandığınız muhasebe programına bağlanın; veri girişini iki kez yapmayın.",
  },
  {
    icon: "ai",
    title: "Mevzuat Asistanı",
    desc: "Güncel beyanname takvimini ve mevzuat hatırlatmalarını yapay zekâ destekli asistanla takip edin.",
  },
  {
    icon: "chart",
    title: "Beyanname Çapraz Kontrol",
    desc: "Muhtasar ile SGK prim bildirgelerini otomatik karşılaştırıp matrah uyumsuzluklarını erkenden yakalayın.",
  },
  {
    icon: "alert",
    title: "e-Tebligat Takibi",
    desc: "GİB, SGK, icra ve belediye tebligatlarını tek ekrandan izleyin; cevap süresi yaklaşınca uyarı alın.",
  },
  {
    icon: "shield",
    title: "Vergi Borç Matrisi",
    desc: "Tüm mükelleflerinizin vergi/SGK borçlarını tek bir konsolide tabloda görün, gecikeni anında fark edin.",
  },
  {
    icon: "chat",
    title: "Otomatik Ekstre Gönderimi",
    desc: "Onaylanan tahakkuk ve cari hesap ekstrelerini tek tıkla e-posta ile (WhatsApp entegrasyonu opsiyonel) müşterinize iletin.",
  },
];

const PLANS = [
  {
    name: "Deneme",
    price: "Ücretsiz",
    period: "14 gün",
    desc: "Panelin tüm özelliklerini sınırsız dener, kurulum yapmadan başlarsınız.",
    features: ["3 kullanıcıya kadar", "25 müşteriye kadar", "Tüm modüller açık", "E-posta desteği"],
    cta: "Ücretsiz Deneyin",
    highlight: false,
  },
  {
    name: "Profesyonel",
    price: "Talep Üzerine",
    period: "ofis / ay",
    desc: "Büyüyen ofisler için: sınırsız müşteri, API erişimi ve öncelikli destek.",
    features: ["Sınırsız kullanıcı", "Sınırsız müşteri", "API modu + entegrasyonlar", "WhatsApp/e-posta botu", "Öncelikli destek"],
    cta: "Bize Ulaşın",
    highlight: true,
  },
  {
    name: "Kurumsal",
    price: "Talep Üzerine",
    period: "çoklu ofis",
    desc: "Birden fazla şube/ofis yöneten mali müşavirlik zincirleri için.",
    features: ["Çoklu ofis yönetimi", "Süper admin paneli", "Özel entegrasyon desteği", "SLA garantili destek"],
    cta: "Bize Ulaşın",
    highlight: false,
  },
];

const COMPARISON_ROWS = [
  { label: "Kullanıcı Sayısı", deneme: "3'e kadar", pro: "Sınırsız", kurumsal: "Sınırsız" },
  { label: "Müşteri (Mükellef) Sayısı", deneme: "25'e kadar", pro: "Sınırsız", kurumsal: "Sınırsız" },
  { label: "Beyanname Takvimi & Risk Motoru", deneme: true, pro: true, kurumsal: true },
  { label: "e-Tebligat & Vergi Borç Matrisi", deneme: true, pro: true, kurumsal: true },
  { label: "API Modu / Entegrasyonlar", deneme: false, pro: true, kurumsal: true },
  { label: "WhatsApp / E-posta Ekstre Botu", deneme: false, pro: true, kurumsal: true },
  { label: "Çoklu Ofis / Şube Yönetimi", deneme: false, pro: false, kurumsal: true },
  { label: "Süper Admin & SLA Destek", deneme: false, pro: false, kurumsal: true },
];

// Not: Aşağıdaki kartlar GERÇEK, isimlendirilmiş müşteri yorumları DEĞİLDİR —
// panelin tipik kullanım senaryolarını gösteren örnek/illüstratif içeriktir.
const USE_CASES = [
  {
    role: "Bir SMMM Ofisi Sahibi",
    quote: "Beyanname vadelerini ve e-Tebligatları tek ekrandan takip etmek, ayrı ayrı portallara girmekten çok daha hızlı.",
  },
  {
    role: "Bir Muhasebeci",
    quote: "Cari hesap ekstresini tek tıkla PDF olarak e-posta ile gönderebilmek, ay sonu telaşını azaltıyor.",
  },
  {
    role: "Bir Ofis Yöneticisi",
    quote: "Vergi borç matrisi sayesinde hangi mükellefin takipte olduğunu tek bakışta görebiliyoruz.",
  },
];

const FAQ_ITEMS = [
  {
    q: "Müşavir Asistanı tam olarak nedir?",
    a: "Mali müşavirlik ofislerinin müşteri takibi, beyanname takvimi, faturalama, evrak, e-Tebligat ve vergi borç takibini tek bir panelden yönetebildiği çok kiracılı (multi-tenant) bir SaaS panelidir.",
  },
  {
    q: "Ücretsiz deneme süresi ne kadar ve kredi kartı gerekiyor mu?",
    a: "14 gün boyunca tüm özellikleri ücretsiz deneyebilirsiniz; kayıt olmak için kredi kartı bilgisi istenmez.",
  },
  {
    q: "Verilerim ve müşterilerimin verileri güvende mi?",
    a: "Veriler HTTPS/TLS ile şifrelenerek iletilir, ofis bazlı erişim izolasyonu (multi-tenant mimari) ile korunur. Detaylar için Gizlilik Politikamıza ve KVKK Aydınlatma Metnimize bakabilirsiniz.",
  },
  {
    q: "GİB/SGK sistemlerine otomatik bağlanıp veri çekiyor mu?",
    a: "Hayır — GİB/SGK'nın resmi kurumsal API'lerine gerçek zamanlı otomatik bağlantı bu sürümde yoktur. Beyanname, e-Tebligat ve borç kayıtlarını elle veya CSV ile toplu olarak panele işlersiniz; panel bu veriler üzerinden takip, hatırlatma ve çapraz kontrol yapar.",
  },
  {
    q: "Mevcut muhasebe yazılımımla (Logo/Mikro/Luca) entegre olur mu?",
    a: "Panelin API modu ve API anahtarı sistemi, dış sistemlerin panel verisine programatik olarak erişmesine izin verir; muhasebe yazılımınızla köprü kurmak bu API üzerinden mümkündür.",
  },
  {
    q: "Birden fazla ofis veya şube yönetebilir miyim?",
    a: "Evet, mimari en baştan çok kiracılı (multi-tenant) tasarlanmıştır — bir kullanıcı birden fazla ofise üye olabilir ve ofisler arasında geçiş yapabilir.",
  },
  {
    q: "İptal edebilir miyim, taahhüt var mı?",
    a: "Deneme paketinde herhangi bir taahhüt yoktur. Ücretli paketlere geçtiğinizde şartlar sözleşmenizde netleştirilir.",
  },
];

export async function renderLanding(rootEl) {
  const authed = isAuthenticated();
  const primaryHref = authed ? "/dashboard" : "/register";
  const primaryLabel = authed ? "Panele Git" : "Ücretsiz Deneyin";
  const secondaryHref = authed ? "/dashboard" : "/login";
  const secondaryLabel = authed ? "Panele Git" : "Giriş Yap";
  const officeAddress = window.__OFFICE_ADDRESS__ || "";

  rootEl.innerHTML = `
    <div class="landing">
      <header class="landing-header">
        <div class="landing-header-inner">
          <a href="/" data-link class="landing-brand"><span class="logo-badge">MM</span> Müşavir Asistanı</a>
          <nav class="landing-nav">
            <a href="#ozellikler">Özellikler</a>
            <a href="#fiyatlandirma">Fiyatlandırma</a>
            <a href="#sss">SSS</a>
          </nav>
          <div class="landing-header-actions">
            <a href="#demo" class="btn btn-ghost-invert">Demo İsteyin</a>
            <a href="${secondaryHref}" data-link class="btn btn-ghost-invert">${secondaryLabel}</a>
            ${authed ? "" : `<a href="${primaryHref}" data-link class="btn btn-primary">${primaryLabel}</a>`}
          </div>
        </div>
      </header>

      <section class="landing-hero">
        <div class="landing-hero-inner">
          <span class="landing-eyebrow">${icons.ai} Yapay zekâ destekli mali müşavirlik paneli</span>
          <h1>Mali Müşavirlikte<br/>Yapay Zeka Devrimi</h1>
          <p class="landing-hero-sub">
            Müşteri takibinden beyanname takvimine, e-Tebligat izlemeden vergi borcu matrisine kadar
            ofisinizin tüm operasyonunu tek panelden yönetin — Hattat Müşavir ve Tek Hamle'nin en güçlü
            özelliklerini tek çatı altında toplayan yerli bir SaaS.
          </p>
          <div class="landing-hero-cta">
            <a href="${primaryHref}" data-link class="btn btn-primary btn-lg">${primaryLabel}</a>
            <a href="#ozellikler" class="btn btn-ghost btn-lg landing-secondary-cta">Özellikleri İncele</a>
          </div>
          <div class="landing-hero-stats">
            <div><strong>%100</strong><span>Türkçe &amp; yerli altyapı</span></div>
            <div><strong>Çoklu Ofis</strong><span>Multi-tenant mimari</span></div>
            <div><strong>7/24</strong><span>Bulutta erişim</span></div>
          </div>
        </div>
      </section>

      <div class="landing-trust-strip">
        <span>${icons.shield} SSL / HTTPS Şifreleme</span>
        <span>${icons.shield} KVKK Uyumlu Altyapı</span>
        <span>${icons.bell} Hızlı Destek Hedefi</span>
        <a href="/durum" data-link>${icons.chart} Canlı Sistem Durumu →</a>
      </div>

      <section class="landing-section" id="ozellikler">
        <h2 class="landing-section-title">Ofisinizi Öne Taşıyan Özellikler</h2>
        <p class="landing-section-sub">Rakip programlardan ilham alınan, gerçek ofis ihtiyaçlarına göre tasarlanmış modüller.</p>
        <div class="landing-features-grid">
          ${FEATURES.map(
            (f) => `
            <div class="landing-feature-card">
              <div class="landing-feature-icon">${icons[f.icon]}</div>
              <h3>${f.title}</h3>
              <p>${f.desc}</p>
            </div>`
          ).join("")}
        </div>
      </section>

      <section class="landing-section landing-section-alt">
        <h2 class="landing-section-title">Ofisler Panelini Nasıl Kullanıyor?</h2>
        <p class="landing-section-sub">Örnek/illüstratif kullanım senaryoları.</p>
        <div class="landing-usecase-grid">
          ${USE_CASES.map(
            (u) => `
            <div class="landing-usecase-card">
              <p>&ldquo;${u.quote}&rdquo;</p>
              <div class="landing-usecase-role">— ${u.role}</div>
            </div>`
          ).join("")}
        </div>
      </section>

      <section class="landing-section" id="fiyatlandirma">
        <h2 class="landing-section-title">Ücretlendirme / Paketler</h2>
        <p class="landing-section-sub">İhtiyacınıza göre büyüyen, şeffaf paketler.</p>
        <div class="landing-pricing-grid">
          ${PLANS.map(
            (p) => `
            <div class="landing-price-card ${p.highlight ? "highlight" : ""}">
              ${p.highlight ? '<div class="landing-price-badge">En Popüler</div>' : ""}
              <h3>${p.name}</h3>
              <div class="landing-price-amount">${p.price}<span>/${p.period}</span></div>
              <p class="landing-price-desc">${p.desc}</p>
              <ul class="landing-price-features">
                ${p.features.map((f) => `<li>${icons.shield} ${f}</li>`).join("")}
              </ul>
              <a href="${p.highlight || p.name === "Kurumsal" ? "#demo" : "/register"}" ${p.highlight || p.name === "Kurumsal" ? "" : 'data-link'} class="btn ${p.highlight ? "btn-primary" : "btn-secondary"} btn-block">${p.cta}</a>
            </div>`
          ).join("")}
        </div>

        <div class="landing-compare-wrap">
          <table class="landing-compare-table">
            <thead>
              <tr><th>Özellik</th><th>Deneme</th><th>Profesyonel</th><th>Kurumsal</th></tr>
            </thead>
            <tbody>
              ${COMPARISON_ROWS.map(
                (r) => `<tr>
                  <td>${r.label}</td>
                  <td>${typeof r.deneme === "boolean" ? (r.deneme ? "✓" : "—") : r.deneme}</td>
                  <td>${typeof r.pro === "boolean" ? (r.pro ? "✓" : "—") : r.pro}</td>
                  <td>${typeof r.kurumsal === "boolean" ? (r.kurumsal ? "✓" : "—") : r.kurumsal}</td>
                </tr>`
              ).join("")}
            </tbody>
          </table>
        </div>
      </section>

      <section class="landing-section landing-section-alt" id="sss">
        <h2 class="landing-section-title">Sıkça Sorulan Sorular</h2>
        <div class="landing-faq">
          ${FAQ_ITEMS.map(
            (f, i) => `
            <div class="faq-item">
              <button class="faq-question" type="button" data-faq="${i}">
                <span>${f.q}</span>
                <span class="faq-caret">${icons.back}</span>
              </button>
              <div class="faq-answer" id="faq-answer-${i}"><p>${f.a}</p></div>
            </div>`
          ).join("")}
        </div>
      </section>

      <section class="landing-section" id="demo">
        <h2 class="landing-section-title">Demo İsteyin</h2>
        <p class="landing-section-sub">Formu doldurun, ekibimiz sizinle iletişime geçsin.</p>
        <div class="landing-contact-grid">
          <form id="demo-form" class="landing-contact-form">
            <div id="demo-error"></div>
            <div class="field"><label>Ad Soyad *</label><input type="text" name="full_name" required /></div>
            <div class="field"><label>Ofis / Firma Adı</label><input type="text" name="office_name" /></div>
            <div class="field-row">
              <div class="field"><label>E-posta *</label><input type="email" name="email" required /></div>
              <div class="field"><label>Telefon</label><input type="tel" name="phone" /></div>
            </div>
            <div class="field"><label>Mesaj</label><textarea name="message" placeholder="İhtiyacınızdan kısaca bahsedin..."></textarea></div>
            <button type="submit" class="btn btn-primary btn-block" id="demo-submit">Talebi Gönder</button>
          </form>
          ${
            officeAddress
              ? `<div class="landing-contact-map">
                  <iframe title="Ofis Konumu" width="100%" height="320" style="border:0;border-radius:12px;"
                    loading="lazy" referrerpolicy="no-referrer-when-downgrade"
                    src="https://www.google.com/maps?q=${encodeURIComponent(officeAddress)}&output=embed"></iframe>
                  <p class="text-sm text-muted" style="margin-top:10px;">${icons.building} ${officeAddress}</p>
                </div>`
              : `<div class="landing-contact-map landing-contact-map-placeholder">
                  <div class="landing-feature-icon" style="margin:0 auto 14px;">${icons.building}</div>
                  <p class="text-sm text-muted" style="text-align:center;">Ofis adresi ve harita, ofis bilgileri yapılandırıldığında burada görünecek.</p>
                </div>`
          }
        </div>
      </section>

      <section class="landing-cta-band">
        <h2>Ofisinizi bugün dijitalleştirin</h2>
        <p>Kurulum gerektirmez, kredi kartı istemez — dakikalar içinde ilk müşterinizi ekleyin.</p>
        <a href="/register" data-link class="btn btn-primary btn-lg">Ücretsiz Deneyin</a>
      </section>

      <footer class="landing-footer">
        <div class="landing-footer-inner">
          <div class="landing-brand"><span class="logo-badge">MM</span> Müşavir Asistanı</div>
          <div class="landing-footer-links">
            <a href="/login" data-link>Giriş Yap</a>
            <a href="/register" data-link>Kayıt Ol</a>
            <a href="/gizlilik-politikasi" data-link>Gizlilik Politikası</a>
            <a href="/kvkk" data-link>KVKK</a>
            <a href="/durum" data-link>Sistem Durumu</a>
          </div>
          <div class="landing-social-links">
            <a href="#" aria-label="LinkedIn" title="LinkedIn (yakında)">in</a>
            <a href="#" aria-label="Instagram" title="Instagram (yakında)">◎</a>
            <a href="#" aria-label="X / Twitter" title="X (yakında)">𝕏</a>
          </div>
          <div class="landing-footer-copy">© ${new Date().getFullYear()} Müşavir Asistanı. Tüm hakları saklıdır.</div>
        </div>
      </footer>
    </div>
  `;

  rootEl.querySelectorAll("[data-faq]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest(".faq-item");
      item.classList.toggle("open");
    });
  });

  const demoForm = rootEl.querySelector("#demo-form");
  if (demoForm) {
    demoForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = rootEl.querySelector("#demo-error");
      errorBox.innerHTML = "";
      const submitBtn = rootEl.querySelector("#demo-submit");
      submitBtn.disabled = true;
      submitBtn.textContent = "Gönderiliyor...";
      const fd = new FormData(demoForm);
      try {
        const res = await fetch(`${window.__API_BASE__ || ""}/api/v1/leads/demo-request/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: fd.get("full_name"),
            office_name: fd.get("office_name"),
            email: fd.get("email"),
            phone: fd.get("phone"),
            message: fd.get("message"),
            source_path: "/",
          }),
        });
        if (!res.ok) throw new Error("Talep gönderilemedi. Lütfen tekrar deneyin.");
        window.__mmpRouter.navigate("/tesekkurler");
      } catch (err) {
        errorBox.innerHTML = `<div class="error-banner">${err.message}</div>`;
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Talebi Gönder";
      }
    });
  }
}
