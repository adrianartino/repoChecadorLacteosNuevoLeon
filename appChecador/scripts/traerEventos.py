import requests
from requests.auth import HTTPDigestAuth
import json

# Configuración confirmada
IP = "192.168.110.19"
USER = "admin"
PASS = "lacteos3312" # <-- Pon el password con el que entraste al portal web

# Endpoint para buscar eventos de asistencia
url = f"http://{IP}/ISAPI/AccessControl/AcsEvent?format=json"

# Payload para buscar checadas (Major 5, Minor 75 son eventos de asistencia)
payload = {
    "AcsEventCond": {
        "searchID": "1",
        "searchResultPosition": 0,
        "maxResults": 10,
        "major": 5,
        "minor": 75
    }
}

try:
    print(f"📡 Solicitando eventos a {IP}...")
    response = requests.post(
        url, 
        auth=HTTPDigestAuth(USER, PASS), 
        json=payload, 
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        eventos = data.get('AcsEvent', {}).get('InfoList', [])
        
        if eventos:
            print(f"✅ Se encontraron {len(eventos)} eventos recientes:")
            for ev in eventos:
                empleado_id = ev.get('employeeNoString')
                nombre = ev.get('name', 'N/A')
                tiempo = ev.get('time')
                print(f"📍 ID: {empleado_id} | Nombre: {nombre} | Hora: {tiempo}")
        else:
            print("📭 El equipo respondió bien, pero no hay eventos de asistencia registrados aún.")
            print("Tip: Ve al checador, pon tu cara para que registre una entrada y vuelve a correr este script.")
            
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"💥 Error de conexión: {e}")