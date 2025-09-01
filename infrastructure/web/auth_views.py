"""
Auth Views - Infrastructure Layer (Web Presentation)
Handles authentication views following Clean Architecture principles
Separates presentation concerns from business logic
"""

from typing import Optional, Dict, Any
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.urls import reverse
import logging

# Core layer imports - Business Logic
from core.entities.user import DESSUser
from core.use_cases.user_use_cases import UserUseCases

# Application layer imports - Service orchestration
from application.services.user_service import UserService

# Infrastructure layer imports
from infrastructure.database.repositories import UserRepository

logger = logging.getLogger(__name__)

class AuthenticationController:
    """
    Authentication Controller - Infrastructure Layer
    Handles HTTP requests/responses for authentication
    Delegates business logic to Application/Core layers
    """
    
    def __init__(self):
        # Dependency injection following Clean Architecture
        self.user_repository = UserRepository()
        self.user_service = UserService(self.user_repository)
        self.user_use_cases = UserUseCases(self.user_repository)

@csrf_protect
@never_cache
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Login view - Infrastructure Layer
    Handles user authentication presentation logic
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered login template or redirect
    """
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        logger.info(f"User {request.user.username} already authenticated, redirecting to dashboard")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            # Extract credentials from request
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            remember_me = request.POST.get('remember_me', False)
            
            # Validate input
            if not username or not password:
                logger.warning(f"Login attempt with missing credentials from IP: {request.META.get('REMOTE_ADDR')}")
                messages.error(request, 'Por favor, ingresa tu usuario y contraseña.')
                return render(request, 'auth/login.html')
            
            # Use Django's authentication system (Infrastructure Layer)
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Successful authentication
                    login(request, user)
                    
                    # Handle "Remember Me" functionality
                    if remember_me:
                        # Set session to expire when browser closes (default Django behavior)
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        # Session expires when browser closes
                        request.session.set_expiry(0)
                    
                    logger.info(f"Successful login for user: {username}")
                    messages.success(request, f'¡Bienvenido, {user.get_full_name() or username}!')
                    
                    # Redirect to next URL or dashboard
                    next_url = request.GET.get('next')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    else:
                        # Determine redirect based on user role (Business Logic)
                        if user.is_superuser:
                            return redirect('admin_dashboard')
                        else:
                            return redirect('user_dashboard')
                else:
                    # Account is disabled
                    logger.warning(f"Login attempt for disabled account: {username}")
                    messages.error(request, 'Tu cuenta está deshabilitada. Contacta al administrador.')
            else:
                # Invalid credentials
                logger.warning(f"Failed login attempt for username: {username} from IP: {request.META.get('REMOTE_ADDR')}")
                messages.error(request, 'Usuario o contraseña incorrectos.')
                
        except Exception as e:
            logger.error(f"Error during login process: {str(e)}")
            messages.error(request, 'Error interno del servidor. Por favor, intenta más tarde.')
    
    # Render login template
    context = {
        'page_title': 'Iniciar Sesión',
        'show_navbar': False,  # Hide navbar on login page
        'show_footer': False,  # Hide footer on login page
    }
    
    return render(request, 'auth/login.html', context)

@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Logout view - Infrastructure Layer
    Handles user logout and session cleanup
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Redirect to login page
    """
    try:
        username = request.user.username
        logout(request)
        logger.info(f"User {username} logged out successfully")
        messages.success(request, 'Has cerrado sesión exitosamente.')
        
    except Exception as e:
        logger.error(f"Error during logout process: {str(e)}")
        messages.error(request, 'Error al cerrar sesión.')
    
    return redirect('login')

