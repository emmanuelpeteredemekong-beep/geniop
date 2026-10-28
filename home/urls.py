from django.urls import path  # Import path for URL routing
from django.contrib.auth import views as auth_views  # Auth views for password reset - Step 4
from . import views  # Import views from same app - home/views.py

# All URLs for home app - Phase 2 Home layout + Step 4 Account Recovery
urlpatterns = [  # List of URL routes
    path('', views.home_view, name='home'),  # Home - root - No login - shows report card + post box + feed
    path('compare/', views.branch_compare, name='compare'),  # Branch compare - 10 max per compare
    path('terms/', views.terms_view, name='terms'),  # Terms page
    path('privacy/', views.privacy_view, name='privacy'),  # Privacy page
    path('download/', views.download_report_view, name='download_report'),  # Download - downloadable results - Phase 2 MUST HAVE
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),  # Step 4 - password reset form
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),  # Step 4 - email sent
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Step 4 - link from email
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Step 4 - password changed
]
