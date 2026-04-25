@echo off
setlocal

set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

if exist "%PROJECT_ROOT%\.venv\Scripts\pythonw.exe" (
    set "PYTHONW=%PROJECT_ROOT%\.venv\Scripts\pythonw.exe"
) else (
    set "PYTHONW=pythonw"
)

set "DJANGO_SETTINGS_MODULE=checador_ln.settings"
start "" /min "%PYTHONW%" manage.py runserver 0.0.0.0:8000

