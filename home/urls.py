from django.urls import path  # Import path for URL routing
from . import views  # Import views from same folder

# List of URL patterns for home app
urlpatterns = [
    # Home page URL, maps to home_view, name is 'home'
    path('', views.home_view, name='home'),
    # Compare page URL, maps to branch_compare, name is 'branch_compare'
    path('compare/', views.branch_compare, name='branch_compare'),
]
