"""
Excepciones de negocio para DESS
Errores relacionados con reglas de negocio y validaciones de dominio
"""
from typing import Dict, List, Optional, Any


class DESSBusinessException(Exception):
    """
    Excepción base para errores de lógica de negocio.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir excepción a diccionario para APIs"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(DESSBusinessException):
    """
    Error de validación de datos de entrada.
    """
    
    def __init__(self, message: str = "Datos de entrada no válidos", 
                 field_errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field_errors = field_errors or {}
        self.details = {'field_errors': self.field_errors}
    
    def add_field_error(self, field: str, error: str) -> None:
        """Agregar error específico de campo"""
        if field not in self.field_errors:
            self.field_errors[field] = []
        self.field_errors[field].append(error)
        self.details['field_errors'] = self.field_errors


class UserNotFoundError(DESSBusinessException):
    """
    Error cuando un usuario no existe.
    """
    
    def __init__(self, user_identifier: str):
        message = f"Usuario '{user_identifier}' no encontrado"
        super().__init__(message, "USER_NOT_FOUND")
        self.details = {'user_identifier': user_identifier}


class SolutionNotFoundError(DESSBusinessException):
    """
    Error cuando una solución no existe.
    """
    
    def __init__(self, solution_identifier: str):
        message = f"Solución '{solution_identifier}' no encontrada"
        super().__init__(message, "SOLUTION_NOT_FOUND")
        self.details = {'solution_identifier': solution_identifier}


class InvalidPermissionsError(DESSBusinessException):
    """
    Error de permisos insuficientes.
    """
    
    def __init__(self, required_permission: str, user_id: Optional[int] = None):
        message = f"Permisos insuficientes. Se requiere: {required_permission}"
        super().__init__(message, "INSUFFICIENT_PERMISSIONS")
        self.details = {
            'required_permission': required_permission,
            'user_id': user_id
        }


class AssignmentError(DESSBusinessException):
    """
    Error en asignación de soluciones a usuarios.
    """
    
    def __init__(self, message: str, user_id: Optional[int] = None, solution_id: Optional[int] = None):
        super().__init__(message, "ASSIGNMENT_ERROR")
        self.details = {
            'user_id': user_id,
            'solution_id': solution_id
        }


class BusinessRuleViolationError(DESSBusinessException):
    """
    Error cuando se viola una regla de negocio.
    """
    
    def __init__(self, rule_name: str, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")
        self.rule_name = rule_name
        self.details = {
            'rule_name': rule_name,
            'context': context or {}
        }


class ConcurrencyError(DESSBusinessException):
    """
    Error de concurrencia en operaciones simultáneas.
    """
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"Conflicto de concurrencia en {resource_type} con ID {resource_id}"
        super().__init__(message, "CONCURRENCY_ERROR")
        self.details = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }


class QuotaExceededError(DESSBusinessException):
    """
    Error cuando se excede una cuota o límite.
    """
    
    def __init__(self, quota_type: str, current_value: int, max_value: int):
        message = f"Cuota excedida para {quota_type}: {current_value}/{max_value}"
        super().__init__(message, "QUOTA_EXCEEDED")
        self.details = {
            'quota_type': quota_type,
            'current_value': current_value,
            'max_value': max_value
        }


class StateTransitionError(DESSBusinessException):
    """
    Error en transición de estados inválida.
    """
    
    def __init__(self, from_state: str, to_state: str, entity_type: str):
        message = f"Transición de estado inválida en {entity_type}: {from_state} -> {to_state}"
        super().__init__(message, "INVALID_STATE_TRANSITION")
        self.details = {
            'from_state': from_state,
            'to_state': to_state,
            'entity_type': entity_type
        }