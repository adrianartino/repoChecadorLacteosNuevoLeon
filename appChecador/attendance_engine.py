from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import Empleado, Horario, JornadaAsistencia, RegistroAsistencia


DUPLICATE_WINDOW = timedelta(minutes=5)
MAX_JORNADA_DURATION = timedelta(hours=20)
LOCAL_TZ = ZoneInfo("America/Mexico_City")


def _a_hora_local(valor):
    if valor.tzinfo is None:
        return valor.replace(tzinfo=LOCAL_TZ)
    return valor.astimezone(LOCAL_TZ)


def _combinar_fecha_hora(fecha_base, hora_base, tzinfo=None):
    valor = datetime.combine(fecha_base, hora_base)
    if tzinfo is not None:
        valor = valor.replace(tzinfo=tzinfo)
    return valor


def _obtener_horario_base(empleado, registro):
    horarios = [empleado.horario] if empleado.horario else []
    if not horarios:
        return None, _a_hora_local(registro.fecha_hora_real).date()

    mejor_horario = None
    registro_local = _a_hora_local(registro.fecha_hora_real)
    mejor_fecha = registro_local.date()
    mejor_diferencia = None

    for horario in horarios:
        for fecha_candidata in (
            registro_local.date() - timedelta(days=1),
            registro_local.date(),
        ):
            inicio_candidato = _combinar_fecha_hora(fecha_candidata, horario.hora_entrada, LOCAL_TZ)
            diferencia = abs(registro_local - inicio_candidato)
            if mejor_diferencia is None or diferencia < mejor_diferencia:
                mejor_diferencia = diferencia
                mejor_horario = horario
                mejor_fecha = fecha_candidata
            elif (
                mejor_diferencia is not None
                and diferencia == mejor_diferencia
                and fecha_candidata > mejor_fecha
            ):
                # Empate (ej. turno nocturno 23:00): preferir la fecha mas reciente para no duplicar jornadas.
                mejor_horario = horario
                mejor_fecha = fecha_candidata

    return mejor_horario, mejor_fecha


def _calcular_salida_programada(fecha_administrativa, horario, tzinfo=None):
    if not horario:
        return None

    fecha_salida = fecha_administrativa
    if horario.hora_entrada > horario.hora_salida:
        fecha_salida = fecha_administrativa + timedelta(days=1)
    return _combinar_fecha_hora(fecha_salida, horario.hora_salida, tzinfo)


