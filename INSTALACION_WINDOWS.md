# Instalacion en Windows

## 1. Copiar el proyecto

1. Copia esta carpeta completa a la computadora destino.
2. Deja el proyecto en una ruta fija, por ejemplo:
   `C:\LacteosNL\repoChecadorLacteosNuevoLeon`

## 2. Instalar Python

1. Descarga el instalador oficial de Python para Windows.
2. Durante la instalacion marca `Add python.exe to PATH`.
3. Verifica con:
   `python --version`

Referencia oficial:
- https://docs.python.org/3.13/using/windows.html

## 3. Instalar MySQL Server

1. Descarga e instala `MySQL Installer for Windows`.
2. Instala al menos:
   - MySQL Server
   - MySQL Workbench
3. En la configuracion del servidor:
   - deja el servicio de Windows activo
   - usa puerto `3306`
   - crea o anota la clave del usuario `root`

Referencia oficial:
- https://dev.mysql.com/doc/mysql-installer/en/

## 4. Crear base de datos e importar respaldo

### Opcion A: con MySQL Workbench

1. Abre MySQL Workbench.
2. Conectate como `root`.
3. Crea la base:
   `CREATE DATABASE checadorlnl CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
4. Usa `Server > Data Import`.
5. Importa tu archivo `.sql` de respaldo.

### Opcion B: por consola

1. Abre PowerShell.
2. Ejecuta:
   `mysql -u root -p -e "CREATE DATABASE checadorlnl CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"`
3. Importa el respaldo:
   `mysql -u root -p checadorlnl < C:\RUTA\TU_RESPALDO.sql`

## 5. Crear entorno virtual e instalar dependencias

1. En PowerShell entra al proyecto:
   `cd C:\LacteosNL\repoChecadorLacteosNuevoLeon`
2. Crea el entorno virtual:
   `python -m venv .venv`
3. Activalo:
   `.\.venv\Scripts\Activate.ps1`
4. Instala dependencias:
   `python -m pip install --upgrade pip`
   `pip install -r requirements.txt`

## 6. Revisar configuracion de base de datos

1. Abre:
   `checador_ln\settings.py`
2. Revisa estos datos:
   - `NAME = 'checadorlnl'`
   - `USER = 'root'`
   - `PASSWORD = 'TU_PASSWORD_REAL'`
   - `HOST = 'localhost'`
   - `PORT = '3306'`

## 7. Aplicar migraciones y validar

Con el entorno virtual activo:

1. `python manage.py migrate`
2. `python manage.py check`
3. Si ocupas un acceso nuevo:
   `python manage.py createsuperuser`

## 8. Prueba manual inicial

1. Ejecuta:
   `python manage.py runserver 0.0.0.0:8000`
2. En esa misma computadora abre:
   `http://127.0.0.1:8000/`
3. Desde otra PC de la misma red abre:
   `http://IP_DE_LA_PC:8000/`

## 9. Arranque automatico sin terminal visible

Ya quedan incluidos estos archivos:

- `scripts\windows\iniciar_servidor_oculto.vbs`
- `scripts\windows\iniciar_servidor_oculto.bat`
- `scripts\windows\sincronizar_checadas_oculto.vbs`
- `scripts\windows\sincronizar_checadas_oculto.bat`

### Tarea 1: iniciar el servidor al prender la computadora

1. Abre `Programador de tareas`.
2. Crea `Crear tarea`, no `Crear tarea basica`.
3. Nombre sugerido:
   `Checador Django`
4. Marca:
   - `Ejecutar tanto si el usuario inicio sesion como si no`
   - `Ejecutar con los privilegios mas altos`
5. En `Desencadenadores`:
   - `Al iniciar el sistema`
6. En `Acciones`:
   - Programa o script:
     `wscript.exe`
   - Agregar argumentos:
     `"C:\LacteosNL\repoChecadorLacteosNuevoLeon\scripts\windows\iniciar_servidor_oculto.vbs"`
7. Guarda la tarea.

### Tarea 2: sincronizar checadas cada 5 minutos

1. Crea otra tarea.
2. Nombre sugerido:
   `Checador Sync Hikvision`
3. Marca:
   - `Ejecutar tanto si el usuario inicio sesion como si no`
   - `Ejecutar con los privilegios mas altos`
4. En `Desencadenadores`:
   - crea uno `Al iniciar el sistema`
   - crea otro `Diariamente`
   - marca repetir tarea cada `5 minutos`
   - durante `Indefinidamente`
5. En `Acciones`:
   - Programa o script:
     `wscript.exe`
   - Agregar argumentos:
     `"C:\LacteosNL\repoChecadorLacteosNuevoLeon\scripts\windows\sincronizar_checadas_oculto.vbs"`

Referencia general de tareas programadas:
- https://learn.microsoft.com/en-us/troubleshoot/windows-client/system-management-components/use-at-command-to-schedule-tasks

## 10. Recomendaciones antes de ponerlo a operar

1. Cambia `DEBUG = False` cuando termines pruebas.
2. Ajusta `ALLOWED_HOSTS` con la IP o nombre de la computadora servidor.
3. Cambia credenciales sensibles del codigo.
4. Haz un respaldo inicial de la base.
5. Ejecuta:
   `python manage.py check --deploy`

Referencia oficial de Django:
- https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

## 11. Nota importante sobre el servidor local

Los scripts incluidos arrancan el proyecto con `runserver` oculto porque es la forma mas simple para tu instalacion local actual y conserva el comportamiento del proyecto tal como hoy funciona.

Si despues quieres dejarlo mas robusto, el siguiente paso recomendable es migrarlo a `waitress`.

Referencia oficial de Waitress:
- https://docs.pylonsproject.org/projects/waitress/en/latest/usage.html
- https://docs.pylonsproject.org/projects/waitress/en/latest/runner.html
