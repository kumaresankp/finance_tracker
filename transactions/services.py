from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
import calendar
from decimal import Decimal


def get_monthly_summary(year=None, month=None):
    """Get income/expense summary for a specific month"""
    from .models import Transaction

    if not year:
        year = timezone.now().year
    if not month:
        month = timezone.now().month

    transactions = Transaction.objects.filter(
        transaction_date__year=year,
        transaction_date__month=month
    )

    income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    expense = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    savings = income - expense
    savings_rate = float(savings / income * 100) if income else 0.0

    return {
        'income': income,
        'expense': expense,
        'savings': savings,
        'savings_rate': savings_rate,
        'year': year,
        'month': month,
    }


def get_category_breakdown(transaction_type='expense', year=None, month=None):
    """Get spending by category"""
    from .models import Transaction

    if not year:
        year = timezone.now().year
    if not month:
        month = timezone.now().month

    transactions = Transaction.objects.filter(
        transaction_type=transaction_type,
        transaction_date__year=year,
        transaction_date__month=month
    ).values(
        'category__name', 'category__color', 'category__icon'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    return list(transactions)


def get_monthly_trend(months=6):
    """Get monthly income/expense trend"""
    from .models import Transaction

    today = timezone.now().date()
    result = []

    for i in range(months - 1, -1, -1):
        # Calculate month offset
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        month_income = Transaction.objects.filter(
            transaction_type='income',
            transaction_date__year=year,
            transaction_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        month_expense = Transaction.objects.filter(
            transaction_type='expense',
            transaction_date__year=year,
            transaction_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        result.append({
            'month': calendar.month_abbr[month],
            'year': year,
            'income': float(month_income),
            'expense': float(month_expense),
            'savings': float(month_income - month_expense),
        })

    return result


def get_daily_expense_trend(days=30):
    """Get daily expense trend"""
    from .models import Transaction

    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)

    transactions = Transaction.objects.filter(
        transaction_type='expense',
        transaction_date__gte=start_date,
        transaction_date__lte=today
    ).values('transaction_date').annotate(
        total=Sum('amount')
    ).order_by('transaction_date')

    # Create full date range with zero-fill
    date_map = {t['transaction_date']: float(t['total']) for t in transactions}
    result = []
    current = start_date
    while current <= today:
        result.append({
            'date': current.strftime('%b %d'),
            'amount': date_map.get(current, 0),
        })
        current += timedelta(days=1)

    return result


def get_account_distribution():
    """Get account balance distribution"""
    from accounts.models import BankAccount

    accounts = BankAccount.objects.filter(is_active=True).values(
        'name', 'balance', 'color', 'account_type'
    )
    return list(accounts)


def get_top_spending_categories(limit=5, year=None, month=None):
    """Get top N spending categories"""
    return get_category_breakdown('expense', year, month)[:limit]


def get_recent_transactions(limit=10):
    """Get recent transactions"""
    from .models import Transaction
    return Transaction.objects.select_related(
        'bank_account', 'target_account', 'category'
    ).order_by('-transaction_date', '-created_at')[:limit]


def get_total_balance():
    """Get total balance across all accounts"""
    from accounts.models import BankAccount
    total = BankAccount.objects.filter(is_active=True).aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0')
    return total


def recalculate_account_balance(account):
    """Recalculate account balance from transactions"""
    from .models import Transaction

    income = Transaction.objects.filter(
        bank_account=account, transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    expense = Transaction.objects.filter(
        bank_account=account, transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    transfer_out = Transaction.objects.filter(
        bank_account=account, transaction_type='transfer'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    transfer_in = Transaction.objects.filter(
        target_account=account, transaction_type='transfer'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # This would need an initial balance field to be accurate
    # For now we just return the computed flow
    return income - expense - transfer_out + transfer_in