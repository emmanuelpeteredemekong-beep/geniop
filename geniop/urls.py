from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Main URL router for Geniop
# This connects all apps to root URL

urlpatterns = [
    # Admin panel - /admin/
    path('admin/', admin.site.urls),
    
    # Home app - landing page / etc - this loads home/urls.py
    path('', include('home.urls')),
    
    # Accounts app - login/signup etc - this loads accounts/urls.py
    path('accounts/', include('accounts.urls')),
]

# Serve media and static files in DEBUG mode (for phone testing)
# On Render, WhiteNoise handles static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
