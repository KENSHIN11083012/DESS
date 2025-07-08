"""
DTOs para operaciones de solución en la capa de aplicación.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class CreateSolutionRequest:
    """DTO para crear una nueva solución."""
    name: str
    description: str
    repository_url: str
    solution_type: str
    version: Optional[str] = None
    is_active: bool = True


@dataclass
class UpdateSolutionRequest:
    """DTO para actualizar una solución existente."""
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass
class SolutionResponse:
    """DTO de respuesta para operaciones de solución."""
    id: int
    name: str
    description: str
    repository_url: str
    solution_type: str
    status: str
    access_url: Optional[str]
    version: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class SolutionListResponse:
    """DTO para lista de soluciones con paginación."""
    solutions: List[SolutionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


@dataclass
class SolutionStatsResponse:
    """DTO para estadísticas de soluciones."""
    total_solutions: int
    active_solutions: int
    inactive_solutions: int
    deployed_solutions: int
    pending_solutions: int
    failed_solutions: int
    by_type: Dict[str, int]


@dataclass
class DeploySolutionRequest:
    """DTO para desplegar una solución."""
    solution_id: int
    deployment_config: Optional[Dict[str, Any]] = None


@dataclass
class DeploymentResponse:
    """DTO para respuesta de despliegue."""
    deployment_id: str
    solution_id: int
    status: str
    deployment_url: Optional[str]
    logs: List[str]
    started_at: datetime
    completed_at: Optional[datetime]


@dataclass
class AssignSolutionRequest:
    """DTO para asignar solución a usuario."""
    solution_id: int
    user_id: int


@dataclass
class SolutionAssignmentResponse:
    """DTO para respuesta de asignación de solución."""
    id: int
    solution: SolutionResponse
    user_id: int
    assigned_at: datetime
    is_active: bool


@dataclass
class UserSolutionsResponse:
    """DTO para soluciones asignadas a un usuario."""
    user_id: int
    solutions: List[SolutionAssignmentResponse]
    total_count: int
