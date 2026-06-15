from django.db import models
from django.utils import timezone
from decimal import Decimal


class BudgetGroup(models.Model):
    """An 'envelope' grouping several category budgets under a shared limit."""

    ICON_CHOICES = [
        ('bi-basket', 'Essentials'),
        ('bi-emoji-smile', 'Lifestyle'),
        ('bi-house-heart', 'Home'),
        ('bi-airplane', 'Travel'),
        ('bi-piggy-bank', 'Savings'),
        ('bi-heart-pulse', 'Health'),
        ('bi-mortarboard', 'Education'),
        ('bi-stars', 'Discretionary'),
        ('bi-collection', 'General'),
    ]

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6366f1')
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='bi-collection')
    monthly_limit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Optional shared cap across all member categories.'
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Budget(models.Model):
    """A monthly recurring spending limit, per-category or overall."""

    BUDGET_TYPES = [
        ('category', 'Category'),
        ('overall', 'Overall Monthly'),
    ]

    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPES, default='category')
    category = models.ForeignKey(
        'transactions.Category',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='budgets',
    )
    group = models.ForeignKey(
        BudgetGroup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='budgets',
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    alert_threshold = models.PositiveSmallIntegerField(
        default=80, help_text='Warn when spending reaches this percentage of the limit.'
    )
    is_active = models.BooleanField(default=True)
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # At most one active budget per category.
            models.UniqueConstraint(
                fields=['category'],
                condition=models.Q(budget_type='category', is_active=True),
                name='unique_active_category_budget',
            ),
            # At most one active overall budget.
            models.UniqueConstraint(
                fields=['budget_type'],
                condition=models.Q(budget_type='overall', is_active=True),
                name='unique_active_overall_budget',
            ),
        ]

    def __str__(self):
        if self.budget_type == 'overall':
            return f'Overall Monthly Budget (₹{self.amount})'
        name = self.category.name if self.category else 'Uncategorized'
        return f'{name} Budget (₹{self.amount})'

    @property
    def display_name(self):
        if self.budget_type == 'overall':
            return 'Overall Monthly Budget'
        return self.category.name if self.category else 'Uncategorized'

    @property
    def color(self):
        if self.budget_type == 'category' and self.category:
            return self.category.color
        return '#6366f1'

    @property
    def icon(self):
        if self.budget_type == 'category' and self.category:
            return self.category.icon
        return 'bi-wallet2'

    # ── Thin wrappers around the services layer ──
    def spent(self, year=None, month=None):
        from .services import budget_spent
        return budget_spent(self, year, month)

    def remaining(self, year=None, month=None):
        return Decimal(self.amount) - self.spent(year, month)

    def pct_used(self, year=None, month=None):
        spent = self.spent(year, month)
        if not self.amount:
            return 0.0
        return float(spent / Decimal(self.amount) * 100)

    def status(self, year=None, month=None):
        pct = self.pct_used(year, month)
        if pct >= 100:
            return 'over'
        if pct >= self.alert_threshold:
            return 'warning'
        return 'under'