def _calcular_metricas(jornada):
    horario = jornada.horario
    if not horario or not jornada.entrada_real:
        jornada.retardo = False
        jornada.minutos_retardo = 0
        jornada.minutos_extra = 0
        jornada.horas_extra = 0
        return

    entrada_real_local = _a_hora_local(jornada.entrada_real)
    entrada_programada = _combinar_fecha_hora(
        jornada.fecha_administrativa,
        horario.hora_entrada,
        LOCAL_TZ,
    )
    limite_retardo = entrada_programada + timedelta(minutes=horario.tolerancia_entrada)
    if entrada_real_local > limite_retardo:
        jornada.retardo = True
        jornada.minutos_retardo = int((entrada_real_local - limite_retardo).total_seconds() // 60)
    else:
        jornada.retardo = False
        jornada.minutos_retardo = 0

    if not jornada.salida_real:
        jornada.minutos_extra = 0
        jornada.horas_extra = 0
        return

    salida_programada = _calcular_salida_programada(
        jornada.fecha_administrativa,
        horario,
        LOCAL_TZ,
    )
    if not salida_programada:
        jornada.minutos_extra = 0
        jornada.horas_extra = 0
        return

    salida_real_local = _a_hora_local(jornada.salida_real)
    minutos_despues_salida = int((salida_real_local - salida_programada).total_seconds() // 60)
    if minutos_despues_salida < 0:
        minutos_despues_salida = 0

    jornada.minutos_extra = minutos_despues_salida
    if minutos_despues_salida < horario.minimo_minutos_para_contar_extra:
        jornada.horas_extra = 0
    else:
        jornada.horas_extra = 1 + (
            (minutos_despues_salida - horario.minimo_minutos_para_contar_extra) // 60
        )


def _es_nueva_jornada(jornada, registro):
    if not jornada.entrada_real:
        return False

    horario = jornada.horario
    registro_local = _a_hora_local(registro.fecha_hora_real)
    entrada_local = _a_hora_local(jornada.entrada_real)
    if not horario:
        return registro_local - entrada_local >= MAX_JORNADA_DURATION

    if registro_local - entrada_local >= MAX_JORNADA_DURATION:
        return True

    # Turno nocturno aun sin salida: la salida cae al dia siguiente; no confundirla con inicio de otra jornada.
    if (
        not jornada.salida_real
        and horario.hora_entrada > horario.hora_salida
    ):
        salida_prog = _calcular_salida_programada(
            jornada.fecha_administrativa, horario, LOCAL_TZ
        )
        if salida_prog and registro_local <= salida_prog + timedelta(hours=20):
            return False

    if not horario.usa_corte_madrugada and registro_local.date() > jornada.fecha_administrativa:
        return True

    return False


def reprocesar_jornadas_empleado(empleado):
    registros = list(
        RegistroAsistencia.objects.filter(empleado=empleado).order_by('fecha_hora_real', 'id')
    )

    JornadaAsistencia.objects.filter(empleado=empleado).delete()
    if not registros:
        return []

    jornadas = []
    ultima_checada_valida = None
    jornada_actual = None

    for registro in registros:
        registro_local = _a_hora_local(registro.fecha_hora_real)
        registro.retardo = False
        registro.minutos_extra = 0
        registro.horas_extra = 0

        if (
            ultima_checada_valida
            and (registro_local - _a_hora_local(ultima_checada_valida.fecha_hora_real)) < DUPLICATE_WINDOW
        ):
            registro.observaciones = (registro.observaciones or '') + ' | Duplicada por ventana de 5 minutos'
            registro.save(update_fields=['retardo', 'minutos_extra', 'horas_extra', 'observaciones'])
            continue

        ultima_checada_valida = registro

        if jornada_actual and _es_nueva_jornada(jornada_actual, registro):
            _calcular_metricas(jornada_actual)
            jornada_actual.save()
            jornadas.append(jornada_actual)
            jornada_actual = None

        if jornada_actual is None:
            horario, fecha_administrativa = _obtener_horario_base(empleado, registro)
            jornada_actual = JornadaAsistencia(
                empleado=empleado,
                horario=horario,
                fecha_administrativa=fecha_administrativa,
                entrada_real=registro_local,
                observaciones='Generada automaticamente desde checadas Hikvision',
            )
            registro.tipo = 'IN'
            registro.fecha_administrativa = fecha_administrativa
            registro.save(update_fields=['tipo', 'fecha_administrativa', 'retardo', 'minutos_extra', 'horas_extra', 'observaciones'])
            continue

        jornada_actual.salida_real = registro_local
        registro.tipo = 'OUT'
        registro.fecha_administrativa = jornada_actual.fecha_administrativa
        registro.save(update_fields=['tipo', 'fecha_administrativa', 'retardo', 'minutos_extra', 'horas_extra', 'observaciones'])

    if jornada_actual:
        _calcular_metricas(jornada_actual)
        jornada_actual.save()
        jornadas.append(jornada_actual)

    for jornada in jornadas:
        entrada = (
            RegistroAsistencia.objects.filter(
                empleado=empleado,
                fecha_hora_real=jornada.entrada_real,
                fecha_administrativa=jornada.fecha_administrativa,
            ).first()
        )
        if entrada:
            entrada.retardo = jornada.retardo
            entrada.save(update_fields=['retardo'])

        if jornada.salida_real:
            salida = (
                RegistroAsistencia.objects.filter(
                    empleado=empleado,
                    fecha_hora_real=jornada.salida_real,
                    fecha_administrativa=jornada.fecha_administrativa,
                ).first()
            )
            if salida:
                salida.minutos_extra = jornada.minutos_extra
                salida.horas_extra = jornada.horas_extra
                salida.save(update_fields=['minutos_extra', 'horas_extra'])

    return jornadas


def reprocesar_todas_las_jornadas():
    total = 0
    for empleado in Empleado.objects.all():
        reprocesar_jornadas_empleado(empleado)
        total += 1
    return total
