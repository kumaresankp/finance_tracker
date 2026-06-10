from django.contrib import admin
from .models import Transaction, Category


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_date', 'transaction_type', 'category',
        'bank_account', 'amount', 'note'
    ]
    list_filter = ['transaction_type', 'transaction_date', 'category']
    search_fields = ['note', 'bank_account__name', 'category__name']
    date_hierarchy = 'transaction_date'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'color', 'icon']
    list_filter = ['category_type']
    search_fields = ['name']