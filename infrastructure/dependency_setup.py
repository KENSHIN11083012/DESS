"""
Configuración de dependencias para DESS.
"""
from infrastructure.database.repositories import (
    DjangoUserRepository,
    DjangoSolutionRepository,
    DjangoSolutionAssignmentRepository,
)
from application.services import UserService, SolutionService, ProfileService
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
    DeploySolutionUseCase
)
from core.use_cases.user_solution_use_cases import (
    AssignSolutionToUserUseCase,
    UnassignSolutionFromUserUseCase,
    GetUserSolutionsUseCase
)
from core.use_cases.profile_use_cases import (
    GetUserProfileUseCase,
    UpdateUserProfileUseCase,
    ChangePasswordUseCase,
    GetUserActivityUseCase,
    ValidateUserDataUseCase
)

# Instancias de repositorios concretos
user_repository = DjangoUserRepository()
solution_repository = DjangoSolutionRepository()
assignment_repository = DjangoSolutionAssignmentRepository()


def get_user_service():
    """Obtener servicio de usuario configurado."""
    # Crear casos de uso
    create_user = CreateUserUseCase(user_repository)
    get_user = GetUserUseCase(user_repository)
    update_user = UpdateUserUseCase(user_repository)
    delete_user = DeleteUserUseCase(user_repository)
    list_users = ListUsersUseCase(user_repository)
    get_user_stats = GetUserStatsUseCase(user_repository)
    
    return UserService(
        create_user_use_case=create_user,
        get_user_use_case=get_user,
        update_user_use_case=update_user,
        delete_user_use_case=delete_user,
        list_users_use_case=list_users,
        get_user_stats_use_case=get_user_stats
    )


def get_solution_service():
    """Obtener servicio de solución configurado."""
    return SolutionService(
        solution_repository=solution_repository,
        assignment_repository=assignment_repository,
        user_repository=user_repository
    )


def get_profile_service():
    """Obtener servicio de perfil configurado."""
    # Crear casos de uso
    get_profile = GetUserProfileUseCase(user_repository)
    update_profile = UpdateUserProfileUseCase(user_repository)
    change_password = ChangePasswordUseCase(user_repository)
    get_activity = GetUserActivityUseCase(user_repository)
    validate_data = ValidateUserDataUseCase(user_repository)
    
    return ProfileService(
        get_profile_use_case=get_profile,
        update_profile_use_case=update_profile,
        change_password_use_case=change_password,
        get_activity_use_case=get_activity,
        validate_data_use_case=validate_data
    )
