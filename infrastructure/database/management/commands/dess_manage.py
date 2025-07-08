"""
Comando unificado para gestión completa de DESS
Reemplaza comandos redundantes: create_sample_data, reset_admin, setup_dess
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from infrastructure.database.models import DESSUser, Solution, UserSolutionAssignment, UserSolutionAccess


class Command(BaseCommand):
    help = 'Comando unificado para gestión completa de DESS'

    def add_arguments(self, parser):
        # Subcomandos principales
        subparsers = parser.add_subparsers(dest='action', help='Acciones disponibles')
        
        # Reset completo
        reset_parser = subparsers.add_parser('reset', help='Resetear sistema completo')
        reset_parser.add_argument('--admin-user', default='admin', help='Usuario administrador')
        reset_parser.add_argument('--admin-password', default='admin123', help='Contraseña administrador')
        reset_parser.add_argument('--admin-email', default='admin@dess.com', help='Email administrador')
        
        # Setup inicial
        setup_parser = subparsers.add_parser('setup', help='Setup inicial con datos de ejemplo')
        setup_parser.add_argument('--skip-admin', action='store_true', help='No crear admin si ya existe')
        
        # Solo soluciones
        solutions_parser = subparsers.add_parser('solutions', help='Crear solo soluciones de ejemplo')
        
        # Solo usuarios
        users_parser = subparsers.add_parser('users', help='Crear usuarios de ejemplo')
        users_parser.add_argument('--count', type=int, default=3, help='Número de usuarios a crear')
        
        # Estadísticas
        stats_parser = subparsers.add_parser('stats', help='Mostrar estadísticas del sistema')

    def handle(self, *args, **options):
        action = options.get('action')
        
        if action == 'reset':
            self.reset_system(options)
        elif action == 'setup':
            self.setup_system(options)
        elif action == 'solutions':
            self.create_solutions()
        elif action == 'users':
            self.create_users(options)
        elif action == 'stats':
            self.show_stats()
        else:
            self.stdout.write(
                self.style.ERROR('Debes especificar una acción: reset, setup, solutions, users, stats')
            )

    def reset_system(self, options):
        """Resetear sistema completo"""
        self.stdout.write(self.style.WARNING('🔄 Reseteando sistema DESS...'))
        
        # Eliminar todos los datos
        self.stdout.write('Eliminando datos existentes...')
        UserSolutionAccess.objects.all().delete()
        UserSolutionAssignment.objects.all().delete()
        DESSUser.objects.all().delete()
        Solution.objects.all().delete()
        
        # Crear admin
        admin_data = {
            'username': options['admin_user'],
            'email': options['admin_email'],
            'full_name': 'Administrador DESS',
            'role': 'super_admin',
        }
        
        admin_user = DESSUser.objects.create(**admin_data)
        admin_user.set_password(options['admin_password'])
        admin_user.save()
        
        self.stdout.write(self.style.SUCCESS(f'✅ Sistema reseteado. Admin: {admin_user.username}'))
        self.print_admin_credentials(admin_user, options['admin_password'])

    def setup_system(self, options):
        """Setup inicial completo"""
        self.stdout.write(self.style.SUCCESS('🚀 Configurando sistema DESS...'))
        
        # Crear soluciones
        self.create_solutions()
        
        # Crear admin si no existe
        if not options.get('skip_admin') or not DESSUser.objects.filter(role='super_admin').exists():
            self.create_admin()
        
        # Crear usuarios de ejemplo
        self.create_users({'count': 3})
        
        # Asignar soluciones
        self.assign_solutions()
        
        self.stdout.write(self.style.SUCCESS('✅ Setup completo'))
        self.show_stats()

    def create_solutions(self):
        """Crear soluciones de ejemplo"""
        solutions_data = [
            {
                'name': 'Portal Corporativo',
                'description': 'Portal web corporativo con noticias, recursos HR y comunicaciones internas',
                'repository_url': 'https://github.com/empresa/portal-corporativo',
                'solution_type': 'web_app',
                'status': 'active',
                'access_url': 'https://portal.empresa.com',
                'version': '2.1.0'
            },
            {
                'name': 'Sistema CRM',
                'description': 'Sistema de gestión de relaciones con clientes y ventas',
                'repository_url': 'https://github.com/empresa/crm-system',
                'solution_type': 'web_app',
                'status': 'active',
                'access_url': 'https://crm.empresa.com',
                'version': '3.5.2'
            },
            {
                'name': 'API de Facturación',
                'description': 'API REST para gestión de facturación electrónica',
                'repository_url': 'https://github.com/empresa/billing-api',
                'solution_type': 'api',
                'status': 'active',
                'access_url': 'https://api.empresa.com/billing',
                'version': '1.8.1'
            },
            {
                'name': 'Herramienta de Reportes',
                'description': 'Aplicación de escritorio para generación de reportes financieros',
                'repository_url': 'https://github.com/empresa/reports-tool',
                'solution_type': 'desktop',
                'status': 'maintenance',
                'version': '4.2.0'
            },
            {
                'name': 'Dashboard Analytics',
                'description': 'Dashboard interactivo para análisis de datos empresariales',
                'repository_url': 'https://github.com/empresa/analytics-dashboard',
                'solution_type': 'web_app',
                'status': 'active',
                'access_url': 'https://analytics.empresa.com',
                'version': '1.5.3'
            }
        ]
        
        created_count = 0
        for solution_data in solutions_data:
            solution, created = Solution.objects.get_or_create(
                name=solution_data['name'],
                defaults=solution_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Solución "{solution.name}" creada')
            else:
                self.stdout.write(f'  ⚠️  Solución "{solution.name}" ya existe')
        
        self.stdout.write(f'📦 {created_count} soluciones nuevas creadas')

    def create_admin(self):
        """Crear administrador por defecto"""
        admin_data = {
            'username': 'admin',
            'email': 'admin@dess.com',
            'full_name': 'Administrador DESS',
            'role': 'super_admin',
        }
        
        admin_user, created = DESSUser.objects.get_or_create(
            username=admin_data['username'],
            defaults=admin_data
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('👤 Administrador creado')
            self.print_admin_credentials(admin_user, 'admin123')
        else:
            self.stdout.write('⚠️  Administrador ya existe')

    def create_users(self, options):
        """Crear usuarios de ejemplo"""
        users_data = [
            {
                'username': 'maria.garcia',
                'email': 'maria.garcia@empresa.com',
                'full_name': 'María García López',
                'role': 'user'
            },
            {
                'username': 'carlos.rodriguez',
                'email': 'carlos.rodriguez@empresa.com',
                'full_name': 'Carlos Rodríguez Martín',
                'role': 'user'
            },
            {
                'username': 'ana.martinez',
                'email': 'ana.martinez@empresa.com',
                'full_name': 'Ana Martínez Fernández',
                'role': 'user'
            },
            {
                'username': 'luis.hernandez',
                'email': 'luis.hernandez@empresa.com',
                'full_name': 'Luis Hernández Gómez',
                'role': 'user'
            },
            {
                'username': 'sofia.lopez',
                'email': 'sofia.lopez@empresa.com',
                'full_name': 'Sofía López Ruiz',
                'role': 'user'
            }
        ]
        
        count = min(options.get('count', 3), len(users_data))
        created_count = 0
        
        for user_data in users_data[:count]:
            user, created = DESSUser.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('demo123456')
                user.save()
                created_count += 1
                self.stdout.write(f'  👤 Usuario "{user.username}" creado')
            else:
                self.stdout.write(f'  ⚠️  Usuario "{user.username}" ya existe')
        
        self.stdout.write(f'👥 {created_count} usuarios nuevos creados')

    def assign_solutions(self):
        """Asignar soluciones a usuarios"""
        assignments_config = [
            ('maria.garcia', ['Portal Corporativo', 'Sistema CRM']),
            ('carlos.rodriguez', ['Sistema CRM', 'API de Facturación', 'Dashboard Analytics']),
            ('ana.martinez', ['Portal Corporativo', 'Dashboard Analytics']),
            ('luis.hernandez', ['Portal Corporativo', 'Sistema CRM', 'Dashboard Analytics']),
            ('sofia.lopez', ['Sistema CRM', 'API de Facturación']),
        ]
        
        admin_user = DESSUser.objects.filter(role='super_admin').first()
        assigned_count = 0
        
        for username, solution_names in assignments_config:
            try:
                user = DESSUser.objects.get(username=username)
                for solution_name in solution_names:
                    try:
                        solution = Solution.objects.get(name=solution_name)
                        assignment, created = UserSolutionAssignment.objects.get_or_create(
                            user=user,
                            solution=solution,
                            defaults={
                                'assigned_by': admin_user,
                                'is_active': True
                            }
                        )
                        if created:
                            assigned_count += 1
                    except Solution.DoesNotExist:
                        continue
            except DESSUser.DoesNotExist:
                continue
        
        self.stdout.write(f'🔗 {assigned_count} asignaciones nuevas creadas')

    def show_stats(self):
        """Mostrar estadísticas del sistema"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 ESTADÍSTICAS DEL SISTEMA DESS')
        self.stdout.write('='*60)
        
        # Usuarios
        total_users = DESSUser.objects.count()
        admins = DESSUser.objects.filter(role='super_admin').count()
        regular_users = DESSUser.objects.filter(role='user').count()
        
        self.stdout.write(f'👥 Usuarios: {total_users} total ({admins} admins, {regular_users} regulares)')
        
        # Soluciones
        total_solutions = Solution.objects.count()
        active_solutions = Solution.objects.filter(status='active').count()
        
        self.stdout.write(f'📦 Soluciones: {total_solutions} total ({active_solutions} activas)')
        
        # Asignaciones
        total_assignments = UserSolutionAssignment.objects.filter(is_active=True).count()
        total_accesses = UserSolutionAccess.objects.count()
        
        self.stdout.write(f'🔗 Asignaciones activas: {total_assignments}')
        self.stdout.write(f'📈 Accesos registrados: {total_accesses}')
        
        # URLs importantes
        self.stdout.write('\n🌐 ACCESOS AL SISTEMA:')
        self.stdout.write('Login: http://127.0.0.1:8000/login/')
        self.stdout.write('Admin Django: http://127.0.0.1:8000/admin/')
        self.stdout.write('API Docs: http://127.0.0.1:8000/api/docs/')

    def print_admin_credentials(self, admin_user, password):
        """Imprimir credenciales del administrador"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('🔐 CREDENCIALES DEL ADMINISTRADOR:')
        self.stdout.write('='*50)
        self.stdout.write(f'Usuario: {admin_user.username}')
        self.stdout.write(f'Contraseña: {password}')
        self.stdout.write(f'Email: {admin_user.email}')
        self.stdout.write(f'Nombre: {admin_user.full_name}')
        self.stdout.write('-'*50)
