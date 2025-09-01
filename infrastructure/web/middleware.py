"""
Middleware para unificar interfaces de DESS
Redirige automáticamente del admin Django al dashboard DESS
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy


class UnifyInterfacesMiddleware:
    """
    Middleware que unifica las interfaces eliminando acceso al admin Django
    y redirigiendo todo al dashboard DESS
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs del admin Django que deben redirigirse al dashboard DESS
        admin_redirects = {
            '/admin/': reverse_lazy('dashboard'),
            '/admin/database/dessuser/': reverse_lazy('admin_users'),
            '/admin/database/dessuser/add/': reverse_lazy('admin_create_user'),
            '/admin/database/solution/': reverse_lazy('admin_solutions'),
        }
        
        # Si es una URL del admin Django
        for admin_url, dess_url in admin_redirects.items():
            if request.path.startswith(admin_url):
                # Solo permitir acceso técnico a desarrolladores (superuser con staff)
                if not (request.user.is_authenticated and 
                       request.user.is_superuser and 
                       request.user.is_staff and
                       'dev' in request.GET):  # Parámetro especial para desarrolladores
                    
                    messages.info(request, 
                        '🔄 Redirigido al panel DESS unificado para una mejor experiencia')
                    return redirect(dess_url)
        
        # Manejar URLs específicas del admin Django con IDs
        if '/admin/database/dessuser/' in request.path and request.path.endswith('/'):
            try:
                # Extraer ID del usuario
                path_parts = request.path.split('/')
                user_id = path_parts[-2]  # Obtener el ID antes del último /
                if user_id.isdigit():
                    messages.info(request, 
                        '🔄 Redirigido al panel DESS unificado')
                    return redirect('admin_user_detail', user_id=int(user_id))
            except (IndexError, ValueError):
                pass
        
        response = self.get_response(request)
        return response


"""
Middleware personalizado para DESS
"""
import time
import logging
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de requests de API.
    """
    
    def process_request(self, request):
        """Procesar request entrante."""
        if request.path.startswith('/api/'):
            request.start_time = time.time()
            
            # Log de request
            logger.info(f"API Request: {request.method} {request.path}", extra={
                'method': request.method,
                'path': request.path,
                'user': getattr(request.user, 'username', 'anonymous'),
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            })
    
    def process_response(self, request, response):
        """Procesar response saliente."""
        if hasattr(request, 'start_time') and request.path.startswith('/api/'):
            duration = time.time() - request.start_time
            
            # Log de response
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
        if request.path.startswith('/api/'):
            logger.error(f"API Exception: {str(exception)}", extra={
                'method': request.method,
                'path': request.path,
                'exception': str(exception),
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
    
    def get_client_ip(self, request):
        """Obtener IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para agregar headers de seguridad.
    """
    
    def process_response(self, request, response):
        """Agregar headers de seguridad."""
        # Evitar clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Evitar MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Strict Transport Security (HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy básica
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
        
        return response


class CORSMiddleware(MiddlewareMixin):
    """
    Middleware básico para CORS (Cross-Origin Resource Sharing).
    """
    
    def process_response(self, request, response):
        """Agregar headers CORS."""
        if request.path.startswith('/api/'):
            # Configurar origins permitidos
            allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', ['http://localhost:8000'])
            origin = request.META.get('HTTP_ORIGIN')
            
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
            
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Requested-With'
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def process_request(self, request):
        """Manejar requests OPTIONS (preflight)."""
        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            response = JsonResponse({'status': 'ok'})
            return response
