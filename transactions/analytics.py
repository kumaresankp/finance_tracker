"""Derived analytics for the Insights page and enriched dashboard widgets.

Everything here is computed on the fly from existing Transaction / Category /
BankAccount data — no extra models, no migrations. Functions are defensive about
empty data (no transactions, zero income, etc.) and return JSON-safe primitives.
"""
from django.db.models import Sum, Count, Max
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import calendar
import statistics

from .services import get_monthly_summary, get_monthly_trend, get_category_breakdown


# ── helpers ──────────────────────────────────────────────────────────────

def _shift_month(year, month, delta):
    """Return (year, month) shifted by `delta` months."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def _today():
    return timezone.now().date()


def _f(value):
    """Decimal/None -> float."""
    return float(value or 0)


def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


# ── 1. Financial health score ───────────────────────────────────────────

def get_financial_health_score(year=None, month=None):
    """Composite 0-100 score built from four weighted components."""
    today = _today()
    year = year or today.year
    month = month or today.month

    summary = get_monthly_summary(year, month)
    income = _f(summary['income'])
    expense = _f(summary['expense'])

    # Component 1 — savings rate (target >= 20%). Weight 40%.
    savings_rate = (income - expense) / income * 100 if income else 0.0
    savings_score = _clamp(savings_rate / 20 * 100)

    # Component 2 — expense-to-income ratio (lower is better). Weight 20%.
    if income:
        ratio = expense / income
        ratio_score = _clamp((1 - ratio) * 100 + 20)
    else:
        ratio_score = 0.0

    # Component 3 — income stability over trailing 6 months (low variation
    # is better). Weight 20%.
    trend = get_monthly_trend(6, year, month)
    incomes = [m['income'] for m in trend]
    income_score = _stability_score(incomes)

    # Component 4 — spending consistency over trailing 6 months. Weight 20%.
    expenses = [m['expense'] for m in trend]
    spend_score = _stability_score(expenses)

    components = [
        {'label': 'Savings Rate', 'score': round(savings_score),
         'detail': f'{savings_rate:.0f}% of income saved', 'icon': 'bi-piggy-bank'},
        {'label': 'Expense Control', 'score': round(ratio_score),
         'detail': f'{(expense / income * 100) if income else 0:.0f}% of income spent',
         'icon': 'bi-shield-check'},
        {'label': 'Income Stability', 'score': round(income_score),
         'detail': 'Steadiness of income over 6 months', 'icon': 'bi-graph-up-arrow'},
        {'label': 'Spending Consistency', 'score': round(spend_score),
         'detail': 'How predictable your spending is', 'icon': 'bi-activity'},
    ]

    score = (savings_score * 0.40 + ratio_score * 0.20
             + income_score * 0.20 + spend_score * 0.20)
    score = round(_clamp(score))

    return {
        'score': score,
        'grade': _grade(score),
        'label': _grade_label(score),
        'components': components,
    }


def _stability_score(values):
    """100 = perfectly steady, lower = more volatile. Uses coefficient of variation."""
    nonzero = [v for v in values if v > 0]
    if len(nonzero) < 2:
        return 50.0  # not enough history to judge
    mean = statistics.mean(nonzero)
    if mean == 0:
        return 50.0
    cv = statistics.pstdev(nonzero) / mean  # 0 = steady, grows with volatility
    return _clamp((1 - cv) * 100)


def _grade(score):
    if score >= 85:
        return 'A'
    if score >= 70:
        return 'B'
    if score >= 55:
        return 'C'
    if score >= 40:
        return 'D'
    return 'E'


def _grade_label(score):
    if score >= 85:
        return 'Excellent'
    if score >= 70:
        return 'Good'
    if score >= 55:
        return 'Fair'
    if score >= 40:
        return 'Needs Attention'
    return 'At Risk'


# ── 2. Spending anomalies ────────────────────────────────────────────────

def get_spending_anomalies(year=None, month=None):
    """Flag categories spending notably above their trailing 3-month norm,
    plus unusually large single transactions this month."""
    from .models import Transaction

    today = _today()
    year = year or today.year
    month = month or today.month

    alerts = []

    # Per-category month-over-month spike detection.
    current = {c['category__name']: _f(c['total'])
               for c in get_category_breakdown('expense', year, month)}

    history = {}  # category -> [monthly totals over trailing 3 months]
    for i in range(1, 4):
        y, m = _shift_month(year, month, -i)
        for c in get_category_breakdown('expense', y, m):
            history.setdefault(c['category__name'], []).append(_f(c['total']))

    for name, amount in current.items():
        past = history.get(name, [])
        if len(past) < 2:
            continue
        mean = statistics.mean(past)
        std = statistics.pstdev(past) if len(past) > 1 else 0
        threshold = mean + 1.5 * std
        if mean > 0 and amount > threshold and amount > mean * 1.25:
            pct = (amount - mean) / mean * 100
            alerts.append({
                'level': 'warning',
                'title': f'{name or "Uncategorized"} spending spike',
                'detail': f'₹{amount:,.0f} this month vs ₹{mean:,.0f} avg of last 3 months',
                'category': name,
                'amount': amount,
                'pct_change': round(pct),
            })

    # Unusually large single transaction this month.
    big = (Transaction.objects.filter(
        transaction_type='expense',
        transaction_date__year=year, transaction_date__month=month,
    ).select_related('category').order_by('-amount').first())
    if big:
        avg = (Transaction.objects.filter(
            transaction_type='expense',
            transaction_date__year=year, transaction_date__month=month,
        ).aggregate(a=Sum('amount'), n=Count('id')))
        count = avg['n'] or 1
        mean_txn = _f(avg['a']) / count
        if count >= 3 and _f(big.amount) > mean_txn * 2.5:
            alerts.append({
                'level': 'info',
                'title': 'Large single transaction',
                'detail': (f'₹{_f(big.amount):,.0f} on '
                           f'{big.category.name if big.category else "Uncategorized"} '
                           f'({big.transaction_date:%b %d}) — well above your average.'),
                'category': big.category.name if big.category else None,
                'amount': _f(big.amount),
                'pct_change': round((_f(big.amount) - mean_txn) / mean_txn * 100) if mean_txn else 0,
            })

    return alerts


# ── 3. Top movers ────────────────────────────────────────────────────────

def get_top_movers(year=None, month=None, limit=5):
    """Per-category change vs previous month."""
    today = _today()
    year = year or today.year
    month = month or today.month
    prev_year, prev_month = _shift_month(year, month, -1)

    current = {c['category__name']: c for c in get_category_breakdown('expense', year, month)}
    previous = {c['category__name']: _f(c['total'])
                for c in get_category_breakdown('expense', prev_year, prev_month)}

    movers = []
    for name in set(current) | set(previous):
        now = _f(current.get(name, {}).get('total')) if name in current else 0.0
        was = previous.get(name, 0.0)
        delta = now - was
        if abs(delta) < 1:
            continue
        meta = current.get(name, {})
        movers.append({
            'category': name or 'Uncategorized',
            'color': meta.get('category__color') or '#6366f1',
            'icon': meta.get('category__icon') or 'bi-tag',
            'now': now,
            'was': was,
            'delta': delta,
            'pct': round(delta / was * 100) if was else None,
        })

    increases = sorted([m for m in movers if m['delta'] > 0],
                       key=lambda m: m['delta'], reverse=True)[:limit]
    decreases = sorted([m for m in movers if m['delta'] < 0],
                       key=lambda m: m['delta'])[:limit]
    return {'increases': increases, 'decreases': decreases}


# ── 4. Spend forecast ────────────────────────────────────────────────────

def get_spend_forecast(year=None, month=None):
    """Project month-end expense from the current run-rate."""
    today = _today()
    year = year or today.year
    month = month or today.month

    summary = get_monthly_summary(year, month)
    spent = _f(summary['expense'])
    days_in_month = calendar.monthrange(year, month)[1]

    is_current = (year == today.year and month == today.month)
    if is_current:
        days_elapsed = today.day
    elif (year, month) > (today.year, today.month):
        days_elapsed = 0  # future month
    else:
        days_elapsed = days_in_month  # past month — already complete

    if days_elapsed:
        daily_rate = spent / days_elapsed
        projected = daily_rate * days_in_month
    else:
        daily_rate = 0.0
        projected = spent

    prev_year, prev_month = _shift_month(year, month, -1)
    prev = _f(get_monthly_summary(prev_year, prev_month)['expense'])

    pace_pct = round((projected - prev) / prev * 100) if prev else None

    return {
        'spent_so_far': spent,
        'daily_rate': daily_rate,
        'projected': projected,
        'prev_month': prev,
        'days_elapsed': days_elapsed,
        'days_in_month': days_in_month,
        'pace_pct': pace_pct,
        'on_track': (projected <= prev) if prev else True,
        'is_current': is_current,
    }


# ── 5. Recurring charge detection ────────────────────────────────────────

def detect_recurring(lookback_months=4):
    """Detect likely recurring/subscription expenses.

    Groups expenses by (category, rounded amount bucket) and flags groups that
    recur across >= 3 distinct months with a stable amount.
    """
    from .models import Transaction

    today = _today()
    start_year, start_month = _shift_month(today.year, today.month, -(lookback_months - 1))
    start = date(start_year, start_month, 1)

    txns = (Transaction.objects.filter(
        transaction_type='expense', transaction_date__gte=start)
        .select_related('category')
        .values('category__name', 'category__color', 'category__icon',
                'amount', 'transaction_date'))

    groups = {}
    for t in txns:
        amount = _f(t['amount'])
        bucket = round(amount / 50) * 50 if amount >= 50 else round(amount)
        key = (t['category__name'], bucket)
        g = groups.setdefault(key, {
            'category': t['category__name'] or 'Uncategorized',
            'color': t['category__color'] or '#6366f1',
            'icon': t['category__icon'] or 'bi-arrow-repeat',
            'amounts': [], 'months': set(), 'last_date': t['transaction_date'],
        })
        g['amounts'].append(amount)
        g['months'].add((t['transaction_date'].year, t['transaction_date'].month))
        if t['transaction_date'] > g['last_date']:
            g['last_date'] = t['transaction_date']

    recurring = []
    for g in groups.values():
        if len(g['months']) >= 3:
            recurring.append({
                'label': g['category'],
                'category': g['category'],
                'color': g['color'],
                'icon': g['icon'],
                'avg_amount': round(statistics.mean(g['amounts'])),
                'frequency': f"{len(g['months'])} of last {lookback_months} months",
                'occurrences': len(g['amounts']),
                'last_date': g['last_date'],
            })

    recurring.sort(key=lambda r: r['avg_amount'], reverse=True)
    monthly_total = sum(r['avg_amount'] for r in recurring)
    return {'items': recurring, 'monthly_total': monthly_total}


# ── 6. Narrative insights ────────────────────────────────────────────────

def get_narrative_insights(year=None, month=None):
    """Compose short, human-readable insight sentences from the analytics above."""
    today = _today()
    year = year or today.year
    month = month or today.month

    cards = []
    summary = get_monthly_summary(year, month)
    income, expense = _f(summary['income']), _f(summary['expense'])

    # Savings standing vs trailing months.
    trend = get_monthly_trend(6, year, month)
    savings_series = [m['savings'] for m in trend]
    if len(savings_series) >= 2 and summary['savings'] is not None:
        this_savings = _f(summary['savings'])
        if this_savings >= max(savings_series):
            cards.append({'icon': 'bi-trophy', 'tone': 'success',
                          'text': 'Best savings month in the last 6 months. Keep it up!'})
        elif this_savings < 0:
            cards.append({'icon': 'bi-exclamation-triangle', 'tone': 'danger',
                          'text': f'You spent ₹{abs(this_savings):,.0f} more than you earned this month.'})

    # Top mover.
    movers = get_top_movers(year, month, limit=1)
    if movers['increases']:
        m = movers['increases'][0]
        if m['pct']:
            cards.append({'icon': 'bi-arrow-up-right-circle', 'tone': 'warning',
                          'text': f"Spending on {m['category']} rose {m['pct']}% vs last month "
                                  f"(₹{m['delta']:,.0f} more)."})
    if movers['decreases']:
        m = movers['decreases'][0]
        if m['pct']:
            cards.append({'icon': 'bi-arrow-down-right-circle', 'tone': 'success',
                          'text': f"You cut {m['category']} spending by ₹{abs(m['delta']):,.0f} "
                                  f"vs last month."})

    # Forecast.
    forecast = get_spend_forecast(year, month)
    if forecast['is_current'] and forecast['pace_pct'] is not None:
        direction = 'more' if forecast['pace_pct'] > 0 else 'less'
        cards.append({'icon': 'bi-speedometer', 'tone': 'info',
                      'text': f"On pace to spend ₹{forecast['projected']:,.0f} this month "
                              f"— {abs(forecast['pace_pct'])}% {direction} than last month."})

    # Recurring commitments.
    recurring = detect_recurring()
    if recurring['monthly_total'] > 0:
        cards.append({'icon': 'bi-arrow-repeat', 'tone': 'info',
                      'text': f"About ₹{recurring['monthly_total']:,.0f}/month goes to "
                              f"{len(recurring['items'])} recurring charge(s)."})

    # Top spending category share.
    breakdown = get_category_breakdown('expense', year, month)
    if breakdown and expense:
        top = breakdown[0]
        share = _f(top['total']) / expense * 100
        cards.append({'icon': 'bi-pie-chart', 'tone': 'neutral',
                      'text': f"{top['category__name'] or 'Uncategorized'} was your biggest "
                              f"expense at {share:.0f}% of spending."})

    if not cards:
        cards.append({'icon': 'bi-info-circle', 'tone': 'neutral',
                      'text': 'Not enough data yet — add more transactions to unlock insights.'})

    return cards


# ── 7. Dashboard support helpers ─────────────────────────────────────────

def get_income_breakdown(year=None, month=None):
    """Income by category (for a donut chart)."""
    return get_category_breakdown('income', year, month)


def get_weekday_spending(year=None, month=None):
    """Total expense per weekday (Mon..Sun) for the given month."""
    from .models import Transaction

    today = _today()
    year = year or today.year
    month = month or today.month

    txns = Transaction.objects.filter(
        transaction_type='expense',
        transaction_date__year=year, transaction_date__month=month,
    ).values('transaction_date', 'amount')

    totals = [0.0] * 7  # Mon=0 .. Sun=6
    for t in txns:
        totals[t['transaction_date'].weekday()] += _f(t['amount'])

    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return {'labels': labels, 'data': totals}


def get_cumulative_cashflow(year=None, month=None):
    """Running net (income - expense) across each day of the month."""
    from .models import Transaction

    today = _today()
    year = year or today.year
    month = month or today.month
    days_in_month = calendar.monthrange(year, month)[1]

    txns = Transaction.objects.filter(
        transaction_date__year=year, transaction_date__month=month,
    ).exclude(transaction_type='transfer').values(
        'transaction_date', 'transaction_type', 'amount')

    daily = {}
    for t in txns:
        d = t['transaction_date'].day
        delta = _f(t['amount']) if t['transaction_type'] == 'income' else -_f(t['amount'])
        daily[d] = daily.get(d, 0.0) + delta

    labels, data = [], []
    running = 0.0
    for day in range(1, days_in_month + 1):
        running += daily.get(day, 0.0)
        labels.append(str(day))
        data.append(round(running, 2))
    return {'labels': labels, 'data': data}


def get_spending_calendar(year=None, month=None):
    """Per-day expense totals laid out as calendar weeks for a heatmap grid."""
    from .models import Transaction

    today = _today()
    year = year or today.year
    month = month or today.month

    txns = Transaction.objects.filter(
        transaction_type='expense',
        transaction_date__year=year, transaction_date__month=month,
    ).values('transaction_date').annotate(total=Sum('amount'))
    day_map = {t['transaction_date'].day: _f(t['total']) for t in txns}

    max_amount = max(day_map.values()) if day_map else 0.0

    # calendar.monthcalendar -> list of weeks, each a list of 7 day-numbers (0 = padding)
    weeks = []
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(None)
            else:
                amount = day_map.get(day, 0.0)
                # intensity 0..4 for CSS color steps
                if max_amount <= 0 or amount <= 0:
                    level = 0
                else:
                    level = min(4, int(amount / max_amount * 4) + 1)
                row.append({'day': day, 'amount': amount, 'level': level})
        weeks.append(row)

    return {
        'weeks': weeks,
        'max_amount': max_amount,
        'weekday_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    }


def get_stat_sparklines(year=None, month=None):
    """6-month income / expense / savings series for mini stat-card sparklines."""
    trend = get_monthly_trend(6, year, month)
    return {
        'income': [m['income'] for m in trend],
        'expense': [m['expense'] for m in trend],
        'savings': [m['savings'] for m in trend],
        'labels': [m['month'] for m in trend],
    }
