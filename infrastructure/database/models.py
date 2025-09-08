from django.contrib.auth.models import AbstractUser
from django.db import models
import json
from .managers import SolutionManager, DESSUserManager, UserSolutionAssignmentManager, UserSolutionAccessManager

# Importar modelos de deployment
from .models_package.deployment import Deployment, DeploymentLog, WebhookEvent


class Solution(models.Model):
    """
    Modelo para las soluciones empresariales
    """
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('maintenance', 'En Mantenimiento'),
        ('error', 'Error'),
    ]
    
    TYPE_CHOICES = [
        ('web_app', 'Aplicación Web'),
        ('desktop_app', 'Aplicación de Escritorio'),
        ('mobile_app', 'Aplicación Móvil'),
        ('api', 'API/Servicio Web'),
        ('database', 'Base de Datos'),
        ('other', 'Otro'),
    ]
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Nombre único de la solución"
    )
    description = models.TextField(
        help_text="Descripción detallada de la solución"
    )
    repository_url = models.URLField(
        help_text="URL del repositorio Git"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inactive',
        help_text="Estado actual de la solución"
    )
    solution_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='web_app',
        help_text="Tipo de aplicación"
    )
    access_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL de acceso a la solución desplegada"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Versión actual desplegada"
    )
    created_by = models.ForeignKey(
        'DESSUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_solutions',
        help_text="Usuario que creó la solución"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = SolutionManager()

    class Meta:
        db_table = 'dess_solutions'
        verbose_name = 'Solución'
        verbose_name_plural = 'Soluciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='idx_solution_status'),
            models.Index(fields=['solution_type'], name='idx_solution_type'),
            models.Index(fields=['created_by'], name='idx_solution_created_by'),
            models.Index(fields=['-created_at'], name='idx_solution_created_at'),
            models.Index(fields=['name', 'status'], name='idx_solution_name_status'),
        ]

    def is_accessible(self):
        """Verificar si la solución está accesible"""
        return self.status == 'active' and self.access_url

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class DESSUser(AbstractUser):
    """
    Modelo de usuario personalizado para DESS
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('user', 'User'),
    ]
    
    role = models.CharField(        max_length=20, 
        choices=ROLE_CHOICES, 
        default='user',
        help_text="Rol del usuario en el sistema DESS"
    )
    full_name = models.CharField(
        max_length=200,
        help_text="Nombre completo del usuario"
    )
    assigned_solutions = models.ManyToManyField(
        Solution,
        blank=True,
        through='UserSolutionAssignment',
        through_fields=('user', 'solution'),
        help_text="Soluciones asignadas al usuario"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = DESSUserManager()

    class Meta:
        db_table = 'dess_users'
        verbose_name = 'Usuario DESS'
        verbose_name_plural = 'Usuarios DESS'
        indexes = [
            models.Index(fields=['role'], name='idx_user_role'),
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['username', 'role'], name='idx_user_username_role'),
            models.Index(fields=['is_active'], name='idx_user_is_active'),
        ]

    def is_super_admin(self):
        """Verificar si el usuario es super administrador"""
        return self.role == 'super_admin'

    def can_access_solution(self, solution_id):
        """Verificar si puede acceder a una solución específica"""
        if self.is_super_admin():
            return True
        return self.assigned_solutions.filter(id=solution_id).exists()

    def get_assigned_solutions_list(self):
        """Obtener lista de soluciones asignadas"""
        return self.assigned_solutions.all()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserSolutionAssignment(models.Model):
    """
    Modelo intermedio para asignación de soluciones a usuarios
    """
    user = models.ForeignKey(DESSUser, on_delete=models.CASCADE)
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        DESSUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assignments_made',
        help_text="Usuario que realizó la asignación"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si la asignación está activa"
    )
    
    objects = UserSolutionAssignmentManager()

    class Meta:
        db_table = 'dess_user_solution_assignments'
        verbose_name = 'Asignación de Solución'
        verbose_name_plural = 'Asignaciones de Soluciones'
        unique_together = ['user', 'solution']
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_assignment_user_active'),
            models.Index(fields=['solution', 'is_active'], name='idx_assignment_solution_active'),
            models.Index(fields=['assigned_by'], name='idx_assignment_assigned_by'),
            models.Index(fields=['-assigned_at'], name='idx_assignment_assigned_at'),
        ]
    def __str__(self):
        status = "Activa" if self.is_active else "Inactiva"
        return f"{self.user.username} -> {self.solution.name} ({status})"


class UserSolutionAccess(models.Model):
    """
    Modelo para tracking de accesos (auditoría)
    """
    user = models.ForeignKey(DESSUser, on_delete=models.CASCADE)
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    objects = UserSolutionAccessManager()

    class Meta:
        db_table = 'dess_user_solution_access'
        verbose_name = 'Acceso a Solución'
        verbose_name_plural = 'Accesos a Soluciones'
        indexes = [
            models.Index(fields=['user', '-accessed_at'], name='idx_access_user_time'),
            models.Index(fields=['solution', '-accessed_at'], name='idx_access_solution_time'),
            models.Index(fields=['-accessed_at'], name='idx_access_time'),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.solution.name} at {self.accessed_at}"


class UserFavoriteSolution(models.Model):
    """
    Modelo para gestionar soluciones favoritas de usuarios
    """
    user = models.ForeignKey(
        DESSUser, 
        on_delete=models.CASCADE,
        related_name='favorite_solutions'
    )
    solution = models.ForeignKey(
        Solution, 
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dess_user_favorite_solutions'
        verbose_name = 'Solución Favorita'
        verbose_name_plural = 'Soluciones Favoritas'
        unique_together = ('user', 'solution')
        indexes = [
            models.Index(fields=['user', '-added_at'], name='idx_favorite_user_time'),
            models.Index(fields=['solution'], name='idx_favorite_solution'),
        ]
    
    def __str__(self):
        return f"{self.user.username} ⭐ {self.solution.name}"
