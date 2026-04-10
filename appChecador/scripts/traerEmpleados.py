import requests
from requests.auth import HTTPDigestAuth
import json

IP = "192.168.110.19"
USER = "admin"
PASS = "lacteos3312" 

# Nuevo Endpoint para búsqueda de información de usuarios
url = f"http://{IP}/ISAPI/AccessControl/UserInfo/Search?format=json"

# Payload específico para este endpoint
payload = {
    "UserInfoSearchCond": {
        "searchID": "1",
        "searchResultPosition": 0,
        "maxResults": 100
    }
}

try:
    print(f"📡 Consultando lista de empleados en {IP}...")
    response = requests.post(
        url, 
        auth=HTTPDigestAuth(USER, PASS), 
        json=payload, 
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        # En este modelo la lista viene dentro de 'UserInfo'
        usuarios = data.get('UserInfoSearch', {}).get('UserInfo', [])
        
        if usuarios:
            print(f"✅ Se encontraron {len(usuarios)} personas registradas:")
            print("-" * 50)
            for u in usuarios:
                id_bio = u.get('employeeNo')
                nombre = u.get('name')
                print(f"👤 Nombre: {nombre} | ID Biométrico: {id_bio}")
            print("-" * 50)
        else:
            print("📭 No hay usuarios registrados en el equipo.")
            
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"💥 Error de conexión: {e}")