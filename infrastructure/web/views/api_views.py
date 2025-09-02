"""
APIs AJAX - DESS
Controlador para APIs internas AJAX del dashboard
"""
import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess
from infrastructure.security.permissions import ajax_login_required, ajax_super_admin_required
from infrastructure.validation.decorators import sanitize_input
from infrastructure.validation.validators import AssignmentValidator

logger = logging.getLogger(__name__)


@ajax_login_required
def api_user_profile(request):
    """API para obtener perfil del usuario"""
    user = request.user
    
    data = {
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'role': user.get_role_display(),
        'is_super_admin': user.is_super_admin(),
        'assigned_solutions_count': user.assigned_solutions.filter(
            usersolutionassignment__is_active=True
        ).count() if not user.is_super_admin() else 'ALL'
    }
    
    return JsonResponse(data)


@ajax_super_admin_required
@sanitize_input(fields=['assignment_id'], max_lengths={'assignment_id': 20})
def api_remove_assignment(request):
    """API para remover asignación de solución"""
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')
        
        # Validar ID de asignación
        if not assignment_id or not assignment_id.isdigit():
            return JsonResponse({
                'success': False,
                'error': 'INVALID_ASSIGNMENT_ID',
                'message': 'ID de asignación inválido'
            }, status=400)
        
        try:
            assignment = UserSolutionAssignment.objects.get(id=int(assignment_id))
            assignment.is_active = False
            assignment.save()
            
            logger.info(f"Assignment {assignment_id} removed by admin {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': 'Asignación removida correctamente'
            })
        except UserSolutionAssignment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'ASSIGNMENT_NOT_FOUND',
                'message': 'Asignación no encontrada'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_super_admin_required
def api_delete_user(request):
    """API para eliminar un usuario"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        
        try:
            # Usar el servicio de usuario para eliminar
            from infrastructure.dependency_setup import get_user_service
            user_service = get_user_service()
            
            # Verificar que el usuario existe
            existing_user = user_service.get_user(user_id)
            if not existing_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no encontrado'
                }, status=404)
            
            # Verificar que no sea el usuario actual
            if int(user_id) == request.user.id:
                return JsonResponse({
                    'success': False,
                    'message': 'No puedes eliminar tu propia cuenta'
                }, status=400)
            
            # Eliminar usuario
            deleted = user_service.delete_user(int(user_id))
            
            if deleted:
                return JsonResponse({
                    'success': True,
                    'message': f'Usuario "{existing_user.username}" eliminado exitosamente'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al eliminar usuario'
                }, status=500)
                
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f'Error deleting user: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_super_admin_required
def api_delete_solution(request):
    """API para eliminar una solución"""
    if request.method == 'POST':
        solution_id = request.POST.get('solution_id')
        
        try:
            # Verificar que la solución existe
            solution = get_object_or_404(Solution, id=solution_id)
            
            # Obtener información antes de eliminar para logging
            solution_name = solution.name
            
            # Eliminar todas las asignaciones y accesos relacionados
            UserSolutionAssignment.objects.filter(solution=solution).delete()
            UserSolutionAccess.objects.filter(solution=solution).delete()
            
            # Eliminar la solución
            solution.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Solución "{solution_name}" eliminada exitosamente'
            })
            
        except Exception as e:
            logger.error(f'Error deleting solution: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_super_admin_required
def admin_stats_api(request):
    """
    API para estadísticas del dashboard de admin
    Devuelve datos en formato JSON para gráficos y métricas
    """
    try:
        # Estadísticas de usuarios
        total_users = DESSUser.objects.count()
        active_users = DESSUser.objects.filter(is_active=True).count()
        super_admins = DESSUser.objects.filter(role='super_admin').count()
        
        # Estadísticas de soluciones
        total_solutions = Solution.objects.count()
        active_solutions = Solution.objects.filter(status='active').count()
        inactive_solutions = Solution.objects.filter(status='inactive').count()
        maintenance_solutions = Solution.objects.filter(status='maintenance').count()
        
        # Estadísticas de asignaciones
        total_assignments = UserSolutionAssignment.objects.filter(is_active=True).count()
        
        # Accesos recientes (últimas 24 horas)
        from django.utils import timezone
        from datetime import timedelta
        yesterday = timezone.now() - timedelta(days=1)
        recent_accesses = UserSolutionAccess.objects.filter(
            accessed_at__gte=yesterday
        ).count()
        
        # Preparar respuesta
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users,
                'super_admins': super_admins,
                'regular_users': total_users - super_admins
            },
            'solutions': {
                'total': total_solutions,
                'active': active_solutions,
                'inactive': inactive_solutions,
                'maintenance': maintenance_solutions,
                'error': total_solutions - active_solutions - inactive_solutions - maintenance_solutions
            },
            'assignments': {
                'total': total_assignments,
                'recent_accesses': recent_accesses
            },
            'system': {
                'uptime': 'OK',  # TODO: implementar uptime real
                'version': '1.0.0'
            }
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f'Error getting admin stats: {str(e)}')
        return JsonResponse({
            'error': 'Error al obtener estadísticas',
            'message': str(e)
        }, status=500)