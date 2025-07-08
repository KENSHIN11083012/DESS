"""
Decoradores de permisos para DESS
Controladores de acceso basados en roles
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


def super_admin_required(view_func):
    """
    Decorador que requiere que el usuario sea super administrador
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_super_admin():
            messages.error(request, 'No tienes permisos para acceder a esta sección')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_only_required(view_func):
    """
    Decorador que requiere que el usuario sea un usuario regular (no admin)
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_super_admin():
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
    Decorador para vistas AJAX que requieren ser super administrador
    """
    @wraps(view_func)
    @ajax_login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_super_admin():
            return JsonResponse({'error': 'Super admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def solution_access_required(view_func):
    """
    Decorador que verifica que el usuario tenga acceso a una solución específica
    Espera que se pase solution_id como parámetro en la URL
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, solution_id, *args, **kwargs):
        if not request.user.can_access_solution(solution_id):
            messages.error(request, 'No tienes permisos para acceder a esta solución')
            return redirect('user_dashboard')
        return view_func(request, solution_id, *args, **kwargs)
    return wrapper
