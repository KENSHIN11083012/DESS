"""
Vistas de Usuario mejoradas siguiendo Clean Architecture
Separación completa de lógica de negocio de la capa de presentación
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from infrastructure.security.permissions import user_only_required, solution_access_required
from infrastructure.dependency_injection import get_container
from core.use_cases.user_solution_use_cases import (
    GetUserSolutionsUseCase, 
    FilterUserSolutionsUseCase,
    CheckSolutionAccessUseCase
)
from core.use_cases.user_use_cases import GetUserUseCase

logger = logging.getLogger(__name__)


class CleanUserViewController:
    """
    Controlador limpio para vistas de usuario.
    No contiene lógica de negocio, solo orquestación.
    """
    
    def __init__(self):
        self.container = get_container()
    
    @user_only_required
    def dashboard_view(self, request):
        """Dashboard para usuarios regulares - redirige a soluciones"""
        return redirect('user_solutions')
    
    @user_only_required 
    def solutions_view(self, request):
        """Vista de soluciones con filtrado usando casos de uso"""
        try:
            # Obtener parámetros de filtrado
            search = request.GET.get('search', '').strip()
            solution_type = request.GET.get('type', '').strip()
            status = request.GET.get('status', '').strip()
            
            # Resolver casos de uso desde el contenedor DI
            filter_use_case = self.container.resolve(FilterUserSolutionsUseCase)
            
            # Ejecutar caso de uso con filtros
            user_solutions = filter_use_case.execute(
                user_id=request.user.id,
                search_term=search if search else None,
                solution_type=solution_type if solution_type else None,
                status=status if status else None
            )
            
            # Calcular estadísticas usando casos de uso
            stats = self._calculate_solution_stats(request.user.id)
            
            # Preparar contexto para la vista
            context = {
                'user': request.user,
                'page_title': 'Mis Soluciones',
                'user_solutions': user_solutions,
                'solutions_stats': stats,
                'search_query': search,
                'selected_type': solution_type,
                'selected_status': status,
            }
            
            return render(request, 'dashboard/user_solutions.html', context)
            
        except Exception as e:
            logger.error(f"Error in user solutions view: {str(e)}")
            messages.error(request, 'Error al cargar las soluciones')
            return redirect('user_dashboard')
    
    @solution_access_required
    def solution_access_view(self, request, solution_id):
        """Vista para acceder a una solución específica"""
        try:
            # Verificar acceso usando caso de uso
            check_access_use_case = self.container.resolve(CheckSolutionAccessUseCase)
            
            has_access = check_access_use_case.execute(
                user_id=request.user.id,
                solution_id=solution_id
            )
            
            if not has_access:
                messages.error(request, 'No tienes permisos para acceder a esta solución')
                return redirect('user_solutions')
            
            # Obtener detalles de la solución
            from core.use_cases.solution_use_cases import GetSolutionUseCase
            get_solution_use_case = self.container.resolve(GetSolutionUseCase)
            solution = get_solution_use_case.execute(solution_id)
            
            if not solution:
                messages.error(request, 'Solución no encontrada')
                return redirect('user_solutions')
            
            # Registrar acceso para auditoría
            self._log_solution_access(request.user.id, solution_id, request)
            
            # Redirigir a la solución si tiene URL de acceso
            if solution.access_url and solution.status == 'active':
                return redirect(solution.access_url)
            else:
                messages.error(request, 'La solución no está disponible en este momento')
                return redirect('user_solutions')
                
        except Exception as e:
            logger.error(f"Error accessing solution {solution_id}: {str(e)}")
            messages.error(request, 'Error al acceder a la solución')
            return redirect('user_solutions')
    
    @user_only_required
    def profile_view(self, request):
        """Vista de perfil de usuario"""
        try:
            # Obtener detalles del usuario usando caso de uso
            get_user_use_case = self.container.resolve(GetUserUseCase)
            user_entity = get_user_use_case.execute(request.user.id)
            
            if not user_entity:
                messages.error(request, 'Error al cargar perfil de usuario')
                return redirect('user_dashboard')
            
            context = {
                'user': request.user,
                'user_entity': user_entity,
                'page_title': 'Mi Perfil',
            }
            
            return render(request, 'dashboard/user_profile.html', context)
            
        except Exception as e:
            logger.error(f"Error in user profile view: {str(e)}")
            messages.error(request, 'Error al cargar el perfil')
            return redirect('user_dashboard')
    
    def _calculate_solution_stats(self, user_id: int) -> dict:
        """Calcular estadísticas de soluciones usando casos de uso"""
        try:
            get_user_solutions_use_case = self.container.resolve(GetUserSolutionsUseCase)
            all_solutions = get_user_solutions_use_case.execute(user_id)
            
            stats = {
                'total_assigned': len(all_solutions),
                'ready_solutions': len([s for s in all_solutions 
                                      if s.status == 'active' and s.access_url]),
                'configuring_solutions': len([s for s in all_solutions 
                                            if s.status == 'active' and not s.access_url]),
                'maintenance_solutions': len([s for s in all_solutions 
                                            if s.status == 'maintenance']),
                'recent_accesses': 0,  # TODO: implementar con caso de uso específico
                'favorite_count': 0    # TODO: implementar favoritos
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating solution stats: {str(e)}")
            return {
                'total_assigned': 0,
                'ready_solutions': 0,
                'configuring_solutions': 0,
                'maintenance_solutions': 0,
                'recent_accesses': 0,
                'favorite_count': 0
            }
    
    def _log_solution_access(self, user_id: int, solution_id: int, request):
        """Registrar acceso a solución para auditoría"""
        try:
            # TODO: Implementar caso de uso para logging de accesos
            from django.utils import timezone
            logger.info(f"User {user_id} accessed solution {solution_id} at {timezone.now()}")
        except Exception as e:
            logger.error(f"Error logging solution access: {str(e)}")


# Crear instancia del controlador
clean_user_controller = CleanUserViewController()

# Exportar vistas individuales para compatibilidad con URLs
user_dashboard_view = clean_user_controller.dashboard_view
user_solutions_view = clean_user_controller.solutions_view
solution_access_view = clean_user_controller.solution_access_view
user_profile_view = clean_user_controller.profile_view