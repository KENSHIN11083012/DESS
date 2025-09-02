"""
Mixins de permisos para Class-Based Views de DESS
Proporcionan control de acceso granular y reutilizable
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from ..validators import SecurityValidator


class BasePermissionMixin:
    """Mixin base para validaciones de permisos."""
    
    permission_denied_message = "No tienes permisos para acceder a esta sección"
    redirect_url = 'user_dashboard'
    
    def handle_no_permission(self):
        """Manejar cuando no se tienen permisos."""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Request AJAX
            return JsonResponse({
                'error': self.permission_denied_message,
                'redirect': self.redirect_url
            }, status=403)
        
        # Request normal
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class SuperAdminRequiredMixin(LoginRequiredMixin, BasePermissionMixin):
    """
    Mixin que requiere que el usuario sea super administrador.
    """
    
    permission_denied_message = "Acceso restringido a super administradores"
    redirect_url = 'user_dashboard'
    
    def dispatch(self, request, *args, **kwargs):
        if not SecurityValidator.is_super_admin(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class UserOnlyMixin(LoginRequiredMixin, BasePermissionMixin):
    """
    Mixin que requiere que el usuario sea regular (no admin).
    Redirige admins a su dashboard correspondiente.
    """
    
    redirect_url = 'admin_dashboard'
    
    def dispatch(self, request, *args, **kwargs):
        if SecurityValidator.is_super_admin(request.user):
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class SolutionAccessMixin(LoginRequiredMixin, BasePermissionMixin):
    """
    Mixin que verifica acceso a una solución específica.
    Espera solution_id en kwargs.
    """
    
    permission_denied_message = "No tienes acceso a esta solución"
    
    def dispatch(self, request, *args, **kwargs):
        solution_id = kwargs.get('solution_id')
        if not solution_id:
            raise ValueError("SolutionAccessMixin requiere solution_id en kwargs")
        
        if not SecurityValidator.can_access_solution(request.user, solution_id):
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)


class AjaxPermissionMixin(BasePermissionMixin):
    """
    Mixin específico para vistas AJAX que requieren autenticación.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return super().dispatch(request, *args, **kwargs)


class AjaxSuperAdminMixin(AjaxPermissionMixin):
    """
    Mixin para vistas AJAX que requieren permisos de super admin.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not SecurityValidator.is_super_admin(request.user):
            return JsonResponse({'error': 'Super admin access required'}, status=403)
        
        return super().dispatch(request, *args, **kwargs)


class UserProfileAccessMixin(LoginRequiredMixin, BasePermissionMixin):
    """
    Mixin para controlar acceso a perfiles de usuario.
    Permite acceso a propio perfil o a super admins.
    """
    
    permission_denied_message = "No puedes acceder a este perfil"
    
    def dispatch(self, request, *args, **kwargs):
        target_user_id = kwargs.get('user_id')
        if not target_user_id:
            raise ValueError("UserProfileAccessMixin requiere user_id en kwargs")
        
        # Permitir acceso a propio perfil
        if request.user.id == int(target_user_id):
            return super().dispatch(request, *args, **kwargs)
        
        # Permitir acceso a super admins
        if SecurityValidator.is_super_admin(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        return self.handle_no_permission()


class RateLimitMixin:
    """
    Mixin para implementar rate limiting en vistas.
    """
    
    rate_limit_key = None
    rate_limit_message = "Demasiadas peticiones. Intenta más tarde."
    
    def dispatch(self, request, *args, **kwargs):
        # TODO: Implementar rate limiting real
        # Por ahora solo es un placeholder
        return super().dispatch(request, *args, **kwargs)