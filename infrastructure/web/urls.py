"""
URLs principales de DESS
Estructura modular organizada por funcionalidad
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import home_view, api_status

# Router para ViewSets (futuro)
router = DefaultRouter()

# URLs principales organizadas por módulos
urlpatterns = [
    # Página de inicio
    path('', home_view, name='home'),
    
    # Estado del sistema
    path('status/', api_status, name='api_status'),
    
    # URLs de autenticación (login, logout, JWT)
    path('', include('infrastructure.web.urls_auth')),
    
    # URLs de dashboards (user, admin)
    path('', include('infrastructure.web.urls_dashboard')),
    
    # URLs de APIs (AJAX internas y REST)
    path('', include('infrastructure.web.urls_api')),
    
    # Router para ViewSets (futuro)
    path('api/', include(router.urls)),
]
