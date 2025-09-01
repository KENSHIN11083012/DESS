@echo off
REM Script para iniciar el servidor de desarrollo DESS

echo ========================================
echo    DESS - Iniciando Servidor
echo ========================================

REM Verificar que existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Error: No se encontró el entorno virtual
    echo Por favor ejecuta: python -m venv venv
    pause
    exit /b 1
)

REM Activar entorno virtual
echo 🔄 Activando entorno virtual...
call venv\Scripts\activate.bat

REM Verificar que Django funcione
echo 🔍 Verificando configuración...
call venv\Scripts\python.exe manage.py check

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: Hay problemas con la configuración de Django
    echo.
    echo Para diagnosticar ejecuta: python diagnose_dess.py
    pause
    exit /b 1
)

echo.
echo ✅ Sistema DESS listo
echo.
echo 🌐 URLs Disponibles:
echo    Login: http://127.0.0.1:8000/login/
echo    Admin: http://127.0.0.1:8000/admin/
echo    API:   http://127.0.0.1:8000/api/docs/
echo.
echo 🔐 Credenciales de Admin:
echo    Usuario: admin
echo    Contraseña: admin123
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================

REM Iniciar servidor Django usando el Python del entorno virtual
call venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
