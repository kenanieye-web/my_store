"""
Django settings for my_store project.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ===== حماية البيانات (الموقع الحي) =====
# مجلد البيانات الحية: خارج مجلد المشروع، فلا يلمسه git pull ولا git stash ولا git clean.
# هذا المجلد موجود على PythonAnywhere فقط، وغير موجود على جهازك المحلي،
# لذلك يعمل الكود تلقائياً بشكل صحيح في الحالتين بدون أي متغيرات بيئة
# (ويعمل في الطرفية Console والـ WSGI والمهام المجدولة بنفس الطريقة).
LIVE_DATA_DIR = Path('/home/Kenan2026/data')
ON_LIVE_SERVER = LIVE_DATA_DIR.is_dir()


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-local-dev-only-CHANGE-ME')

# القيمة الافتراضية True (مريحة للتطوير المحلي)، ونجبرها False على الموقع الحي عبر متغير بيئة
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['kenan2026.pythonanywhere.com', 'localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'shop',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_store.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # تمكين الميديا داخل القوالب
                'shop.context_processors.nav_categories',
                'shop.context_processors.cart_summary',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_store.wsgi.application'


# Database (SQLite)
# - على الموقع الحي: /home/Kenan2026/data/db.sqlite3  (خارج المشروع وخارج Git)
# - على جهازك المحلي: BASE_DIR / 'db.sqlite3'
# - يمكن تجاوز المسار بمتغير البيئة DJANGO_DB_PATH عند الحاجة.
_db_override = os.environ.get('DJANGO_DB_PATH')
if _db_override:
    DB_PATH = Path(_db_override)
elif ON_LIVE_SERVER:
    DB_PATH = LIVE_DATA_DIR / 'db.sqlite3'
else:
    DB_PATH = BASE_DIR / 'db.sqlite3'

# حماية أساسية: على الموقع الحي لا نسمح أبداً بإنشاء قاعدة فارغة جديدة بصمت
# (هذا ما يحدث عندما يفقد المشروع ملف القاعدة ثم يشغَّل migrate).
if ON_LIVE_SERVER and not DB_PATH.exists():
    raise ImproperlyConfigured(
        f'ملف قاعدة البيانات غير موجود: {DB_PATH} . '
        'تم إيقاف المشروع عمداً حتى لا تُنشأ قاعدة فارغة. '
        'استعد الملف من ~/backups ثم أعد المحاولة.'
    )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
    }
}

# نوع المفاتيح الأساسية الافتراضي (نفس النوع المستخدم حالياً؛ يُسكت تحذيرات W042 دون أي migration)
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'ar'

TIME_ZONE = 'Asia/Aden'

USE_I18N = True

USE_TZ = True
USE_L10N = False
DECIMAL_SEPARATOR = '.'
THOUSAND_SEPARATOR = ','
USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'shop/static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (Uploaded by user)
# اختياري: عندما تنقل الصور إلى /home/Kenan2026/data/media يستخدمها الموقع تلقائياً.
# (غيّر أيضاً مسار /media/ في تبويب Web > Static files إلى /home/Kenan2026/data/media)
# وقبل ذلك (إن لم يوجد ذلك المجلد) تبقى الصور في BASE_DIR / 'media' كما هي الآن.
MEDIA_URL = '/media/'
if (LIVE_DATA_DIR / 'media').is_dir():
    MEDIA_ROOT = LIVE_DATA_DIR / 'media'
else:
    MEDIA_ROOT = BASE_DIR / 'media'


# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# حماية النطاق والسماح بطلب الدخول عبر بروتوكول الآمان والنطاق الخاص بك
CSRF_TRUSTED_ORIGINS = ['https://kenan2026.pythonanywhere.com']
AUTH_USER_MODEL = 'shop.CustomUser'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ===== واجهة API لتطبيق الجوال =====
CORS_ALLOW_ALL_ORIGINS = DEBUG  # مفتوح محلياً فقط ومغلق على الموقع الحي

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/min', 'user': '200/min'},
}