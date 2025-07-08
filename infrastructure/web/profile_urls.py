"""
Profile URLs - URLs para funcionalidad de perfil
"""
from django.urls import path
from . import profile_views

urlpatterns = [
    # Vista principal del perfil
    path('profile/', profile_views.profile_view, name='profile'),
    
    # Actualizar perfil
    path('profile/update/', profile_views.update_profile_view, name='update_profile'),
    
    # Cambiar contraseña
    path('profile/change-password/', profile_views.change_password_view, name='change_password'),
    
    # Validación de campos (AJAX)
    path('profile/validate-field/', profile_views.validate_field_view, name='validate_field'),
    
    # Actividad del usuario (AJAX)
    path('profile/activity/', profile_views.profile_activity_view, name='profile_activity'),
    
    # Resumen del perfil (AJAX)
    path('profile/summary/', profile_views.profile_summary_view, name='profile_summary'),
]
