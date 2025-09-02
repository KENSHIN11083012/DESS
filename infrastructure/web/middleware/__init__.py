"""
Middleware de DESS - Estructura modular
"""

# Importar middlewares principales
from .interface_unify import UnifyInterfacesMiddleware
from .api_logging import APILoggingMiddleware  
from .security_headers import SecurityHeadersMiddleware

__all__ = [
    'UnifyInterfacesMiddleware',
    'APILoggingMiddleware', 
    'SecurityHeadersMiddleware',
]