from django.urls import path  # Import path for URL routing
from . import views  # Import views from same folder

# List of URL patterns for home app
urlpatterns = [
    # Home page URL, maps to home view, name is 'home' - your marketplace
    path('', views.home, name='home'),  # Use views.home - matches function name in views.py

    # Compare page URL, maps to branch_compare, name is 'branch_compare' - professional 10 max
    path('compare/', views.branch_compare, name='branch_compare'),  # New: branch compare with 10 limit
]
