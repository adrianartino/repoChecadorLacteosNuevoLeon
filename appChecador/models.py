from django.db import models
from datetime import time, timedelta

# Create your models here.
from django.db import models
from datetime import time, timedelta

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Departamento")
    # Esta es la clave para Ordeña:
    usa_corte_madrugada = models.BooleanField(
        default=False, 
        help_text="Si se marca, los registros antes de las 6:00 AM cuentan como el día anterior."
    )

    def __str__(self):
        return self.nombre

class Empleado(models.Model):
    id_biometrico = models.CharField(max_length=20, unique=True, verbose_name="ID en Checador")
    nombre = models.CharField(max_length=150)
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

    def save(self, *args, **kwargs):
        # 1. Extraemos hora y fecha del timestamp real
        hora_checado = self.fecha_hora_real.time()
        fecha_checado = self.fecha_hora_real.date()

        # 2. Lógica de Ordeña (Corte 06:00 AM)
        # Si el depto tiene la regla y es antes de las 6 AM, restamos un día
        if self.empleado.departamento.usa_corte_madrugada and hora_checado < time(6, 0):
            self.fecha_administrativa = fecha_checado - timedelta(days=1)
        else:
            self.fecha_administrativa = fecha_checado
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-fecha_hora_real']