"""
Middleware para logging de APIs de DESS
"""
import time
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware optimizado para logging de requests de API.
    """
    
    def process_request(self, request):
        """Procesar request entrante."""
        # Solo procesar requests de API para eficiencia
        if self._is_api_request(request):
            request.start_time = time.time()
            
            # Log de request solo si es necesario
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"API Request: {request.method} {request.path}", extra={
                    'method': request.method,
                    'path': request.path,
                    'user': getattr(request.user, 'username', 'anonymous'),
                    'ip': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100]  # Limitar longitud
                })
    
    def process_response(self, request, response):
        """Procesar response saliente."""
        if hasattr(request, 'start_time') and self._is_api_request(request):
            duration = time.time() - request.start_time
            
            # Log de response solo para requests lentos o errores
            if duration > 1.0 or response.status_code >= 400:
                logger.info(f"API Response: {response.status_code} - {duration:.3f}s", extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user': getattr(request.user, 'username', 'anonymous')
                })
        
        return response
    
    def process_exception(self, request, exception):
        """Procesar excepciones no manejadas."""
        if self._is_api_request(request):
            logger.error(f"API Exception: {str(exception)[:200]}", extra={
                'method': request.method,
                'path': request.path,
                'exception': str(exception)[:200],  # Limitar longitud
                'user': getattr(request.user, 'username', 'anonymous')
            }, exc_info=True)
            
            # En modo DEBUG, propagar la excepción
            if settings.DEBUG:
                return None
            
            # En producción, devolver error genérico
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)
    
    def _is_api_request(self, request):
        """Verificar si es un request de API."""
        return request.path.startswith('/api/')
    
    def _get_client_ip(self, request):
        """Obtener IP del cliente de forma optimizada."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')