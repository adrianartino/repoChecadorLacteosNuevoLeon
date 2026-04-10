from django.contrib import admin
from .models import Departamento, Empleado, RegistroAsistencia

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usa_corte_madrugada')

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id_biometrico', 'nombre', 'apellido', 'departamento')
    search_fields = ('nombre', 'id_biometrico')

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_hora_real', 'fecha_administrativa')
    list_filter = ('fecha_administrativa', 'empleado__departamento')