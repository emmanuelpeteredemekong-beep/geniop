from django.db import models  # Django models
from django.contrib.auth.models import User  # User model
from django.db.models.signals import post_save  # Signal
from django.dispatch import receiver  # Receiver
import uuid  # For code generation

# Store = Branch: Must access branches first before business account
class Store(models.Model):  # Branch model
    name = models.CharField(max_length=100)  # Branch name
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_stores')  # Owner: unlimited branches
    staff = models.ManyToManyField(User, blank=True, related_name='staff_stores')  # Staff members
    address = models.CharField(max_length=200, blank=True)  # Address
    is_active = models.BooleanField(default=True)  # Active
    referral_code_used = models.CharField(max_length=20, blank=True)  # Affiliate code used
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stores_referred')  # Who referred store owner
    created_at = models.DateTimeField(auto_now_add=True)  # Created date
    def __str__(self):  # String
        return f"{self.name} - {self.owner.username}"  # Return

# Profile: customer, vendor, admin, affiliate + privacy + blocking
class Profile(models.Model):  # Profile model
    ROLE_CHOICES = [('customer','Customer'),('vendor','Vendor'),('admin','Admin'),('affiliate','Affiliate')]  # Roles
    PRIVACY_CHOICES = [('public','Public'),('private','Private'),('followers','Followers Only')]  # Privacy
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')  # User link
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')  # Role
    bio = models.TextField(blank=True)  # Bio
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # Avatar
    phone = models.CharField(max_length=20, blank=True)  # Phone for recovery
    location = models.CharField(max_length=100, blank=True)  # Location
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')  # Privacy
    is_business_verified = models.BooleanField(default=False)  # Business verified
    is_verified = models.BooleanField(default=False)  # Blue tick
    is_blocked = models.BooleanField(default=False)  # Blocked by admin
    blocked_users = models.ManyToManyField(User, blank=True, related_name='blocked_by')  # Blocked list
    reported_count = models.IntegerField(default=0)  # Report count
    account_recovery_code = models.CharField(max_length=20, blank=True)  # Recovery code
    created_at = models.DateTimeField(auto_now_add=True)  # Created
    updated_at = models.DateTimeField(auto_now=True)  # Updated
    def can_access_business(self):  # Must have branch first: your rule
        return self.user.owned_stores.exists() or self.user.staff_stores.exists()  # Has branch?
    def __str__(self):  # String
        return f"{self.user.username} - {self.role}"  # Return

# Affiliate: inside profile, straight to account no minimum withdrawal
class Affiliate(models.Model):  # Affiliate inside profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='affiliate')  # User
    code = models.CharField(max_length=20, unique=True, blank=True)  # Code GENIOP-XXXX
    balance = models.FloatField(default=0.0)  # Withdrawable balance: no minimum
    total_earnings = models.FloatField(default=0.0)  # Lifetime earnings
    total_withdrawn = models.FloatField(default=0.0)  # Withdrawn
    total_referrals = models.IntegerField(default=0)  # User referrals count: target 100
    total_store_referrals = models.IntegerField(default=0)  # Stores referred
    total_product_clicks = models.IntegerField(default=0)  # Clicks
    is_active = models.BooleanField(default=True)  # Active
    has_paid_1500 = models.BooleanField(default=False)  # Paid for unlimited
    product_links_count = models.IntegerField(default=0)  # Product links count: max 5 free
    created_at = models.DateTimeField(auto_now_add=True)  # Joined date
    def save(self, *args, **kwargs):  # Save
        if not self.code:  # No code
            self.code = f"GENIOP-{str(uuid.uuid4())[:8].upper()}"  # Generate
        super().save(*args, **kwargs)  # Save
    def is_unlimited(self):  # Unlimited check: paid 1500 or 100 referrals
        return self.has_paid_1500 or self.total_referrals >= 100  # Unlimited?
    def can_create_product_link(self):  # Can create link: max 5 free
        if self.is_unlimited():  # Unlimited
            return True  # Yes
        return self.product_links_count < 5  # Check 5 limit
    def __str__(self):  # String
        return f"{self.user.username} - {self.code} - ₦{self.balance}"  # Details

# Referral tracking: at least 100 referrals
class Referral(models.Model):  # Referral tracking
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='referrals')  # Affiliate
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referred_by_affiliate')  # Referred user
    has_paid_1500 = models.BooleanField(default=False)  # Paid 1500?
    store_created = models.BooleanField(default=False)  # Created store?
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)  # Store
    created_at = models.DateTimeField(auto_now_add=True)  # Date
    def __str__(self):  # String
        return f"{self.affiliate.user.username} -> {self.referred_user.username}"  # Arrow

