from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages

# Temporary deploy-safe views - Phase 2 LIVE

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
    return HttpResponse("Pay 1500 - coming")ted_affiliate=affiliate)  # Commission notification
                    # Create advice if high sales
                    if product_link.sales >= 5:  # 5 sales
                        AffiliateAdvice.objects.create(affiliate=affiliate, title='Top Performing Product', message=f'{product_link.product_name} is your top product with {product_link.sales} sales! Promote it more - it sells 3x better than others. Share your link {product_link.link} on WhatsApp.', type='success')  # Advice
        except Exception as e:  # Exception
            print(f"Affiliate sale error: {e}")  # Print error
    return redirect(f'/product/{product_id}/')  # Redirect to product page

# Marketplace Access Payment: user pays 1500 for unlimited
@login_required  # Login required
def marketplace_access_payment_view(request):  # Pay 1500 for unlimited
    rates = GeniopCommissionRate.objects.filter(is_active=True).first()  # Rates
    price = rates.marketplace_access_price if rates else 1500.0  # Price
    if request.method == 'POST':  # POST: paid via Flutterwave
        flutterwave_ref = request.POST.get('flutterwave_ref', '')  # Flutterwave ref
        # Check if user was referred
        affiliate_referral = None  # Affiliate referral
        try:  # Try
            referral = Referral.objects.get(referred_user=request.user)  # Get referral
            affiliate_referral = referral.affiliate  # Affiliate
            referral.has_paid_1500 = True  # Mark paid 1500
            referral.save()  # Save
        except:  # Except
            pass  # No referral
        # Create payment record
        payment = MarketplaceAccessPayment.objects.create(user=request.user, amount=price, affiliate=affiliate_referral, is_paid=True, flutterwave_ref=flutterwave_ref)  # Payment
        # Mark affiliate as paid for unlimited
        request.user.affiliate.has_paid_1500 = True  # Paid 1500
        request.user.affiliate.save
