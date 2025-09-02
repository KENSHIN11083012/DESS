"""
Excepciones de infraestructura para DESS
Errores relacionados con servicios externos, base de datos, etc.
"""
from typing import Dict, Optional, Any


class DESSInfrastructureException(Exception):
    """
    Excepción base para errores de infraestructura.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir excepción a diccionario para APIs"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details,
            'cause': str(self.cause) if self.cause else None
        }


class DatabaseConnectionError(DESSInfrastructureException):
    """
    Error de conexión a la base de datos.
    """
    
    def __init__(self, database_name: str, cause: Optional[Exception] = None):
        message = f"Error conectando a la base de datos: {database_name}"
        super().__init__(message, "DATABASE_CONNECTION_ERROR", 
                        {'database_name': database_name}, cause)


class DatabaseQueryError(DESSInfrastructureException):
    """
    Error en consulta de base de datos.
    """
    
    def __init__(self, query: str, cause: Optional[Exception] = None):
        message = "Error ejecutando consulta de base de datos"
        super().__init__(message, "DATABASE_QUERY_ERROR", 
                        {'query': query[:200] + '...' if len(query) > 200 else query}, cause)


class CacheError(DESSInfrastructureException):
    """
    Error en sistema de caché.
    """
    
    def __init__(self, operation: str, cache_key: Optional[str] = None, cause: Optional[Exception] = None):
        message = f"Error en operación de caché: {operation}"
        super().__init__(message, "CACHE_ERROR", 
                        {'operation': operation, 'cache_key': cache_key}, cause)


class ExternalServiceError(DESSInfrastructureException):
    """
    Error comunicándose con servicio externo.
    """
    
    def __init__(self, service_name: str, status_code: Optional[int] = None, 
                 response_body: Optional[str] = None, cause: Optional[Exception] = None):
        message = f"Error comunicándose con {service_name}"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", {
            'service_name': service_name,
            'status_code': status_code,
            'response_body': response_body[:500] + '...' if response_body and len(response_body) > 500 else response_body
        }, cause)


class FileSystemError(DESSInfrastructureException):
    """
    Error en operaciones de sistema de archivos.
    """
    
    def __init__(self, operation: str, file_path: str, cause: Optional[Exception] = None):
        message = f"Error en operación de archivo: {operation}"
        super().__init__(message, "FILESYSTEM_ERROR", 
                        {'operation': operation, 'file_path': file_path}, cause)


class ConfigurationError(DESSInfrastructureException):
    """
    Error en configuración del sistema.
    """
    
    def __init__(self, config_key: str, expected_type: Optional[str] = None):
        message = f"Error en configuración: {config_key}"
        super().__init__(message, "CONFIGURATION_ERROR", {
            'config_key': config_key,
            'expected_type': expected_type
        })


class NetworkError(DESSInfrastructureException):
    """
    Error de red o conectividad.
    """
    
    def __init__(self, endpoint: str, timeout: Optional[float] = None, cause: Optional[Exception] = None):
        message = f"Error de red conectando a: {endpoint}"
        super().__init__(message, "NETWORK_ERROR", 
                        {'endpoint': endpoint, 'timeout': timeout}, cause)


class AuthenticationError(DESSInfrastructureException):
    """
    Error de autenticación con servicios externos.
    """
    
    def __init__(self, service_name: str, auth_method: Optional[str] = None):
        message = f"Error de autenticación con {service_name}"
        super().__init__(message, "AUTHENTICATION_ERROR", {
            'service_name': service_name,
            'auth_method': auth_method
        })


class RateLimitExceededError(DESSInfrastructureException):
    """
    Error cuando se excede límite de velocidad de API externa.
    """
    
    def __init__(self, service_name: str, limit: int, reset_time: Optional[int] = None):
        message = f"Límite de velocidad excedido para {service_name}"
        super().__init__(message, "RATE_LIMIT_EXCEEDED", {
            'service_name': service_name,
            'limit': limit,
            'reset_time': reset_time
        })