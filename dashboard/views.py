from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Q
import json
from decimal import Decimal

from transactions.services import (
    get_monthly_summary,
    get_category_breakdown,
    get_monthly_trend,
    get_daily_expense_trend,
    get_account_distribution,
    get_top_spending_categories,
    get_recent_transactions,
    get_total_balance,
)
from transactions.analytics import (
    get_income_breakdown,
    get_weekday_spending,
    get_cumulative_cashflow,
    get_spending_calendar,
    get_stat_sparklines,
    get_spend_forecast,
)
from budgets.services import get_budget_status, get_budget_alerts
from accounts.models import BankAccount
from transactions.models import Transaction


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def dashboard_view(request):
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

    # ── Summary Cards ──
    monthly = get_monthly_summary(year, month)
    total_balance = get_total_balance()
    total_accounts = BankAccount.objects.filter(is_active=True).count()

    # ── Charts Data ──
    expense_categories = get_category_breakdown('expense', year, month)
    income_categories = get_category_breakdown('income', year, month)
    monthly_trend = get_monthly_trend(6, year, month)
    daily_trend = get_daily_expense_trend(30, year, month)
    account_dist = get_account_distribution()
    top_categories = get_top_spending_categories(8, year, month)
    recent_transactions = get_recent_transactions(10)

    # ── Advanced widgets ──
    income_categories_dist = get_income_breakdown(year, month)
    weekday_spending = get_weekday_spending(year, month)
    cumulative_cashflow = get_cumulative_cashflow(year, month)
    spending_calendar = get_spending_calendar(year, month)
    sparklines = get_stat_sparklines(year, month)
    forecast = get_spend_forecast(year, month)

    # ── Budget status (top 5 by usage) + alerts ──
    budget_status = get_budget_status(year, month)[:5]
    budget_alerts = get_budget_alerts(year, month)

    # ── Previous Month Comparison ──
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    prev_monthly = get_monthly_summary(prev_year, prev_month)

    income_change = 0
    expense_change = 0
    if prev_monthly['income'] > 0:
        income_change = float(
            (monthly['income'] - prev_monthly['income']) / prev_monthly['income'] * 100
        )
    if prev_monthly['expense'] > 0:
        expense_change = float(
            (monthly['expense'] - prev_monthly['expense']) / prev_monthly['expense'] * 100
        )

    # ── Build Chart JSON ──
    chart_data = {
        'expense_pie': {
            'labels': [c['category__name'] or 'Uncategorized' for c in expense_categories],
            'data': [float(c['total']) for c in expense_categories],
            'colors': [c['category__color'] or '#6366f1' for c in expense_categories],
        },
        'monthly_bar': {
            'labels': [m['month'] for m in monthly_trend],
            'income': [m['income'] for m in monthly_trend],
            'expense': [m['expense'] for m in monthly_trend],
            'savings': [m['savings'] for m in monthly_trend],
        },
        'daily_trend': {
            'labels': [d['date'] for d in daily_trend],
            'data': [d['amount'] for d in daily_trend],
        },
        'account_donut': {
            'labels': [a['name'] for a in account_dist],
            'data': [float(a['balance']) for a in account_dist],
            'colors': [a['color'] for a in account_dist],
        },
        'income_pie': {
            'labels': [c['category__name'] or 'Uncategorized' for c in income_categories_dist],
            'data': [float(c['total']) for c in income_categories_dist],
            'colors': [c['category__color'] or '#10b981' for c in income_categories_dist],
        },
        'weekday': {
            'labels': weekday_spending['labels'],
            'data': weekday_spending['data'],
        },
        'cashflow': {
            'labels': cumulative_cashflow['labels'],
            'data': cumulative_cashflow['data'],
        },
        'sparklines': sparklines,
    }

    # ── Month selector ──
    import calendar
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(now.year - 3, now.year + 2))

    context = {
        'monthly': monthly,
        'total_balance': total_balance,
        'total_accounts': total_accounts,
        'income_change': income_change,
        'expense_change': expense_change,
        'recent_transactions': recent_transactions,
        'top_categories': top_categories,
        'account_dist': account_dist,
        'spending_calendar': spending_calendar,
        'forecast': forecast,
        'budget_status': budget_status,
        'budget_alerts': budget_alerts,
        'chart_data_json': json.dumps(chart_data, default=decimal_default),
        'selected_year': year,
        'selected_month': month,
        'months': months,
        'years': years,
        'page_title': 'Dashboard',
    }
    return render(request, 'dashboard/dashboard.html', context)