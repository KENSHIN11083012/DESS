"""
Dashboard Context Builder - Construye contextos para dashboards siguiendo Clean Architecture
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from django.utils import timezone
from infrastructure.dependency_setup import get_user_service, get_solution_service
from infrastructure.database.models import DESSUser
import logging

logger = logging.getLogger('dess')


class DashboardContextBuilder:
    """
    Constructor de contexto para dashboards siguiendo el patrón Builder
    Utiliza los servicios de aplicación para obtener datos del dominio
    """
    
    def __init__(self, user: DESSUser):
        self.user = user
        self.context = {
            'user': user,
            'timestamp': timezone.now(),
        }
        
        # Inicializar servicios
        try:
            self.user_service = get_user_service()
            self.solution_service = get_solution_service()
        except Exception as e:
            logger.error(f"Error inicializando servicios en DashboardContextBuilder: {e}")
            self.user_service = None
            self.solution_service = None
    
    def add_user_stats(self) -> 'DashboardContextBuilder':
        """Agregar estadísticas de usuarios al contexto"""
        try:
            if self.user_service:
                # Usar consultas directas ya que el servicio no tiene método de estadísticas
                total_users = DESSUser.objects.count()
                active_users = DESSUser.objects.filter(is_active=True).count()
                super_admins = DESSUser.objects.filter(role='super_admin').count()
                regular_users = DESSUser.objects.filter(role='user').count()
                
                self.context['stats'] = {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': total_users - active_users,
                    'super_admins': super_admins,
                    'regular_users': regular_users,
                }
                
                logger.info(f"Estadísticas de usuarios obtenidas: {self.context['stats']}")
            else:
                logger.warning("user_service no disponible, usando valores por defecto")
                self.context['stats'] = {
                    'total_users': 0,
                    'active_users': 0,
                    'inactive_users': 0,
                    'super_admins': 0,
                    'regular_users': 0,
                }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de usuarios: {e}")
            self.context['stats'] = self._get_default_stats()
            
        return self
    
    def add_solution_stats(self) -> 'DashboardContextBuilder':
        """Agregar estadísticas de soluciones al contexto"""
        try:
            if self.solution_service:
                from infrastructure.database.models import Solution
                
                total_solutions = Solution.objects.count()
                active_solutions = Solution.objects.filter(status='ACTIVE').count()
                deployed_solutions = Solution.objects.filter(deployment_status='DEPLOYED').count()
                
                if 'stats' not in self.context:
                    self.context['stats'] = {}
                    
                self.context['stats'].update({
                    'total_solutions': total_solutions,
                    'active_solutions': active_solutions,
                    'inactive_solutions': total_solutions - active_solutions,
                    'deployed_solutions': deployed_solutions,
                })
                
                logger.info(f"Estadísticas de soluciones obtenidas: total={total_solutions}, active={active_solutions}, deployed={deployed_solutions}")
            else:
                logger.warning("solution_service no disponible, usando valores por defecto")
                if 'stats' not in self.context:
                    self.context['stats'] = {}
                self.context['stats'].update({
                    'total_solutions': 0,
                    'active_solutions': 0,
                    'inactive_solutions': 0,
                    'deployed_solutions': 0,
                })
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de soluciones: {e}")
            if 'stats' not in self.context:
                self.context['stats'] = {}
            self.context['stats'].update({
                'total_solutions': 0,
                'active_solutions': 0,
                'inactive_solutions': 0,
                'deployed_solutions': 0,
            })
            
        return self
    
    def add_assignment_stats(self) -> 'DashboardContextBuilder':
        """Agregar estadísticas de asignaciones al contexto"""
        try:
            from infrastructure.database.models import UserSolutionAssignment
            
            total_assignments = UserSolutionAssignment.objects.filter(is_active=True).count()
            recent_assignments = UserSolutionAssignment.objects.filter(
                assigned_at__gte=timezone.now() - timedelta(days=7),
                is_active=True
            ).count()
            
            if 'stats' not in self.context:
                self.context['stats'] = {}
                
            self.context['stats'].update({
                'total_assignments': total_assignments,
                'recent_assignments': recent_assignments,
            })
            
            logger.info(f"Estadísticas de asignaciones obtenidas: total={total_assignments}, recent={recent_assignments}")
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de asignaciones: {e}")
            if 'stats' not in self.context:
                self.context['stats'] = {}
            self.context['stats'].update({
                'total_assignments': 0,
                'recent_assignments': 0,
            })
            
        return self
    
    def add_recent_activity(self) -> 'DashboardContextBuilder':
        """Agregar actividad reciente al contexto"""
        try:
            activities = self._get_recent_activities()
            self.context['recent_activities'] = activities
        except Exception as e:
            logger.error(f"Error obteniendo actividad reciente: {e}")
            self.context['recent_activities'] = []
            
        return self
    
    def add_solutions_data(self) -> 'DashboardContextBuilder':
        """Agregar datos de soluciones para el usuario actual"""
        try:
            if self.user.role == 'super_admin':
                # Super admin ve todas las soluciones
                from infrastructure.database.models import Solution
                solutions = Solution.objects.all()[:10]  # Últimas 10
                self.context['user_solutions'] = solutions
            else:
                # Usuario regular ve solo sus soluciones asignadas
                from infrastructure.database.models import UserSolutionAssignment
                assignments = UserSolutionAssignment.objects.filter(
                    user=self.user,
                    is_active=True
                ).select_related('solution').order_by('-assigned_at')
                
                self.context['user_solutions'] = assignments
                
                # Estadísticas para el dashboard de usuario
                total_assigned = assignments.count()
                active_solutions = assignments.filter(solution__status='active').count()
                deployed_solutions = assignments.filter(solution__status='deployed').count()
                recent_accesses = 0  # TODO: implementar después
                
                self.context['solutions_stats'] = {
                    'total_assigned': total_assigned,
                    'active_solutions': active_solutions,
                    'deployed_solutions': deployed_solutions,
                    'recent_accesses': recent_accesses,
                    'favorite_count': 0  # TODO: implementar favoritos después
                }
            
            self.context['solutions_count'] = len(self.context['user_solutions'])
            
        except Exception as e:
            logger.error(f"Error obteniendo soluciones del usuario: {e}")
            self.context['user_solutions'] = []
            self.context['solutions_count'] = 0
            self.context['solutions_stats'] = {
                'total_assigned': 0,
                'active_solutions': 0,
                'deployed_solutions': 0,
                'recent_accesses': 0,
                'favorite_count': 0
            }
            
        return self
    
    def add_system_health(self) -> 'DashboardContextBuilder':
        """Agregar información de salud del sistema"""
        try:
            # Verificar salud de componentes críticos
            health_status = {
                'database': self._check_database_health(),
                'cache': self._check_cache_health(),
                'storage': self._check_storage_health(),
                'apis': self._check_apis_health(),
            }
            
            overall_health = all(health_status.values())
            
            self.context['system_health'] = {
                'overall': 'healthy' if overall_health else 'warning',
                'components': health_status,
                'last_check': timezone.now(),
            }
            
        except Exception as e:
            logger.error(f"Error verificando salud del sistema: {e}")
            self.context['system_health'] = {
                'overall': 'unknown',
                'components': {},
                'last_check': timezone.now(),
            }
            
        return self
    
    def build(self) -> Dict[str, Any]:
        """Construir y retornar el contexto final"""
        # Agregar metadatos finales
        self.context['build_timestamp'] = timezone.now()
        self.context['user_role'] = self.user.role
        self.context['is_super_admin'] = self.user.role == 'super_admin'
        
        return self.context
    
    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Obtener actividades recientes del sistema"""
        activities = []
        
        try:
            # Actividades de usuarios recientes
            from infrastructure.database.models import DESSUser
            recent_users = DESSUser.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=7)
            ).order_by('-date_joined')[:5]
            
            for user in recent_users:
                activities.append({
                    'timestamp': user.date_joined,
                    'description': f'Nuevo usuario registrado: {user.username}',
                    'type': 'user_created',
                    'user': user.username,
                })
            
            # Actividades de asignaciones recientes
            from infrastructure.database.models import UserSolutionAssignment
            recent_assignments = UserSolutionAssignment.objects.filter(
                assigned_at__gte=timezone.now() - timedelta(days=7),
                is_active=True
            ).select_related('user', 'solution').order_by('-assigned_at')[:5]
            
            for assignment in recent_assignments:
                activities.append({
                    'timestamp': assignment.assigned_at,
                    'description': f'Solución "{assignment.solution.name}" asignada a {assignment.user.username}',
                    'type': 'solution_assigned',
                    'user': assignment.user.username,
                    'solution': assignment.solution.name,
                })
                
            # Ordenar por timestamp descendente
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo actividades recientes: {e}")
        
        return activities[:10]  # Últimas 10 actividades
    
    def _get_default_stats(self) -> Dict[str, int]:
        """Estadísticas por defecto en caso de error"""
        return {
            'total_users': 0,
            'active_users': 0,
            'inactive_users': 0,
            'super_admins': 0,
            'regular_users': 0,
            'total_solutions': 0,
            'active_solutions': 0,
            'inactive_solutions': 0,
            'deployed_solutions': 0,
            'total_assignments': 0,
            'recent_assignments': 0,
        }
    
    def _check_database_health(self) -> bool:
        """Verificar salud de la base de datos"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except:
            return False
    
    def _check_cache_health(self) -> bool:
        """Verificar salud del cache"""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 30)
            return cache.get('health_check') == 'ok'
        except:
            return False
    
    def _check_storage_health(self) -> bool:
        """Verificar salud del almacenamiento"""
        try:
            from django.conf import settings
            import os
            return os.path.exists(str(settings.MEDIA_ROOT))
        except:
            return False
    
    def _check_apis_health(self) -> bool:
        """Verificar salud de las APIs"""
        try:
            # Verificar que las URLs principales respondan
            from django.urls import reverse
            from django.test import Client
            
            client = Client()
            response = client.get('/status/')
            return response.status_code == 200
        except:
            return False


class AdminDashboardContextBuilder(DashboardContextBuilder):
    """Builder especializado para dashboards de administrador"""
    
    def build_admin_context(self) -> Dict[str, Any]:
        """Construir contexto completo para administrador"""
        return (self
                .add_user_stats()
                .add_solution_stats() 
                .add_assignment_stats()
                .add_recent_activity()
                .add_system_health()
                .build())


class UserDashboardContextBuilder(DashboardContextBuilder):
    """Builder especializado para dashboards de usuario"""
    
    def build_user_context(self) -> Dict[str, Any]:
        """Construir contexto completo para usuario regular"""
        return (self
                .add_solutions_data()
                .add_recent_activity()
                .build())
