"""
Cache layer para consultas de base de datos frecuentes
"""
import logging
from typing import Optional, List, Dict, Any
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import DESSUser, Solution, UserSolutionAssignment

logger = logging.getLogger(__name__)


class DatabaseCache:
    """
    Clase para manejar cache de consultas de base de datos
    """
    
    # Prefijos para diferentes tipos de cache
    USER_STATS_PREFIX = "dess:user_stats:"
    SOLUTION_STATS_PREFIX = "dess:solution_stats:"
    ASSIGNMENT_STATS_PREFIX = "dess:assignment_stats:"
    DASHBOARD_PREFIX = "dess:dashboard:"
    
    # TTL por defecto (15 minutos)
    DEFAULT_TTL = 900
    
    @classmethod
    def get_user_stats(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de usuario desde cache"""
        cache_key = f"{cls.USER_STATS_PREFIX}{user_id}"
        return cache.get(cache_key)
    
    @classmethod
    def set_user_stats(cls, user_id: int, stats: Dict[str, Any], ttl: int = DEFAULT_TTL) -> None:
        """Guardar estadísticas de usuario en cache"""
        cache_key = f"{cls.USER_STATS_PREFIX}{user_id}"
        cache.set(cache_key, stats, ttl)
        logger.debug(f"User stats cached for user {user_id}")
    
    @classmethod
    def get_solution_stats(cls, solution_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de solución desde cache"""
        cache_key = f"{cls.SOLUTION_STATS_PREFIX}{solution_id}"
        return cache.get(cache_key)
    
    @classmethod
    def set_solution_stats(cls, solution_id: int, stats: Dict[str, Any], ttl: int = DEFAULT_TTL) -> None:
        """Guardar estadísticas de solución en cache"""
        cache_key = f"{cls.SOLUTION_STATS_PREFIX}{solution_id}"
        cache.set(cache_key, stats, ttl)
        logger.debug(f"Solution stats cached for solution {solution_id}")
    
    @classmethod
    def get_dashboard_data(cls, user_id: int, dashboard_type: str) -> Optional[Dict[str, Any]]:
        """Obtener datos de dashboard desde cache"""
        cache_key = f"{cls.DASHBOARD_PREFIX}{dashboard_type}:{user_id}"
        return cache.get(cache_key)
    
    @classmethod
    def set_dashboard_data(cls, user_id: int, dashboard_type: str, data: Dict[str, Any], ttl: int = DEFAULT_TTL) -> None:
        """Guardar datos de dashboard en cache"""
        cache_key = f"{cls.DASHBOARD_PREFIX}{dashboard_type}:{user_id}"
        cache.set(cache_key, data, ttl)
        logger.debug(f"Dashboard data cached for user {user_id}, type {dashboard_type}")
    
    @classmethod
    def get_assignment_summary(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener resumen de asignaciones desde cache"""
        cache_key = f"{cls.ASSIGNMENT_STATS_PREFIX}{user_id}"
        return cache.get(cache_key)
    
    @classmethod
    def set_assignment_summary(cls, user_id: int, summary: Dict[str, Any], ttl: int = DEFAULT_TTL) -> None:
        """Guardar resumen de asignaciones en cache"""
        cache_key = f"{cls.ASSIGNMENT_STATS_PREFIX}{user_id}"
        cache.set(cache_key, summary, ttl)
        logger.debug(f"Assignment summary cached for user {user_id}")
    
    @classmethod
    def invalidate_user_cache(cls, user_id: int) -> None:
        """Invalidar todo el cache relacionado con un usuario"""
        patterns = [
            f"{cls.USER_STATS_PREFIX}{user_id}",
            f"{cls.ASSIGNMENT_STATS_PREFIX}{user_id}",
            f"{cls.DASHBOARD_PREFIX}*:{user_id}",
        ]
        
        for pattern in patterns:
            if '*' in pattern:
                # Para patrones con wildcard, necesitamos buscar las claves
                cls._delete_pattern(pattern)
            else:
                cache.delete(pattern)
        
        logger.info(f"User cache invalidated for user {user_id}")
    
    @classmethod
    def invalidate_solution_cache(cls, solution_id: int) -> None:
        """Invalidar cache relacionado con una solución"""
        cache_key = f"{cls.SOLUTION_STATS_PREFIX}{solution_id}"
        cache.delete(cache_key)
        
        # También invalidar cache de usuarios que tienen esta solución asignada
        try:
            user_ids = UserSolutionAssignment.objects.filter(
                solution_id=solution_id,
                is_active=True
            ).values_list('user_id', flat=True)
            
            for user_id in user_ids:
                cls.invalidate_user_cache(user_id)
        except Exception as e:
            logger.error(f"Error invalidating related user caches: {e}")
        
        logger.info(f"Solution cache invalidated for solution {solution_id}")
    
    @classmethod
    def _delete_pattern(cls, pattern: str) -> None:
        """Eliminar claves que coincidan con un patrón"""
        try:
            # Esto depende del backend de cache usado
            # Para Redis, se podría usar SCAN
            # Para Memcache, no hay soporte nativo para patrones
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(pattern)
            else:
                # Fallback: invalidar manualmente conociendo los tipos de dashboard
                if 'dashboard' in pattern.lower():
                    dashboard_types = ['admin', 'user']
                    user_id = pattern.split(':')[-1]
                    for dash_type in dashboard_types:
                        key = f"{cls.DASHBOARD_PREFIX}{dash_type}:{user_id}"
                        cache.delete(key)
        except Exception as e:
            logger.warning(f"Could not delete pattern {pattern}: {e}")


class CachedQueryMixin:
    """
    Mixin para agregar capacidades de cache a queries
    """
    
    @classmethod
    def get_user_dashboard_data(cls, user):
        """Obtener datos de dashboard con cache"""
        cache_data = DatabaseCache.get_dashboard_data(
            user.id, 
            'admin' if user.is_super_admin() else 'user'
        )
        
        if cache_data:
            logger.debug(f"Dashboard data retrieved from cache for user {user.id}")
            return cache_data
        
        # Calcular datos desde base de datos
        data = cls._calculate_dashboard_data(user)
        
        # Guardar en cache
        DatabaseCache.set_dashboard_data(
            user.id,
            'admin' if user.is_super_admin() else 'user',
            data,
            ttl=600  # 10 minutos para dashboard
        )
        
        return data
    
    @classmethod
    def get_user_assignment_summary(cls, user_id: int):
        """Obtener resumen de asignaciones con cache"""
        summary = DatabaseCache.get_assignment_summary(user_id)
        
        if summary:
            logger.debug(f"Assignment summary retrieved from cache for user {user_id}")
            return summary
        
        # Calcular desde base de datos
        summary = cls._calculate_assignment_summary(user_id)
        
        # Guardar en cache
        DatabaseCache.set_assignment_summary(user_id, summary)
        
        return summary
    
    @classmethod
    def get_solution_usage_stats(cls, solution_id: int):
        """Obtener estadísticas de uso de solución con cache"""
        stats = DatabaseCache.get_solution_stats(solution_id)
        
        if stats:
            logger.debug(f"Solution stats retrieved from cache for solution {solution_id}")
            return stats
        
        # Calcular desde base de datos
        stats = cls._calculate_solution_stats(solution_id)
        
        # Guardar en cache
        DatabaseCache.set_solution_stats(solution_id, stats)
        
        return stats
    
    @classmethod
    def _calculate_dashboard_data(cls, user):
        """Calcular datos de dashboard desde base de datos"""
        if user.is_super_admin():
            return {
                'total_users': DESSUser.objects.active_users().count(),
                'total_solutions': Solution.objects.count(),
                'active_solutions': Solution.objects.active().count(),
                'total_assignments': UserSolutionAssignment.objects.active().count(),
                'recent_users': list(
                    DESSUser.objects.active_users()
                    .order_by('-date_joined')[:5]
                    .values('id', 'username', 'full_name', 'date_joined')
                ),
                'recent_solutions': list(
                    Solution.objects.order_by('-created_at')[:5]
                    .values('id', 'name', 'status', 'created_at')
                ),
                'calculated_at': timezone.now().isoformat()
            }
        else:
            assignments = UserSolutionAssignment.objects.for_user(user).active()
            return {
                'assigned_solutions_count': assignments.count(),
                'active_solutions_count': assignments.filter(solution__status='active').count(),
                'recent_solutions': list(
                    assignments.select_related('solution')
                    .order_by('-assigned_at')[:5]
                    .values('solution__id', 'solution__name', 'solution__status', 'assigned_at')
                ),
                'calculated_at': timezone.now().isoformat()
            }
    
    @classmethod
    def _calculate_assignment_summary(cls, user_id: int):
        """Calcular resumen de asignaciones desde base de datos"""
        assignments = UserSolutionAssignment.objects.for_user_id(user_id)
        
        return {
            'total_assignments': assignments.count(),
            'active_assignments': assignments.active().count(),
            'inactive_assignments': assignments.inactive().count(),
            'solutions_by_status': dict(
                assignments.active()
                .select_related('solution')
                .values_list('solution__status')
                .annotate(count=models.Count('id'))
            ),
            'calculated_at': timezone.now().isoformat()
        }
    
    @classmethod
    def _calculate_solution_stats(cls, solution_id: int):
        """Calcular estadísticas de solución desde base de datos"""
        from django.db import models
        
        assignments = UserSolutionAssignment.objects.for_solution_id(solution_id)
        
        return {
            'total_assigned_users': assignments.count(),
            'active_assigned_users': assignments.active().count(),
            'recent_accesses': UserSolutionAccess.objects.for_solution_id(solution_id)
                              .recent_access(days=30).count(),
            'last_accessed': UserSolutionAccess.objects.for_solution_id(solution_id)
                           .order_by('-accessed_at').first(),
            'calculated_at': timezone.now().isoformat()
        }


# Signals para invalidar cache automáticamente
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=UserSolutionAssignment)
def invalidate_assignment_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica una asignación"""
    DatabaseCache.invalidate_user_cache(instance.user_id)
    DatabaseCache.invalidate_solution_cache(instance.solution_id)

@receiver(post_delete, sender=UserSolutionAssignment)
def invalidate_assignment_cache_delete(sender, instance, **kwargs):
    """Invalidar cache cuando se elimina una asignación"""
    DatabaseCache.invalidate_user_cache(instance.user_id)
    DatabaseCache.invalidate_solution_cache(instance.solution_id)

@receiver(post_save, sender=Solution)
def invalidate_solution_cache_save(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica una solución"""
    DatabaseCache.invalidate_solution_cache(instance.id)

@receiver(post_save, sender=DESSUser)
def invalidate_user_cache_save(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica un usuario"""
    DatabaseCache.invalidate_user_cache(instance.id)