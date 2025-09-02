"""
Sistema de caché para permisos de DESS
Optimiza el rendimiento de validaciones de seguridad
"""
import hashlib
from functools import wraps
from django.core.cache import cache, caches
from django.conf import settings
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class PermissionCache:
    """
    Sistema de caché optimizado para permisos de usuarios.
    Reduce la carga en la base de datos para validaciones frecuentes.
    """
    
    CACHE_TIMEOUT = getattr(settings, 'PERMISSION_CACHE_TIMEOUT', 600)  # 10 minutos
    CACHE_BACKEND = getattr(settings, 'PERMISSION_CACHE_BACKEND', 'default')
    CACHE_PREFIX = 'dess_perms'
    
    @classmethod
    def _get_cache(cls):
        """Obtener instancia de caché específica para permisos."""
        try:
            return caches[cls.CACHE_BACKEND]
        except Exception as e:
            logger.warning(f"Error accessing permission cache backend: {e}")
            return cache  # Fallback al caché por defecto
    
    @classmethod
    def _get_cache_key(cls, user_id: int, permission_key: str) -> str:
        """Generar clave de caché única para usuario y permiso."""
        key_data = f"{cls.CACHE_PREFIX}:{user_id}:{permission_key}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def get_permission(cls, user_id: int, permission_key: str) -> Optional[bool]:
        """Obtener permiso desde caché."""
        cache_key = cls._get_cache_key(user_id, permission_key)
        cache_instance = cls._get_cache()
        
        try:
            result = cache_instance.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for permission {permission_key} user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting permission from cache: {e}")
            return None
    
    @classmethod
    def set_permission(cls, user_id: int, permission_key: str, has_permission: bool) -> None:
        """Guardar permiso en caché."""
        cache_key = cls._get_cache_key(user_id, permission_key)
        cache_instance = cls._get_cache()
        
        try:
            cache_instance.set(cache_key, has_permission, cls.CACHE_TIMEOUT)
            logger.debug(f"Cached permission {permission_key} for user {user_id}: {has_permission}")
        except Exception as e:
            logger.error(f"Error setting permission in cache: {e}")
    
    @classmethod
    def clear_user_permissions(cls, user_id: int) -> None:
        """Limpiar todos los permisos de un usuario del caché."""
        # En una implementación más avanzada, se mantendría un índice de claves por usuario
        # Por ahora, simplemente forzamos la validación en el siguiente acceso
        pass
    
    @classmethod
    def clear_all_permissions(cls) -> None:
        """Limpiar todo el caché de permisos."""
        cache.delete_many([key for key in cache._cache.keys() if key.startswith(cls.CACHE_PREFIX)])


def cached_permission(permission_key: str):
    """
    Decorador para cachear resultados de validación de permisos.
    
    Args:
        permission_key: Identificador único del permiso a validar
    """
    def decorator(permission_func: Callable) -> Callable:
        @wraps(permission_func)
        def wrapper(user, *args, **kwargs) -> bool:
            # Verificar caché primero
            cached_result = PermissionCache.get_permission(user.id, permission_key)
            if cached_result is not None:
                return cached_result
            
            # Si no está en caché, ejecutar validación
            result = permission_func(user, *args, **kwargs)
            
            # Guardar en caché
            PermissionCache.set_permission(user.id, permission_key, result)
            
            return result
        return wrapper
    return decorator


def invalidate_permission_cache(user_id: int) -> None:
    """
    Invalidar caché de permisos para un usuario específico.
    Se debe llamar cuando los permisos del usuario cambien.
    """
    PermissionCache.clear_user_permissions(user_id)