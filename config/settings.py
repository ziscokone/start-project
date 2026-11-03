"""
Configuration Django du projet.

Les valeurs sensibles ou propres à chaque machine sont lues dans le fichier .env
(voir .env.example).
"""
import os
from pathlib import Path

from django.contrib.messages import constants as messages
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(nom, defaut=False):
    return os.environ.get(nom, str(defaut)).strip().lower() in ('1', 'true', 'yes', 'oui')


def env_liste(nom, defaut=''):
    return [v.strip() for v in os.environ.get(nom, defaut).split(',') if v.strip()]


# ── Base ────────────────────────────────────────────────────────────────
DEBUG = env_bool('DEBUG', False)
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-uniquement-cle-non-securisee')
if not DEBUG and SECRET_KEY.startswith('dev-'):
    raise RuntimeError("SECRET_KEY doit être défini dans .env en production.")

ALLOWED_HOSTS = env_liste('ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_liste('CSRF_TRUSTED_ORIGINS')
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')


# ── Applications ────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'axes',

    # Le cœur doit rester avant les modules : il charge leur fichier module.py.
    'core',
    'apps.comptes',
    'apps.etablissement',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Toutes les pages demandent une connexion, sauf celles marquées @login_not_required.
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ChangementMotDePasseMiddleware',
    'core.middleware.AccesModuleMiddleware',
    # Axes doit rester en dernier.
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.interface',
            ],
        },
    },
]


# ── Base de données : PostgreSQL si DB_NAME est défini, sinon SQLite ─────
if os.environ.get('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['DB_NAME'],
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── Authentification ────────────────────────────────────────────────────
AUTH_USER_MODEL = 'comptes.Utilisateur'
LOGIN_URL = 'compte:connexion'
LOGIN_REDIRECT_URL = 'hub'
LOGOUT_REDIRECT_URL = 'compte:connexion'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Session : 12 h maximum. Sans « Se souvenir de moi », elle se ferme avec le navigateur.
SESSION_COOKIE_AGE = 60 * 60 * 12

# Axes : blocage après 5 échecs pour le couple identifiant + adresse IP, pendant 1 h.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_LOCKOUT_TEMPLATE = 'comptes/bloque.html'
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_VERBOSE = False


# ── Langue et fuseau ────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True


# ── Fichiers statiques et médias ────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


# ── Application installable (PWA) ───────────────────────────────────────
# À augmenter après une mise à jour du CSS/JS : vide le cache des appareils.
PWA_VERSION = '1'


# ── Messages : classes Bootstrap ────────────────────────────────────────
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# ── Sécurité en production ──────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = env_bool('COOKIES_SECURISES', True)
    CSRF_COOKIE_SECURE = env_bool('COOKIES_SECURISES', True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))


# ── Journalisation ──────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}
