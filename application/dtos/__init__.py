"""
DTOs para la capa de aplicación.
"""

# User DTOs
from .user_dto import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
)

# Solution DTOs
from .solution_dto import (
    CreateSolutionRequest,
    UpdateSolutionRequest,
    SolutionResponse,
    SolutionListResponse,
    SolutionStatsResponse,
    DeploySolutionRequest,
    DeploymentResponse,
    AssignSolutionRequest,
    SolutionAssignmentResponse,
    UserSolutionsResponse,
)

__all__ = [
    # User DTOs
    'CreateUserRequest',
    'UpdateUserRequest',
    'UserResponse',
    'UserListResponse',
    'UserStatsResponse',
    'LoginRequest',
    'LoginResponse',
    'ChangePasswordRequest',
    
    # Solution DTOs
    'CreateSolutionRequest',
    'UpdateSolutionRequest',
    'SolutionResponse',
    'SolutionListResponse',
    'SolutionStatsResponse',
    'DeploySolutionRequest',
    'DeploymentResponse',
    'AssignSolutionRequest',
    'SolutionAssignmentResponse',
    'UserSolutionsResponse',
]