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
    return HttpResponse("Pay 1500 - coming")nt via {store.name}', related_store=store)  # Notification
        request.session['active_store_id'] = store.id  # Set active store in session
        return redirect('business_dashboard')  # Redirect business dashboard
    return render(request, 'accounts/branches.html', {'stores': all_stores})  # Render branches

# Create Store: with referral code tracking
@login_required  # Login required
def create_store_view(request):  # Create store
    if request.method == 'POST':  # POST
        name = request.POST.get('name')  # Store name
        address = request.POST.get('address')  # Address
        store = Store.objects.create(name=name, owner=request.user, address=address)  # Create store
        # Check if owner was referred: if store owner was referred, link store to referral
        try:  # Try
            referral = Referral.objects.get(referred_user=request.user, store_created=False)  # Get referral where store not yet created
            referral.store_created = True  # Mark store created
            referral.store = store  # Set store
            referral.save()  # Save
            # Update affiliate counts
            affiliate = referral.affiliate  # Affiliate
            affiliate.total_store_referrals += 1  # Increment store referrals
            affiliate.save()  # Save
            # Update store referral info
            store.referral_code_used = affiliate.code  # Code used
            store.referred_by = affiliate.user  # Referred by
            store.save()  # Save
            # Notification to affiliate: store created
            Notification.objects.create(user=affiliate.user, type='store_created', title='Referred User Created Store', message=f'{request.user.username} created store {name} with your referral', related_store=store)  # Notification
        except:  # Except
            pass  # No referral
        return redirect('branches')  # Redirect branches
    return render(request, 'accounts/create_store.html')  # Render create store

# Create Product Affiliate Link: get product link from marketplace and promote
@login_required  # Login required
def create_product_link_view(request):  # Create product link
    affiliate = request.user.affiliate  # Affiliate
    # Check limit: 5 different product Links on dashboard max free
    if not affiliate.can_create_product_link():  # Cannot create
        messages.error(request, f'You reached max {affiliate.product_links_count}/5 product links. Pay ₦1500 for unlimited marketplace access')  # Error: 5 max
        return redirect('profile')  # Redirect profile
    if request.method == 'POST':  # POST
        product_id = request.POST.get('product_id')  # Product ID from marketplace
        product_name = request.POST.get('product_name')  # Product name
        product_price = float(request.POST.get('product_price', 0))  # Product price
        product_store_id = request.POST.get('product_store_id')  # Store ID
        # Check if product store is from affiliate's referred store: Link 1 vs Link 2
        is_from_referred = False  # Default: not from referred store
        store_obj = None  # Store obj
        if product_store_id:  # If store ID provided
            try:  # Try
                store_obj = Store.objects.get(id=product_store_id)  # Get store
                # Check if this store was referred by this affiliate
                if Referral.objects.filter(affiliate=affiliate, store=store_obj).exists():  # Is from referred store
                    is_from_referred = True  # Link 1: My referred store
            except:  # Except
                pass  # Ignore
        # Create product affiliate link
        link = ProductAffiliateLink.objects.create(affiliate=affiliate, product_id=product_id, product_name=product_name, product_price=product_price, product_store=store_obj, is_from_referred_store=is_from_referred)  # Create link
        affiliate.product_links_count += 1  # Increment count
        affiliate.save()  # Save
        return redirect('profile')  # Redirect profile
    return render(request, 'accounts/create_product_link.html')  # Render create link

# Product Sale via Affiliate Link: when someone buys via affiliate link
def product_sale_via_affiliate(request, product_id):  # Sale via affiliate link
    capture_referral(request)  # Capture ref
    ref_code = request.GET.get('ref') or request.session.get('affiliate_ref')  # Get ref code
    if ref_code:  # If ref exists
        try:  # Try to track sale
            affiliate = Affiliate.objects.get(code=ref_code)  # Get affiliate
            product_link = ProductAffiliateLink.objects.filter(affiliate=affiliate, product_id=product_id).first()  # Get product link
            if product_link:  # If product link exists
                product_link.sales += 1  # Increment sales
                product_link.save()  # Save
                # Calculate commission from Geniop: not vendor to affiliate
                rates = GeniopCommissionRate.objects.filter(is_active=True).first()  # Get rates
                if rates:  # If rates exists
                    vendor_fee = (rates.vendor_platform_fee / 100) * product_link.product_price  # Vendor pays Geniop: 10%
                    if product_link.is_from_referred_store:  # Link 1: My referred store
                        commission_amount = (rates.link1_store_referred_percent / 100) * vendor_fee  # 60% of vendor fee
                        commission_type = 'store_product'  # Type
                    else:  # Link 2: General product
                        commission_amount = (rates.link2_general_percent / 100) * vendor_fee  # 40% of vendor fee
                        commission_type = 'general_product'  # Type
                    # Create commission: straight to account no minimum withdrawal
                    Commission.objects.create(affiliate=affiliate, type=commission_type, amount=commission_amount, product_link=product_link, buyer=request.user if request.user.is_authenticated else None)  # Commission
                    # Update affiliate balance
                    affiliate.balance += commission_amount  # Add to balance
                    affiliate.total_earnings += commission_amount  # Lifetime
                    affiliate.save()  # Save
                    # Update analytics
                    try:  # Try analytics
                        analytics = affiliate.analytics  # Analytics
                        if product_link.is_from_referred_store:  # Store product
                            analytics.total_store_sales += 1  # Increment
                        else:  # General
                            analytics.total_general_sales += 1  # Increment
                        analytics.save()  # Save
                    except:  # Except
                        pass  # Ignore
                    # Update earnings breakdown
                    today = EarningsBreakdown.objects.filter(affiliate=affiliate).order_by('-date').first()  # Today breakdown
                    if not today:  # No today
                        today = EarningsBreakdown.objects.create(affiliate=affiliate)  # Create
                    if commission_type == 'store_product':  # Store
                        today.store_product_earnings += commission_amount  # Add
                    else:  # General
                        today.general_product_earnings += commission_amount  # Add
                    today.total_earnings += commission_amount  # Total
                    today.top_product_today = product_link.product_name  # Top product today
                    today.save()  # Save
                    # Create notification: product sale
                    Notification.objects.create(user=affiliate.user, type='product_sale', title='Product Sold via Your Link', message=f'{product_link.product_name} sold! You earned ₦{commission_amount:.0f}', related_affiliate=affiliate)  # Notification
                    Notification.objects.create(user=affiliate.user, type='commission_earned', title='Commission Earned', message=f'₦{commission_amount:.0f} added to your balance - straight to account', related_affiliate=affiliate)  # Commission notification
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
