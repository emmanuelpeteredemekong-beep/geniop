from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'owner_name', 'phone', 'email', 'city', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'city', 'state', 'created_at']
    search_fields = ['store_name', 'owner_name', 'phone', 'email']
    list_editable = ['is_verified']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Store Information', {
            'fields': ('store_name', 'owner_name', 'user')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address', 'city', 'state')
        }),
        ('Verification & Dates', {
            'fields': ('is_verified', 'created_at', 'updated_at')
        }),
    )
