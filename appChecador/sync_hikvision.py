import os
import sys
import django
import requests  # <--- ESTA ES LA LÍNEA QUE FALTA
from requests.auth import HTTPDigestAuth
from datetime import datetime

# 1. Configuración de rutas para que encuentre checador_ln
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 2. Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'checador_ln.settings')
django.setup()

# 3. Importación de modelos (SIEMPRE después de django.setup)
from appChecador.models import Empleado, RegistroAsistencia

# ... el resto de la función traer_datos_checador() ...


def traer_datos_checador():
    # 1. Dirección de tu SIMULADOR (Flask)
    URL = "http://127.0.0.1:5000/ISAPI/AccessControl/AcsEvent?format=json"

    # 2. Definimos el payload (EL "PAQUETE" QUE FALTABA)
    payload = {
        "AcsEventCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 50,
            "major": 5, 
            "minor": 75 
        }
    }

    try:
        # 3. Hacemos la petición al simulador (sin auth por ahora)
        print(f"🛰️ Conectando al simulador en {URL}...")
        response = requests.post(URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # El simulador nos devuelve una lista de eventos
            eventos = data.get('AcsEvent', {}).get('InfoList', [])
            
            if not eventos:
                print("📭 No hay eventos nuevos en el simulador.")
                return

            for ev in eventos:
                id_bio = ev.get('employeeNoString')
                fecha_str = ev.get('time')
                
                # Buscamos al empleado en tu MySQL de Django
                empleado = Empleado.objects.filter(id_biometrico=id_bio).first()
                
                if empleado:
                    fecha_obj = datetime.fromisoformat(fecha_str)
                    
                    # get_or_create evita duplicados en la base de datos
                    obj, created = RegistroAsistencia.objects.get_or_create(
                        empleado=empleado,
                        fecha_hora_real=fecha_obj,
                        defaults={'tipo': 'IN'}
                    )
                    
                    if created:
                        print(f"✅ [ID {id_bio}] Registro exitoso: {empleado.nombre} | Fecha Adm: {obj.fecha_administrativa}")
                    else:
                        print(f"⏭️ [ID {id_bio}] El registro ya existía en MySQL.")
                else:
                    print(f"⚠️ [ID {id_bio}] Empleado no encontrado en Django. Crea el ID en el /admin.")
        else:
            print(f"❌ Error del simulador. Código: {response.status_code}")

    except Exception as e:
        print(f"💥 Error de conexión: {e}")

if __name__ == "__main__":
    traer_datos_checador()