"""
Manejadores globales de excepciones para DESS
"""
import logging
from typing import Dict, Any
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.defaults import server_error, page_not_found, permission_denied, bad_request
from .business_exceptions import DESSBusinessException, ValidationError
from .infrastructure_exceptions import DESSInfrastructureException

# Loggers especializados
security_logger = logging.getLogger('dess.security')
performance_logger = logging.getLogger('dess.performance')
audit_logger = logging.getLogger('dess.audit')
logger = logging.getLogger(__name__)


def exception_handler(get_response):
    """
    Middleware global de manejo de excepciones.
    """
    def middleware(request):
        try:
            response = get_response(request)
        except DESSBusinessException as e:
            return handle_business_exception(request, e)
        except DESSInfrastructureException as e:
            return handle_infrastructure_exception(request, e)
        except Exception as e:
            return handle_unexpected_exception(request, e)
        
        return response
    
    return middleware


def handle_business_exception(request, exception: DESSBusinessException) -> HttpResponse:
    """
    Manejar excepciones de lógica de negocio.
    """
    # Log de la excepción
    logger.warning(f"Business exception: {exception.error_code} - {exception.message}", 
                  extra={'details': exception.details, 'user': getattr(request.user, 'username', 'anonymous')})
    
    # Si es una request AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': exception.error_code,
            'message': exception.message,
            'details': exception.details
        }, status=400)
    
    # Para requests normales, mostrar página de error
    context = {
        'error_type': 'Error de Validación',
        'error_message': exception.message,
        'error_details': exception.details if hasattr(exception, 'field_errors') else None
    }
    
    return render(request, 'errors/business_error.html', context, status=400)


def handle_infrastructure_exception(request, exception: DESSInfrastructureException) -> HttpResponse:
    """
    Manejar excepciones de infraestructura.
    """
    # Log crítico para infraestructura
    logger.error(f"Infrastructure exception: {exception.error_code} - {exception.message}", 
                extra={'details': exception.details, 'cause': str(exception.cause)}, 
                exc_info=True)
    
    # Notificar a sistemas de monitoreo
    _notify_monitoring_system(exception)
    
    # Respuesta genérica para no exponer detalles internos
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'Error interno del servidor. Por favor, intenta más tarde.'
        }, status=500)
    
    return render(request, 'errors/server_error.html', {
        'error_message': 'Error interno del servidor. Nuestro equipo ha sido notificado.'
    }, status=500)


def handle_unexpected_exception(request, exception: Exception) -> HttpResponse:
    """
    Manejar excepciones no controladas.
    """
    # Log crítico con stack trace completo
    logger.critical(f"Unexpected exception: {type(exception).__name__} - {str(exception)}", 
                   exc_info=True, 
                   extra={'user': getattr(request.user, 'username', 'anonymous')})
    
    # Audit log para excepciones críticas
    audit_logger.error(f"Critical system error", extra={
        'event': 'unexpected_exception',
        'exception_type': type(exception).__name__,
        'user': getattr(request.user, 'username', 'anonymous'),
        'path': request.path,
        'method': request.method
    })
    
    # Notificar sistemas críticos
    _notify_critical_error(exception, request)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'CRITICAL_ERROR',
            'message': 'Error crítico del sistema'
        }, status=500)
    
    return render(request, 'errors/critical_error.html', status=500)


def validation_error_handler(validation_error: ValidationError) -> Dict[str, Any]:
    """
    Handler especializado para errores de validación.
    """
    return {
        'success': False,
        'error': 'VALIDATION_ERROR',
        'message': validation_error.message,
        'field_errors': validation_error.field_errors
    }


def api_exception_handler(request, exception):
    """
    Handler específico para APIs REST.
    """
    if isinstance(exception, DESSBusinessException):
        status_code = 400 if exception.error_code != 'USER_NOT_FOUND' else 404
        return JsonResponse(exception.to_dict(), status=status_code)
    
    elif isinstance(exception, DESSInfrastructureException):
        logger.error(f"API Infrastructure error: {exception}", exc_info=True)
        return JsonResponse({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'Error interno del servidor'
        }, status=500)
    
    else:
        logger.critical(f"API Critical error: {exception}", exc_info=True)
        return JsonResponse({
            'error': 'CRITICAL_ERROR',
            'message': 'Error crítico del sistema'
        }, status=500)


def _notify_monitoring_system(exception: DESSInfrastructureException):
    """
    Notificar a sistemas de monitoreo (placeholder).
    """
    # TODO: Integrar con sistemas de monitoreo como Sentry, DataDog, etc.
    logger.info(f"Notifying monitoring system about: {exception.error_code}")


def _notify_critical_error(exception: Exception, request):
    """
    Notificar errores críticos a sistemas de alerta.
    """
    # TODO: Integrar con sistemas de alertas críticas
    logger.critical(f"Critical error notification sent for: {type(exception).__name__}")


# Handlers para errores HTTP estándar de Django
def custom_404_handler(request, exception):
    """Handler personalizado para errores 404"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'NOT_FOUND',
            'message': 'Recurso no encontrado'
        }, status=404)
    
    return render(request, 'errors/404.html', status=404)


def custom_403_handler(request, exception):
    """Handler personalizado para errores 403"""
    security_logger.warning(f"Access denied for user {getattr(request.user, 'username', 'anonymous')} to {request.path}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'FORBIDDEN',
            'message': 'Acceso denegado'
        }, status=403)
    
    return render(request, 'errors/403.html', status=403)


def custom_500_handler(request):
    """Handler personalizado para errores 500"""
    logger.error(f"Server error for path {request.path}", exc_info=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'Error interno del servidor'
        }, status=500)
    
    return render(request, 'errors/500.html', status=500)