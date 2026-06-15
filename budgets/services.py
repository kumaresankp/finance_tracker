"""Budget computation layer — live tracking of budgets against real transactions.

All functions are defensive about empty data and return JSON-safe primitives.
Spend figures come from the transactions services/analytics already in the project.
"""
from django.utils import timezone
from decimal import Decimal
import calendar

from transactions.services import get_category_breakdown, get_monthly_summary


# ── helpers ──────────────────────────────────────────────────────────────

def _today():
    return timezone.now().date()


def _resolve(year, month):
    today = _today()
    return (year or today.year), (month or today.month)


def _f(value):
    return float(value or 0)


def _projection_factor(year, month):
    """days_in_month / days_elapsed for the current month, else 1.0 (final)."""
    today = _today()
    days_in_month = calendar.monthrange(year, month)[1]
    if year == today.year and month == today.month:
        elapsed = max(today.day, 1)
        return days_in_month / elapsed
    return 1.0


def _category_spend_map(year, month):
    """{category_name: spent_float} for expenses in the period."""
    return {c['category__name']: _f(c['total'])
            for c in get_category_breakdown('expense', year, month)}


# ── per-budget spend (used by Budget model wrappers) ─────────────────────

def budget_spent(budget, year=None, month=None):
    """Decimal amount spent against a single budget in the given month."""
    year, month = _resolve(year, month)
    if budget.budget_type == 'overall':
        return Decimal(str(get_monthly_summary(year, month)['expense']))
    if not budget.category:
        return Decimal('0')
    spend = _category_spend_map(year, month).get(budget.category.name, 0.0)
    return Decimal(str(spend))


# ── status builders ──────────────────────────────────────────────────────

def _build_status(budget, spent, year, month):
    amount = _f(budget.amount)
    spent = _f(spent)
    factor = _projection_factor(year, month)
    projected = spent * factor
    pct = (spent / amount * 100) if amount else 0.0
    projected_pct = (projected / amount * 100) if amount else 0.0

    if pct >= 100:
        status = 'over'
    elif pct >= budget.alert_threshold:
        status = 'warning'
    else:
        status = 'under'

    return {
        'budget': budget,
        'id': budget.id,
        'name': budget.display_name,
        'color': budget.color,
        'icon': budget.icon,
        'amount': amount,
        'spent': spent,
        'remaining': amount - spent,
        'pct_used': round(pct, 1),
        'pct_bar': min(pct, 100),
        'status': status,
        'threshold': budget.alert_threshold,
        'projected': projected,
        'projected_pct': round(projected_pct, 1),
        'will_exceed': projected > amount and status != 'over',
    }


def get_budget_status(year=None, month=None):
    """List of per-category budget status dicts, sorted worst-first."""
    from .models import Budget

    year, month = _resolve(year, month)
    budgets = (Budget.objects.filter(budget_type='category', is_active=True)
               .select_related('category', 'group'))
    spend_map = _category_spend_map(year, month)

    rows = []
    for b in budgets:
        spent = spend_map.get(b.category.name, 0.0) if b.category else 0.0
        rows.append(_build_status(b, spent, year, month))

    rows.sort(key=lambda r: r['pct_used'], reverse=True)
    return rows


def get_overall_budget_status(year=None, month=None):
    """Status dict for the single overall monthly budget, or None."""
    from .models import Budget

    year, month = _resolve(year, month)
    budget = Budget.objects.filter(budget_type='overall', is_active=True).first()
    if not budget:
        return None
    spent = get_monthly_summary(year, month)['expense']
    return _build_status(budget, spent, year, month)


