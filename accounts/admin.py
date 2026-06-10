from django.contrib import admin
from .models import BankAccount


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'balance', 'is_active', 'created_at']
    list_filter = ['account_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']