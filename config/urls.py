from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # URLs principales de DESS (incluye todas las funcionalidades)
    path('', include('infrastructure.web.urls')),
]

# Servir archivos media (WhiteNoise maneja los archivos estáticos automáticamente)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Solo en desarrollo, servir archivos estáticos manualmente si es necesario
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
