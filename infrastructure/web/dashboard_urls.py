"""
URLs para el sistema de dashboard de DESS
Rutas para usuarios y administradores
"""
from django.urls import path, include
from . import dashboard_views

# URLs del dashboard
dashboard_urlpatterns = [
    # Autenticación
    path('login/', dashboard_views.login_view, name='login'),
    path('logout/', dashboard_views.logout_view, name='logout'),    # Dashboard principal
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    
    # Dashboard de usuario
    path('user/dashboard/', dashboard_views.user_dashboard_view, name='user_dashboard'),
    path('user/solutions/', dashboard_views.user_solutions_view, name='user_solutions'),
    path('user/profile/', dashboard_views.user_profile_view, name='user_profile'),
    path('solution/access/<int:solution_id>/', dashboard_views.solution_access_view, name='solution_access'),    # Dashboard de administrador
    path('admin-panel/dashboard/', dashboard_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/users/', dashboard_views.admin_users_view, name='admin_users'),
    path('admin-panel/users/create/', dashboard_views.admin_create_user_view, name='admin_create_user'),
    path('admin-panel/users/<int:user_id>/', dashboard_views.admin_user_detail_view, name='admin_user_detail'),
    path('admin-panel/solutions/', dashboard_views.admin_solutions_view, name='admin_solutions'),
    path('admin-panel/solutions/create/', dashboard_views.admin_create_solution_view, name='admin_create_solution'),
    path('admin-panel/solutions/<int:solution_id>/', dashboard_views.admin_solution_detail_view, name='admin_solution_detail'),
    path('admin-panel/solutions/<int:solution_id>/edit/', dashboard_views.admin_edit_solution_view, name='admin_edit_solution'),
    path('admin-panel/solutions/<int:solution_id>/assign/', dashboard_views.admin_assign_solution_view, name='admin_assign_solution'),
    
    # Sistema de Diseño - Documentación
    path('admin-panel/design-system/', dashboard_views.design_system_view, name='design_system'),
    
    # APIs AJAX
    path('api/user/profile/', dashboard_views.api_user_profile, name='api_user_profile'),
    path('api/admin/remove-assignment/', dashboard_views.api_remove_assignment, name='api_remove_assignment'),
    path('api/admin/delete-user/', dashboard_views.api_delete_user, name='api_delete_user'),
    path('api/admin/delete-solution/', dashboard_views.api_delete_solution, name='api_delete_solution'),
    
    # URLs de perfil - TEMPORALMENTE COMENTADAS PARA DEBUGGING
    # path('', include('infrastructure.web.profile_urls')),
]
