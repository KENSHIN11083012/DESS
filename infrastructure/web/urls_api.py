"""
URLs de API - DESS  
Rutas para APIs internas (AJAX) y REST API completa
"""
from django.urls import path, include
from .views import api_views, deployment_views
from . import base_views
from .api_urls import urlpatterns as rest_api_patterns

# APIs AJAX internas para el dashboard
urlpatterns = [
    # Estado del sistema
    path('api/status/', base_views.api_status, name='api_status_endpoint'),
    
    path('api/user/profile/', api_views.api_user_profile, name='api_user_profile'),
    path('api/admin/remove-assignment/', api_views.api_remove_assignment, name='api_remove_assignment'),
    path('api/admin/delete-user/', api_views.api_delete_user, name='api_delete_user'),
    path('api/admin/delete-solution/', api_views.api_delete_solution, name='api_delete_solution'),
    
    # APIs de despliegue
    path('api/deployments/<uuid:deployment_id>/deploy/', deployment_views.deploy_project_action, name='api_deploy_project'),
    path('api/deployments/<uuid:deployment_id>/stop/', deployment_views.stop_deployment_action, name='api_stop_deployment'),
    path('api/deployments/<uuid:deployment_id>/restart/', deployment_views.restart_deployment_action, name='api_restart_deployment'),
    path('api/deployments/<uuid:deployment_id>/logs/', deployment_views.deployment_logs_view, name='api_deployment_logs'),
    path('api/deployments/detect-type/', deployment_views.detect_project_type_ajax, name='api_detect_project_type'),
    
    # Webhook de GitHub
    path('webhooks/github/<uuid:deployment_id>/', deployment_views.github_webhook_view, name='github_webhook'),
] + rest_api_patterns