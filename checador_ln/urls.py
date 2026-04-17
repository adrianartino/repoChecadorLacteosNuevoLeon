"""
URL configuration for checador_ln project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from appChecador.views import login, inicio, logout, usuarios, empleados, importar_empleados_sin_configurar, exportar_empleados_sin_configurar, departamentos, horarios, editar_horario, cambiar_password_usuario, editar_empleado, sincronizar_checadas_view, asistencias_hoy, exportar_asistencias_excel, exportar_asistencias_pdf, exportar_asistencias_excel_imss, exportar_asistencias_pdf_imss, retardos, exportar_retardos_excel, exportar_retardos_pdf, exportar_retardos_excel_imss, exportar_retardos_pdf_imss, horas_extra, exportar_horas_extra_excel, exportar_horas_extra_pdf, exportar_horas_extra_excel_imss, exportar_horas_extra_pdf_imss, resumen_departamento, resumen_empleado, semana_operativa, exportar_semana_operativa_excel, exportar_semana_operativa_pdf, exportar_semana_operativa_excel_imss, exportar_semana_operativa_pdf_imss # Importa tu vista

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login, name='login'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('inicio/', inicio, name='inicio'),
    path('sincronizar-checadas/', sincronizar_checadas_view, name='sincronizar_checadas'),
    path('usuarios/', usuarios, name='usuarios'),
    path('usuarios/<int:usuario_id>/password/', cambiar_password_usuario, name='cambiar_password_usuario'),
    path('empleados/', empleados, name='empleados'),
    path('empleados/importar-sin-configurar/', importar_empleados_sin_configurar, name='importar_empleados_sin_configurar'),
    path('empleados/exportar-sin-configurar/', exportar_empleados_sin_configurar, name='exportar_empleados_sin_configurar'),
    path('departamentos/', departamentos, name='departamentos'),
    path('horarios/', horarios, name='horarios'),
    path('horarios/editar/<int:horario_id>/', editar_horario, name='editar_horario'),
    path('asistencias/hoy/', asistencias_hoy, name='asistencias_hoy'),
    path('asistencias/resumen/departamento/', resumen_departamento, name='resumen_departamento'),
    path('asistencias/resumen/empleado/', resumen_empleado, name='resumen_empleado'),
    path('asistencias/semana-operativa/', semana_operativa, name='semana_operativa'),
    path('asistencias/exportar/excel/', exportar_asistencias_excel, name='exportar_asistencias_excel'),
    path('asistencias/exportar/pdf/', exportar_asistencias_pdf, name='exportar_asistencias_pdf'),
    path('asistencias/exportar/excel-imss/', exportar_asistencias_excel_imss, name='exportar_asistencias_excel_imss'),
    path('asistencias/exportar/pdf-imss/', exportar_asistencias_pdf_imss, name='exportar_asistencias_pdf_imss'),
    path('asistencias/semana-operativa/exportar/excel/', exportar_semana_operativa_excel, name='exportar_semana_operativa_excel'),
    path('asistencias/semana-operativa/exportar/pdf/', exportar_semana_operativa_pdf, name='exportar_semana_operativa_pdf'),
    path('asistencias/semana-operativa/exportar/excel-imss/', exportar_semana_operativa_excel_imss, name='exportar_semana_operativa_excel_imss'),
    path('asistencias/semana-operativa/exportar/pdf-imss/', exportar_semana_operativa_pdf_imss, name='exportar_semana_operativa_pdf_imss'),
    path('asistencias/retardos/', retardos, name='retardos'),
    path('asistencias/retardos/exportar/excel/', exportar_retardos_excel, name='exportar_retardos_excel'),
    path('asistencias/retardos/exportar/pdf/', exportar_retardos_pdf, name='exportar_retardos_pdf'),
    path('asistencias/retardos/exportar/excel-imss/', exportar_retardos_excel_imss, name='exportar_retardos_excel_imss'),
    path('asistencias/retardos/exportar/pdf-imss/', exportar_retardos_pdf_imss, name='exportar_retardos_pdf_imss'),
    path('asistencias/horas-extra/', horas_extra, name='horas_extra'),
    path('asistencias/horas-extra/exportar/excel/', exportar_horas_extra_excel, name='exportar_horas_extra_excel'),
    path('asistencias/horas-extra/exportar/pdf/', exportar_horas_extra_pdf, name='exportar_horas_extra_pdf'),
    path('asistencias/horas-extra/exportar/excel-imss/', exportar_horas_extra_excel_imss, name='exportar_horas_extra_excel_imss'),
    path('asistencias/horas-extra/exportar/pdf-imss/', exportar_horas_extra_pdf_imss, name='exportar_horas_extra_pdf_imss'),
    path('empleados/editar/<int:empleado_id>/', editar_empleado, name='editar_empleado'),
]
