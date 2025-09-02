"""
Configuración de dependencias para DESS
Registra todas las dependencias en el contenedor DI
"""
import logging
from .container import get_container

logger = logging.getLogger(__name__)


def setup_dependencies():
    """
    Configurar todas las dependencias de la aplicación.
    """
    container = get_container()
    
    try:
        # === INTERFACES Y REPOSITORIOS ===
        from core.interfaces.repositories import (
            UserRepository, 
            SolutionRepository, 
            SolutionAssignmentRepository
        )
        from infrastructure.database.repositories import (
            DjangoUserRepository,
            DjangoSolutionRepository, 
            DjangoSolutionAssignmentRepository
        )
        
        # Registrar repositorios como singletons
        container.register_singleton(UserRepository, DjangoUserRepository)
        container.register_singleton(SolutionRepository, DjangoSolutionRepository)
        container.register_singleton(SolutionAssignmentRepository, DjangoSolutionAssignmentRepository)
        
        logger.info("Repositories registered successfully")
        
        # === CASOS DE USO ===
        from core.use_cases.user_use_cases import (
            CreateUserUseCase,
            GetUserUseCase,
            UpdateUserUseCase,
            DeleteUserUseCase,
            ListUsersUseCase,
            GetUserStatsUseCase
        )
        from core.use_cases.solution_use_cases import (
            CreateSolutionUseCase,
            GetSolutionUseCase,
            UpdateSolutionUseCase,
            DeleteSolutionUseCase,
            ListSolutionsUseCase,
            GetSolutionStatsUseCase
        )
        from core.use_cases.user_solution_use_cases import (
            GetUserSolutionsUseCase,
            FilterUserSolutionsUseCase,
            AssignSolutionToUserUseCase,
            UnassignSolutionFromUserUseCase,
            CheckSolutionAccessUseCase
        )
        
        # Registrar casos de uso como transients (nueva instancia cada vez)
        container.register_transient(CreateUserUseCase, CreateUserUseCase)
        container.register_transient(GetUserUseCase, GetUserUseCase)
        container.register_transient(UpdateUserUseCase, UpdateUserUseCase)
        container.register_transient(DeleteUserUseCase, DeleteUserUseCase)
        container.register_transient(ListUsersUseCase, ListUsersUseCase)
        container.register_transient(GetUserStatsUseCase, GetUserStatsUseCase)
        
        container.register_transient(CreateSolutionUseCase, CreateSolutionUseCase)
        container.register_transient(GetSolutionUseCase, GetSolutionUseCase)
        container.register_transient(UpdateSolutionUseCase, UpdateSolutionUseCase)
        container.register_transient(DeleteSolutionUseCase, DeleteSolutionUseCase)
        container.register_transient(ListSolutionsUseCase, ListSolutionsUseCase)
        container.register_transient(GetSolutionStatsUseCase, GetSolutionStatsUseCase)
        
        container.register_transient(GetUserSolutionsUseCase, GetUserSolutionsUseCase)
        container.register_transient(FilterUserSolutionsUseCase, FilterUserSolutionsUseCase)
        container.register_transient(AssignSolutionToUserUseCase, AssignSolutionToUserUseCase)
        container.register_transient(UnassignSolutionFromUserUseCase, UnassignSolutionFromUserUseCase)
        container.register_transient(CheckSolutionAccessUseCase, CheckSolutionAccessUseCase)
        
        logger.info("Use cases registered successfully")
        
        # === SERVICIOS DE APLICACIÓN ===
        from application.services.user_service import UserService
        from application.services.solution_service import SolutionService
        
        # Registrar UserService con sus dependencias
        def create_user_service():
            return UserService(
                user_repository=container.resolve(UserRepository),
                get_user_use_case=container.resolve(GetUserUseCase),
                create_user_use_case=container.resolve(CreateUserUseCase),
                update_user_use_case=container.resolve(UpdateUserUseCase),
                delete_user_use_case=container.resolve(DeleteUserUseCase),
                list_users_use_case=container.resolve(ListUsersUseCase),
                get_user_stats_use_case=container.resolve(GetUserStatsUseCase)
            )
        
        # Registrar SolutionService con sus dependencias
        def create_solution_service():
            return SolutionService(
                solution_repository=container.resolve(SolutionRepository),
                assignment_repository=container.resolve(SolutionAssignmentRepository)
            )
        
        container.register_transient(UserService, create_user_service)
        container.register_transient(SolutionService, create_solution_service)
        
        logger.info("Application services registered successfully")
        
        logger.info("All dependencies registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Error setting up dependencies: {str(e)}")
        raise


def setup_test_dependencies():
    """
    Configurar dependencias para testing (con mocks).
    """
    # TODO: Implementar configuración de testing con mocks
    pass