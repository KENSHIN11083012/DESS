import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='dess-dev-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver,*').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
]

LOCAL_APPS = [
    'infrastructure.web',
    'infrastructure.database',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    # 1. Middleware de seguridad (primero para eficiencia)
    'django.middleware.security.SecurityMiddleware',
    
    # 2. WhiteNoise para servir archivos estáticos (después de SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    # 3. Middleware de sesiones (requerido antes de auth)
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # 4. CORS (debe estar temprano para preflight requests)
    'corsheaders.middleware.CorsMiddleware',
    
    # 5. Middleware común (análisis de URLs)
    'django.middleware.common.CommonMiddleware',
    
    # 6. CSRF (después de sesiones, antes de auth)
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # 7. Autenticación (requerido para middlewares personalizados)
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # 8. Middleware de unificación DESS (requiere auth)
    'infrastructure.web.middleware.interface_unify.UnifyInterfacesMiddleware',
    
    # 9. Mensajes (después de auth para mostrar mensajes)
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # 10. Logging de APIs (para monitoreo)
    'infrastructure.web.middleware.api_logging.APILoggingMiddleware',
    
    # 11. Headers de seguridad adicionales (antes de clickjacking)
    'infrastructure.web.middleware.security_headers.SecurityHeadersMiddleware',
    
    # 12. Clickjacking (al final para no interferir)
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
from .database_config import get_database_config

DATABASES = get_database_config()

# ============================================================================
# USER MODEL CONFIGURATION
# ============================================================================

AUTH_USER_MODEL = 'database.DESSUser'

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

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ]
}

# JWT Configuration - Optimizada para DESS
from datetime import timedelta
SIMPLE_JWT = {
    # Tiempos de vida de tokens optimizados
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),  # Reducido para mayor seguridad
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Extendido para mejor UX
    'ROTATE_REFRESH_TOKENS': True,  # Seguridad adicional
    'BLACKLIST_AFTER_ROTATION': True,  # Previene reuso de tokens
    
    # Configuración de seguridad
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': 'dess-api',  # Identificador específico de DESS
    'ISSUER': 'dess-auth-service',  # Emisor específico
    
    # Headers personalizados
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Configuración de claims
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    
    # Configuración avanzada
    'UPDATE_LAST_LOGIN': True,  # Actualizar último login para auditoría
    'LEEWAY': 10,  # 10 segundos de tolerancia para clock skew
    
    # Sliding tokens (opcional)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=8),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=30),
}

# Spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'DESS API',
    'DESCRIPTION': 'Desarrollador de Ecosistemas de Soluciones Empresariales',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Configuración de Cache optimizada para DESS
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dess-cache',
        'TIMEOUT': 300,  # 5 minutos por defecto
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    },
    'permissions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 
        'LOCATION': 'dess-perms-cache',
        'TIMEOUT': 600,  # 10 minutos para permisos
        'OPTIONS': {
            'MAX_ENTRIES': 500,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Configuración específica de caché de permisos
PERMISSION_CACHE_TIMEOUT = 600  # 10 minutos
PERMISSION_CACHE_BACKEND = 'permissions'

# Configuración de Logging optimizada para DESS
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname:8} {name} {module}.{funcName}:{lineno} | {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname:8} {name} | {message}',
            'style': '{',
        },
        'json': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console_dev': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_prod': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'application_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'application.log',
            'maxBytes': 1024 * 1024 * 20,  # 20MB
            'backupCount': 15,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 30,
            'formatter': 'json',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'performance.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 30,
            'formatter': 'json',
        },
    },
    'loggers': {
        # Django core
        'django': {
            'handlers': ['console_dev', 'console_prod', 'application_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['application_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # DESS Application
        'core': {
            'handlers': ['console_dev', 'console_prod', 'application_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'application': {
            'handlers': ['console_dev', 'console_prod', 'application_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'infrastructure': {
            'handlers': ['console_dev', 'console_prod', 'application_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Loggers especializados
        'dess.security': {
            'handlers': ['security_file', 'console_prod'],
            'level': 'INFO',
            'propagate': False,
        },
        'dess.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'dess.audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Root logger para toda la aplicación DESS
        '': {
            'handlers': ['console_dev', 'console_prod', 'application_file'],
            'level': 'INFO',
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ============================================================================
# WHITENOISE CONFIGURATION - Archivos estáticos en producción
# ============================================================================

# Configuración de WhiteNoise para servir archivos estáticos
WHITENOISE_USE_FINDERS = True  # Habilita uso de staticfiles finders
WHITENOISE_AUTOREFRESH = True  # Auto-refresh en desarrollo
WHITENOISE_MAX_AGE = 31536000  # Cache por 1 año (en segundos)

# Compresión de archivos estáticos
WHITENOISE_USE_FINDERS = True
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

# Configurar mimetypes correctos para archivos CSS/JS
import mimetypes
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("application/javascript", ".js", True)