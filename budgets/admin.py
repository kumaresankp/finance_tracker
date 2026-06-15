from django.contrib import admin
from .models import Budget, BudgetGroup


@admin.register(BudgetGroup)
class BudgetGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_limit', 'sort_order', 'created_at')
    ordering = ('sort_order', 'name')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'budget_type', 'amount', 'alert_threshold',
                    'is_active', 'group', 'created_at')
    list_filter = ('budget_type', 'is_active', 'group')
