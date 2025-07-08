from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response


def home_view(request):
    """Vista de inicio del proyecto DESS - redirección al dashboard"""
    if request.user.is_authenticated:
        return redirect('dashboard')
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
            'documentation': '/api/docs/',
            'schema': '/api/schema/',
            'auth': '/api/v1/auth/',
        }
    })
