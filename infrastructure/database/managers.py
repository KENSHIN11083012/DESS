"""
Managers optimizados para consultas eficientes
"""
from django.db import models
from django.db.models import Prefetch, Q, Count, Case, When, Value, IntegerField
from django.contrib.auth.models import UserManager
from typing import Optional, List


class SolutionManager(models.Manager):
    """Manager optimizado para el modelo Solution"""
    
    def active(self):
        """Obtener solo soluciones activas"""
        return self.filter(status='active')
    
    def accessible(self):
        """Obtener soluciones accesibles (activas con URL)"""
        return self.filter(status='active', access_url__isnull=False)
    
    def by_type(self, solution_type: str):
        """Filtrar por tipo de solución"""
        return self.filter(solution_type=solution_type)
    
    def with_assignment_counts(self):
        """Incluir conteo de asignaciones activas"""
        return self.annotate(
            active_assignments=Count(
                'usersolutionassignment',
                filter=Q(usersolutionassignment__is_active=True),
                distinct=True
            ),
            total_assignments=Count('usersolutionassignment', distinct=True)
        )
    
    def with_creator_info(self):
        """Incluir información del creador optimizada"""
        return self.select_related('created_by')
    
    def for_admin_dashboard(self):
        """Optimizado para dashboard de administrador con toda la información necesaria"""
        return self.select_related('created_by').annotate(
            active_assignments=Count(
                'usersolutionassignment',
                filter=Q(usersolutionassignment__is_active=True),
                distinct=True
            ),
            total_assignments=Count('usersolutionassignment', distinct=True)
        )
    
    def for_user_dashboard(self, user):
        """Optimizado para dashboard de usuario"""
        if user.is_super_admin():
            return self.with_assignment_counts().with_creator_info()
        else:
            return self.filter(
                usersolutionassignment__user=user,
                usersolutionassignment__is_active=True
            ).select_related('created_by')
    
    def search(self, query: str):
        """Búsqueda optimizada por nombre y descripción"""
        if not query:
            return self.none()
        
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()


class DESSUserManager(UserManager):
    """Manager optimizado para el modelo DESSUser - hereda de UserManager para mantener funcionalidad de auth"""
    
    def active_users(self):
        """Usuarios activos únicamente"""
        return self.filter(is_active=True)
    
    def by_role(self, role: str):
        """Filtrar por rol específico"""
        return self.filter(role=role)
    
    def super_admins(self):
        """Solo super administradores"""
        return self.filter(role='super_admin', is_active=True)
    
    def regular_users(self):
        """Solo usuarios regulares"""
        return self.filter(role='user', is_active=True)
    
    def with_solution_counts(self):
        """Incluir conteo de soluciones asignadas"""
        return self.annotate(
            assigned_solutions_count=Count(
                'usersolutionassignment',
                filter=Q(usersolutionassignment__is_active=True),
                distinct=True
            ),
            total_assignments=Count('usersolutionassignment', distinct=True)
        )
    
    def with_assigned_solutions(self):
        """Prefetch de soluciones asignadas activas"""
        return self.prefetch_related(
            Prefetch(
                'assigned_solutions',
                queryset=models.get_model('database', 'Solution').objects.filter(
                    usersolutionassignment__is_active=True
                ),
                to_attr='active_solutions'
            )
        )
    
    def for_admin_dashboard(self):
        """Optimizado para dashboard de administrador"""
        return self.with_solution_counts().order_by('-date_joined')
    
    def search(self, query: str):
        """Búsqueda optimizada por username, email y nombre completo"""
        if not query:
            return self.none()
        
        return self.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(full_name__icontains=query)
        ).distinct()


class UserSolutionAssignmentManager(models.Manager):
    """Manager optimizado para asignaciones"""
    
    def active(self):
        """Solo asignaciones activas"""
        return self.filter(is_active=True)
    
    def inactive(self):
        """Solo asignaciones inactivas"""
        return self.filter(is_active=False)
    
    def for_user(self, user):
        """Asignaciones para un usuario específico"""
        return self.filter(user=user)
    
    def for_solution(self, solution):
        """Asignaciones para una solución específica"""
        return self.filter(solution=solution)
    
    def with_related_info(self):
        """Incluir información relacionada optimizada"""
        return self.select_related('user', 'solution', 'assigned_by')
    
    def recent_assignments(self, days: int = 7):
        """Asignaciones recientes"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(assigned_at__gte=cutoff_date)
    
    def assignment_stats(self):
        """Estadísticas de asignaciones"""
        return self.aggregate(
            total_assignments=Count('id'),
            active_assignments=Count('id', filter=Q(is_active=True)),
            inactive_assignments=Count('id', filter=Q(is_active=False))
        )
    
    def by_admin(self, admin_user):
        """Asignaciones hechas por un administrador específico"""
        return self.filter(assigned_by=admin_user)


class UserSolutionAccessManager(models.Manager):
    """Manager optimizado para accesos a soluciones"""
    
    def recent_access(self, days: int = 30):
        """Accesos recientes"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(accessed_at__gte=cutoff_date)
    
    def for_user(self, user):
        """Accesos para un usuario específico"""
        return self.filter(user=user)
    
    def for_solution(self, solution):
        """Accesos para una solución específica"""
        return self.filter(solution=solution)
    
    def with_related_info(self):
        """Incluir información relacionada optimizada"""
        return self.select_related('user', 'solution')
    
    def access_frequency(self):
        """Estadísticas de frecuencia de acceso"""
        return self.values('solution__name').annotate(
            access_count=Count('id'),
            unique_users=Count('user', distinct=True)
        ).order_by('-access_count')
    
    def user_activity_summary(self, user):
        """Resumen de actividad del usuario"""
        return self.filter(user=user).values('solution__name').annotate(
            last_access=models.Max('accessed_at'),
            access_count=Count('id')
        ).order_by('-last_access')


# Mixins para consultas comunes
class OptimizedQueryMixin:
    """Mixin con métodos de consulta optimizada comunes"""
    
    @classmethod
    def get_paginated_queryset(cls, queryset, page: int = 1, per_page: int = 20):
        """Obtener queryset paginado optimizado"""
        offset = (page - 1) * per_page
        return queryset[offset:offset + per_page]
    
    @classmethod
    def get_filtered_queryset(cls, queryset, filters: dict):
        """Aplicar filtros de forma optimizada"""
        for field, value in filters.items():
            if value is not None and value != '':
                if field.endswith('__icontains'):
                    queryset = queryset.filter(**{field: value})
                elif field.endswith('__in'):
                    if isinstance(value, (list, tuple)) and len(value) > 0:
                        queryset = queryset.filter(**{field: value})
                else:
                    queryset = queryset.filter(**{field: value})
        
        return queryset
    
    @classmethod
    def bulk_update_status(cls, model_class, ids: List[int], status: str):
        """Actualización masiva de estado optimizada"""
        return model_class.objects.filter(id__in=ids).update(status=status)
    
    @classmethod
    def bulk_deactivate(cls, model_class, ids: List[int]):
        """Desactivación masiva optimizada"""
        return model_class.objects.filter(id__in=ids).update(is_active=False)