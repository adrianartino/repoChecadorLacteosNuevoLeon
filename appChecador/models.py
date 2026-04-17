from django.db import models
from datetime import time, timedelta


HORA_CORTE_ORDENA = time(5, 45)
INICIO_SEMANA_OPERATIVA = 3


class Departamento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Departamento")
    # Esta es la clave para Ordeña:
    usa_corte_madrugada = models.BooleanField(
        default=False, 
        help_text="Si se marca, los registros antes de las 6:00 AM cuentan como el día anterior."
    )

    def __str__(self):
        return self.nombre
    
class Horario(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    nombre_turno = models.CharField(max_length=50, verbose_name="Nombre del Turno") # Ej: Matutino, Nocturno
    dia_semana = models.IntegerField(choices=DIAS_SEMANA, null=True, blank=True)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    usa_corte_madrugada = models.BooleanField(
        default=False,
        help_text="Si se marca y el horario cruza medianoche, las checadas antes de la hora de salida cuentan para el día anterior.",
    )
    
    # Configuraciones de asistencia
    tolerancia_entrada = models.IntegerField(default=15, help_text="Minutos de tolerancia para entrada")
    inicio_entrada = models.TimeField(null=True, blank=True, help_text="Hora desde la cual se puede empezar a checar entrada")
    minimo_minutos_para_contar_extra = models.IntegerField(
        default=30,
        help_text="Minutos minimos despues de la salida para que empiece a contar la primera hora extra.",
    )
    
    def __str__(self):
        etiqueta_dia = self.get_dia_semana_display() if self.dia_semana is not None else "General"
        return f"{etiqueta_dia} - {self.nombre_turno} ({self.hora_entrada})"


class Empleado(models.Model):
    id_biometrico = models.CharField(max_length=20, unique=True, verbose_name="ID en Checador")
    nombre = models.CharField(max_length=150)
    puesto = models.CharField(max_length=150, null=True, blank=True)
    apellido = models.CharField(max_length=150, null=True, blank=True) # También apellido por si el checador solo trae un nombre
    # Cambio aquí:
    departamento = models.ForeignKey(
        'Departamento', 
        on_delete=models.SET_NULL, # Si borras un depto, el empleado no se borra, solo queda en NULL
        null=True, 
        blank=True
    )
    numero_empleado = models.CharField(max_length=20, null=True, blank=True)
    numero_seguridad_social = models.CharField(max_length=20, null=True, blank=True)
    activo = models.BooleanField(default=True)
    horario = models.ForeignKey(Horario, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados_asignados')

    def __str__(self):
        return f"{self.id_biometrico} - {self.nombre}"
    
class RegistroAsistencia(models.Model):
    TIPO_EVENTO = [
        ('IN', 'Entrada'),
        ('OUT', 'Salida'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    
    # El timestamp exacto que nos da el DS-K1T343EFWX-B
    fecha_hora_real = models.DateTimeField(verbose_name="Fecha/Hora del Checador")
    
    # La fecha que usaremos para la nómina
    fecha_administrativa = models.DateField(editable=False)
    
    tipo = models.CharField(max_length=3, choices=TIPO_EVENTO)
    
    # Guardamos el ID del evento de Hikvision para evitar duplicados al jalar datos
    hikvision_event_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Campos nuevos para reportes rápidos
    retardo = models.BooleanField(default=False)
    minutos_extra = models.IntegerField(default=0) 
    horas_extra = models.IntegerField(default=0)
    observaciones = models.TextField(null=True, blank=True)

    @staticmethod
    def obtener_semana_operativa(fecha_base):
        dias_desde_jueves = (fecha_base.weekday() - INICIO_SEMANA_OPERATIVA) % 7
        inicio_semana = fecha_base - timedelta(days=dias_desde_jueves)
        fin_semana = inicio_semana + timedelta(days=6)
        return inicio_semana, fin_semana

    def save(self, *args, **kwargs):
        # 1. Extraemos hora y fecha del timestamp real
        hora_checado = self.fecha_hora_real.time()
        fecha_checado = self.fecha_hora_real.date()

        horario = self.empleado.horario
        aplica_corte = bool(
            horario
            and horario.usa_corte_madrugada
            and horario.hora_entrada > horario.hora_salida
            and hora_checado < horario.hora_salida
        )

        # 2. Lógica de turnos nocturnos:
        # Si el empleado tiene un horario con corte de madrugada y la checada cae antes de la hora de salida,
        # administrativamente cuenta para el día anterior.
        if aplica_corte:
            self.fecha_administrativa = fecha_checado - timedelta(days=1)
        else:
            self.fecha_administrativa = fecha_checado
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-fecha_hora_real']


class JornadaAsistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='jornadas')
    horario = models.ForeignKey(Horario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_administrativa = models.DateField()
    entrada_real = models.DateTimeField(null=True, blank=True)
    salida_real = models.DateTimeField(null=True, blank=True)
    retardo = models.BooleanField(default=False)
    minutos_retardo = models.IntegerField(default=0)
    minutos_extra = models.IntegerField(default=0)
    horas_extra = models.IntegerField(default=0)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_administrativa', '-entrada_real']
        unique_together = ('empleado', 'fecha_administrativa')

    def __str__(self):
        return f"{self.empleado} - {self.fecha_administrativa}"
