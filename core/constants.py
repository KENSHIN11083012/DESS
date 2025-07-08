"""
DESS - Constantes del Sistema
Centralización de valores para evitar magic numbers y hardcoded values
"""

# Constantes de validación
class ValidationConstants:
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 150
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MIN_FULL_NAME_LENGTH = 2
    MAX_FULL_NAME_LENGTH = 200
    MIN_SOLUTION_NAME_LENGTH = 3
    MAX_SOLUTION_NAME_LENGTH = 100
    MIN_SOLUTION_DESCRIPTION_LENGTH = 10
    MAX_SOLUTION_DESCRIPTION_LENGTH = 1000

# Constantes de UI/UX
class UIConstants:
    NOTIFICATION_DURATION_MS = 3000
    ALERT_AUTO_HIDE_DURATION_MS = 5000
    MODAL_TRANSITION_DURATION_MS = 300
    SEARCH_DEBOUNCE_DELAY_MS = 500
    REDIRECT_DELAY_MS = 1500

# Constantes de red
class NetworkConstants:
    AJAX_TIMEOUT_MS = 10000
    DEFAULT_PAGE_SIZE = 20
    MAX_UPLOAD_SIZE_MB = 10

# Constantes de sistema
class SystemConstants:
    DEFAULT_LANGUAGE = 'es'
    DEFAULT_TIMEZONE = 'UTC'
    LOG_LEVEL_DEBUG = 'DEBUG'
    LOG_LEVEL_INFO = 'INFO'
    LOG_LEVEL_WARNING = 'WARNING'
    LOG_LEVEL_ERROR = 'ERROR'

# Constantes de base de datos
class DatabaseConstants:
    DEFAULT_CHARSET = 'utf8mb4'
    CONNECTION_TIMEOUT = 30
    QUERY_TIMEOUT = 60

# Constantes de seguridad
class SecurityConstants:
    SESSION_TIMEOUT_MINUTES = 30
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24

# Constantes de archivos
class FileConstants:
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx']
    MAX_FILENAME_LENGTH = 255

# Constantes de API
class APIConstants:
    API_VERSION = 'v1'
    DEFAULT_FORMAT = 'json'
    MAX_RESULTS_PER_PAGE = 100

# Constantes de cache
class CacheConstants:
    DEFAULT_CACHE_TIMEOUT = 300  # 5 minutos
    LONG_CACHE_TIMEOUT = 3600   # 1 hora
    SHORT_CACHE_TIMEOUT = 60    # 1 minuto
