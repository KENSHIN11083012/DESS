"""
Repository Interfaces - Contratos para acceso a datos sin dependencias de infraestructura
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.entities.user import User, UserRole
from core.entities.solution import Solution


class UserRepository(ABC):
    """
    Interfaz abstracta para repositorio de usuarios.
    
    Define el contrato para operaciones de datos sin acoplarse
    a ninguna implementación específica (Django ORM, MongoDB, etc.)
    """
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Guardar usuario (crear o actualizar)"""
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Buscar usuario por ID"""
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """Buscar usuario por nombre de usuario"""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Buscar usuario por email"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[User]:
        """Obtener todos los usuarios"""
        pass
    
    @abstractmethod
    def find_by_role(self, role: UserRole) -> List[User]:
        """Buscar usuarios por rol"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Eliminar usuario por ID"""
        pass
    
    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """Verificar si existe un usuario con este username"""
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Verificar si existe un usuario con este email"""
        pass
    
    @abstractmethod
    def count_total(self) -> int:
        """Contar total de usuarios"""
        pass
    
    @abstractmethod
    def count_active(self) -> int:
        """Contar usuarios activos"""
        pass


class SolutionRepository(ABC):
    """
    Interfaz abstracta para repositorio de soluciones.
    """
    
    @abstractmethod
    def save(self, solution: Solution) -> Solution:
        """Guardar solución (crear o actualizar)"""
        pass
    
    @abstractmethod
    def find_by_id(self, solution_id: int) -> Optional[Solution]:
        """Buscar solución por ID"""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Solution]:
        """Buscar solución por nombre"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Solution]:
        """Obtener todas las soluciones"""
        pass
    
    @abstractmethod
    def find_active(self) -> List[Solution]:
        """Obtener soluciones activas"""
        pass
    
    @abstractmethod
    def find_by_type(self, solution_type) -> List[Solution]:
        """Buscar soluciones por tipo"""
        pass
    
    @abstractmethod
    def delete(self, solution_id: int) -> bool:
        """Eliminar solución por ID"""
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """Verificar si existe una solución con este nombre"""
        pass
    
    @abstractmethod
    def count_total(self) -> int:
        """Contar total de soluciones"""
        pass
    
    @abstractmethod
    def count_active(self) -> int:
        """Contar soluciones activas"""
        pass


class SolutionAssignmentRepository(ABC):
    """
    Interfaz abstracta para repositorio de asignaciones.
    Gestiona la relación entre usuarios y soluciones.
    """
    
    @abstractmethod
    def assign_solution_to_user(self, user_id: int, solution_id: int) -> bool:
        """Asignar solución a usuario"""
        pass
    
    @abstractmethod
    def unassign_solution_from_user(self, user_id: int, solution_id: int) -> bool:
        """Desasignar solución de usuario"""
        pass
    
    @abstractmethod
    def is_solution_assigned_to_user(self, user_id: int, solution_id: int) -> bool:
        """Verificar si solución está asignada a usuario"""
        pass
    
    @abstractmethod
    def get_user_solutions(self, user_id: int) -> List[int]:
        """Obtener IDs de soluciones asignadas a usuario"""
        pass
    
    @abstractmethod
    def get_solution_users(self, solution_id: int) -> List[int]:
        """Obtener IDs de usuarios asignados a solución"""
        pass
    
    @abstractmethod
    def get_all_assignments(self) -> List[tuple]:
        """Obtener todas las asignaciones como tuplas (user_id, solution_id)"""
        pass
    
    @abstractmethod
    def remove_all_user_assignments(self, user_id: int) -> int:
        """Remover todas las asignaciones de un usuario"""
        pass
    
    @abstractmethod
    def remove_all_solution_assignments(self, solution_id: int) -> int:
        """Remover todas las asignaciones de una solución"""
        pass
