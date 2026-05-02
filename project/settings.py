import os
from pathlib import Path
import logging

from django.core.exceptions import ImproperlyConfigured

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    import dj_database_url
except Exception:
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv:
    load_dotenv(BASE_DIR / ".env", override=False)


# ======================
# Helpers
# ======================
def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw_value = os.environ.get(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_list_any(names, default=""):
    for name in names:
        raw_value = os.environ.get(name)
        if raw_value:
            return [item.strip() for item in raw_value.split(",") if item.strip()]
    return [item.strip() for item in default.split(",") if item.strip()]


def env_int(name, default=0):
    try:
        return int(str(os.environ.get(name, default)).strip())
    except (TypeError, ValueError):
        return int(default)


# ======================
# Core
# ======================
DEFAULT_DEV_SECRET_KEY = "local-dev-secret-key-for-getsiaq-online-sqlite-2026-change-in-production-8f4c2a7b"
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY") or DEFAULT_DEV_SECRET_KEY
DEBUG = env_bool("DEBUG", False) or env_bool("DJANGO_DEBUG", False)
DJANGO_PRODUCTION = env_bool("DJANGO_PRODUCTION", False)


# ======================
# Domain
# ======================
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "getsiaq.online")
WWW_SITE_DOMAIN = os.environ.get("WWW_SITE_DOMAIN", f"www.{SITE_DOMAIN}")
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
SITE_URL = os.environ.get("SITE_URL", f"https://{SITE_DOMAIN}").rstrip("/")


# ======================
# Hosts
# ======================
ALLOWED_HOSTS = env_list_any(
    ("DJANGO_ALLOWED_HOSTS", "ALLOWED_HOSTS"),
    f"{SITE_DOMAIN},{WWW_SITE_DOMAIN},127.0.0.1,localhost,testserver",
)
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env_list_any(
    ("DJANGO_CSRF_TRUSTED_ORIGINS", "CSRF_TRUSTED_ORIGINS"),
    f"https://{SITE_DOMAIN},https://{WWW_SITE_DOMAIN}",
)
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)


# ======================
# Apps
# ======================
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "cloudinary",
    "cloudinary_storage",

    "core.apps.CoreConfig",
]

JAZZMIN_SETTINGS = {
    "site_title": "إدارة الموقع",
    "site_header": "لوحة تحكم الموقع",
    "site_brand": "SEO محلي",
    "welcome_sign": "لوحة التحكم والتحسين اليومي",
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_models": [
        "auth.User",
        "auth.Group",
        "core.AIContentGenerationLog",
        "core.BlogComment",
        "core.MediaFolder",
    ],
    "order_with_respect_to": [
        "core.SiteSettings",
        "core.SiteVerification",
        "core.NavigationItem",
        "core.SEOReportIssue",
        "core.SEOAutomationRun",
        "core.SearchConsoleQuery",
        "core.LegacyRedirect",
        "core.City",
        "core.Service",
        "core.CityServicePage",
        "core.Page",
        "core.BlogPost",
        "core.BlogCategory",
        "core.BlogTag",
        "core.Project",
        "core.Lead",
        "core.Testimonial",
        "core.PageMedia",
        "core.LibraryImage",
    ],
    "custom_links": {
        "core": [
            {
                "name": "مولد المحتوى بالذكاء الاصطناعي",
                "url": "/admin/ai-content/",
                "icon": "fas fa-robot",
            },
        ]
    },
    "icons": {
        "core.SiteSettings": "fas fa-cogs",
        "core.SiteVerification": "fas fa-shield-alt",
        "core.NavigationItem": "fas fa-list",
        "core.SEOReportIssue": "fas fa-chart-line",
        "core.SEOAutomationRun": "fas fa-sync-alt",
        "core.SearchConsoleQuery": "fas fa-search",
        "core.LegacyRedirect": "fas fa-route",
        "core.City": "fas fa-map-marker-alt",
        "core.Service": "fas fa-tools",
        "core.CityServicePage": "fas fa-link",
        "core.Page": "fas fa-file-alt",
        "core.BlogPost": "fas fa-newspaper",
        "core.BlogCategory": "fas fa-folder-open",
        "core.BlogTag": "fas fa-tags",
        "core.Project": "fas fa-briefcase",
        "core.Lead": "fas fa-phone",
        "core.Testimonial": "fas fa-star",
        "core.PageMedia": "fas fa-image",
        "core.LibraryImage": "fas fa-images",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "default_theme_mode": "auto",
    "navbar": "navbar-white navbar-light",
    "sidebar": "sidebar-dark-primary",
    "accent": "accent-success",
    "rtl": True,
}


# ======================
# Middleware
# ======================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.LegacyRedirectMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================
# URLs
# ======================
ROOT_URLCONF = "project.urls"

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
                "core.context_processors.site_defaults",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"


# ======================
# Database
# ======================
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    if dj_database_url is None:
        raise ImproperlyConfigured(
            "DATABASE_URL is set, but dj-database-url is not installed. "
            "Run `pip install -r requirements.txt`."
        )
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    # Local fallback: keep development simple when DATABASE_URL is not provided.
    SQLITE_NAME = os.environ.get("SQLITE_NAME", "db.sqlite3").strip() or "db.sqlite3"
    SQLITE_PATH = Path(SQLITE_NAME)
    if not SQLITE_PATH.is_absolute():
        SQLITE_PATH = BASE_DIR / SQLITE_PATH

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": SQLITE_PATH,
        }
    }


# ======================
# Static
# ======================
STATIC_URL = "/static/"
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", "staticfiles_build"))
if not STATIC_ROOT.is_absolute():
    STATIC_ROOT = BASE_DIR / STATIC_ROOT
STATICFILES_DIRS = [
    path for path in (BASE_DIR / "static", BASE_DIR / "imge") if path.exists()
]
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
if not MEDIA_ROOT.is_absolute():
    MEDIA_ROOT = BASE_DIR / MEDIA_ROOT
DJANGO_SERVE_MEDIA_FILES = env_bool("DJANGO_SERVE_MEDIA_FILES", bool(RENDER_EXTERNAL_HOSTNAME))


# ======================
# 🔥 STORAGE (FIX النهائي)
# ======================
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
USE_CLOUDINARY_MEDIA = env_bool("USE_CLOUDINARY_MEDIA", False)
if USE_CLOUDINARY_MEDIA:
    STORAGES["default"]["BACKEND"] = "cloudinary_storage.storage.MediaCloudinaryStorage"

WHITENOISE_MANIFEST_STRICT = env_bool("WHITENOISE_MANIFEST_STRICT", False)


# ======================
# Auth
# ======================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ======================
# Security
# ======================
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ENABLE_HTTPS_SECURITY = (not DEBUG) and env_bool(
    "DJANGO_ENABLE_HTTPS_SECURITY",
    DJANGO_PRODUCTION or bool(RENDER_EXTERNAL_HOSTNAME),
)

if ENABLE_HTTPS_SECURITY:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", True)
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# ======================
# Logging
# ======================
LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "core": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
    },
}

if ENABLE_HTTPS_SECURITY:
    logging.captureWarnings(True)
