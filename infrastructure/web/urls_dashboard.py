"""
URLs de Dashboard - DESS
Rutas para dashboards de usuarios y administradores
"""
from django.urls import path, include
from .views import auth_views, user_views, admin_views, admin_crud_views, deployment_views

# URLs del dashboard
urlpatterns = [
    # Dashboard principal
    path('dashboard/', auth_views.dashboard_view, name='dashboard'),
    
    # Dashboard de usuario
    path('user/dashboard/', user_views.user_dashboard_view, name='user_dashboard'),
    path('user/solutions/', user_views.user_solutions_view, name='user_solutions'),
    path('user/profile/', user_views.user_profile_view, name='user_profile'),
    path('solution/access/<int:solution_id>/', user_views.solution_access_view, name='solution_access'),
    
    # Dashboard de administrador
    path('admin-panel/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/users/', admin_views.admin_users_view, name='admin_users'),
    path('admin-panel/users/create/', admin_crud_views.admin_create_user_view, name='admin_create_user'),
    path('admin-panel/users/<int:user_id>/', admin_views.admin_user_detail_view, name='admin_user_detail'),
    path('admin-panel/solutions/', admin_views.admin_solutions_view, name='admin_solutions'),
    path('admin-panel/solutions/create/', admin_crud_views.admin_create_solution_view, name='admin_create_solution'),
    path('admin-panel/solutions/<int:solution_id>/', admin_views.admin_solution_detail_view, name='admin_solution_detail'),
    path('admin-panel/solutions/<int:solution_id>/edit/', admin_crud_views.admin_edit_solution_view, name='admin_edit_solution'),
    path('admin-panel/solutions/<int:solution_id>/assign/', admin_crud_views.admin_assign_solution_view, name='admin_assign_solution'),
    path('admin-panel/design-system/', admin_crud_views.design_system_view, name='design_system'),
    
    # Gestión de Despliegues
    path('admin-panel/deployments/', deployment_views.deployments_list_view, name='deployments_list'),
    path('admin-panel/deployments/create/', deployment_views.create_deployment_view, name='create_deployment'),
    path('admin-panel/deployments/<uuid:deployment_id>/', deployment_views.deployment_detail_view, name='deployment_detail'),
    
    # URLs de perfil
    # path('', include('infrastructure.web.profile_urls')),
]