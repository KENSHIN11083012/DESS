from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import api_status
from .dashboard_urls import dashboard_urlpatterns
from .api_urls import urlpatterns as api_urlpatterns

# Router para ViewSets
router = DefaultRouter()

# URLs principales de la aplicación web
urlpatterns = [
    # Estado de la API
    path('status/', api_status, name='api_v1_status'),
    
    # Autenticación JWT
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API Endpoints del router
    path('', include(router.urls)),
] + dashboard_urlpatterns + api_urlpatterns
