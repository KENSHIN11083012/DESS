"""
Middleware para headers de seguridad específicos de DESS
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware optimizado para headers de seguridad específicos de DESS.
    No duplica funcionalidad ya cubierta por Django SecurityMiddleware.
    """
    
    def process_response(self, request, response):
        """Agregar headers de seguridad específicos de DESS."""
        # Solo agregar headers que no están cubiertos por Django SecurityMiddleware
        
        # Content Security Policy específica para DESS
        if not response.get('Content-Security-Policy'):
            # CSP optimizada para DESS con soporte para Tailwind CSS
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        
        # Headers específicos para APIs de DESS
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache' 
            response['Expires'] = '0'
            
            # Header personalizado para identificar respuestas de DESS API
            response['X-DESS-API'] = 'v1.0'
        
        # Headers para dashboard administrativo
        elif request.path.startswith('/admin-panel/'):
            response['X-Robots-Tag'] = 'noindex, nofollow'
        
        return response