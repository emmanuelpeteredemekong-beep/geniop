from django.urls import path
from . import views

# Phase 3 + Affiliate - only live views
urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('branches/', views.branches_view, name='branches'),
    path('create-store/', views.create_store_view, name='create_store'),
    path('create-product-link/', views.create_product_link_view, name='create_product_link'),
    path('product-sale/<str:product_id>/', views.product_sale_view, name='product_sale'),
    path('pay-1500/', views.marketplace_access_payment_view, name='pay_1500'),

    # Phase 4 - will add later after views exist
    # path('block/<int:user_id>/', views.block_user_view, name='block_user'),
    # path('report/<int:user_id>/', views.report_account_view, name='report_account'),
    # path('notifications/', views.notifications_view, name='notifications'),
]
