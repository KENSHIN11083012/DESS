from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Cambiar configuración de base de datos entre SQLite y Oracle'

    def add_arguments(self, parser):
        parser.add_argument(
            'database',
            choices=['sqlite', 'oracle'],
            help='Tipo de base de datos a configurar'
        )
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Ejecutar migraciones automáticamente después del cambio'
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Crear superusuario después de las migraciones'
        )
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Cargar datos de ejemplo después de las migraciones'
        )

    def handle(self, *args, **options):
        database_type = options['database']
        
        self.stdout.write(f'Cambiando configuración a {database_type.upper()}...')
        
        # Leer archivo .env actual
        env_path = Path('.env')
        if not env_path.exists():
            self.stdout.write(
                self.style.ERROR('Archivo .env no encontrado. Créalo primero.')
            )
            return
        
        # Leer contenido actual
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Modificar la línea DATABASE_ENGINE
        new_lines = []
        engine_updated = False
        
        for line in lines:
            if line.startswith('DATABASE_ENGINE='):
                new_lines.append(f'DATABASE_ENGINE={database_type}\n')
                engine_updated = True
            else:
                new_lines.append(line)
        
        # Si no existe la línea, agregarla
        if not engine_updated:
            new_lines.append(f'DATABASE_ENGINE={database_type}\n')
        
        # Escribir el archivo actualizado
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Configuración cambiada a {database_type.upper()}')
        )
        
        if database_type == 'oracle':
            self.stdout.write('\n' + '='*60)
            self.stdout.write('CONFIGURACIÓN ORACLE')
            self.stdout.write('='*60)
            self.stdout.write('Asegúrate de configurar las siguientes variables en .env:')
            self.stdout.write('- ORACLE_HOST=tu-servidor-oracle.com')
            self.stdout.write('- ORACLE_PORT=1521')
            self.stdout.write('- ORACLE_SERVICE_NAME=XE')
            self.stdout.write('- ORACLE_USER=dess_user')
            self.stdout.write('- ORACLE_PASSWORD=tu_password_seguro')
            self.stdout.write('\nTambién asegúrate de tener cx_Oracle instalado:')
            self.stdout.write('pip install cx_Oracle')
        
        # Ejecutar migraciones si se solicita
        if options['migrate']:
            self.stdout.write('\nEjecutando migraciones...')
            try:
                call_command('migrate')
                self.stdout.write(self.style.SUCCESS('✓ Migraciones completadas'))
                
                # Crear superusuario si se solicita
                if options['create_superuser']:
                    self.stdout.write('\nCreando superusuario...')
                    call_command('createsuperuser')
                
                # Cargar datos de ejemplo si se solicita
                if options['sample_data']:
                    self.stdout.write('\nCargando datos de ejemplo...')
                    call_command('create_sample_data')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error durante las migraciones: {e}')
                )
                self.stdout.write('Verifica la configuración de la base de datos.')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('PRÓXIMOS PASOS')
        self.stdout.write('='*60)
        
        if not options['migrate']:
            self.stdout.write('1. Ejecutar migraciones:')
            self.stdout.write('   python manage.py migrate')
        
        if not options['create_superuser'] and options['migrate']:
            self.stdout.write('2. Crear superusuario:')
            self.stdout.write('   python manage.py createsuperuser')
        
        if not options['sample_data'] and options['migrate']:
            self.stdout.write('3. Cargar datos de ejemplo (opcional):')
            self.stdout.write('   python manage.py create_sample_data')
        
        self.stdout.write('4. Iniciar servidor:')
        self.stdout.write('   python manage.py runserver')
        
        self.stdout.write(f'\n✓ Configuración de {database_type.upper()} lista!')
