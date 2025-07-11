import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key-here-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_extensions',
    
    # Local apps
    'authentication',
    # 'employees',
    'pointage',
    'leaves',
    'departments',
    'employees.apps.EmployeesConfig',  # UNE SEULE fois
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

ROOT_URLCONF = 'systeme_pointage.urls'
# AUTH_USER_MODEL = 'employees.Employee'
AUTH_USER_MODEL = 'authentication.Authentication'
# # Custom User Model
# AUTH_USER_MODEL = 'authentication.Employee'


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
            ],
        },
    },
]

WSGI_APPLICATION = 'systeme_pointage.wsgi.application'


# Alternative PostgreSQL configuration (uncomment if needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pointage_db',
        'USER': 'postgres',
        'PASSWORD': 'andry[1234]',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# EMAIL CONFIGURATION
# Option 1 : console.EmailBackend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Option 2 : smtp.EmailBackend (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465                           
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ravintsoandraibeandrianiaina@gmail.com'
EMAIL_HOST_PASSWORD = 'andry[1234]'
DEFAULT_FROM_EMAIL = 'ravintsoandraibeandrianiaina@gmail.com'


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Indian/Antananarivo'  # Madagascar timezone

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
         'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue dev server
    "http://127.0.0.1:8080",
    "http://localhost:4200",  # Angular dev server
    "http://127.0.0.1:4200",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only in development

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Face Recognition Settings
FACE_RECOGNITION_SETTINGS = {
    'ENCODINGS_FILE': os.path.join(MEDIA_ROOT, 'face_encodings.pkl'),
    'TOLERANCE': 800.0,  # Seuil pour MediaPipe (distance euclidienne)
    'MAX_IMAGE_SIZE': 800,  # Taille maximale de l'image en pixels
    'MIN_FACE_SIZE': 100,   # Taille minimale du visage détecté
    'DETECTION_CONFIDENCE': 0.5,  # Confiance minimale pour la détection
    'RECOGNITION_CONFIDENCE': 0.7,  # Confiance minimale pour la reconnaissance
}

# Seuil de reconnaissance faciale (pour compatibilité)
FACE_RECOGNITION_THRESHOLD = 0.6

# Répertoires pour les fichiers de reconnaissance faciale
FACE_IMAGES_DIR = os.path.join(MEDIA_ROOT, 'face_images')
BIOMETRIC_DATA_DIR = os.path.join(MEDIA_ROOT, 'biometric_data')

# Configuration du système de pointage
ATTENDANCE_SETTINGS = {
    'WORK_START_TIME': '08:00',  # Heure de début de travail
    'WORK_END_TIME': '17:00',    # Heure de fin de travail
    'LUNCH_START_TIME': '12:00', # Début de pause déjeuner
    'LUNCH_END_TIME': '13:00',   # Fin de pause déjeuner
    'LATE_THRESHOLD_MINUTES': 15,  # Minutes de retard tolérées
    'OVERTIME_THRESHOLD_MINUTES': 30,  # Minutes supplémentaires pour overtime
    'MAX_DAILY_HOURS': 10,       # Heures maximales par jour
    'WEEKEND_DAYS': [5, 6],      # Samedi et Dimanche (0=Lundi)
}

# Configuration de géolocalisation (optionnel)
GEOLOCATION_SETTINGS = {
    'ENABLED': False,  # Activer la vérification de géolocalisation
    'OFFICE_LATITUDE': -18.8792,   # Latitude du bureau (Antananarivo)
    'OFFICE_LONGITUDE': 47.5079,   # Longitude du bureau
    'ALLOWED_RADIUS_METERS': 100,  # Rayon autorisé en mètres
}

# Configuration des notifications (optionnel)
NOTIFICATION_SETTINGS = {
    'EMAIL_ENABLED': False,
    'SMS_ENABLED': False,
    'PUSH_ENABLED': False,
}

# Configuration de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'face_recognition_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'face_recognition.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'utils.face_recognition_utils': {
            'handlers': ['face_recognition_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'authentication.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'attendance.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configuration de sécurité pour la production
if not DEBUG:
    # HTTPS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Headers de sécurité
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Configuration des emails (à configurer selon vos besoins)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Pour développement

# Pour production avec Gmail:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
# DEFAULT_FROM_EMAIL = 'your-email@gmail.com'

# Configuration du cache (optionnel)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuration de session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_SAVE_EVERY_REQUEST = True

# Créer les répertoires nécessaires
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)
os.makedirs(BIOMETRIC_DATA_DIR, exist_ok=True)
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(BASE_DIR / 'staticfiles', exist_ok=True)

# Variables d'environnement pour la production
# Vous pouvez créer un fichier .env pour ces valeurs
try:
    from .local_settings import *
except ImportError:
    pass