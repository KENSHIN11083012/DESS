"""
URLs de API - DESS  
Rutas para APIs internas (AJAX) y REST API completa
"""
from django.urls import path, include
from . import dashboard_views
from .api_urls import urlpatterns as rest_api_patterns

# APIs AJAX internas para el dashboard
urlpatterns = [
    path('api/user/profile/', dashboard_views.api_user_profile, name='api_user_profile'),
    path('api/admin/remove-assignment/', dashboard_views.api_remove_assignment, name='api_remove_assignment'),
    path('api/admin/delete-user/', dashboard_views.api_delete_user, name='api_delete_user'),
    path('api/admin/delete-solution/', dashboard_views.api_delete_solution, name='api_delete_solution'),
    path('api/admin/stats/', dashboard_views.admin_stats_api, name='api_admin_stats'),
] + rest_api_patterns