# Product Affiliate Link: get product link from marketplace and promote
class ProductAffiliateLink(models.Model):  # Product link: 5 max free
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='product_links')  # Affiliate
    product_id = models.CharField(max_length=100)  # Product ID
    product_name = models.CharField(max_length=200)  # Product name
    product_price = models.FloatField()  # Price
    product_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)  # Store
    is_from_referred_store = models.BooleanField(default=False)  # Link 1 vs Link 2: your referred store?
    link = models.CharField(max_length=500, blank=True)  # Full link /product/123/?ref=CODE
    clicks = models.IntegerField(default=0)  # Clicks
    sales = models.IntegerField(default=0)  # Sales
    earnings = models.FloatField(default=0.0)  # Earnings from this link
    created_at = models.DateTimeField(auto_now_add=True)  # Created
    def save(self, *args, **kwargs):  # Save
        if not self.link:  # No link
            self.link = f"/product/{self.product_id}/?ref={self.affiliate.code}"  # Generate link
        super().save(*args, **kwargs)  # Save
    def __str__(self):  # String
        return f"{self.affiliate.user.username} - {self.product_name}"  # Details

# Commission: from Geniop to affiliate, not vendor to affiliate
class Commission(models.Model):  # Commission earned
    COMMISSION_TYPE = [('store_product','Store Product - My Referred Store + My Link'),('general_product','General Product - My Link Only'),('marketplace_access','Marketplace Access - User paid 1500')]  # Types
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='commissions')  # Affiliate
    type = models.CharField(max_length=30, choices=COMMISSION_TYPE)  # Type
    amount = models.FloatField()  # Amount: straight to account
    product_link = models.ForeignKey(ProductAffiliateLink, on_delete=models.SET_NULL, null=True, blank=True)  # Product link
    referral = models.ForeignKey(Referral, on_delete=models.SET_NULL, null=True, blank=True)  # Referral
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Buyer
    is_withdrawn = models.BooleanField(default=False)  # Withdrawn?
    created_at = models.DateTimeField(auto_now_add=True)  # Date
    def __str__(self):  # String
        return f"{self.affiliate.user.username} - ₦{self.amount} - {self.type}"  # Details

# Geniop Commission Rate: calm down and determine percentage: configurable in admin
class GeniopCommissionRate(models.Model):  # Configurable rates
    name = models.CharField(max_length=100, default="Default Rates")  # Name
    vendor_platform_fee = models.FloatField(default=10.0)  # Vendor pays Geniop: 10%
    link1_store_referred_percent = models.FloatField(default=60.0)  # Link 1: 60% of Geniop fee
    link2_general_percent = models.FloatField(default=40.0)  # Link 2: 40% of Geniop fee
    link3_marketplace_access_percent = models.FloatField(default=30.0)  # Link 3: 30% of 1500 = 450
    marketplace_access_price = models.FloatField(default=1500.0)  # Price: 1500
    free_product_links_limit = models.IntegerField(default=5)  # Free limit: 5
    referral_target = models.IntegerField(default=100)  # Target: 100
    is_active = models.BooleanField(default=True)  # Active
    updated_at = models.DateTimeField(auto_now=True)  # Updated
    def __str__(self):  # String
        return f"Rates - Vendor {self.vendor_platform_fee}% - L1 {self.link1_store_referred_percent}% L2 {self.link2_general_percent}% L3 {self.link3_marketplace_access_percent}%"  # Rates

# Marketplace Access Payment: user pays 1500 for unlimited
class MarketplaceAccessPayment(models.Model):  # 1500 payment
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_payments')  # User
    amount = models.FloatField(default=1500.0)  # Amount
    affiliate = models.ForeignKey(Affiliate, on_delete=models.SET_NULL, null=True, blank=True)  # Affiliate who referred
    is_paid = models.BooleanField(default=False)  # Paid?
    flutterwave_ref = models.CharField(max_length=100, blank=True)  # Flutterwave ref
    created_at = models.DateTimeField(auto_now_add=True)  # Date
    def __str__(self):  # String
        return f"{self.user.username} - ₦{self.amount} - Paid: {self.is_paid}"  # Details

# Analytics: counts referrals and stores and what calculate earnings from where which product sold more
class AffiliateAnalytics(models.Model):  # Interactive analytics
    affiliate = models.OneToOneField(Affiliate, on_delete=models.CASCADE, related_name='analytics')  # Affiliate
    top_selling_product = models.ForeignKey(ProductAffiliateLink, on_delete=models.SET_NULL, null=True, blank=True, related_name='top_product')  # Top product
    worst_selling_product = models.ForeignKey(ProductAffiliateLink, on_delete=models.SET_NULL, null=True, blank=True, related_name='worst_product')  # Worst product
    top_earning_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='top_earning_store')  # Top store
    total_store_sales = models.IntegerField(default=0)  # Store sales
    total_general_sales = models.IntegerField(default=0)  # General sales
    last_sale_date = models.DateTimeField(null=True, blank=True)  # Last sale
    best_day = models.CharField(max_length=20, blank=True)  # Best day
    updated_at = models.DateTimeField(auto_now=True)  # Updated
    def __str__(self):  # String
        return f"Analytics - {self.affiliate.user.username}"  # Name

