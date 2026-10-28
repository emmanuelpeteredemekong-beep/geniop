from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# All URLs for home app - Phase 2 Geniop landing + tools
urlpatterns = [
    # Main landing page - / - shows index.html
    path('', views.home_view, name='home'),
    
    # Compare tool - /compare/
    path('compare/', views.branch_compare, name='compare'),
    
    # Legal pages - /terms/ and /privacy/
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    
    # Download PDF report - /download/
    path('download/', views.download_report_view, name='download_report'),
    
    # Password reset flow - Django auth views
    # /password_reset/ -> /password_reset/done/ -> /reset/<uid>/<token>/ -> /reset/done/
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='home/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='home/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='home/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='home/password_reset_complete.html'), name='password_reset_complete'),
]
