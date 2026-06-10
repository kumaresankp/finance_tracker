from django.db import models
from django.utils import timezone
from accounts.models import BankAccount


class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    ICON_CHOICES = [
        ('bi-cart', 'Shopping'),
        ('bi-house', 'Housing'),
        ('bi-car-front', 'Transport'),
        ('bi-heart-pulse', 'Health'),
        ('bi-mortarboard', 'Education'),
        ('bi-film', 'Entertainment'),
        ('bi-cup-hot', 'Food & Drinks'),
        ('bi-lightning', 'Utilities'),
        ('bi-briefcase', 'Salary'),
        ('bi-graph-up', 'Investment'),
        ('bi-gift', 'Gifts'),
        ('bi-airplane', 'Travel'),
        ('bi-phone', 'Phone'),
        ('bi-controller', 'Gaming'),
        ('bi-book', 'Books'),
        ('bi-scissors', 'Personal Care'),
        ('bi-three-dots', 'Other'),
        ('bi-cash-coin', 'Business'),
        ('bi-piggy-bank', 'Savings'),
        ('bi-star', 'Miscellaneous'),
    ]

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    color = models.CharField(max_length=7, default='#6366f1')
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='bi-three-dots')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    target_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transfers'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    note = models.TextField(blank=True, default='')
    transaction_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount} - {self.transaction_date}"

    def save(self, *args, **kwargs):
        """Override save to update account balances"""
        is_new = self.pk is None

        if is_new:
            super().save(*args, **kwargs)
            self._update_balances_on_create()
        else:
            # Get old transaction for reversal
            old = Transaction.objects.get(pk=self.pk)
            self._reverse_old_balance(old)
            super().save(*args, **kwargs)
            self._update_balances_on_create()

    def _update_balances_on_create(self):
        """Apply transaction effect to account balances"""
        account = self.bank_account
        if self.transaction_type == 'income':
            account.balance += self.amount
            account.save(update_fields=['balance'])
        elif self.transaction_type == 'expense':
            account.balance -= self.amount
            account.save(update_fields=['balance'])
        elif self.transaction_type == 'transfer' and self.target_account:
            account.balance -= self.amount
            account.save(update_fields=['balance'])
            target = self.target_account
            target.balance += self.amount
            target.save(update_fields=['balance'])

    def _reverse_old_balance(self, old):
        """Reverse the effect of old transaction"""
        account = old.bank_account
        if old.transaction_type == 'income':
            account.balance -= old.amount
            account.save(update_fields=['balance'])
        elif old.transaction_type == 'expense':
            account.balance += old.amount
            account.save(update_fields=['balance'])
        elif old.transaction_type == 'transfer' and old.target_account:
            account.balance += old.amount
            account.save(update_fields=['balance'])
            target = old.target_account
            target.balance -= old.amount
            target.save(update_fields=['balance'])

    def delete(self, *args, **kwargs):
        """Override delete to reverse balance"""
        self._reverse_old_balance(self)
        super().delete(*args, **kwargs)