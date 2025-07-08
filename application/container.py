"""
Contenedor de dependencias para la capa de aplicación.
Configuración de inyección de dependencias usando Dependency Injector.
"""
from dependency_injector import containers, providers

from core.interfaces.repositories import (
    UserRepository,
    SolutionRepository,
    SolutionAssignmentRepository,
)
from application.services import UserService, SolutionService


class ApplicationContainer(containers.DeclarativeContainer):
    """Contenedor de dependencias para la capa de aplicación."""
    
    # Configuración
    wiring_config = containers.WiringConfiguration(
        modules=[
            "infrastructure.web.views",
            "infrastructure.web.api",
        ]
    )
    
    # Repositorios (se configurarán desde la capa de infraestructura)
    user_repository = providers.Dependency(instance_of=UserRepository)
    solution_repository = providers.Dependency(instance_of=SolutionRepository)
    assignment_repository = providers.Dependency(instance_of=SolutionAssignmentRepository)
    
    # Servicios de aplicación
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )
    
    solution_service = providers.Factory(
        SolutionService,
        solution_repository=solution_repository,
        assignment_repository=assignment_repository,
    )


# Instancia global del contenedor
application_container = ApplicationContainer()


def get_user_service() -> UserService:
    """Obtener instancia del servicio de usuario."""
    return application_container.user_service()


def get_solution_service() -> SolutionService:
    """Obtener instancia del servicio de solución."""
    return application_container.solution_service()


def configure_dependencies(
    user_repo: UserRepository,
    solution_repo: SolutionRepository,
    assignment_repo: SolutionAssignmentRepository
):
    """Configurar dependencias del contenedor."""
    application_container.user_repository.override(user_repo)
    application_container.solution_repository.override(solution_repo)
    application_container.assignment_repository.override(assignment_repo)
