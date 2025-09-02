# -*- coding: utf-8 -*-
"""
Sistema de seguridad optimizado de DESS
Incluye autenticacion, autorizacion y cache de permisos
"""

# Decoradores de permisos (compatibilidad hacia atras)
from .permissions import (
    super_admin_required,
    user_only_required,
    ajax_login_required,
    ajax_super_admin_required,
    solution_access_required,
)

# Validadores centralizados
from .validators import SecurityValidator, RateLimitValidator

# Sistema de cache
from .cache import PermissionCache, cached_permission, invalidate_permission_cache

# Autenticacion JWT personalizada
from .jwt_auth import DESSJWTAuthentication, invalidate_user_tokens, refresh_user_permissions

# Mixins para Class-Based Views
from .mixins import (
    SuperAdminRequiredMixin,
    UserOnlyMixin,
    SolutionAccessMixin,
    AjaxPermissionMixin,
    AjaxSuperAdminMixin,
    UserProfileAccessMixin,
    RateLimitMixin,
)

__all__ = [
    # Decoradores (legacy)
    'super_admin_required',
    'user_only_required', 
    'ajax_login_required',
    'ajax_super_admin_required',
    'solution_access_required',
    
    # Validadores
    'SecurityValidator',
    'RateLimitValidator',
    
    # Cache
    'PermissionCache',
    'cached_permission',
    'invalidate_permission_cache',
    
    # JWT
    'DESSJWTAuthentication',
    'invalidate_user_tokens',
    'refresh_user_permissions',
    
    # Mixins
    'SuperAdminRequiredMixin',
    'UserOnlyMixin',
    'SolutionAccessMixin', 
    'AjaxPermissionMixin',
    'AjaxSuperAdminMixin',
    'UserProfileAccessMixin',
    'RateLimitMixin',
]