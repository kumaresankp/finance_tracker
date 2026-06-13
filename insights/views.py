from django.shortcuts import render
from django.utils import timezone
import json
import calendar
from decimal import Decimal

from transactions.analytics import (
    get_financial_health_score,
    get_spending_anomalies,
    get_top_movers,
    get_spend_forecast,
    detect_recurring,
    get_narrative_insights,
)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def insights_view(request):
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

    health = get_financial_health_score(year, month)
    anomalies = get_spending_anomalies(year, month)
    movers = get_top_movers(year, month)
    forecast = get_spend_forecast(year, month)
    recurring = detect_recurring()
    narratives = get_narrative_insights(year, month)

    # Data for the health-score gauge (doughnut) rendered client-side.
    chart_data = {
        'health': {
            'score': health['score'],
            'components': [
                {'label': c['label'], 'score': c['score']} for c in health['components']
            ],
        },
        'forecast': {
            'projected': forecast['projected'],
            'prev_month': forecast['prev_month'],
            'spent_so_far': forecast['spent_so_far'],
        },
    }

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(now.year - 3, now.year + 2))

    context = {
        'health': health,
        'anomalies': anomalies,
        'movers': movers,
        'forecast': forecast,
        'recurring': recurring,
        'narratives': narratives,
        'chart_data_json': json.dumps(chart_data, default=decimal_default),
        'selected_year': year,
        'selected_month': month,
        'months': months,
        'years': years,
        'page_title': 'Insights',
    }
    return render(request, 'insights/insights.html', context)
