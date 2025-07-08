"""
Profile Views - Vistas para funcionalidad de perfil de usuario
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

# Configurar logging
logger = logging.getLogger(__name__)


@login_required
def profile_view(request):
    """
    Vista principal del perfil de usuario
    """
    try:
        # Importar servicios localmente para evitar circular imports
        from infrastructure.dependency_setup import get_profile_service
        
        profile_service = get_profile_service()
        user_id = request.user.id
        
        # Obtener datos del perfil
        profile_data = profile_service.get_user_profile(user_id)
        activity_data = profile_service.get_user_activity(user_id)
        
        context = {
            'profile': profile_data,
            'activity': activity_data,
            'user': request.user,
            'page_title': 'Mi Perfil'
        }
        
        return render(request, 'dashboard/profile.html', context)
        
    except Exception as e:
        logger.error(f"Error en profile_view: {str(e)}")
        messages.error(request, f"Error al cargar el perfil: {str(e)}")
        return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def update_profile_view(request):
    """
    Vista para actualizar perfil de usuario
    """
    try:
        # Importar servicios localmente
        from infrastructure.dependency_setup import get_profile_service
        
        profile_service = get_profile_service()
        user_id = request.user.id
        
        # Obtener datos del formulario
        updates = {
            'email': request.POST.get('email', '').strip(),
            'full_name': request.POST.get('full_name', '').strip()
        }
        
        # Filtrar campos vacíos
        updates = {k: v for k, v in updates.items() if v}
        
        if not updates:
            messages.warning(request, "No se especificaron cambios")
            return redirect('profile')
        
        # Actualizar perfil
        updated_user = profile_service.update_profile(user_id, updates)
        
        messages.success(request, "Perfil actualizado exitosamente")
        
        # Si es una petición AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Perfil actualizado exitosamente',
                'user': {
                    'email': updated_user.email,
                    'full_name': updated_user.full_name
                }
            })
        
        return redirect('profile')
        
    except Exception as e:
        logger.error(f"Error en update_profile_view: {str(e)}")
        messages.error(request, f"Error al actualizar perfil: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
        
        return redirect('profile')


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    """
    Vista para cambiar contraseña
    """
    try:
        # Importar servicios localmente
        from infrastructure.dependency_setup import get_profile_service
        
        profile_service = get_profile_service()
        user_id = request.user.id
        
        # Obtener datos del formulario
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validaciones
        if not all([current_password, new_password, confirm_password]):
            raise ValueError("Todos los campos son requeridos")
        
        if new_password != confirm_password:
            raise ValueError("Las contraseñas no coinciden")
        
        if len(new_password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        
        # Cambiar contraseña
        success = profile_service.change_password(user_id, current_password, new_password)
        
        if success:
            messages.success(request, "Contraseña cambiada exitosamente")
        
        # Si es una petición AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': 'Contraseña cambiada exitosamente' if success else 'Error al cambiar contraseña'
            })
        
        return redirect('profile')
        
    except Exception as e:
        logger.error(f"Error en change_password_view: {str(e)}")
        messages.error(request, f"Error al cambiar contraseña: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
        
        return redirect('profile')


@login_required
def validate_field_view(request):
    """
    Vista AJAX para validar campos del perfil
    """
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'message': 'Método no permitido'})
    
    try:
        # Importar servicios localmente
        from infrastructure.dependency_setup import get_profile_service
        
        profile_service = get_profile_service()
        user_id = request.user.id
        
        # Obtener datos
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value', '').strip()
        
        if field == 'username':
            result = profile_service.validate_username(value, user_id)
        elif field == 'email':
            result = profile_service.validate_email(value, user_id)
        else:
            result = {'valid': False, 'message': 'Campo no válido'}
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en validate_field_view: {str(e)}")
        return JsonResponse({
            'valid': False,
            'message': f"Error en validación: {str(e)}"
        })


@login_required
def profile_activity_view(request):
    """
    Vista para obtener actividad del usuario (AJAX)
    """
    try:
        # Importar servicios localmente
        from infrastructure.dependency_setup import get_profile_service
        
        profile_service = get_profile_service()
        user_id = request.user.id
        
        activity_data = profile_service.get_user_activity(user_id)
        
        return JsonResponse({
            'success': True,
            'activity': activity_data
        })
        
    except Exception as e:
        logger.error(f"Error en profile_activity_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def profile_summary_view(request):
    """
    Vista para obtener resumen del perfil (AJAX)
    """
    try:
        # Importar servicios localmente
        from infrastructure.dependency_setup import get_profile_service
        
        profile_service = get_profile_service()
        user_id = request.user.id
        
        summary_data = profile_service.get_profile_summary(user_id)
        
        return JsonResponse({
            'success': True,
            'summary': summary_data
        })
        
    except Exception as e:
        logger.error(f"Error en profile_summary_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
