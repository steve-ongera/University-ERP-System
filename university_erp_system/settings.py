import os
from decouple import config
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8t&4cf+i%o&wfj)e99da5^41o2^1(8c_tg9jjcw*-69z%lg#7o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'whitenoise.runserver_nostatic',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'core_application',
]

SITE_ID = 1 

AUTH_USER_MODEL='core_application.User'

CSRF_TRUSTED_ORIGINS = [
    "https://6493f9542099.ngrok-free.app"
]
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000  # or a higher number as needed


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core_application.middleware.UserSessionMiddleware',  
    'core_application.middleware.ActivityTrackingMiddleware',
    'core_application.middleware.BankWebhookIPWhitelistMiddleware',

    # Add custom security  middleware
    'core_application.middleware.SecurityAuditMiddleware',
    'core_application.middleware.DeletionControlMiddleware',
    #'core_application.signals.AuditMiddleware',  # For tracking user in signals

]

# Backup Settings
MAX_BACKUPS = 30  # Keep last 30 backups
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

ROOT_URLCONF = 'university_erp_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'university_erp_system.wsgi.application'

CSRF_COOKIE_HTTPONLY = False
# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'  # Kenya timezone

USE_I18N = True

USE_TZ = True

# Redirect URLs
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# STATIC FILES CONFIG
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # for development
STATIC_ROOT = BASE_DIR / 'staticfiles'    # for production (collected files)


# MEDIA FILES CONFIG
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# For WhiteNoise compression support (optional)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

WKHTMLTOPDF_CMD = r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# University Information
UNIVERSITY_NAME = "MURANGA UNIVERSITY OF TECHNOLOGY"
UNIVERSITY_ADDRESS = "Muranga Town 351, Kiambu, Kenya"
UNIVERSITY_CONTACT = "Tel: +254-763-7474893 | Email: finance@mutuniversity.edu"

# Logo (static or media path)
# Example if stored in static/
LOGO_URL = "/static/logo.png"


# ============ BANK API CREDENTIALS ============
# Equity Bank Configuration
EQUITY_BANK_API_URL = 'https://api.equitybank.co.ke/v1/'
EQUITY_BANK_API_KEY = 'your_equity_api_key'
EQUITY_BANK_SECRET_KEY = 'your_equity_secret_key'
EQUITY_BANK_MERCHANT_CODE = 'MUT001'

# KCB Bank Configuration
KCB_BANK_API_URL = 'https://api.kcbgroup.com/v1/'
KCB_BANK_API_KEY = 'your_kcb_api_key'
KCB_BANK_SECRET_KEY = 'your_kcb_secret_key'
KCB_BANK_MERCHANT_CODE = 'MUT002'

# M-Pesa Configuration
MPESA_ENVIRONMENT = 'sandbox'  # or 'production'
MPESA_CONSUMER_KEY = 'your_mpesa_consumer_key'
MPESA_CONSUMER_SECRET = 'your_mpesa_consumer_secret'
MPESA_SHORTCODE = '174379'  # Your paybill number
MPESA_PASSKEY = 'your_mpesa_passkey'
MPESA_CALLBACK_URL = 'https://youruniversity.ac.ke/api/payments/mpesa/callback/'

# ============ SMS CONFIGURATION ============
# Using Africa's Talking (https://africastalking.com)
AT_USERNAME = 'MurangaUniversity'
AT_API_KEY = 'your_africastalking_api_key'
AT_SENDER_ID = 'MUT'

# ============ PAYMENT SETTINGS ============
PAYMENT_WEBHOOK_IPS = [
    '41.90.x.x',  # Equity Bank IP
    '105.x.x.x',  # KCB Bank IP
    # Add bank IP addresses for security
]

# Email settings for security alerts
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="University Security System <security@yourdomain.com>"
)

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session security
SESSION_COOKIE_SECURE =  False  # Set to True only if using HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/admin_security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'your_app.views': {  # Replace with your app name
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

