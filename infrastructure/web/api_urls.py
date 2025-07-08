"""
URLs para las APIs REST de DESS usando Clean Architecture.
"""
from django.urls import path, include

from .api_user_views import (
    user_list,
    user_detail,
    user_create,
    user_update,
    user_delete,
    user_stats,
    user_login,
    user_profile,
)

from .api_solution_views import (
    solution_list,
    solution_detail,
    solution_create,
    solution_update,
    solution_delete,
    solution_stats,
    solution_assign,
    solution_unassign,
    user_solutions,
)

# URLs para usuarios
user_patterns = [
    path('', user_list, name='api_user_list'),
    path('create/', user_create, name='api_user_create'),
    path('stats/', user_stats, name='api_user_stats'),
    path('profile/', user_profile, name='api_user_profile_jwt'),
    path('<int:user_id>/', user_detail, name='api_user_detail'),
    path('<int:user_id>/update/', user_update, name='api_user_update'),
    path('<int:user_id>/delete/', user_delete, name='api_user_delete'),
    path('<int:user_id>/solutions/', user_solutions, name='api_user_solutions'),
]

# URLs para soluciones
solution_patterns = [
    path('', solution_list, name='api_solution_list'),
    path('create/', solution_create, name='api_solution_create'),
    path('stats/', solution_stats, name='api_solution_stats'),
    path('assign/', solution_assign, name='api_solution_assign'),
    path('unassign/', solution_unassign, name='api_solution_unassign'),
    path('<int:solution_id>/', solution_detail, name='api_solution_detail'),
    path('<int:solution_id>/update/', solution_update, name='api_solution_update'),
    path('<int:solution_id>/delete/', solution_delete, name='api_solution_delete'),
]

# URLs para autenticación
auth_patterns = [
    path('login/', user_login, name='api_auth_login'),
]

# URLs principales de la API v1
api_v1_patterns = [
    path('users/', include(user_patterns)),
    path('solutions/', include(solution_patterns)),
    path('auth/', include(auth_patterns)),
]

# Patrón principal
urlpatterns = [
    path('api/v1/', include(api_v1_patterns)),
]