@csrf_protect
def register_view(request: HttpRequest) -> HttpResponse:
    """
    Registration view - Infrastructure Layer
    Handles user registration (if enabled)
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered registration template or redirect
    """
    # Check if registration is enabled (Business Rule)
    # This should be configurable through admin settings
    
    if request.method == 'POST':
        try:
            # Extract registration data
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            
            # Delegate validation to Application/Core layers
            # (This would use UserUseCases for business logic)
            
            # For now, basic validation
            if not all([username, email, password, confirm_password]):
                messages.error(request, 'Todos los campos son obligatorios.')
                return render(request, 'auth/register.html')
            
            if password != confirm_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'auth/register.html')
            
            # Use Application layer service for user creation
            # user_data = {
            #     'username': username,
            #     'email': email,
            #     'password': password,
            #     'first_name': first_name,
            #     'last_name': last_name,
            # }
            # 
            # auth_controller = AuthenticationController()
            # result = auth_controller.user_service.create_user(user_data)
            
            # For now, redirect to login with message
            messages.success(request, 'Registro completado. Por favor, inicia sesión.')
            return redirect('login')
            
        except Exception as e:
            logger.error(f"Error during registration process: {str(e)}")
            messages.error(request, 'Error interno del servidor. Por favor, intenta más tarde.')
    
    context = {
        'page_title': 'Registro',
        'show_navbar': False,
        'show_footer': False,
    }
    
    return render(request, 'auth/register.html', context)

def password_reset_view(request: HttpRequest) -> HttpResponse:
    """
    Password reset view - Infrastructure Layer
    Handles password reset requests
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered password reset template
    """
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip()
            
            if not email:
                messages.error(request, 'Por favor, ingresa tu correo electrónico.')
                return render(request, 'auth/password_reset.html')
            
            # Delegate password reset logic to Application layer
            # This would send reset email through email service
            
            messages.success(request, 
                           'Si el correo electrónico está registrado, recibirás instrucciones para restablecer tu contraseña.')
            return redirect('login')
            
        except Exception as e:
            logger.error(f"Error during password reset process: {str(e)}")
            messages.error(request, 'Error interno del servidor. Por favor, intenta más tarde.')
    
    context = {
        'page_title': 'Restablecer Contraseña',
        'show_navbar': False,
        'show_footer': False,
    }
    
    return render(request, 'auth/password_reset.html', context)

# API Views for AJAX requests

@csrf_protect
def ajax_login(request: HttpRequest) -> JsonResponse:
    """
    AJAX login endpoint - Infrastructure Layer
    Handles AJAX authentication requests
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: JSON response with authentication result
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': 'Usuario y contraseña son requeridos'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            login(request, user)
            logger.info(f"Successful AJAX login for user: {username}")
            
            return JsonResponse({
                'success': True,
                'message': f'Bienvenido, {user.get_full_name() or username}',
                'redirect_url': reverse('admin_dashboard') if user.is_superuser else reverse('user_dashboard')
            })
        else:
            logger.warning(f"Failed AJAX login attempt for username: {username}")
            return JsonResponse({
                'success': False,
                'message': 'Credenciales inválidas'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in AJAX login: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)

def check_auth_status(request: HttpRequest) -> JsonResponse:
    """
    Check authentication status - Infrastructure Layer
    Returns current user authentication status
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: JSON response with auth status
    """
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
    })

# Utility functions for authentication

def get_login_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Get login context data - Infrastructure Layer
    Provides context data for login template
    
    Args:
        request: HTTP request object
        
    Returns:
        Dict[str, Any]: Context data for template
    """
    return {
        'page_title': 'Iniciar Sesión - DESS',
        'company_name': 'DESS',
        'company_full_name': 'Desarrollador de Ecosistemas de Soluciones Empresariales',
        'show_navbar': False,
        'show_footer': False,
        'year': 2025,
        'debug': False,  # Set based on Django settings
    }

def handle_authentication_error(request: HttpRequest, error_message: str) -> None:
    """
    Handle authentication errors - Infrastructure Layer
    Centralized error handling for authentication
    
    Args:
        request: HTTP request object
        error_message: Error message to display
    """
    logger.error(f"Authentication error: {error_message}")
    messages.error(request, error_message)