def get_group_status(year=None, month=None):
    """Per-group rollup: shared limit vs summed spend of member categories."""
    from .models import BudgetGroup

    year, month = _resolve(year, month)
    spend_map = _category_spend_map(year, month)
    factor = _projection_factor(year, month)

    groups = []
    for group in BudgetGroup.objects.prefetch_related('budgets__category'):
        members = [b for b in group.budgets.all()
                   if b.is_active and b.budget_type == 'category']
        if not members and group.monthly_limit is None:
            continue

        spent = sum(spend_map.get(b.category.name, 0.0)
                    for b in members if b.category)
        limit = _f(group.monthly_limit) if group.monthly_limit is not None \
            else sum(_f(b.amount) for b in members)
        projected = spent * factor
        pct = (spent / limit * 100) if limit else 0.0

        groups.append({
            'group': group,
            'name': group.name,
            'color': group.color,
            'icon': group.icon,
            'limit': limit,
            'spent': spent,
            'remaining': limit - spent,
            'pct_used': round(pct, 1),
            'pct_bar': min(pct, 100),
            'projected': projected,
            'has_shared_cap': group.monthly_limit is not None,
            'member_count': len(members),
            'members': [_build_status(
                b, spend_map.get(b.category.name, 0.0) if b.category else 0.0,
                year, month) for b in members],
        })
    return groups


def get_budget_alerts(year=None, month=None):
    """Flat list of alert dicts for budgets at/over threshold or projected to exceed."""
    year, month = _resolve(year, month)
    alerts = []

    rows = get_budget_status(year, month)
    overall = get_overall_budget_status(year, month)
    if overall:
        rows = [overall] + rows

    for r in rows:
        if r['status'] == 'over':
            alerts.append({
                'level': 'danger',
                'title': f"{r['name']} over budget",
                'detail': (f"₹{r['spent']:,.0f} spent of ₹{r['amount']:,.0f} "
                           f"({r['pct_used']:.0f}%)."),
            })
        elif r['status'] == 'warning':
            alerts.append({
                'level': 'warning',
                'title': f"{r['name']} nearing limit",
                'detail': (f"₹{r['spent']:,.0f} of ₹{r['amount']:,.0f} "
                           f"({r['pct_used']:.0f}%) used."),
            })
        elif r['will_exceed']:
            alerts.append({
                'level': 'warning',
                'title': f"{r['name']} projected to exceed",
                'detail': (f"On pace for ₹{r['projected']:,.0f} vs ₹{r['amount']:,.0f} limit."),
            })
    return alerts


def get_budget_history(budget=None, months=6, year=None, month=None):
    """6-month budget-vs-actual series. If budget is None, uses the overall budget
    (or total of category budgets when no overall budget exists)."""
    from .models import Budget

    year, month = _resolve(year, month)

    if budget is None:
        budget = Budget.objects.filter(budget_type='overall', is_active=True).first()

    labels, budget_line, actual_line = [], [], []
    for i in range(months - 1, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1

        if budget is not None:
            limit = _f(budget.amount)
            actual = _f(budget_spent(budget, y, m))
        else:
            # aggregate of all active category budgets
            active = Budget.objects.filter(budget_type='category', is_active=True)\
                .select_related('category')
            limit = sum(_f(b.amount) for b in active)
            spend_map = _category_spend_map(y, m)
            actual = sum(spend_map.get(b.category.name, 0.0)
                         for b in active if b.category)

        labels.append(calendar.month_abbr[m])
        budget_line.append(limit)
        actual_line.append(actual)

    return {'labels': labels, 'budget': budget_line, 'actual': actual_line}


def get_budget_summary(year=None, month=None):
    """Totals for the overview stat cards."""
    year, month = _resolve(year, month)
    rows = get_budget_status(year, month)

    total_budgeted = sum(r['amount'] for r in rows)
    total_spent = sum(r['spent'] for r in rows)
    over_count = sum(1 for r in rows if r['status'] == 'over')
    warning_count = sum(1 for r in rows if r['status'] == 'warning')
    on_track = sum(1 for r in rows if r['status'] == 'under')

    return {
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'total_remaining': total_budgeted - total_spent,
        'pct_used': round(total_spent / total_budgeted * 100, 1) if total_budgeted else 0.0,
        'count': len(rows),
        'over_count': over_count,
        'warning_count': warning_count,
        'on_track': on_track,
    }
