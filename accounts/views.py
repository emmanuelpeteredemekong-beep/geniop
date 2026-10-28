from django.shortcuts import render, redirect, get_object_or_404  # Shortcuts
from django.contrib.auth import login, logout, authenticate  # Auth
from django.contrib.auth.models import User  # User
from django.contrib.auth.decorators import login_required  # Login required
from django.contrib import messages  # Messages
from django.db.models import Sum, Count  # Aggregation
from .models import *  # All models
from home.models import Post  # Post model: home page posts stored in profile

# Capture referral code from URL: ?ref=CODE
def capture_referral(request):  # Capture ref from URL
    ref_code = request.GET.get('ref')  # Get ref code from URL
    if ref_code:  # If ref exists
        request.session['affiliate_ref'] = ref_code  # Save to session
        # Increment clicks for product link if product page
        try:  # Try to increment clicks
            affiliate = Affiliate.objects.get(code=ref_code)  # Get affiliate
            affiliate.total_product_clicks += 1  # Increment clicks
            affiliate.save()  # Save
        except:  # Except
            pass  # Ignore if no affiliate

# Register: with referral tracking
def register_view(request):  # Register view
    capture_referral(request)  # Capture referral code first
    if request.method == 'POST':  # POST request
        username = request.POST.get('username')  # Username
        email = request.POST.get('email')  # Email
        password = request.POST.get('password')  # Password
        if User.objects.filter(username=username).exists():  # Check if exists
            messages.error(request, 'Username already exists')  # Error
        else:  # Not exists
            user = User.objects.create_user(username=username, email=email, password=password)  # Create user
            # Check if user was referred by affiliate
            ref_code = request.session.get('affiliate_ref')  # Get ref from session
            if ref_code:  # If ref exists
                try:  # Try to create referral
                    affiliate = Affiliate.objects.get(code=ref_code)  # Get affiliate
                    Referral.objects.create(affiliate=affiliate, referred_user=user)  # Create referral
                    affiliate.total_referrals += 1  # Increment referrals count: at least 100 target
                    affiliate.save()  # Save
                    # Create notification for affiliate: referral joined
                    Notification.objects.create(user=affiliate.user, type='referral_joined', title='New Referral Joined', message=f'{username} joined with your referral code')  # Notification
                    # Create advice if milestone
                    if affiliate.total_referrals == 100:  # Hit 100 referrals
                        AffiliateAdvice.objects.create(affiliate=affiliate, title='Milestone Unlocked!', message='You hit 100 referrals! You now have unlimited product links and can earn from marketplace access payments.', type='success')  # Advice
                except:  # Except
                    pass  # Ignore
            login(request, user)  # Login user
            return redirect('profile')  # Redirect to profile
    return render(request, 'accounts/register.html')  # Render register page

# Login
def login_view(request):  # Login view
    capture_referral(request)  # Capture ref even on login page
    if request.method == 'POST':  # POST
        username = request.POST.get('username')  # Username
        password = request.POST.get('password')  # Password
        user = authenticate(request, username=username, password=password)  # Authenticate
        if user:  # If user exists
            login(request, user)  # Login
            return redirect('home')  # Redirect home
        else:  # No user
            messages.error(request, 'Invalid credentials')  # Error
    return render(request, 'accounts/login.html')  # Render login

# Logout
def logout_view(request):  # Logout view
    logout(request)  # Logout
    return redirect('login')  # Redirect login

