"""
Autenticación JWT personalizada para DESS
Integración optimizada con el sistema de permisos
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .cache import PermissionCache
from .validators import SecurityValidator
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class DESSJWTAuthentication(JWTAuthentication):
    """
    Autenticación JWT personalizada para DESS con validaciones adicionales.
    """
    
    def get_user(self, validated_token):
        """
        Obtener usuario del token con validaciones adicionales.
        """
        try:
            user_id = validated_token[self.get_user_id_claim()]
            user = User.objects.get(id=user_id)
            
            # Validaciones adicionales específicas de DESS
            if not user.is_active:
                logger.warning(f"Intento de acceso con usuario inactivo: {user.username}")
                return AnonymousUser()
            
            # Pre-cargar permisos en caché si es necesario
            self._preload_user_permissions(user)
            
            return user
            
        except (User.DoesNotExist, KeyError) as e:
            logger.error(f"Error obteniendo usuario del token: {str(e)}")
            return AnonymousUser()
    
    def authenticate(self, request):
        """
        Autenticar request con validaciones adicionales.
        """
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            # Log de autenticación exitosa
            if user and user.is_authenticated:
                logger.info(f"Autenticación JWT exitosa para: {user.username}")
            
            return (user, validated_token)
            
        except TokenError as e:
            logger.warning(f"Token JWT inválido: {str(e)}")
            return None
    
    def _preload_user_permissions(self, user):
        """
        Pre-cargar permisos frecuentemente usados en caché.
        """
        # Solo pre-cargar para usuarios autenticados
        if not user or not user.is_authenticated:
            return
        
        # Pre-cargar permisos básicos
        try:
            SecurityValidator.is_super_admin(user)
            SecurityValidator.can_manage_users(user)
            SecurityValidator.can_manage_solutions(user)
        except Exception as e:
            logger.error(f"Error pre-cargando permisos para {user.username}: {str(e)}")
    
    def get_user_id_claim(self):
        """
        Obtener el claim que contiene el ID del usuario.
        """
        return 'user_id'


class DESSTokenError(Exception):
    """
    Excepción personalizada para errores de token de DESS.
    """
    pass


class TokenValidator:
    """
    Validador de tokens JWT específico para DESS.
    """
    
    @staticmethod
    def validate_token_claims(token):
        """
        Validar claims específicos de DESS en el token.
        """
        required_claims = ['user_id', 'token_type', 'exp']
        
        for claim in required_claims:
            if claim not in token:
                raise DESSTokenError(f"Token missing required claim: {claim}")
        
        # Validar audience específico
        if token.get('aud') != 'dess-api':
            raise DESSTokenError("Token audience mismatch")
        
        # Validar issuer específico  
        if token.get('iss') != 'dess-auth-service':
            raise DESSTokenError("Token issuer mismatch")
        
        return True
    
    @staticmethod
    def is_token_blacklisted(token_jti):
        """
        Verificar si un token está en la lista negra.
        """
        # TODO: Implementar blacklist real con Redis/cache
        return False


def invalidate_user_tokens(user_id):
    """
    Invalidar todos los tokens de un usuario específico.
    Se debe llamar cuando el usuario cambie contraseña o sea desactivado.
    """
    # Limpiar caché de permisos
    PermissionCache.clear_user_permissions(user_id)
    
    # TODO: Implementar invalidación real de tokens JWT
    logger.info(f"Tokens invalidados para usuario ID: {user_id}")


def refresh_user_permissions(user_id):
    """
    Refrescar permisos de un usuario en caché.
    Se debe llamar cuando los permisos del usuario cambien.
    """
    PermissionCache.clear_user_permissions(user_id)
    logger.info(f"Permisos refrescados para usuario ID: {user_id}")