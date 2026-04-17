"""
Inserta checadas ficticias (prefijo hikvision_event_id SIM-) y reprocesa jornadas.

Uso:
  python manage.py seed_asistencias_ficticias
  python manage.py seed_asistencias_ficticias --dry-run
  python manage.py seed_asistencias_ficticias --append
  python manage.py seed_asistencias_ficticias --anio 2026 --mes 4 --dia-inicio 9 --dia-fin 15
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from appChecador.attendance_engine import reprocesar_todas_las_jornadas
from appChecador.models import Empleado, RegistroAsistencia

LOCAL_TZ = ZoneInfo('America/Mexico_City')
MIN_GAP = timedelta(minutes=10)
# Evita solapamientos raros en reprocesar_jornadas (unicidad empleado + fecha_administrativa).
MAX_DURACION_JORNADA = timedelta(hours=15)


def _combine(fecha, hora, tz=LOCAL_TZ):
    return datetime.combine(fecha, hora, tzinfo=tz)


def _salida_programada_dia(fecha_admin, horario):
    """Fecha/hora local de salida programada para la jornada que inicia en fecha_admin."""
    if not horario:
        return _combine(fecha_admin, time(17, 0))
    fecha_salida = fecha_admin
    if horario.hora_entrada > horario.hora_salida:
        fecha_salida = fecha_admin + timedelta(days=1)
    return _combine(fecha_salida, horario.hora_salida)


def _entrada_programada(fecha_admin, horario):
    if not horario:
        return _combine(fecha_admin, time(8, 0))
    return _combine(fecha_admin, horario.hora_entrada)


def _ajustar_entrada_salida(entrada, salida):
    if salida - entrada < MIN_GAP:
        salida = entrada + MIN_GAP
    return entrada, salida


def _dia_tiene_checadas_reales(empleado, dia, ventana_ini, ventana_fin):
    """True si ya hay checadas reales que ocupan ese día (hora o fecha admin dentro de la ventana)."""
    inicio = timezone.make_aware(datetime.combine(dia, time.min), LOCAL_TZ)
    fin = timezone.make_aware(datetime.combine(dia, time(23, 59, 59)), LOCAL_TZ)
    qs = RegistroAsistencia.objects.filter(empleado=empleado).exclude(
        hikvision_event_id__startswith='SIM-'
    )
    if qs.filter(fecha_hora_real__range=(inicio, fin)).exists():
        return True
    if qs.filter(
        fecha_administrativa=dia,
        fecha_hora_real__gte=ventana_ini,
        fecha_hora_real__lte=ventana_fin,
    ).exists():
        return True
    return False


def _cap_salida_segura(entrada, salida, horario):
    """Limita salida para no cruzar ventanas que confunden al motor de jornadas."""
    salida = min(salida, entrada + MAX_DURACION_JORNADA)
    if horario and horario.hora_entrada <= horario.hora_salida:
        tope = _combine(entrada.date(), time(23, 55))
        salida = min(salida, tope)
    if salida <= entrada:
        salida = entrada + timedelta(hours=8)
    return salida


class Command(BaseCommand):
    help = (
        'Crea checadas ficticias (SIM-) por empleado con horario (9–15 abr por defecto) y reprocesa jornadas. '
        'Por defecto BORRA todas las checadas que solapan ese periodo por empleado (incluye datos reales de esa semana). '
        'Usa --append para no borrar datos reales y solo insertar SIM donde no haya checadas.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--anio', type=int, default=2026)
        parser.add_argument('--mes', type=int, default=4)
        parser.add_argument('--dia-inicio', type=int, default=9)
        parser.add_argument('--dia-fin', type=int, default=15)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument(
            '--append',
            action='store_true',
            help='No borrar checadas reales; solo quita SIM- previas en la ventana y omite dias ya ocupados.',
        )

    def handle(self, *args, **options):
        anio = options['anio']
        mes = options['mes']
        d0 = options['dia_inicio']
        d1 = options['dia_fin']
        dry = options['dry_run']
        append = options['append']

        fecha_ini = date(anio, mes, d0)
        fecha_fin = date(anio, mes, d1)
        ventana_borra_ini = timezone.make_aware(
            datetime.combine(fecha_ini - timedelta(days=1), time(0, 0)),
            LOCAL_TZ,
        )
        ventana_borra_fin = timezone.make_aware(
            datetime.combine(fecha_fin + timedelta(days=2), time(23, 59, 59)),
            LOCAL_TZ,
        )

        empleados = list(
            Empleado.objects.filter(activo=True, horario__isnull=False).select_related('horario')
        )
        sin_horario = Empleado.objects.filter(activo=True, horario__isnull=True).count()

        self.stdout.write(
            f'Empleados con horario: {len(empleados)} | Sin horario (omitidos): {sin_horario}'
        )

        borrar_qs = RegistroAsistencia.objects.filter(
            hikvision_event_id__startswith='SIM-',
            fecha_hora_real__gte=ventana_borra_ini,
            fecha_hora_real__lte=ventana_borra_fin,
        )
        n_borrar = borrar_qs.count()

        if dry:
            if append:
                self.stdout.write(self.style.WARNING(f'[dry-run] Se borrarian {n_borrar} registros SIM-'))
            else:
                q_overlap = Q(fecha_administrativa__range=(fecha_ini, fecha_fin)) | Q(
                    fecha_hora_real__range=(ventana_borra_ini, ventana_borra_fin)
                )
                n_borrar_todo = sum(
                    RegistroAsistencia.objects.filter(empleado=e).filter(q_overlap).count()
                    for e in empleados
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'[dry-run] Modo reemplazo: se borrarian ~{n_borrar_todo} checadas '
                        f'(reales + SIM) que solapan el periodo, por empleado con horario.'
                    )
                )
            dias_inc = (fecha_fin - fecha_ini).days + 1
            self.stdout.write(f'[dry-run] Hasta {len(empleados) * dias_inc * 2} checadas SIM nuevas')
            return

        with transaction.atomic():
            if append:
                deleted = borrar_qs.delete()[0]
                self.stdout.write(self.style.NOTICE(f'Borrados registros SIM- en ventana: {deleted}'))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Reemplazo: borrando checadas reales y SIM que solapan el periodo por cada empleado.'
                    )
                )

            creados = 0
            q_overlap = Q(fecha_administrativa__range=(fecha_ini, fecha_fin)) | Q(
                fecha_hora_real__range=(ventana_borra_ini, ventana_borra_fin)
            )
            total_borrados = 0
            for emp in empleados:
                if not append:
                    borrados_emp, _ = RegistroAsistencia.objects.filter(empleado=emp).filter(q_overlap).delete()
                    total_borrados += borrados_emp

                h = emp.horario
                tol = timedelta(minutes=h.tolerancia_entrada or 0)
                min_extra = h.minimo_minutos_para_contar_extra or 30

                dia = fecha_ini
                while dia <= fecha_fin:
                    if append and _dia_tiene_checadas_reales(emp, dia, ventana_borra_ini, ventana_borra_fin):
                        dia += timedelta(days=1)
                        continue
                    modo = (emp.id + dia.toordinal()) % 6
                    ent_prog = _entrada_programada(dia, h)
                    sal_prog = _salida_programada_dia(dia, h)

                    entrada = ent_prog
                    salida = sal_prog

                    if modo == 0:
                        # Puntual
                        pass
                    elif modo == 1:
                        # Retardo: despues del limite de tolerancia
                        entrada = ent_prog + tol + timedelta(minutes=22)
                    elif modo == 2:
                        # Salida tarde con horas extra (moderado)
                        salida = sal_prog + timedelta(minutes=max(min_extra + 45, 60))
                    elif modo == 3:
                        # "Doble jornada": jornada muy larga (muchas horas extra)
                        salida = sal_prog + timedelta(minutes=max(min_extra + 280, 300))
                    elif modo == 4:
                        # Llega un poco antes
                        entrada = ent_prog - timedelta(minutes=12)
                        salida = sal_prog + timedelta(minutes=min_extra + 75)
                    else:
                        # Salida tarde fuerte
                        entrada = ent_prog + timedelta(minutes=5)
                        salida = sal_prog + timedelta(minutes=min_extra + 130)

                    entrada, salida = _ajustar_entrada_salida(entrada, salida)
                    salida = _cap_salida_segura(entrada, salida, h)
                    entrada, salida = _ajustar_entrada_salida(entrada, salida)

                    suf = dia.isoformat().replace('-', '')
                    id_in = f'SIM-{suf}-E{emp.id}-IN'
                    id_out = f'SIM-{suf}-E{emp.id}-OUT'

                    RegistroAsistencia.objects.create(
                        empleado=emp,
                        fecha_hora_real=entrada,
                        tipo='IN',
                        hikvision_event_id=id_in,
                        observaciones='DEMO seed_asistencias_ficticias',
                    )
                    RegistroAsistencia.objects.create(
                        empleado=emp,
                        fecha_hora_real=salida,
                        tipo='OUT',
                        hikvision_event_id=id_out,
                        observaciones='DEMO seed_asistencias_ficticias',
                    )
                    creados += 2
                    dia += timedelta(days=1)

            if not append and total_borrados:
                self.stdout.write(self.style.NOTICE(f'Total checadas borradas (periodo): {total_borrados}'))
            self.stdout.write(self.style.SUCCESS(f'Checadas creadas: {creados}'))

            self.stdout.write('Reprocesando jornadas de todos los empleados...')
            n = reprocesar_todas_las_jornadas()
            self.stdout.write(self.style.SUCCESS(f'Listo. Empleados reprocesados: {n}.'))
