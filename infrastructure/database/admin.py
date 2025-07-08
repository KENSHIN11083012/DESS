from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from django import forms
from .models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess


class UserSolutionAssignmentInline(admin.TabularInline):
    """
    Inline para mostrar asignaciones de soluciones en el usuario
    """
    model = UserSolutionAssignment
    fk_name = 'user'
    extra = 1
    readonly_fields = ('assigned_at', 'assigned_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.assigned_by:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


class SolutionAssignmentInline(admin.TabularInline):
    """
    Inline para mostrar usuarios asignados en la solución
    """
    model = UserSolutionAssignment
    fk_name = 'solution'
    extra = 1
    readonly_fields = ('assigned_at', 'assigned_by')


@admin.register(DESSUser)
class DESSUserAdmin(UserAdmin):
    """
    Administración mejorada para usuarios DESS
    """
    list_display = (
        'username', 
        'full_name', 
        'email', 
        'role_badge', 
        'solutions_count',
        'is_active',
        'last_login',
        'created_at'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'created_at')
    search_fields = ('username', 'full_name', 'email')
    ordering = ('-created_at',)
    
    # Configuración de campos en el formulario
    fieldsets = (
        ('Información Básica', {
            'fields': ('username', 'password', 'full_name', 'email')
        }),
        ('Permisos y Rol', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser'),
            'description': 'Configure el rol y permisos del usuario en DESS'
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    inlines = [UserSolutionAssignmentInline]
    
    def role_badge(self, obj):
        """Mostrar rol con badge colorido"""
        color = '#28a745' if obj.role == 'super_admin' else '#007bff'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Rol'
    
    def solutions_count(self, obj):
        """Mostrar número de soluciones asignadas"""
        if obj.is_super_admin():
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">TODAS</span>'
            )
        count = obj.assigned_solutions.filter(usersolutionassignment__is_active=True).count()
        color = '#dc3545' if count == 0 else '#007bff'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            count
        )
    solutions_count.short_description = 'Soluciones'


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    """
    Administración para soluciones DESS
    """
    list_display = (
        'name',
        'solution_type',
        'status_badge',
        'access_link',
        'version',
        'users_count',
        'created_at'
    )
    list_filter = ('status', 'solution_type', 'created_at')
    search_fields = ('name', 'description', 'repository_url')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'description', 'solution_type')
        }),
        ('Configuración Técnica', {
            'fields': ('repository_url', 'version', 'access_url'),
            'description': 'URLs y configuración técnica de la solución'
        }),
        ('Estado y Control', {
            'fields': ('status',),
            'description': 'Estado actual de la solución'
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SolutionAssignmentInline]
    
    def status_badge(self, obj):
        """Mostrar estado con badge colorido"""
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d',
            'maintenance': '#ffc107',
            'error': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def access_link(self, obj):
        """Mostrar enlace de acceso si está disponible"""
        if obj.access_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007bff; text-decoration: none;">'
                '🔗 Acceder</a>',
                obj.access_url
            )
        return mark_safe('<span style="color: #6c757d;">No disponible</span>')
    access_link.short_description = 'Acceso'
    
    def users_count(self, obj):
        """Mostrar número de usuarios asignados"""
        # Contar usuarios asignados activos
        active_assignments = obj.usersolutionassignment_set.filter(is_active=True).count()
        
        # También contar super admins
        super_admins = DESSUser.objects.filter(role='super_admin').count()
        
        total = active_assignments + super_admins
        color = '#dc3545' if total == 0 else '#007bff'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            total
        )
    users_count.short_description = 'Usuarios'


@admin.register(UserSolutionAssignment)
class UserSolutionAssignmentAdmin(admin.ModelAdmin):
    """
    Administración para asignaciones de soluciones
    """
    list_display = (
        'user',
        'solution',
        'status_badge',
        'assigned_by',
        'assigned_at'
    )
    list_filter = ('is_active', 'assigned_at', 'solution__status')
    search_fields = ('user__username', 'user__full_name', 'solution__name')
    ordering = ('-assigned_at',)
    readonly_fields = ('assigned_at',)
    
    def status_badge(self, obj):
        """Mostrar estado de la asignación"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 8px; '
                'border-radius: 4px; font-size: 11px; font-weight: bold;">Activa</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 4px 8px; '
                'border-radius: 4px; font-size: 11px; font-weight: bold;">Inactiva</span>'
            )
    status_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        if not obj.assigned_by:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserSolutionAccess)
class UserSolutionAccessAdmin(admin.ModelAdmin):
    """
    Administración para auditoría de accesos
    """
    list_display = (
        'user',
        'solution',
        'accessed_at',
        'ip_address'
    )
    list_filter = ('accessed_at', 'solution')
    search_fields = ('user__username', 'user__full_name', 'solution__name')
    ordering = ('-accessed_at',)
    readonly_fields = ('accessed_at',)
    
    def has_add_permission(self, request):
        """No permitir agregar registros manualmente"""
        return False


# Personalizar el sitio de administración
admin.site.site_header = "DESS - Panel de Administración"
admin.site.site_title = "DESS Admin"
admin.site.index_title = "Gestión de Ecosistemas de Soluciones Empresariales"