# Advice: little text box that understands business logic from data
class AffiliateAdvice(models.Model):  # Advice box: interactive
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='advices')  # Affiliate
    title = models.CharField(max_length=100, default="Business Advice")  # Title
    message = models.TextField()  # Message: e.g "Store A sells 3x more on weekends"
    type = models.CharField(max_length=20, default="insight")  # Type: insight, warning, success
    is_read = models.BooleanField(default=False)  # Read?
    created_at = models.DateTimeField(auto_now_add=True)  # Created
    def __str__(self):  # String
        return f"Advice for {self.affiliate.user.username} - {self.title}"  # Details

# Notifications: connect to affiliate and others
class Notification(models.Model):  # Notification system
    NOTIFICATION_TYPES = [('referral_joined','New Referral Joined'),('store_created','Referred User Created Store'),('product_sale','Product Sold via Your Link'),('commission_earned','Commission Earned'),('marketplace_paid','User Paid 1500 for Unlimited'),('advice','New Business Advice'),('account_report','Account Reported'),('business_access','Business Account Accessed')]  # Types
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # User
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)  # Type
    title = models.CharField(max_length=200)  # Title
    message = models.TextField()  # Message
    related_affiliate = models.ForeignKey(Affiliate, on_delete=models.SET_NULL, null=True, blank=True)  # Affiliate
    related_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)  # Store
    is_read = models.BooleanField(default=False)  # Read?
    created_at = models.DateTimeField(auto_now_add=True)  # Date
    class Meta:  # Meta
        ordering = ['-created_at']  # Newest first
    def __str__(self):  # String
        return f"{self.user.username} - {self.title}"  # Title

# Earnings Breakdown: daily breakdown where earnings came from
class EarningsBreakdown(models.Model):  # Daily earnings
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='earnings_breakdown')  # Affiliate
    date = models.DateField(auto_now_add=True)  # Date
    store_product_earnings = models.FloatField(default=0.0)  # Link 1 earnings
    general_product_earnings = models.FloatField(default=0.0)  # Link 2 earnings
    marketplace_access_earnings = models.FloatField(default=0.0)  # Link 3 earnings
    total_earnings = models.FloatField(default=0.0)  # Total
    top_product_today = models.CharField(max_length=200, blank=True)  # Top product today
    class Meta:  # Meta
        ordering = ['-date']  # Newest first
    def __str__(self):  # String
        return f"{self.affiliate.user.username} - {self.date} - ₦{self.total_earnings}"  # Details

# Account Switching Log: business account entry and switching
class AccountSwitchLog(models.Model):  # Switch log: branches first
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='switch_logs')  # User
    from_account = models.CharField(max_length=50)  # From
    to_account = models.CharField(max_length=50)  # To
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)  # Store used
    ip_address = models.CharField(max_length=50, blank=True)  # IP
    created_at = models.DateTimeField(auto_now_add=True)  # Date
    def __str__(self):  # String
        return f"{self.user.username} switched {self.from_account} -> {self.to_account}"  # Details

# Account Reporting: Phase 3 requirement
class AccountReport(models.Model):  # Reporting
    REPORT_CHOICES = [('spam','Spam'),('fake','Fake Account'),('abuse','Abuse'),('scam','Scam')]  # Reasons
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')  # Reporter
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')  # Reported
    reason = models.CharField(max_length=20, choices=REPORT_CHOICES)  # Reason
    description = models.TextField(blank=True)  # Description
    is_resolved = models.BooleanField(default=False)  # Resolved?
    created_at = models.DateTimeField(auto_now_add=True)  # Date
    def __str__(self):  # String
        return f"{self.reporter.username} reported {self.reported_user.username} - {self.reason}"  # Details

# Auto-create Profile and Affiliate
@receiver(post_save, sender=User)  # When User created
def create_user_profile(sender, instance, created, **kwargs):  # Create profile
    if created:  # New user
        Profile.objects.get_or_create(user=instance)  # Create profile
        Affiliate.objects.get_or_create(user=instance)  # Create affiliate inside profile
        AffiliateAnalytics.objects.get_or_create(affiliate=instance.affiliate)  # Create analytics
