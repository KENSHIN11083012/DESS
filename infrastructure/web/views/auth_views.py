"""
Vistas de Autenticación - DESS
Responsable de login, logout y redirección por roles
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

logger = logging.getLogger(__name__)


@csrf_protect
def login_view(request):
    """Vista de login personalizada para DESS"""
    if request.user.is_authenticated:
        # Redirigir según el rol del usuario
        if request.user.role == 'super_admin':
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')
    
    # Limpiar mensajes antiguos al acceder al login (GET)
    if request.method == 'GET':
        storage = messages.get_messages(request)
        for message in storage:
            pass  # Esto consume y elimina los mensajes viejos
    
    if request.method == 'POST':
        logger.info(f"Login attempt for user: {request.POST.get('username')}")
        logger.info(f"CSRF token in POST: {'csrfmiddlewaretoken' in request.POST}")
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.full_name}!')
            
            # Redirigir según el rol del usuario después del login
            if user.role == 'super_admin':
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'auth/login.html')


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard principal - redirige según el rol del usuario"""
    if request.user.role == 'super_admin':
        return redirect('admin_dashboard')
    else:
        return redirect('user_dashboard')