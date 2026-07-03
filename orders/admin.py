from django.contrib import admin
from .models import Owner, Staff, Order

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_name', 'email', 'created_at')
    search_fields = ('name', 'shop_name', 'email')
    list_filter = ('created_at',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'owner', 'is_active', 'device_id')
    search_fields = ('name', 'username', 'owner__name', 'device_id')
    list_filter = ('is_active', 'created_at', 'owner')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'staff', 'total', 'created_at', 'synced_at')
    search_fields = ('order_id', 'staff__name', 'staff__username')
    list_filter = ('created_at', 'synced_at', 'staff__owner')
