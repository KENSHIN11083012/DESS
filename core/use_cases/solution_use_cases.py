"""
Solution Use Cases - Lógica de negocio para operaciones de soluciones
Clean Architecture Implementation
"""
from typing import List, Optional
from core.entities.solution import Solution, SolutionStatus, SolutionType
from core.interfaces.repositories import SolutionRepository, SolutionAssignmentRepository


class CreateSolutionUseCase:
    """Caso de uso: Crear una nueva solución"""
    
    def __init__(self, solution_repository: SolutionRepository):
        self.solution_repository = solution_repository
    
    def execute(self, name: str, description: str, repository_url: str,
                solution_type: str, version: str = "1.0.0", is_active: bool = False) -> Solution:
        """
        Ejecutar creación de solución con validaciones de negocio
        """
        # Convertir string a enum
        sol_type = SolutionType(solution_type) if isinstance(solution_type, str) else solution_type
        
        # Validar que no exista el nombre
        if self.solution_repository.exists_by_name(name):
            raise ValueError(f"La solución '{name}' ya existe")
        
        # Crear entidad solución
        solution = Solution(
            id=None,
            name=name,
            description=description,
            repository_url=repository_url,
            solution_type=sol_type,
            version=version,
            status=SolutionStatus.ACTIVE if is_active else SolutionStatus.INACTIVE
        )
        
        # Guardar y retornar
        return self.solution_repository.save(solution)


class GetSolutionUseCase:
    """Caso de uso: Obtener una solución"""
    
    def __init__(self, solution_repository: SolutionRepository):
        self.solution_repository = solution_repository
    
    def execute(self, solution_id: int) -> Optional[Solution]:
        """Obtener solución por ID"""
        return self.solution_repository.find_by_id(solution_id)


class UpdateSolutionUseCase:
    """Caso de uso: Actualizar una solución"""
    
    def __init__(self, solution_repository: SolutionRepository):
        self.solution_repository = solution_repository
    
    def execute(self, solution_id: int, **updates) -> Solution:
        """
        Actualizar solución con validaciones
        """
        # Obtener solución existente
        solution = self.solution_repository.find_by_id(solution_id)
        if not solution:
            raise ValueError(f"Solución con ID {solution_id} no encontrada")
        
        # Validar cambios de nombre si se especifica
        if 'name' in updates and updates['name'] != solution.name:
            if self.solution_repository.exists_by_name(updates['name']):
                raise ValueError(f"La solución '{updates['name']}' ya existe")
        
        # Aplicar actualizaciones
        if 'name' in updates:
            solution.name = updates['name']
        if 'description' in updates:
            solution.description = updates['description']
        if 'repository_url' in updates:
            solution.repository_url = updates['repository_url']
        if 'solution_type' in updates:
            solution.solution_type = updates['solution_type']
        if 'status' in updates:
            solution.status = updates['status']
        if 'version' in updates:
            solution.version = updates['version']
        
        # Validar entidad actualizada
        solution.validate()
        
        return self.solution_repository.save(solution)


class DeleteSolutionUseCase:
    """Caso de uso: Eliminar una solución"""
    
    def __init__(self, solution_repository: SolutionRepository, 
                 assignment_repository: SolutionAssignmentRepository = None):
        self.solution_repository = solution_repository
        self.assignment_repository = assignment_repository
    
    def execute(self, solution_id: int) -> bool:
        """
        Eliminar solución con limpieza de asignaciones
        """
        # Verificar que la solución existe
        solution = self.solution_repository.find_by_id(solution_id)
        if not solution:
            raise ValueError(f"Solución con ID {solution_id} no encontrada")
        
        # Regla de negocio: Limpiar asignaciones antes de eliminar
        if self.assignment_repository:
            self.assignment_repository.remove_all_solution_assignments(solution_id)
        
        # Eliminar solución
        return self.solution_repository.delete(solution_id)


class ListSolutionsUseCase:
    """Caso de uso: Listar soluciones"""
    
    def __init__(self, solution_repository: SolutionRepository):
        self.solution_repository = solution_repository
    
    def execute(self, page: int = 1, page_size: int = 10) -> tuple:
        """Obtener todas las soluciones con paginación"""
        return self.solution_repository.list(page=page, page_size=page_size)


class DeploySolutionUseCase:
    """Caso de uso: Desplegar una solución"""
    
    def __init__(self, solution_repository: SolutionRepository):
        self.solution_repository = solution_repository
    
    def execute(self, solution_id: int, access_url: str = None, version: str = None) -> Solution:
        """
        Desplegar solución - actualizar estado y configuración de despliegue
        """
        # Obtener solución
        solution = self.solution_repository.find_by_id(solution_id)
        if not solution:
            raise ValueError(f"Solución con ID {solution_id} no encontrada")
        
        # Usar método de negocio de la entidad
        solution.deploy(access_url, version)
        
        # Guardar cambios
        return self.solution_repository.save(solution)


class AssignSolutionToUserUseCase:
    """Caso de uso: Asignar solución a usuario"""
    
    def __init__(self, solution_repository: SolutionRepository,
                 assignment_repository: SolutionAssignmentRepository):
        self.solution_repository = solution_repository
        self.assignment_repository = assignment_repository
    
    def execute(self, user_id: int, solution_id: int) -> bool:
        """
        Asignar solución a usuario con validaciones
        """
        # Verificar que la solución existe y está activa
        solution = self.solution_repository.find_by_id(solution_id)
        if not solution:
            raise ValueError(f"Solución con ID {solution_id} no encontrada")
        
        if not solution.is_available_for_users():
            raise ValueError(f"La solución '{solution.name}' no está disponible")
        
        # Verificar que no esté ya asignada
        if self.assignment_repository.is_solution_assigned_to_user(user_id, solution_id):
            raise ValueError(f"La solución ya está asignada al usuario")
        
        return self.assignment_repository.assign_solution_to_user(user_id, solution_id)


class UnassignSolutionFromUserUseCase:
    """Caso de uso: Desasignar solución de usuario"""
    
    def __init__(self, assignment_repository: SolutionAssignmentRepository):
        self.assignment_repository = assignment_repository
    
    def execute(self, user_id: int, solution_id: int) -> bool:
        """
        Desasignar solución de usuario
        """
        # Verificar que esté asignada
        if not self.assignment_repository.is_solution_assigned_to_user(user_id, solution_id):
            raise ValueError(f"La solución no está asignada al usuario")
        
        return self.assignment_repository.unassign_solution_from_user(user_id, solution_id)


class GetUserSolutionsUseCase:
    """Caso de uso: Obtener soluciones de un usuario"""
    
    def __init__(self, assignment_repository: SolutionAssignmentRepository,
                 solution_repository: SolutionRepository):
        self.assignment_repository = assignment_repository
        self.solution_repository = solution_repository
    
    def execute(self, user_id: int) -> List[Solution]:
        """
        Obtener todas las soluciones asignadas a un usuario
        """
        solution_ids = self.assignment_repository.get_user_solutions(user_id)
        
        solutions = []
        for solution_id in solution_ids:
            solution = self.solution_repository.find_by_id(solution_id)
            if solution:
                solutions.append(solution)
        
        return solutions


class GetSolutionStatsUseCase:
    """Caso de uso para obtener estadísticas de soluciones"""
    
    def __init__(self, solution_repository: SolutionRepository):
        self.solution_repository = solution_repository
    
    def execute(self):
        """Obtener estadísticas de soluciones"""
        return {
            'total_solutions': 0,
            'active_solutions': 0,
            'inactive_solutions': 0
        }
