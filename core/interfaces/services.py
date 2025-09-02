"""
Interfaces de servicios de dominio
Define contratos para servicios que contienen lógica de negocio compleja
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from core.entities.user import User, UserRole
from core.entities.solution import Solution
from datetime import datetime


class UserDomainService(ABC):
    """
    Interfaz para servicios de dominio relacionados con usuarios.
    Contiene lógica de negocio compleja que no pertenece a entidades.
    """
    
    @abstractmethod
    def validate_user_creation(self, username: str, email: str, full_name: str) -> Dict[str, List[str]]:
        """
        Validar datos para creación de usuario.
        Retorna diccionario con errores por campo.
        """
        pass
    
    @abstractmethod
    def can_user_be_deleted(self, user: User) -> tuple[bool, Optional[str]]:
        """
        Verificar si un usuario puede ser eliminado.
        Retorna (puede_eliminarse, razón_si_no_puede).
        """
        pass
    
    @abstractmethod
    def calculate_user_permissions(self, user: User) -> Dict[str, bool]:
        """
        Calcular permisos efectivos de un usuario.
        """
        pass
    
    @abstractmethod
    def suggest_username(self, full_name: str) -> str:
        """
        Sugerir un nombre de usuario basado en el nombre completo.
        """
        pass


class SolutionDomainService(ABC):
    """
    Interfaz para servicios de dominio relacionados con soluciones.
    """
    
    @abstractmethod
    def validate_solution_creation(self, name: str, repository_url: str) -> Dict[str, List[str]]:
        """
        Validar datos para creación de solución.
        """
        pass
    
    @abstractmethod
    def can_solution_be_deleted(self, solution: Solution) -> tuple[bool, Optional[str]]:
        """
        Verificar si una solución puede ser eliminada.
        """
        pass
    
    @abstractmethod
    def calculate_solution_health_score(self, solution: Solution) -> int:
        """
        Calcular puntaje de salud de la solución (0-100).
        """
        pass
    
    @abstractmethod
    def suggest_solution_version(self, solution: Solution) -> str:
        """
        Sugerir próxima versión para la solución.
        """
        pass


class AssignmentDomainService(ABC):
    """
    Interfaz para servicios de dominio relacionados con asignaciones.
    """
    
    @abstractmethod
    def can_assign_solution_to_user(self, user: User, solution: Solution) -> tuple[bool, Optional[str]]:
        """
        Verificar si una solución puede ser asignada a un usuario.
        """
        pass
    
    @abstractmethod
    def calculate_user_solution_compatibility(self, user: User, solution: Solution) -> int:
        """
        Calcular compatibilidad entre usuario y solución (0-100).
        """
        pass
    
    @abstractmethod
    def get_assignment_recommendations(self, user: User) -> List[Solution]:
        """
        Obtener recomendaciones de soluciones para un usuario.
        """
        pass
    
    @abstractmethod
    def validate_bulk_assignment(self, user_ids: List[int], solution_ids: List[int]) -> Dict[str, List[str]]:
        """
        Validar asignación masiva de soluciones.
        """
        pass


class AuditDomainService(ABC):
    """
    Interfaz para servicios de dominio relacionados con auditoría.
    """
    
    @abstractmethod
    def log_user_action(self, user_id: int, action: str, target_type: str, target_id: int, metadata: Dict[str, Any]) -> None:
        """
        Registrar acción de usuario para auditoría.
        """
        pass
    
    @abstractmethod
    def log_solution_access(self, user_id: int, solution_id: int, ip_address: str, user_agent: str) -> None:
        """
        Registrar acceso a solución.
        """
        pass
    
    @abstractmethod
    def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Obtener resumen de actividad de usuario.
        """
        pass
    
    @abstractmethod
    def get_solution_usage_stats(self, solution_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Obtener estadísticas de uso de solución.
        """
        pass


class NotificationDomainService(ABC):
    """
    Interfaz para servicios de dominio relacionados con notificaciones.
    """
    
    @abstractmethod
    def notify_solution_assigned(self, user: User, solution: Solution) -> None:
        """
        Notificar asignación de solución a usuario.
        """
        pass
    
    @abstractmethod
    def notify_solution_status_change(self, solution: Solution, old_status: str, new_status: str) -> None:
        """
        Notificar cambio de estado de solución.
        """
        pass
    
    @abstractmethod
    def notify_system_maintenance(self, users: List[User], maintenance_window: tuple[datetime, datetime]) -> None:
        """
        Notificar mantenimiento del sistema.
        """
        pass


class SecurityDomainService(ABC):
    """
    Interfaz para servicios de dominio relacionados con seguridad.
    """
    
    @abstractmethod
    def validate_password_strength(self, password: str) -> tuple[bool, List[str]]:
        """
        Validar fortaleza de contraseña.
        Retorna (es_válida, lista_de_errores).
        """
        pass
    
    @abstractmethod
    def detect_suspicious_activity(self, user_id: int, ip_address: str, user_agent: str) -> bool:
        """
        Detectar actividad sospechosa.
        """
        pass
    
    @abstractmethod
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generar token seguro.
        """
        pass
    
    @abstractmethod
    def validate_access_patterns(self, user_id: int, solution_id: int) -> Dict[str, Any]:
        """
        Validar patrones de acceso de usuario.
        """
        pass