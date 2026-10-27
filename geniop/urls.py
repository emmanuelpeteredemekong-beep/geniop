from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('upload-report/', views.upload_report, name='upload_report'),
    path('mark-paid/<int:id>/', views.mark_paid, name='mark_paid'),
]
