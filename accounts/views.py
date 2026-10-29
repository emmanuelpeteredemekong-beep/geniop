from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username exists')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('profile')
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def profile_view(request):
    return render(request, 'accounts/profile.html')

def branches_view(request):
    return render(request, 'accounts/branches.html')

def create_store_view(request):
    return render(request, 'accounts/create_store.html')

def create_product_link_view(request):
    return render(request, 'accounts/create_product_link.html')

def product_sale_view(request, product_id):
    from django.http import HttpResponse
    return HttpResponse(f"Product {product_id}")

def marketplace_access_payment_view(request):
    from django.http import HttpResponse
    return HttpResponse("Pay 1500 - coming")
