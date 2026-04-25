from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from .attendance_engine import reprocesar_jornadas_empleado
from .models import Departamento, Empleado, Horario, JornadaAsistencia, RegistroAsistencia


class RegistroAsistenciaTests(TestCase):
    def setUp(self):
        departamento = Departamento.objects.create(
            nombre='Ordeña',
            usa_corte_madrugada=True,
        )
        self.empleado = Empleado.objects.create(
            id_biometrico='prueba-1',
            nombre='Empleado Prueba',
            departamento=departamento,
        )
        self.horario_nocturno = Horario.objects.create(
            nombre_turno='Tercer turno',
            hora_entrada=datetime.fromisoformat('2026-04-16T21:45:00-06:00').time(),
            hora_salida=datetime.fromisoformat('2026-04-17T05:45:00-06:00').time(),
            usa_corte_madrugada=True,
            minimo_minutos_para_contar_extra=59,
        )
        self.empleado.horario = self.horario_nocturno
        self.empleado.save()
        self.tz = ZoneInfo("America/Mexico_City")

    def test_ordena_antes_de_545_cuenta_como_dia_anterior(self):
        registro = RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-16T05:44:59-06:00'),
            fecha_administrativa=date(2026, 4, 16),
            tipo='IN',
            hikvision_event_id='qa-1',
        )
        self.assertEqual(registro.fecha_administrativa.isoformat(), '2026-04-15')

    def test_ordena_desde_545_cuenta_como_mismo_dia(self):
        registro = RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-16T05:45:00-06:00'),
            fecha_administrativa=date(2026, 4, 16),
            tipo='IN',
            hikvision_event_id='qa-2',
        )
        self.assertEqual(registro.fecha_administrativa.isoformat(), '2026-04-16')

    def test_semana_operativa_es_jueves_a_miercoles(self):
        inicio, fin = RegistroAsistencia.obtener_semana_operativa(date(2026, 4, 20))
        self.assertEqual(inicio.isoformat(), '2026-04-16')
        self.assertEqual(fin.isoformat(), '2026-04-22')

    def test_jornada_nocturna_con_horas_extra_largas_permanece_mismo_dia_administrativo(self):
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-17T21:00:00-06:00'),
            fecha_administrativa=date(2026, 4, 17),
            tipo='IN',
            hikvision_event_id='qa-3',
        )
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-18T13:00:00-06:00'),
            fecha_administrativa=date(2026, 4, 18),
            tipo='OUT',
            hikvision_event_id='qa-4',
        )

        jornadas = reprocesar_jornadas_empleado(self.empleado)
        jornada = jornadas[0]

        self.assertEqual(jornada.fecha_administrativa.isoformat(), '2026-04-17')
        self.assertEqual(jornada.horas_extra, 7)
        self.assertEqual(jornada.minutos_extra, 435)

    def test_checada_duplicada_en_5_minutos_se_ignora(self):
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-17T21:00:00-06:00'),
            fecha_administrativa=date(2026, 4, 17),
            tipo='IN',
            hikvision_event_id='qa-5',
        )
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-17T21:03:00-06:00'),
            fecha_administrativa=date(2026, 4, 17),
            tipo='IN',
            hikvision_event_id='qa-6',
        )
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-18T05:40:00-06:00'),
            fecha_administrativa=date(2026, 4, 18),
            tipo='OUT',
            hikvision_event_id='qa-7',
        )

        reprocesar_jornadas_empleado(self.empleado)
        jornada = JornadaAsistencia.objects.get(empleado=self.empleado, fecha_administrativa=date(2026, 4, 17))

        self.assertEqual(jornada.entrada_real.astimezone(self.tz).isoformat(), '2026-04-17T21:00:00-06:00')
        self.assertEqual(jornada.salida_real.astimezone(self.tz).isoformat(), '2026-04-18T05:40:00-06:00')

    def test_horas_extra_empiezan_a_contar_despues_de_59_minutos(self):
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-17T21:45:00-06:00'),
            fecha_administrativa=date(2026, 4, 17),
            tipo='IN',
            hikvision_event_id='qa-8',
        )
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha_hora_real=datetime.fromisoformat('2026-04-18T07:43:00-06:00'),
            fecha_administrativa=date(2026, 4, 18),
            tipo='OUT',
            hikvision_event_id='qa-9',
        )

        jornadas = reprocesar_jornadas_empleado(self.empleado)
        jornada = jornadas[0]
        self.assertEqual(jornada.minutos_extra, 118)
        self.assertEqual(jornada.horas_extra, 1)

        jornada.salida_real = datetime.fromisoformat('2026-04-18T07:55:00-06:00')
        from appChecador.attendance_engine import _calcular_metricas
        _calcular_metricas(jornada)
        self.assertEqual(jornada.minutos_extra, 130)
        self.assertEqual(jornada.horas_extra, 2)
