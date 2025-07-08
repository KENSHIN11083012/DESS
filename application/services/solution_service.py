"""
Servicio de aplicación para operaciones de solución.
"""
from typing import List, Optional

from core.entities.solution import Solution
from core.use_cases.solution_use_cases import (
    CreateSolutionUseCase,
    GetSolutionUseCase,
    ListSolutionsUseCase,
    UpdateSolutionUseCase,
    AssignSolutionToUserUseCase,
    GetUserSolutionsUseCase
)
from core.interfaces.repositories import SolutionRepository, SolutionAssignmentRepository
from application.dtos import (
    CreateSolutionRequest,
    UpdateSolutionRequest,
    SolutionResponse,
    SolutionListResponse,
    AssignSolutionRequest,
)


class SolutionService:
    """Servicio de aplicación para operaciones de solución."""
    
    def __init__(self, 
                 solution_repository: SolutionRepository,
                 assignment_repository: SolutionAssignmentRepository):
        self.solution_repository = solution_repository
        self.assignment_repository = assignment_repository
        
        # Inicializar casos de uso
        self.create_solution_use_case = CreateSolutionUseCase(solution_repository)
        self.get_solution_use_case = GetSolutionUseCase(solution_repository)
        self.list_solutions_use_case = ListSolutionsUseCase(solution_repository)
        self.update_solution_use_case = UpdateSolutionUseCase(solution_repository)
        self.assign_solution_use_case = AssignSolutionToUserUseCase(solution_repository, assignment_repository)
        self.get_user_solutions_use_case = GetUserSolutionsUseCase(assignment_repository, solution_repository)
    
    def create_solution(self, request: CreateSolutionRequest) -> SolutionResponse:
        """Crear una nueva solución."""
        solution = self.create_solution_use_case.execute(
            name=request.name,
            description=request.description,
            repository_url=request.repository_url,
            solution_type=request.solution_type,
            version=request.version,
            is_active=request.is_active
        )
        return self._solution_to_response(solution)
    
    def get_solution(self, solution_id: int) -> Optional[SolutionResponse]:
        """Obtener una solución por ID."""
        solution = self.get_solution_use_case.execute(solution_id)
        return self._solution_to_response(solution) if solution else None
    
    def list_solutions(self, page: int = 1, page_size: int = 10) -> SolutionListResponse:
        """Listar soluciones."""
        solutions, total_count = self.list_solutions_use_case.execute(page=page, page_size=page_size)
        
        solution_responses = [self._solution_to_response(solution) for solution in solutions]
        total_pages = (total_count + page_size - 1) // page_size
        
        return SolutionListResponse(
            solutions=solution_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def assign_solution(self, request: AssignSolutionRequest) -> bool:
        """Asignar una solución a un usuario."""
        return self.assign_solution_use_case.execute(
            user_id=request.user_id,
            solution_id=request.solution_id
        )
    
    def get_user_solutions(self, user_id: int) -> List[SolutionResponse]:
        """Obtener soluciones asignadas a un usuario."""
        solutions = self.get_user_solutions_use_case.execute(user_id)
        return [self._solution_to_response(solution) for solution in solutions]
    
    def get_solution_stats(self):
        """Obtener estadísticas de soluciones."""
        from application.dtos import SolutionStatsResponse
        
        # Usar el repositorio para obtener stats reales
        stats = self.solution_repository.get_stats()
        
        return SolutionStatsResponse(
            total_solutions=stats.get('total_solutions', 0),
            active_solutions=stats.get('active_solutions', 0),
            inactive_solutions=stats.get('inactive_solutions', 0),
            deployed_solutions=stats.get('deployed_solutions', 0),
            pending_solutions=stats.get('pending_solutions', 0),
            failed_solutions=stats.get('failed_solutions', 0),
            by_type=stats.get('by_type', {})
        )
    
    def _solution_to_response(self, solution: Solution) -> SolutionResponse:
        """Convertir entidad Solution a SolutionResponse DTO."""
        return SolutionResponse(
            id=solution.id,
            name=solution.name,
            description=solution.description,
            repository_url=solution.repository_url,
            solution_type=solution.solution_type.value,
            status=solution.status.value,
            access_url=solution.access_url,
            version=solution.version,
            created_at=solution.created_at,
            updated_at=solution.updated_at
        )
