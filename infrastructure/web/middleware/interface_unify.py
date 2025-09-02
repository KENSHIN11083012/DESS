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