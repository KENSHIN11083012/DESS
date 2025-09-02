"""
Decoradores de permisos para DESS - OPTIMIZADOS
Controladores de acceso basados en roles con validación centralizada
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .validators import SecurityValidator


def super_admin_required(view_func):
    """
    Decorador optimizado que requiere que el usuario sea super administrador.
    Usa validación centralizada con caché.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not SecurityValidator.is_super_admin(request.user):
            messages.error(request, 'No tienes permisos para acceder a esta sección')
            return redirect(SecurityValidator.get_allowed_redirect_for_user(request.user))
        return view_func(request, *args, **kwargs)
    return wrapper


def user_only_required(view_func):
    """
    Decorador optimizado que requiere que el usuario sea regular (no admin).
    Usa validación centralizada con caché.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if SecurityValidator.is_super_admin(request.user):
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_login_required(view_func):
    """
    Decorador para vistas AJAX que requieren autenticación
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_super_admin_required(view_func):
    """
    Decorador optimizado para vistas AJAX que requieren ser super administrador.
    Usa validación centralizada con caché.
    """
    @wraps(view_func)
    @ajax_login_required
    def wrapper(request, *args, **kwargs):
        if not SecurityValidator.is_super_admin(request.user):
            return JsonResponse({
                'error': 'Super admin access required',
                'redirect': SecurityValidator.get_allowed_redirect_for_user(request.user)
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def solution_access_required(view_func):
    """
    Decorador optimizado que verifica acceso a una solución específica.
    Usa validación centralizada con caché.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, solution_id, *args, **kwargs):
        if not SecurityValidator.can_access_solution(request.user, solution_id):
            messages.error(request, 'No tienes permisos para acceder a esta solución')
            return redirect(SecurityValidator.get_allowed_redirect_for_user(request.user))
        return view_func(request, solution_id, *args, **kwargs)
    return wrapper
