from django.shortcuts import render

# Create your views here.

def login_test(request):
    return render(request, 'appChecador/login/login.html')