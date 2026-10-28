from django.urls import path  # Path
from . import views  # Views

urlpatterns = [  # URL patterns: Phase 3 + Affiliate
    path('register/', views.register_view, name='register'),  # Register: with referral tracking
    path('login/', views.login_view, name='login'),  # Login
    path('logout/', views.logout_view, name='logout'),  # Logout
    path('profile/', views.profile_view, name='profile'),  # Profile: affiliate dashboard inside profile
    path('branches/', views.branches_view, name='branches'),  # Branches: business account entry - must reach branches first
    path('create-store/', views.create_store_view, name='create_store'),  # Create store with referral tracking
    path('create-product-link/', views.create_product_link_view, name='create_product_link'),  # Create product link from marketplace
    path('product-sale/<str:product_id>/', views.product_sale_via_affiliate, name='product_sale_affiliate'),  # Product sale via affiliate link
    path('pay-1500/', views.marketplace_access_payment_view, name='pay_1500'),  # Pay 1500 for unlimited marketplace access
    # path('block/<int:user_id>/', views.block_user_view, name='block_user'),  # Block user: privacy controls - TODO: add view later
    # path('report/<int:user_id>/', views.report_account_view, name='report_account'),  # Report account - TODO: add view later
    # path('notifications/', views.notifications_view, name='notifications'),  # Notifications connected - TODO: add view later
]
