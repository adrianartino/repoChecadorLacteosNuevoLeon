import os
import sys
import django
import requests
from requests.auth import HTTPDigestAuth
import logging # <--- Esto es para el "cuadernito" de notas

# 1. Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'checador_ln.settings') 
django.setup()

from appChecador.models import Empleado

# 2. Configurar el archivo de LOG
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registro_sincronizacion.txt")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def sincronizar_empleados():
    IP = "192.168.110.19"
    USER = "admin"
    PASS = "lacteos3312" 
    URL = f"http://{IP}/ISAPI/AccessControl/UserInfo/Search?format=json"

    payload = {
        "UserInfoSearchCond": { "searchID": "1", "searchResultPosition": 0, "maxResults": 100 }
    }

    try:
        response = requests.post(URL, auth=HTTPDigestAuth(USER, PASS), json=payload, timeout=10)
        
        if response.status_code == 200:
            usuarios = response.json().get('UserInfoSearch', {}).get('UserInfo', [])
            creados = 0
            actualizados = 0

            for u in usuarios:
                nombre_raw = u.get('name', '').strip()
                id_bio = u.get('employeeNo')

                if not nombre_raw:
                    logging.info(f"SALTADO: ID {id_bio} no tiene nombre.")
                    continue

                empleado, created = Empleado.objects.update_or_create(
                    id_biometrico=id_bio,
                    defaults={'nombre': nombre_raw}
                )

                if created:
                    logging.info(f"NUEVO: {nombre_raw} (ID: {id_bio})")
                    creados += 1
                else:
                    logging.info(f"ACTUALIZADO: {nombre_raw} (ID: {id_bio})")
                    actualizados += 1

            logging.info(f"RESUMEN: {creados} creados, {actualizados} actualizados.")
            
        else:
            logging.error(f"ERROR EQUIPO: Código {response.status_code}")

    except Exception as e:
        logging.error(f"ERROR SISTEMA: {e}")

if __name__ == "__main__":
    sincronizar_empleados()