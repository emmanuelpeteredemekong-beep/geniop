from django.urls import path  # Import path for URL routing
from django.contrib.auth import views as auth_views  # Auth views for password reset - Step 4 Account Recovery
from . import views  # Import views from same folder - home/views.py

# URL patterns for home app - Build Home layout and navigation
urlpatterns = [  # List of URL routes for home
    path('', views.home_view, name='home'),  # Home page - root - Phase 2 Home layout - No login required
    path('compare/', views.branch_compare, name='compare'),  # Branch compare - professional: 10 max per compare
    path('terms/', views.terms_view, name='terms'),  # Terms page - static page
    path('privacy/', views.privacy_view, name='privacy'),  # Privacy page - static page
    path('download/', views.download_report_view, name='download_report'),  # Download route - downloadable results CSV - Phase 2 spec - THIS WAS MISSING

    # Step 4: Account Recovery - password reset - you added this - okay to keep
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),  # Password reset form - enter email
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),  # Password reset done - email sent confirmation
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Reset confirm - uid and token from email link
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Reset complete - password changed success
]
