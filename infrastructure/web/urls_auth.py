"""
URLs de Autenticación - DESS
Rutas para login, logout y autenticación JWT
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import dashboard_views

# URLs de autenticación web y API
urlpatterns = [
    # Autenticación web
    path('login/', dashboard_views.login_view, name='login'),
    path('logout/', dashboard_views.logout_view, name='logout'),
    
    # Autenticación API (JWT)
    path('api/auth/login/', TokenObtainPairView.as_view(), name='api_auth_login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api_auth_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='api_auth_verify'),
]