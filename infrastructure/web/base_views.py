from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response


def home_view(request):
    """Vista de inicio del proyecto DESS - redirección directa según el rol"""
    if request.user.is_authenticated:
        # Redirigir directamente según el rol sin pasar por 'dashboard'
        if request.user.role == 'super_admin':
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')
    else:
        return redirect('login')


@api_view(['GET'])
def api_status(request):
    """API endpoint para verificar el estado del sistema"""
    return Response({
        'project': 'DESS',
        'status': 'active',
        'version': '1.0.0',
        'message': 'DESS API funcionando correctamente',
        'endpoints': {
            'admin': '/admin/',
            'documentation': reverse('swagger-ui'),
            'schema': reverse('schema'),
            'auth': reverse('api_auth_login'),
        }
    })
