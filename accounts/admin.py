from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'owner_name', 'phone', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'city', 'state']
    search_fields = ['store_name', 'owner_name', 'phone']
