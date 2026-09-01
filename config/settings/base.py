"""
Ortak Django ayarlari. dev.py ve prod.py bu dosyayi import eder.
"""
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-only-insecure-secret-key")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ---------------------------------------------------------------------------
# Uygulamalar
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # SIMPLE_JWT.BLACKLIST_AFTER_ROTATION icin gerekli
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.core",
    "apps.tenants",
    "apps.accounts",
    "apps.apikeys",
    "apps.clients",
    "apps.declarations",
    "apps.documents",
    "apps.tasks",
    "apps.invoicing",
    "apps.notifications",
    "apps.payroll",
    "apps.legal_notices",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Kimligi dogrulanmis kullaniciyi/API anahtarini aktif ofise (tenant) baglar.
    "apps.core.middleware.TenantMiddleware",
    # Her istegin kim tarafindan / hangi ofis adina yapildigini denetim kaydina yazar.
    "apps.core.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Veritabani
# ---------------------------------------------------------------------------
DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    import dj_database_url  # noqa: WPS433 (opsiyonel bagimlilik, asagida requirements'a eklenebilir)

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    # Gelistirme / hizli deneme icin SQLite varsayilan.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Uluslararasilastirma
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Statik / medya
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "apps.apikeys.authentication.ApiKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Not: API anahtari basina daha ince taneli hiz siniri istenirse,
    # ScopedRateThrottle + ilgili view'larda `throttle_scope = "api-key"`
    # eklenerek genisletilebilir (bkz. backlog).
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/min",
        "anon": "60/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Mali Musavirlik Ofis Paneli API",
    "DESCRIPTION": (
        "Cok kiracili (multi-tenant) SMMM ofis yonetim panelinin REST API'si. "
        "Kimlik dogrulama icin JWT (kullanici oturumu) veya X-API-Key (tenant "
        "entegrasyonlari / dis sistemler) kullanilabilir."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())

# ---------------------------------------------------------------------------
# API modu
# ---------------------------------------------------------------------------
# False yapilirsa apps.apikeys.authentication.ApiKeyAuthentication tum
# X-API-Key isteklerini reddeder; boylece panelin API'si tek bir ayardan
# tamamen kapatilabilir. Ofis bazinda acma/kapama icin Office.api_enabled
# kullanilir (bkz. apps/tenants/models.py).
API_ENABLED = config("API_ENABLED", default=True, cast=bool)

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ---------------------------------------------------------------------------
# E-posta
# ---------------------------------------------------------------------------
EMAIL_HOST = config("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# ---------------------------------------------------------------------------
# Bildirim saglayicilari (ileride gercek SMS/WhatsApp API'leri baglanacak)
# ---------------------------------------------------------------------------
SMS_PROVIDER_API_KEY = config("SMS_PROVIDER_API_KEY", default="")
WHATSAPP_PROVIDER_API_KEY = config("WHATSAPP_PROVIDER_API_KEY", default="")

# ---------------------------------------------------------------------------
# Beyanname hatirlatma ayarlari
# ---------------------------------------------------------------------------
# Vade tarihinden kac gun once hatirlatma bildirimi olusturulacagi (varsayilan).
DECLARATION_REMINDER_DAYS_BEFORE = [7, 3, 1, 0]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