# Profile: affiliate dashboard inside profile + all posts stored in profile
@login_required  # Login required
def profile_view(request):  # Profile view: main Phase 3
    user = request.user  # Current user
    profile = user.profile  # Profile
    affiliate = user.affiliate  # Affiliate inside profile
    # Business access check: must have branches first
    can_access_business = profile.can_access_business()  # Check branches first: your rule
    # All posts in home page stored in profile: Phase 3 requirement
    my_posts = Post.objects.filter(user=user).order_by('-created_at')  # All home posts by user
    # Affiliate data: counts referrals and stores
    referrals = Referral.objects.filter(affiliate=affiliate).order_by('-created_at')  # Referrals list
    my_stores = Store.objects.filter(owner=user)  # Stores he added
    product_links = ProductAffiliateLink.objects.filter(affiliate=affiliate).order_by('-created_at')  # Product links: 5 max free
    commissions = Commission.objects.filter(affiliate=affiliate).order_by('-created_at')[:20]  # Recent commissions
    # Earnings breakdown: from where which product sold more
    total_store_earnings = Commission.objects.filter(affiliate=affiliate, type='store_product').aggregate(Sum('amount'))['amount__sum'] or 0  # Link 1 earnings
    total_general_earnings = Commission.objects.filter(affiliate=affiliate, type='general_product').aggregate(Sum('amount'))['amount__sum'] or 0  # Link 2 earnings
    total_access_earnings = Commission.objects.filter(affiliate=affiliate, type='marketplace_access').aggregate(Sum('amount'))['amount__sum'] or 0  # Link 3 earnings
    # Analytics: top product, worst product
    try:  # Try analytics
        analytics = affiliate.analytics  # Analytics
        # Calculate top product by sales
        top_product = ProductAffiliateLink.objects.filter(affiliate=affiliate).order_by('-sales').first()  # Top product
        worst_product = ProductAffiliateLink.objects.filter(affiliate=affiliate).order_by('sales').first()  # Worst product
        analytics.top_selling_product = top_product  # Set top
        analytics.worst_selling_product = worst_product  # Set worst
        analytics.save()  # Save
    except:  # Except
        analytics = None  # No analytics
    # Advice: little text box that understands business logic
    advices = AffiliateAdvice.objects.filter(affiliate=affiliate, is_read=False).order_by('-created_at')[:3]  # Unread advices: interactive
    # Generate advice based on data: interactive system
    if product_links.count() > 0 and advices.count() == 0:  # If has product links but no advice
        # Check if any product has 0 sales
        zero_sales = ProductAffiliateLink.objects.filter(affiliate=affiliate, sales=0).count()  # Zero sales
        if zero_sales > 2:  # Many zero sales
            AffiliateAdvice.objects.create(affiliate=affiliate, title='Low Performing Links', message=f'{zero_sales} of your product links have 0 sales. Try promoting your top store {my_stores.first().name if my_stores.exists() else "products"} more - they convert better when you use your referred store link.', type='warning')  # Advice
    # Notifications: connected
    notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]  # Unread notifications
    # Earnings breakdown daily
    breakdown = EarningsBreakdown.objects.filter(affiliate=affiliate).order_by('-date')[:7]  # Last 7 days
    # Commission rates: configurable
    rates = GeniopCommissionRate.objects.filter(is_active=True).first()  # Get active rates
    # Account switching log
    switch_logs = AccountSwitchLog.objects.filter(user=user).order_by('-created_at')[:5]  # Recent switches

    context = {  # Context
        'profile': profile,  # Profile
        'affiliate': affiliate,  # Affiliate
        'can_access_business': can_access_business,  # Branches first check
        'my_posts': my_posts,  # All home page posts stored in profile
        'referrals': referrals,  # Referrals count
        'my_stores': my_stores,  # Stores added
        'product_links': product_links,  # Product links: 5 max
        'commissions': commissions,  # Commissions
        'total_store_earnings': total_store_earnings,  # Link 1 earnings
        'total_general_earnings': total_general_earnings,  # Link 2 earnings
        'total_access_earnings': total_access_earnings,  # Link 3 earnings
        'analytics': analytics,  # Analytics
        'advices': advices,  # Advice box
        'notifications': notifications,  # Notifications
        'breakdown': breakdown,  # Earnings breakdown
        'rates': rates,  # Rates
        'switch_logs': switch_logs,  # Switch logs
    }
    return render(request, 'accounts/profile.html', context)  # Render profile

# Branches First: business account entry - must reach branches first
@login_required  # Login required
def branches_view(request):  # Branches view: business entry
    user = request.user  # User
    owned_stores = Store.objects.filter(owner=user)  # Owned stores
    staff_stores = user.staff_stores.all()  # Staff stores
    all_stores = list(owned_stores) + list(staff_stores)  # All stores
    if not all_stores:  # No branches
        messages.error(request, 'You need to create a branch/store first to access Business Account')  # Error: branches first rule
        return redirect('create_store')  # Redirect create store
    # Log account switching: from personal to business via branch
    if request.method == 'POST':  # POST: selected store to access business
        store_id = request.POST.get('store_id')  # Store ID
        store = get_object_or_404(Store, id=store_id)  # Get store
        # Log switch
        AccountSwitchLog.objects.create(user=user, from_account='personal', to_account='business', store=store)  # Log
        # Create notification
        Notification.objects.create(user=user, type='business_access', title='Business Account Accessed', message=f'You accessed business account via {store.name}', related_store=store)  # Notification
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
