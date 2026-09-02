# Mali Musavirlik Ofis Paneli

Cok kiracili (multi-tenant) SMMM ofis yonetim panelinin backend altyapisi.
Django + Django REST Framework ile yazilmistir; her mali musavirlik ofisi
(tenant/"Office") kendi musterisini, beyanname takvimini, evragini,
gorevlerini, faturalamasini ve bildirimlerini yonetir.

> Bu proje, bir Instagram reel'inde bir mali musavirin anlattigi panel
> fikrinden yola cikilarak, Turkiye'deki SMMM ofislerinin tipik ihtiyaclarina
> gore hazirlanmis STANDART bir baslangic altyapisidir. Beyanname vade
> kurallari (bkz. `seed_declaration_types`) makul varsayilanlardir --
> kullanima almadan once guncel mevzuat ile karsilastirin.

## Icindekiler

- [Mimari ozet](#mimari-ozet)
- [Kurulum (yerel gelistirme)](#kurulum-yerel-gelistirme)
- [Docker ile calistirma](#docker-ile-calistirma)
- [API modunu aktiflestirme](#api-modunu-aktiflestirme)
- [Modul haritasi](#modul-haritasi)
- [Genel web sitesi (landing) ve SEO](#genel-web-sitesi-landing-ve-seo)
- [Super Admin paneli](#super-admin-paneli)
- [Beyanname takvimi nasil calisir](#beyanname-takvimi-nasil-calisir)
- [Celery ile otomatik hatirlatmalar](#celery-ile-otomatik-hatirlatmalar)
- [Demo veri](#demo-veri)
- [ONEMLI: Canli ortam (Railway) dagitim notu](#onemli-canli-ortam-railway-dagitim-notu)
- [Bilinen sinirlar / sonraki adimlar](#bilinen-sinirlar--sonraki-adimlar)

## Mimari ozet

- **Cok kiracili model**: tek veritabani, paylasimli sema + her tabloda
  `office` (tenant) alani. Sorgu izolasyonu view katmaninda
  (`apps/core/views.py::TenantScopedViewSetMixin`) otomatik uygulanir.
- **Kimlik dogrulama**: JWT (kullanici oturumu, `djangorestframework-simplejwt`)
  veya `X-API-Key` (dis sistem entegrasyonlari, `apps/apikeys`).
- **Aktif ofis secimi**: bir kullanici birden fazla ofise uye olabilir;
  `X-Office-Id` header'i ile hangi ofis adina istek yapildigi belirtilir
  (belirtilmezse kullanicinin ilk/varsayilan ofisi kullanilir).
- Detayli mimari kararlar ve gerekceleri icin proje bilgi tabanindaki
  `mimari-ve-kapsam.md` dokumanina bakabilirsiniz.

## Kurulum (yerel gelistirme)

Gereksinim: Python 3.11+ (3.12 onerilir).

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # gerekirse degerleri duzenleyin

python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

Sunucu ayaga kalktiktan sonra:

- Swagger UI: <http://127.0.0.1:8000/api/v1/docs/>
- ReDoc: <http://127.0.0.1:8000/api/v1/redoc/>
- Django admin: <http://127.0.0.1:8000/admin/>

`DATABASE_URL` bos birakilirsa proje otomatik olarak SQLite (`db.sqlite3`)
kullanir -- hizli deneme icin idealdir. Gercek kullanimda `.env` icinde
PostgreSQL baglanti dizesini tanimlayin.

Vade hatirlatmalari icin Celery + Redis gerekir (opsiyonel, asagida).

## Docker ile calistirma

```bash
cp .env.example .env
docker compose up --build
```

Bu komut PostgreSQL, Redis, Django (gunicorn), bir Celery worker ve bir
Celery beat (zamanlayici) servisini birlikte ayaga kaldirir.

## API modunu aktiflestirme

"API modu", panelin dis sistemlerle (e-Fatura/e-Defter koprusu, muhasebe
programi, mobil uygulama vb.) konusabilmesi icin REST API'nin
`X-API-Key` ile erisime acilmasidir. Adimlar:

1. **Global anahtar acik olmali.** `.env` dosyasinda `API_ENABLED=True`
   (varsayilan zaten acik). Sistem genelinde API'yi kapatmak icin
   `API_ENABLED=False` yapip sunucuyu yeniden baslatmaniz yeterli.

2. **Ofis bazinda acin.** Her ofis kendi API erisimini ayri acar/kapatir:

   ```bash
   curl -X PATCH http://127.0.0.1:8000/api/v1/tenants/my-office/ \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"api_enabled": true}'
   ```

   Bunu sadece o ofisin **owner** (sahip) rolundeki kullanicisi yapabilir.

3. **Bir API anahtari olusturun:**

   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/apikeys/keys/ \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Muhasebe programi entegrasyonu"}'
   ```

   Yanit icindeki `"key": "mmp_xxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"` degeri
   **sadece bu yanitta** gorunur, bir daha gosterilmez -- guvenli bir yere
   kaydedin.

4. **Anahtari kullanin.** Artik dis sistem bu anahtari her istekte
   gonderebilir:

   ```bash
   curl http://127.0.0.1:8000/api/v1/clients/ \
     -H "X-API-Key: mmp_xxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

   API anahtari ile gelen istekler, anahtari olusturan kullanicinin
   ofisiyle otomatik eslesir (`X-Office-Id` gerekmez).

5. **Iptal etmek icin** `POST /api/v1/apikeys/keys/<id>/revoke/` ya da
   kaydi tamamen silin (`DELETE /api/v1/apikeys/keys/<id>/`).

Kullanici girisi (JWT) icin:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@ofis.test", "password": "demo12345"}'
```

## Modul haritasi

| Modul | Ne yapar |
|---|---|
| `apps/tenants` | Ofis (tenant), abonelik paketi |
| `apps/accounts` | Kullanici, ofis uyeligi/rol, kayit akisi |
| `apps/apikeys` | Tenant basina API anahtari + kimlik dogrulama |
| `apps/clients` | Musteri sirket, yetkili kisi, hizmet paketi, atama |
| `apps/declarations` | Beyanname turleri + otomatik donem/vade uretimi |
| `apps/documents` | Evrak yukleme/kategori |
| `apps/tasks` | Gorev/kanban, yorumlar |
| `apps/invoicing` | Ofis hizmet faturasi, satir, tahsilat |
| `apps/notifications` | Panel-ici + e-posta/SMS/WhatsApp (hook) bildirimleri, PDF ekstre gonderimi |
| `apps/core` | Ortak altyapi: tenant middleware, izinler, denetim kaydi, SEO, genel `spa_view`/`robots.txt`/`sitemap.xml`/`status` |
| `apps/tax_debts` | Vergi/SGK borc matrisi (mukellef bazinda borc kayitlari + CSV toplu import) |
| `apps/pos_sync` | POS/ÖKC gun sonu raporu senkronizasyonu (aylik ozet + CSV toplu import) |
| `apps/einvoices` | e-Fatura/e-Arsiv/e-Irsaliye kayitlari (musteri bazinda konsolide liste + CSV/Excel toplu import) |
| `apps/leads` | Herkese acik "Demo Isteyin" formundan gelen talepler (platform seviyesinde, tenant'a bagli degil) |

Tum uc noktalarin tam listesi icin `/api/v1/docs/` (Swagger) adresine bakin.

### Rakip mimarisinden ilham alinan modul ozeti (dürüst kapsam notu)

Hattat Musavir / Tek Hamle gibi rakip programlardaki bazi ozellikler bu
surumde **elle veri girisi + CSV toplu import + panel-ici takip/uyari**
seklinde uygulandi. GIB/SGK'nin resmi kurumsal API'lerine gercek zamanli
otomatik baglanti **yoktur** (sertifika/erisim anlasmasi gerektirir, bu
kapsamin disindadir):

- **e-Tebligat takibi** (`apps/legal_notices`): kayitlari elle veya CSV ile
  girersiniz, panel cevap suresi yaklasinca listede one cikarir.
- **Beyanname capraz kontrol / risk motoru** (`apps/declarations/risk_engine.py`):
  panele zaten girilmis olan bordro (Muhtasar taban) ile beyan edilen
  tutarlari karsilastirip `DeclarationInstance.risk_report` uc noktasinda
  uyari uretir -- gercek e-fatura/GIB verisi degil, panel-ici veriye dayanir.
- **Vergi/SGK borc matrisi** (`apps/tax_debts`): elle/CSV ile girilen borc
  kayitlarini mukellef bazinda konsolide tablo halinde gosterir.
- **POS/OKC gun sonu senkronizasyonu** (`apps/pos_sync`): CSV import ile
  girilen gunluk POS raporlarini aylik ozetler.
- **e-Fatura kayitlari** (`apps/einvoices`, 2026-09-02): GIB'in resmi
  e-Fatura sistemine (ister dogrudan GIB portali, ister TURMOB'un ucretsiz
  sundugu Luca e-Belge Portali uzerinden) gercek zamanli otomatik bir API
  baglantisi **yoktur** -- arastirildi: Luca e-Belge Portali
  (turmobefatura.luca.com.tr) bir insanin tarayicidan kullanici adi/sifre
  ile giris yaptigi bir web portalidir, ucuncu parti yazilimlarin
  baglanabilecegi genel/dokumante bir REST/SOAP API'si kamuya acik degildir;
  TURMOB'un e-Birlik uzerinden verdigi "servis anahtari" esas olarak Luca
  urunlerini birbirine baglamak ve VKN/TCKN sorgulamak icindir. Bu yuzden
  kayitlar, Luca portalindan (veya kullanilan entegratorden -- Foriba,
  Uyumsoft, QNB eFinans vb.) alinan fatura listesi Excel/CSV dokumunun elle
  veya toplu CSV import ile buraya islenmesiyle olusturulur; panel bunlari
  musteri bazinda, gelen/giden kirilimiyla konsolide bir listede gosterir.
  Ileride gercek bir API erisimi (TURMOB servis anahtari veya bir
  entegrator bayiligi) edinilirse, `apps/einvoices/views.py` icindeki ayni
  ViewSet'e yeni bir `sync` action'i eklemek yeterli olur -- veri modeli ve
  frontend zaten buna hazir.
- **Otomatik ekstre gonderimi** (`apps/notifications/dispatch.py`): cari
  hesap ekstresini gercek bir PDF (reportlab) olarak uretir ve e-posta ile
  gonderir; WhatsApp gonderimi `WHATSAPP_PROVIDER_API_KEY` ortam degiskeni
  tanimlanmadan **calismaz** ve acik bir hata firlatir (sessiz sahte basari
  YOKTUR).

## Genel web sitesi (landing) ve SEO

`/` artik giris ekrani degil, herkese acik bir pazarlama sayfasidir
(`frontend/static/js/pages/landing.js`). Giris ekrani `/login`'e, kayit
`/register`'a tasindi; girisli kullanicilar panele `/dashboard` uzerinden
erisir.

Landing sayfasi icerdikleri: hero + ozellik kartlari, gercek/illustratif
oldugu acikca belirtilen ornek kullanim senaryolari (isim/foto olmadan --
gercek musteri yorumu **degildir**), fiyatlandirma kartlari + karsilastirma
tablosu, SSS akordeonu, `#demo` talep formu (`POST /api/v1/leads/demo-request/`),
guven rozetleri (SSL/KVKK), footer.

Diger genel sayfalar: `/gizlilik-politikasi`, `/kvkk`, `/tesekkurler`
(form sonrasi), `/durum` (gercek DB baglanti kontrolu yapan canli sistem
durumu -- uydurma "%99.9 uptime" YOKTUR).

SEO altyapisi (`apps/core/seo.py`, `apps/core/site_views.py`,
`templates/spa.html`):

- Her bilinen genel rota icin sunucu tarafinda farkli `<title>`/meta
  description/robots/canonical (`spa_view`, `request.path`'i inceler);
  girisli uygulama rotalari varsayilan olarak `noindex, nofollow`.
- `/robots.txt`, `/sitemap.xml` gercek, calisan uc noktalardir.
- Open Graph + Twitter Card (`frontend/static/img/og-image.png`), ana
  sayfada SoftwareApplication + FAQPage JSON-LD.
- GA4 (`GA4_MEASUREMENT_ID`) ve Meta Pixel (`META_PIXEL_ID`) betikleri
  **sadece** ilgili ortam degiskeni tanimliysa render edilir -- sahte/bos
  analytics ID YOKTUR.
- WhatsApp kabarcik butonu + mobil iletisim cubugu (`contactWidgets.js`)
  sadece `WHATSAPP_CONTACT_NUMBER` tanimliysa gorunur.
- Google Maps embed'i sadece `OFFICE_PUBLIC_ADDRESS` tanimliysa gorunur;
  tanimli degilse yer tutucu gosterilir (uydurma adres YOKTUR).

Ilgili ortam degiskenleri (hepsi opsiyonel, bos birakilirsa ilgili ozellik
sessizce gizlenir): `SITE_URL`, `GA4_MEASUREMENT_ID`, `META_PIXEL_ID`,
`WHATSAPP_CONTACT_NUMBER`, `OFFICE_PUBLIC_ADDRESS`.

## Super Admin paneli

`/admin` (SPA rotasi, Django admin'den farkli) sadece `is_superuser=True`
kullanicilara acik bir panel-ici yonetim ekranidir: tum ofisleri, kullanicilari
ve abonelik paketlerini goruntuleme/duzenleme (`apps/tenants` icindeki
`OfficeAdminViewSet`, `AdminUserViewSet`, `SubscriptionPlanAdminViewSet`,
`PlatformStatsView`).

Ilk SuperAdmin kullanicisini olusturmak icin (idempotent -- kullanici zaten
varsa sifreyi DEGISTIRMEZ, sadece is_staff/is_superuser bayraklarini garanti
eder). Bu komut Railway'in `startCommand`'ina eklendi, yani **her deploy'da
otomatik calisir**; elle calistirmak isterseniz:

```bash
python manage.py seed_superadmin
# veya farkli kimlik bilgisiyle:
python manage.py seed_superadmin --email ornek@ofis.com --password GucluBirSifre123
```

Varsayilan kimlik bilgileri (parametre verilmezse):

- E-posta: `cumamert3444@gmail.com`
- Sifre: `Admin2026!`

**Canli ortama aldiktan sonra bu sifreyi mutlaka degistirin** (Super Admin
panelinden veya Django admin'den).

## Beyanname takvimi nasil calisir

1. Bir ofis icin standart beyanname turlerini olusturun:

   ```bash
   python manage.py seed_declaration_types --office-id <ofis_id>
   # veya tum ofisler icin:
   python manage.py seed_declaration_types --all
   ```

2. Bir musteriyi ilgili beyanname turlerine abone edin:

   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/clients/<client_id>/declaration-subscriptions/ \
     -H "Authorization: Bearer <access_token>" \
     -d '{"declaration_type": <kdv_type_id>}'
   ```

   Bu istek, mevcut donemden itibaren birkac donemlik `DeclarationInstance`
   kaydini hemen olusturur.

3. Ileriye donuk donemleri toplu uretmek icin (normalde Celery ile otomatik
   calisir, elle de tetiklenebilir):

   ```bash
   python manage.py generate_declaration_instances --months-ahead 2
   ```

4. Takvimi gormek icin:

   ```
   GET /api/v1/declaration-instances/upcoming/?days=14
   ```

## Celery ile otomatik hatirlatmalar

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Varsayilan plan (`config/celery.py`):

- Her gun 02:00 -- eksik beyanname donemlerini uretir.
- Her gun 08:00 -- vadesi `DECLARATION_REMINDER_DAYS_BEFORE` (varsayilan
  `[7, 3, 1, 0]` gun) icinde olan beyannameler icin bildirim olusturur.
- Her gun 08:15 -- vadesi gecmis hizmet faturalarini `overdue` olarak
  isaretler ve ofis sahibine bildirim gonderir.

## Demo veri

Hizli denemek icin:

```bash
python manage.py seed_demo_data
```

Ornek bir ofis, sahip kullanici (`demo@ofis.test` / `demo12345`), 3 musteri
ve KDV/Muhtasar beyanname takvimi olusturur.

## ONEMLI: Canli ortam (Railway) dagitim notu

**2026-09-02 tarihinde tespit edilen sorun -- COZULDU.**
Canli sitede (Railway) veritabani tablolari hic olusturulmamisti; bu yuzden
giris/kayit istekleri `relation "accounts_user" does not exist` hatasiyla
500 donduruyordu.

**Gercek kok neden:** Railway servisi build sistemi olarak **Railpack**
(Railway'in kendi otomatik build sistemi) kullaniyordu ve repodaki
`Dockerfile`'i tamamen gormezden geliyordu. Yani Dockerfile'a eklenen
`makemigrations` build-time duzeltmesi hicbir zaman gercekten calismiyordu
-- Railpack kendi otomatik Python/Django tespitiyle build ediyordu, migration
dosyalari hic uretilmiyordu ve `startCommand` icindeki `makemigrations`/
`migrate` zinciri de Railpack'in runtime ortaminda sessizce cokuyor ya da
asili kaliyordu.

**Duzeltme:** Railway servis ayarlarinda `dockerfilePath: "Dockerfile"`
set edilerek builder **RAILPACK'ten DOCKERFILE'a** cevrildi (Railway
Dashboard: Service -> Settings -> Build -> Builder = Dockerfile; veya
Railway MCP/CLI ile `dockerfilePath` alani). Bu, repodaki `Dockerfile`'in
gercekten kullanilmasini sagliyor -- `makemigrations` artik build
asamasinda calisiyor (bkz. `Dockerfile`), migration dosyalari imajin
icine gomuluyor, ve container baslarken sadece `migrate --noinput`
calistirmasi yeterli. Duzeltmeden sonra deploy loglarinda `migrate`'in
tum uygulamalarin tablolarini (21 app) saniyeler icinde basariyla
olusturdugu dogrulandi.

**Guncel `startCommand`:**

```
python manage.py migrate --noinput && python manage.py seed_superadmin ; gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 3
```

**Onemli:** Bu, bir Railway servis ayaridir (kod degil) -- Railway
Dashboard'da veya Railway MCP/CLI ile degistirilir, repo'ya `git push`
gerektirmez. Bu depodaki `Dockerfile` zaten dogru sekilde yazilmis
durumda; sorun hep Railway'in onu kullanip kullanmamasindaydi. Ileride
projeyi yeni bir Railway servisine tasirsaniz veya servisi sifirdan
kurarsaniz, **builder'in "Dockerfile" olarak ayarli oldugunu** (Railpack
degil) mutlaka dogrulayin.

**Ozel alan adi / SSL notu:** `www.musavirasistani.com` Railway'e ozel alan
adi olarak eklenmis ve CNAME kaydi dogru sekilde yayilmis (propagated)
durumda, ancak SSL sertifikasi bu inceleme sirasinda hala "dogrulaniyor"
asamasindaydi. Kok alan adi (`musavirasistani.com`, www'siz) mevcut Railway
plani "servis basina ozel alan adi" limitine takildigi icin **eklenemedi**
-- ya Railway planini yukseltip ikinci bir ozel alan adi eklemeniz, ya da
DNS saglayicinizda kok alan adindan `www.musavirasistani.com`'a yonlendirme
(redirect) kurmaniz gerekiyor.

## Bilinen sinirlar / sonraki adimlar

Bu ilk surum bir **altyapi** sunar; asagidakiler bilincli olarak kapsam
disi birakildi (proje bilgi tabanindaki `mimari-ve-kapsam.md` -> "Yol
haritasi" bolumune bakin):

- Gercek e-Fatura/e-Defter/GIB servis entegrasyonu (sertifika/erisim
  bilgisi gerektirir) -- su an sadece `Document`/`DeclarationInstance`
  modelleri ile iliskilendirme yapisi hazir.
- Gercek SMS/WhatsApp saglayici baglantisi (`apps/notifications/services.py`
  icinde acikca isaretli TODO'lar var, su an sadece log'a yaziliyor).
- Musteri portali (musterinin kendi evragini yukleyebildigi ayri giris).
- Gercek, isimlendirilmis musteri referanslari/yorumlari -- landing
  sayfasindaki ornekler bilincli olarak illustratif/rol-bazli tutuldu.
- Otomatik test paketi genisletilmedi (bu surum manuel/statik olarak
  gozden gecirildi; `python manage.py test` icin iskelet hazir ama test
  dosyalari henuz yazilmadi).

**Onemli:** Bu kod bu ortamda calistirilarak test EDILEMEDI, cunku bu
gelistirme ortaminin internet erisimi paket kaynaklarina (PyPI, npm, apt)
kapali -- bagimliliklar kurulamadi. Kod dikkatle elle yazildi ve statik
olarak (syntax + capraz referans) kontrol edildi, ancak kendi
ortaminizda `pip install -r requirements.txt && python manage.py migrate`
calistirdiktan sonra kucuk duzeltmeler gerekebilir. Bir hata ile
karsilasirsaniz hatanin tamamini paylasin, birlikte hizlica cozeriz.
