"""
Sistema de excepciones personalizado para DESS
"""
from .business_exceptions import (
    DESSBusinessException,
    UserNotFoundError,
    SolutionNotFoundError,
    InvalidPermissionsError,
    ValidationError,
    AssignmentError
)
from .infrastructure_exceptions import (
    DESSInfrastructureException,
    DatabaseConnectionError,
    CacheError,
    ExternalServiceError
)
from .handlers import exception_handler, validation_error_handler

__all__ = [
    # Business exceptions
    'DESSBusinessException',
    'UserNotFoundError',
    'SolutionNotFoundError', 
    'InvalidPermissionsError',
    'ValidationError',
    'AssignmentError',
    
    # Infrastructure exceptions
    'DESSInfrastructureException',
    'DatabaseConnectionError',
    'CacheError',
    'ExternalServiceError',
    
    # Handlers
    'exception_handler',
    'validation_error_handler',
]