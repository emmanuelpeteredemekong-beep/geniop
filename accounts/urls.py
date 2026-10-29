from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, logout

# --- TEMP VIEWS FOR DEPLOY - Phase 2 Live ---

def register_view(request):
    return render(request, 'accounts/register.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def profile_view(request):
    return render(request, 'accounts/profile.html')

def branches_view(request):
    return render(request, 'accounts/branches.html')

def create_store_view(request):
    return HttpResponse("Create Store - Coming Phase 3")

def create_product_link_view(request):
    return HttpResponse("Create Product Link - Coming Phase 3")

def product_sale_view(request, product_id):
    return HttpResponse(f"Product Sale {product_id}")

def marketplace_access_payment_view(request):
    return HttpResponse("Pay 1500 - Marketplace Access")
