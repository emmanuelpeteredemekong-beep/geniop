import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# BASE_DIR = root folder where manage.py lives
# geniop/geniop/settings.py -> parent.parent.parent = root (geniop/../)
# Fixed for phone build: was parent.parent before, now correct
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY
# Secret key from .env, fallback for local
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# DEBUG True for phone dev, False in production on Render
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allow all hosts for now, Render will set specific host via .env
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# APPLICATION DEFINITION
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps - our Geniop apps
    'home',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise for serving static files on Render - must be after SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geniop.urls'

# TEMPLATES CONFIG
# DIRS checks root/templates and geniop/templates for index.html
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # root/templates/home/index.html
            BASE_DIR / 'geniop' / 'templates',  # fallback if inside geniop
        ],
        'APP_DIRS': True,  # Also check home/templates/ etc
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'geniop.wsgi.application'

# DATABASE - SQLite for phone dev
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override with DATABASE_URL if exists (for Render PostgreSQL)
# This makes it auto switch to Postgres on Render
if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# STATIC FILES - CSS, JS, Images for Geniop UI
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Where Render collects static
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA FILES - User uploads (lesson plans etc)
MEDIA_URL = '/media/' 
MEDIA_ROOT = BASE_DIR / 'media'

# DEFAULT FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGIN SETTINGS
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email - console for now, SMTP later
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Later for real email, we change to SMTP
