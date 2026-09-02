// pages/legal.js — Gizlilik Politikası ve KVKK Aydınlatma Metni (herkese açık).

function legalShell(rootEl, { title, bodyHtml }) {
  rootEl.innerHTML = `
    <div class="landing">
      <header class="landing-header">
        <div class="landing-header-inner">
          <a href="/" data-link class="landing-brand"><span class="logo-badge">MM</span> Müşavir Asistanı</a>
          <div class="landing-header-actions">
            <a href="/" data-link class="btn btn-ghost-invert">${"← Ana Sayfa"}</a>
          </div>
        </div>
      </header>
      <div class="legal-page">
        <h1>${title}</h1>
        ${bodyHtml}
      </div>
      <footer class="landing-footer">
        <div class="landing-footer-inner">
          <div class="landing-brand"><span class="logo-badge">MM</span> Müşavir Asistanı</div>
          <div class="landing-footer-links">
            <a href="/gizlilik-politikasi" data-link>Gizlilik Politikası</a>
            <a href="/kvkk" data-link>KVKK</a>
          </div>
          <div class="landing-footer-copy">© ${new Date().getFullYear()} Müşavir Asistanı.</div>
        </div>
      </footer>
    </div>
  `;
}

export async function renderPrivacyPolicy(rootEl) {
  legalShell(rootEl, {
    title: "Gizlilik Politikası",
    bodyHtml: `
      <p class="legal-updated">Son güncelleme: ${new Date().toLocaleDateString("tr-TR")}</p>
      <p><strong>Bu bir taslak metindir.</strong> Yayına almadan önce bir hukuk danışmanına
      kontrol ettirmenizi öneririz — bu sayfa hukuki danışmanlık yerine geçmez.</p>

      <h2>1. Kapsam</h2>
      <p>Bu Gizlilik Politikası, Müşavir Asistanı ("Panel", "Hizmet") üzerinden toplanan, işlenen ve
      saklanan verilerin nasıl ele alındığını açıklar. Hizmeti kullanan mali müşavirlik ofisleri
      ("Ofis", "Veri Sorumlusu") ve onların müşterileri ile Hizmet'i işleten taraf ("Veri İşleyen")
      arasındaki ilişkiyi kapsar.</p>

      <h2>2. Toplanan Veriler</h2>
      <p>Hesap oluştururken ve Hizmet'i kullanırken aşağıdaki veri kategorileri işlenebilir:
      kimlik ve iletişim bilgileri (ad soyad, e-posta, telefon), ofis/mükellef bilgileri (unvan,
      vergi numarası, adres), Hizmet kapsamında girilen mali/idari kayıtlar (fatura, beyanname,
      bordro, tebligat özetleri), ve teknik kullanım verileri (oturum/erişim kayıtları, IP adresi).</p>

      <h2>3. Verilerin Kullanım Amacı</h2>
      <p>Toplanan veriler; Hizmet'in sunulması, hesap güvenliğinin sağlanması, destek taleplerinin
      yanıtlanması, yasal yükümlülüklerin yerine getirilmesi ve Hizmet'in geliştirilmesi amacıyla
      işlenir. Veriler, açık rıza veya yasal bir dayanak olmaksızın üçüncü taraflara pazarlama
      amacıyla satılmaz veya kiralanmaz.</p>

      <h2>4. Veri Güvenliği</h2>
      <p>Hizmet, veriler taşınırken şifreleme (HTTPS/TLS) kullanır ve erişim, kimlik doğrulama ve
      yetkilendirme kontrolleriyle sınırlandırılır. Yine de internet üzerinden hiçbir iletim
      yönteminin veya elektronik saklama yönteminin %100 güvenli olmadığını hatırlatırız.</p>

      <h2>5. Veri Saklama</h2>
      <p>Veriler, hesabınız aktif olduğu sürece ve yasal saklama yükümlülükleri (örneğin muhasebe
      kayıtları için Vergi Usul Kanunu kapsamındaki süreler) çerçevesinde saklanır.</p>

      <h2>6. Çerezler</h2>
      <p>Hizmet, oturum yönetimi ve tercihlerin hatırlanması için gerekli çerezleri kullanır. Analitik
      amaçlı çerezler yalnızca açıkça yapılandırılmış ve onayınız alınmışsa aktif olur.</p>

      <h2>7. İletişim</h2>
      <p>Bu politika hakkında sorularınız için ofisinizin size ilettiği iletişim kanallarını
      kullanabilirsiniz.</p>
    `,
  });
}

export async function renderKvkk(rootEl) {
  legalShell(rootEl, {
    title: "KVKK Aydınlatma Metni",
    bodyHtml: `
      <p class="legal-updated">Son güncelleme: ${new Date().toLocaleDateString("tr-TR")}</p>
      <p><strong>Bu bir taslak metindir.</strong> 6698 sayılı Kişisel Verilerin Korunması Kanunu
      ("KVKK") kapsamındaki yükümlülüklerinizi tam olarak karşıladığından emin olmak için
      yayına almadan önce bir hukuk danışmanına kontrol ettirmenizi öneririz.</p>

      <h2>1. Veri Sorumlusu</h2>
      <p>6698 sayılı KVKK uyarınca, Müşavir Asistanı panelini kullanan mali müşavirlik ofisi,
      kendi mükelleflerine ait verilerin veri sorumlusudur. Panel altyapısını işleten taraf,
      Ofis'in talimatları doğrultusunda hareket eden veri işleyen sıfatındadır.</p>

      <h2>2. İşlenen Kişisel Veri Kategorileri</h2>
      <p>Kimlik verisi (ad, soyad, TC kimlik/vergi no), iletişim verisi (telefon, e-posta, adres),
      mesleki/mali veri (bordro, fatura, beyanname bilgileri), işlem güvenliği verisi (IP, oturum
      kayıtları).</p>

      <h2>3. İşleme Amaçları</h2>
      <p>Muhasebe/mali müşavirlik hizmetlerinin yürütülmesi, yasal yükümlülüklerin (vergi, SGK,
      muhasebe mevzuatı) yerine getirilmesi, sözleşme süreçlerinin yönetimi ve iletişim
      faaliyetlerinin sürdürülmesi.</p>

      <h2>4. Hukuki Sebep</h2>
      <p>Kişisel veriler; bir sözleşmenin kurulması veya ifasıyla doğrudan doğruya ilgili olması,
      hukuki yükümlülüğün yerine getirilmesi ve/veya ilgili kişinin açık rızası hukuki
      sebeplerine dayanılarak işlenir (KVKK m. 5).</p>

      <h2>5. Veri Sahibinin Hakları (KVKK m. 11)</h2>
      <p>İlgili kişi; kişisel verisinin işlenip işlenmediğini öğrenme, işlenmişse buna ilişkin
      bilgi talep etme, işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme,
      yurt içinde/yurt dışında aktarıldığı üçüncü kişileri bilme, eksik/yanlış işlenmişse
      düzeltilmesini isteme, silinmesini/yok edilmesini isteme ve bu işlemlerin verilerin
      aktarıldığı üçüncü kişilere bildirilmesini isteme haklarına sahiptir.</p>

      <h2>6. Başvuru Yöntemi</h2>
      <p>Yukarıdaki haklarınızı kullanmak için, hizmet aldığınız mali müşavirlik ofisiyle
      doğrudan iletişime geçebilirsiniz.</p>
    `,
  });
}
