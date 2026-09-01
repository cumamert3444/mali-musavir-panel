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
- [Beyanname takvimi nasil calisir](#beyanname-takvimi-nasil-calisir)
- [Celery ile otomatik hatirlatmalar](#celery-ile-otomatik-hatirlatmalar)
- [Demo veri](#demo-veri)
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
| `apps/notifications` | Panel-ici + e-posta/SMS/WhatsApp (hook) bildirimleri |
| `apps/core` | Ortak altyapi: tenant middleware, izinler, denetim kaydi |

Tum uc noktalarin tam listesi icin `/api/v1/docs/` (Swagger) adresine bakin.

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

## Bilinen sinirlar / sonraki adimlar

Bu ilk surum bir **altyapi** sunar; asagidakiler bilincli olarak kapsam
disi birakildi (proje bilgi tabanindaki `mimari-ve-kapsam.md` -> "Yol
haritasi" bolumune bakin):

- Gercek e-Fatura/e-Defter/GIB servis entegrasyonu (sertifika/erisim
  bilgisi gerektirir) -- su an sadece `Document`/`DeclarationInstance`
  modelleri ile iliskilendirme yapisi hazir.
- Gercek SMS/WhatsApp saglayici baglantisi (`apps/notifications/services.py`
  icinde acikca isaretli TODO'lar var, su an sadece log'a yaziliyor).
- Super admin (SaaS sahibi) icin ayri bir yonetim arayuzu -- API tarafi
  (`OfficeAdminViewSet`) hazir, arayuz yok.
- Musteri portali (musterinin kendi evragini yukleyebildigi ayri giris).
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
