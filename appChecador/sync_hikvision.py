import os
import sys
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

IP = "192.168.110.19"
USER = "admin"
PASS = "lacteos3312"
URL = f"http://{IP}/ISAPI/AccessControl/AcsEvent?format=json"
BATCH_SIZE = 50
DUPLICATE_MARGIN_SECONDS = 300
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ultimo_serial_checadas.txt")


def obtener_modelos():
    from appChecador.models import Empleado, RegistroAsistencia
    return Empleado, RegistroAsistencia


def obtener_motor_asistencias():
    from appChecador.attendance_engine import reprocesar_jornadas_empleado
    return reprocesar_jornadas_empleado


def obtener_ultimo_serial_guardado():
    if not os.path.exists(STATE_FILE):
        return 0

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as archivo:
            return int(archivo.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def guardar_ultimo_serial(serial_no):
    with open(STATE_FILE, 'w', encoding='utf-8') as archivo:
        archivo.write(str(serial_no))


def obtener_ultimo_serial_bd():
    _, RegistroAsistencia = obtener_modelos()
    seriales = (
        RegistroAsistencia.objects.exclude(hikvision_event_id__isnull=True)
        .exclude(hikvision_event_id='')
        .values_list('hikvision_event_id', flat=True)
    )

    ultimo_serial = 0
    for serial in seriales:
        try:
            ultimo_serial = max(ultimo_serial, int(serial))
        except (TypeError, ValueError):
            continue
    return ultimo_serial


def obtener_ultimo_serial_sincronizado():
    return max(obtener_ultimo_serial_guardado(), obtener_ultimo_serial_bd())


def construir_payload(posicion):
    return {
        "AcsEventCond": {
            "searchID": "1",
            "searchResultPosition": posicion,
            "maxResults": BATCH_SIZE,
            "major": 5,
            "minor": 75,
        }
    }


def sincronizar_checadas():
    Empleado, RegistroAsistencia = obtener_modelos()
    reprocesar_jornadas_empleado = obtener_motor_asistencias()
    ultimo_serial = obtener_ultimo_serial_sincronizado()
    posicion = 0
    creados = 0
    duplicados = 0
    sin_empleado = 0
    omitidos_margen = 0
    total_eventos = 0
    ultimo_serial_procesado = ultimo_serial
    empleados_afectados = set()

    while True:
        payload = construir_payload(posicion)
        response = requests.post(
            URL,
            auth=HTTPDigestAuth(USER, PASS),
            json=payload,
            timeout=15,
        )

        if response.status_code != 200:
            print(f"Error del equipo. Codigo: {response.status_code}")
            print(response.text)
            return

        data = response.json().get('AcsEvent', {})
        eventos = data.get('InfoList', [])
        total_matches = data.get('totalMatches', 0)
        response_status = data.get('responseStatusStrg', 'OK')

        if not eventos:
            break

        for evento in eventos:
            total_eventos += 1

            serial_no = evento.get('serialNo')
            if serial_no is None:
                continue
            serial_no = int(serial_no)
            ultimo_serial_procesado = max(ultimo_serial_procesado, serial_no)

            if serial_no <= ultimo_serial:
                duplicados += 1
                continue

            id_bio = evento.get('employeeNoString')
            fecha_str = evento.get('time')

            empleado = Empleado.objects.filter(id_biometrico=id_bio).first()
            if not empleado:
                sin_empleado += 1
                print(f"Empleado no encontrado para ID biometrico {id_bio}. Evento {serial_no} omitido.")
                continue

            fecha_obj = datetime.fromisoformat(fecha_str)
            ultimo_registro = (
                RegistroAsistencia.objects.filter(empleado=empleado)
                .order_by('-fecha_hora_real')
                .first()
            )

            if ultimo_registro:
                diferencia_segundos = abs((fecha_obj - ultimo_registro.fecha_hora_real).total_seconds())
                if diferencia_segundos <= DUPLICATE_MARGIN_SECONDS:
                    omitidos_margen += 1
                    print(
                        f"Evento {serial_no} omitido por doble checada. "
                        f"Empleado {empleado.id_biometrico} con diferencia de {int(diferencia_segundos)} segundos."
                    )
                    continue

            registro, created = RegistroAsistencia.objects.get_or_create(
                hikvision_event_id=str(serial_no),
                defaults={
                    'empleado': empleado,
                    'fecha_hora_real': fecha_obj,
                    'tipo': 'IN',
                    'observaciones': (
                        f"Hikvision | lector {evento.get('cardReaderNo')} | "
                        f"modo {evento.get('currentVerifyMode', 'N/A')}"
                    ),
                }
            )

            if created:
                creados += 1
                empleados_afectados.add(empleado.id)
                print(
                    f"Nuevo registro: serial {serial_no} | "
                    f"empleado {empleado.id_biometrico} - {empleado.nombre} | "
                    f"hora {registro.fecha_hora_real}"
                )
            else:
                duplicados += 1

        posicion += len(eventos)

        if response_status != 'MORE' or posicion >= total_matches:
            break

    guardar_ultimo_serial(ultimo_serial_procesado)

    for empleado_id in empleados_afectados:
        empleado = Empleado.objects.filter(id=empleado_id).first()
        if empleado:
            reprocesar_jornadas_empleado(empleado)

    return {
        'total_eventos': total_eventos,
        'creados': creados,
        'duplicados': duplicados,
        'sin_empleado': sin_empleado,
        'omitidos_margen': omitidos_margen,
        'ultimo_serial': ultimo_serial_procesado,
        'margen_segundos': DUPLICATE_MARGIN_SECONDS,
    }


if __name__ == "__main__":
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(BASE_DIR)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'checador_ln.settings')
        import django
        django.setup()

        resumen = sincronizar_checadas()
        print(f"Consultando Hikvision en {URL}...")
        print(f"Ultimo serial sincronizado en BD o archivo: {obtener_ultimo_serial_sincronizado()}")
        print("")
        print("Resumen de sincronizacion")
        print(f"Eventos leidos del equipo: {resumen['total_eventos']}")
        print(f"Registros nuevos guardados: {resumen['creados']}")
        print(f"Eventos ya existentes o antiguos: {resumen['duplicados']}")
        print(f"Eventos omitidos por empleado no encontrado: {resumen['sin_empleado']}")
        print(f"Eventos omitidos por margen de {resumen['margen_segundos']} segundos: {resumen['omitidos_margen']}")
    except Exception as error:
        print(f"Error de sincronizacion: {error}")
