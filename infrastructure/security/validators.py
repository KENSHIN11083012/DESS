"""
Validadores de seguridad centralizados para DESS
Contiene toda la lógica de validación de permisos
"""
from typing import Union
from django.contrib.auth import get_user_model
from .cache import cached_permission

User = get_user_model()


class SecurityValidator:
    """
    Validador centralizado de permisos y seguridad.
    Todas las validaciones pasan por aquí para consistencia.
    """
    
    @staticmethod
    @cached_permission('is_super_admin')
    def is_super_admin(user) -> bool:
        """Verificar si el usuario es super administrador."""
        if not user or not user.is_authenticated:
            return False
        return hasattr(user, 'is_super_admin') and user.is_super_admin()
    
    @staticmethod
    @cached_permission('is_regular_user')
    def is_regular_user(user) -> bool:
        """Verificar si el usuario es un usuario regular (no admin)."""
        if not user or not user.is_authenticated:
            return False
        return not SecurityValidator.is_super_admin(user)
    
    @staticmethod
    def can_access_solution(user, solution_id: Union[int, str]) -> bool:
        """Verificar si el usuario puede acceder a una solución específica."""
        if not user or not user.is_authenticated:
            return False
        
        # Super admins pueden acceder a todo
        if SecurityValidator.is_super_admin(user):
            return True
        
        # Usuarios regulares solo a soluciones asignadas
        if hasattr(user, 'can_access_solution'):
            return user.can_access_solution(solution_id)
        
        return False
    
    @staticmethod
    @cached_permission('can_manage_users')
    def can_manage_users(user) -> bool:
        """Verificar si el usuario puede gestionar otros usuarios."""
        return SecurityValidator.is_super_admin(user)
    
    @staticmethod
    @cached_permission('can_manage_solutions') 
    def can_manage_solutions(user) -> bool:
        """Verificar si el usuario puede gestionar soluciones."""
        return SecurityValidator.is_super_admin(user)
    
    @staticmethod
    def can_access_admin_panel(user) -> bool:
        """Verificar si el usuario puede acceder al panel de administración."""
        return SecurityValidator.is_super_admin(user)
    
    @staticmethod
    def can_view_user_detail(requesting_user, target_user) -> bool:
        """Verificar si un usuario puede ver el detalle de otro usuario."""
        if not requesting_user or not requesting_user.is_authenticated:
            return False
        
        # Un usuario puede ver su propio perfil
        if requesting_user.id == target_user.id:
            return True
        
        # Super admins pueden ver cualquier perfil
        return SecurityValidator.is_super_admin(requesting_user)
    
    @staticmethod
    def can_edit_user(requesting_user, target_user) -> bool:
        """Verificar si un usuario puede editar a otro usuario."""
        if not requesting_user or not requesting_user.is_authenticated:
            return False
        
        # Solo super admins pueden editar otros usuarios
        if SecurityValidator.is_super_admin(requesting_user):
            return True
        
        # Un usuario puede editar su propio perfil (campos limitados)
        return requesting_user.id == target_user.id
    
    @staticmethod
    def get_allowed_redirect_for_user(user) -> str:
        """Obtener la URL de redirección apropiada según el rol del usuario."""
        if not user or not user.is_authenticated:
            return 'login'
        
        if SecurityValidator.is_super_admin(user):
            return 'admin_dashboard'
        else:
            return 'user_dashboard'


class RateLimitValidator:
    """
    Validador de límites de velocidad para prevenir abuso.
    """
    
    @staticmethod
    def can_make_api_request(user, endpoint: str) -> bool:
        """Verificar si el usuario puede hacer una petición API según límites."""
        # Implementación básica - se puede expandir con Redis
        if not user or not user.is_authenticated:
            return False
        
        # Super admins tienen límites más altos
        if SecurityValidator.is_super_admin(user):
            return True
        
        # TODO: Implementar rate limiting real con Redis/cache
        return True
    
    @staticmethod
    def can_login_attempt(ip_address: str) -> bool:
        """Verificar si se permiten más intentos de login desde esta IP."""
        # TODO: Implementar rate limiting de login
        return True