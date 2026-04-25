@echo off
setlocal

set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

set PYTHONIOENCODING=utf-8
"%PYTHON%" appChecador\sync_hikvision.py

