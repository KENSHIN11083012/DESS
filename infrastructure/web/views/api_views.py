"""
APIs AJAX - DESS
Controlador para APIs internas AJAX del dashboard
"""
import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess, UserFavoriteSolution
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


@ajax_login_required
def api_toggle_favorite(request):
    """API para alternar solución como favorita"""
    if request.method == 'POST':
        solution_id = request.POST.get('solution_id')
        
        try:
            # Verificar que la solución existe y el usuario tiene acceso
            solution = get_object_or_404(Solution, id=solution_id)
            
            # Verificar que el usuario tiene acceso a esta solución
            if not request.user.can_access_solution(solution_id):
                return JsonResponse({
                    'success': False,
                    'message': 'No tienes acceso a esta solución'
                }, status=403)
            
            # Alternar favorito
            favorite, created = UserFavoriteSolution.objects.get_or_create(
                user=request.user,
                solution=solution
            )
            
            if created:
                message = f'"{solution.name}" agregada a favoritos'
                is_favorite = True
            else:
                favorite.delete()
                message = f'"{solution.name}" removida de favoritos'
                is_favorite = False
            
            return JsonResponse({
                'success': True,
                'message': message,
                'is_favorite': is_favorite
            })
                
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f'Error toggling favorite: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_login_required
@sanitize_input(fields=['full_name', 'email'], max_lengths={'full_name': 100, 'email': 254})
def api_update_profile(request):
    """API para actualizar información del perfil de usuario"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        try:
            user = request.user
            
            # Validar datos requeridos
            if not full_name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre completo es requerido'
                }, status=400)
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': 'El email es requerido'
                }, status=400)
            
            # Validar formato de email
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de email inválido'
                }, status=400)
            
            # Verificar que el email no esté en uso por otro usuario
            if DESSUser.objects.filter(email=email).exclude(id=user.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Este email ya está en uso por otro usuario'
                }, status=400)
            
            # Actualizar información
            user.full_name = full_name
            user.email = email
            user.save()
            
            logger.info(f'User profile updated: {user.username}')
            
            return JsonResponse({
                'success': True,
                'message': 'Información actualizada exitosamente',
                'data': {
                    'full_name': user.full_name,
                    'email': user.email
                }
            })
                
        except Exception as e:
            logger.error(f'Error updating profile: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_login_required
@sanitize_input(fields=['current_password', 'new_password', 'confirm_password'], max_lengths={'current_password': 128, 'new_password': 128, 'confirm_password': 128})
def api_change_password(request):
    """API para cambiar contraseña del usuario"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        try:
            user = request.user
            
            # Validar datos requeridos
            if not current_password:
                return JsonResponse({
                    'success': False,
                    'message': 'La contraseña actual es requerida'
                }, status=400)
            
            if not new_password:
                return JsonResponse({
                    'success': False,
                    'message': 'La nueva contraseña es requerida'
                }, status=400)
            
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'message': 'Las contraseñas no coinciden'
                }, status=400)
            
            # Verificar contraseña actual
            if not user.check_password(current_password):
                return JsonResponse({
                    'success': False,
                    'message': 'La contraseña actual es incorrecta'
                }, status=400)
            
            # Validar nueva contraseña
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'message': ' '.join(e.messages)
                }, status=400)
            
            # Cambiar contraseña
            user.set_password(new_password)
            user.save()
            
            logger.info(f'Password changed for user: {user.username}')
            
            return JsonResponse({
                'success': True,
                'message': 'Contraseña cambiada exitosamente. Por seguridad, tu sesión será renovada.'
            })
                
        except Exception as e:
            logger.error(f'Error changing password: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_login_required
def api_update_pagination_preferences(request):
    """API para actualizar preferencias de paginación del usuario"""
    if request.method == 'POST':
        items_per_page = request.POST.get('items_per_page')
        
        try:
            # Validar que sea un número válido
            items_per_page = int(items_per_page)
            
            # Validar rango permitido (entre 5 y 50 elementos por página)
            if items_per_page < 5 or items_per_page > 50:
                return JsonResponse({
                    'success': False,
                    'message': 'El número de elementos debe estar entre 5 y 50'
                }, status=400)
            
            # Guardar en sesión del usuario
            request.session['pagination_items_per_page'] = items_per_page
            
            return JsonResponse({
                'success': True,
                'message': f'Configuración actualizada: {items_per_page} elementos por página',
                'items_per_page': items_per_page
            })
                
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Valor de paginación inválido'
            }, status=400)
        except Exception as e:
            logger.error(f'Error updating pagination preferences: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@ajax_login_required
def api_get_user_preferences(request):
    """API para obtener preferencias del usuario"""
    try:
        preferences = {
            'pagination': {
                'items_per_page': request.session.get('pagination_items_per_page', 12)
            },
            'filters': {
                'auto_apply': request.session.get('auto_apply_filters', True)
            }
        }
        
        return JsonResponse({
            'success': True,
            'preferences': preferences
        })
        
    except Exception as e:
        logger.error(f'Error getting user preferences: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)