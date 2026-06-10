from django.db import models
from django.utils import timezone


class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
        ('salary', 'Salary'),
        ('cash', 'Cash'),
        ('credit', 'Credit Card'),
        ('upi', 'UPI Wallet'),
        ('investment', 'Investment'),
        ('other', 'Other'),
    ]

    ICON_CHOICES = [
        ('bi-bank', 'Bank'),
        ('bi-cash-stack', 'Cash'),
        ('bi-credit-card', 'Credit Card'),
        ('bi-phone', 'UPI/Mobile'),
        ('bi-wallet2', 'Wallet'),
        ('bi-piggy-bank', 'Piggy Bank'),
        ('bi-currency-dollar', 'Investment'),
        ('bi-building', 'Building'),
    ]

    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    color = models.CharField(max_length=7, default='#6366f1')
    icon = models.CharField(max_length=50, default='bi-bank', choices=ICON_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    def get_total_income(self):
        return self.transactions.filter(
            transaction_type='income'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def get_total_expense(self):
        return self.transactions.filter(
            transaction_type='expense'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def get_recent_transactions(self, limit=5):
        from transactions.models import Transaction
        return Transaction.objects.filter(
            models.Q(bank_account=self) | models.Q(target_account=self)
        ).order_by('-transaction_date', '-created_at')[:limit]