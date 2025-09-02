"""
Decoradores para validación automática de entrada
"""
import functools
import logging
from typing import Callable, Dict, List, Any, Optional, Type
from django.http import JsonResponse
from django.shortcuts import render
from .validators import BaseValidator, InputSanitizer
from ..exceptions.business_exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_input(validator_class: Type[BaseValidator], 
                  validation_method: str,
                  fields_mapping: Optional[Dict[str, str]] = None):
    """
    Decorador para validación automática de entrada en vistas.
    
    Args:
        validator_class: Clase del validador a usar
        validation_method: Nombre del método de validación a ejecutar
        fields_mapping: Mapeo de nombres de campos entre request y validador
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Crear instancia del validador
                validator = validator_class()
                
                # Obtener datos del request
                data = _extract_request_data(request)
                
                # Mapear campos si es necesario
                if fields_mapping:
                    data = {fields_mapping.get(k, k): v for k, v in data.items()}
                
                # Ejecutar validación
                validation_func = getattr(validator, validation_method)
                is_valid = validation_func(**data)
                
                if not is_valid:
                    return _handle_validation_error(request, validator.get_errors())
                
                # Si todo está bien, continuar con la vista
                return view_func(request, *args, **kwargs)
                
            except ValidationError as e:
                return _handle_validation_error(request, e.field_errors)
            except Exception as e:
                logger.error(f"Error in validation decorator: {e}", exc_info=True)
                return _handle_unexpected_error(request)
        
        return wrapper
    return decorator


def sanitize_input(fields: List[str], 
                  html_fields: Optional[List[str]] = None,
                  sql_fields: Optional[List[str]] = None,
                  max_lengths: Optional[Dict[str, int]] = None):
    """
    Decorador para sanitización automática de entrada.
    
    Args:
        fields: Campos a sanitizar básicamente
        html_fields: Campos que requieren sanitización HTML
        sql_fields: Campos que requieren sanitización SQL
        max_lengths: Longitudes máximas por campo
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Sanitizar campos según tipo
                _sanitize_request_data(
                    request, fields, html_fields, sql_fields, max_lengths
                )
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in sanitization decorator: {e}", exc_info=True)
                return _handle_unexpected_error(request)
        
        return wrapper
    return decorator


def validate_user_creation(view_func: Callable) -> Callable:
    """Decorador específico para validación de creación de usuarios"""
    from .validators import UserValidator
    
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            data = _extract_request_data(request)
            validator = UserValidator()
            
            required_fields = ['username', 'email', 'full_name', 'password', 'role']
            if not all(field in data for field in required_fields):
                missing = [f for f in required_fields if f not in data]
                return _handle_validation_error(
                    request, 
                    {'missing_fields': [f'Campos requeridos faltantes: {", ".join(missing)}']}
                )
            
            is_valid = validator.validate_create_user(
                data['username'], data['email'], data['full_name'], 
                data['password'], data['role']
            )
            
            if not is_valid:
                return _handle_validation_error(request, validator.get_errors())
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validate_solution_creation(view_func: Callable) -> Callable:
    """Decorador específico para validación de creación de soluciones"""
    from .validators import SolutionValidator
    
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            data = _extract_request_data(request)
            validator = SolutionValidator()
            
            required_fields = ['name', 'description', 'repository_url', 'solution_type', 'version']
            if not all(field in data for field in required_fields):
                missing = [f for f in required_fields if f not in data]
                return _handle_validation_error(
                    request,
                    {'missing_fields': [f'Campos requeridos faltantes: {", ".join(missing)}']}
                )
            
            is_valid = validator.validate_create_solution(
                data['name'], data['description'], data['repository_url'],
                data['solution_type'], data['version'], data.get('access_url')
            )
            
            if not is_valid:
                return _handle_validation_error(request, validator.get_errors())
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def _extract_request_data(request) -> Dict[str, Any]:
    """Extraer datos del request de forma segura"""
    if request.method == 'GET':
        return dict(request.GET)
    elif request.method == 'POST':
        data = dict(request.POST)
        # Convertir listas de un elemento a string
        return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}
    return {}


def _sanitize_request_data(request, fields: List[str], 
                          html_fields: Optional[List[str]] = None,
                          sql_fields: Optional[List[str]] = None,
                          max_lengths: Optional[Dict[str, int]] = None) -> None:
    """Sanitizar datos del request in-place"""
    html_fields = html_fields or []
    sql_fields = sql_fields or []
    max_lengths = max_lengths or {}
    
    # Sanitizar POST data
    if hasattr(request, '_post') and request._post:
        for field in fields:
            if field in request.POST:
                value = request.POST[field]
                
                # Sanitización básica
                sanitized = InputSanitizer.sanitize_string(value, max_lengths.get(field))
                
                # Sanitización específica
                if field in html_fields:
                    sanitized = InputSanitizer.sanitize_html_input(sanitized)
                if field in sql_fields:
                    sanitized = InputSanitizer.sanitize_sql_input(sanitized)
                
                # Actualizar el valor
                request.POST._mutable = True
                request.POST[field] = sanitized
                request.POST._mutable = False
    
    # Sanitizar GET data
    if hasattr(request, '_get') and request._get:
        for field in fields:
            if field in request.GET:
                value = request.GET[field]
                sanitized = InputSanitizer.sanitize_string(value, max_lengths.get(field))
                
                request.GET._mutable = True
                request.GET[field] = sanitized
                request.GET._mutable = False


def _handle_validation_error(request, field_errors: Dict[str, List[str]]) -> JsonResponse:
    """Manejar errores de validación"""
    # Para requests AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos de entrada no válidos',
            'field_errors': field_errors
        }, status=400)
    
    # Para requests normales, renderizar página con errores
    context = {
        'validation_errors': field_errors,
        'error_message': 'Por favor corrige los errores y vuelve a intentar'
    }
    
    return render(request, 'errors/validation_error.html', context, status=400)


def _handle_unexpected_error(request) -> JsonResponse:
    """Manejar errores inesperados en decoradores"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno durante la validación'
        }, status=500)
    
    return render(request, 'errors/500.html', status=500)