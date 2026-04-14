from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout

def login(request):
    # 1. Verificamos si el usuario ya tiene una sesión iniciada
    if 'usuario_id' in request.session:
        return redirect('inicio')

    if request.method == 'POST':
        usuario = request.POST.get('username')
        contra = request.POST.get('password')
        
        user = authenticate(request, username=usuario, password=contra)
        
        if user is not None:
            # 2. auth_login crea la sesión automáticamente en la base de datos y el navegador
            auth_login(request, user) 
            
            # --- CREAMOS VARIABLES GLOBALES DE SESIÓN ---
            request.session['usuario_id'] = user.id
            request.session['usuario_nombre'] = user.username
            request.session['es_admin'] = user.is_superuser
            # --------------------------------------------
            
            return redirect('inicio') 
        else:
            print("malo")
            return render(request, 'appChecador/login/login.html', {'error': True})
            
    return render(request, 'appChecador/login/login.html')

def logout(request):
    # Borra las variables de sesión personalizadas y la cookie de Django
    request.session.flush() 
    auth_logout(request)
    # Redirige al login
    return redirect('login')

def inicio(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    nombreUsuarioLogueado = request.session['usuario_nombre']
    
    return render(request, 'appChecador/inicio/inicio.html', {'nombre_usuario': nombreUsuarioLogueado})

def empleados(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    nombreUsuarioLogueado = request.session['usuario_nombre']
    
    return render(request, 'appChecador/checador/empleados.html', {'nombre_usuario': nombreUsuarioLogueado})


    