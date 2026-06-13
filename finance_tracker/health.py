"""Lightweight health-check endpoint for uptime monitors / load balancers.

Returns JSON and an HTTP status that reflects real liveness:
- 200 when the app can serve requests and reach the database.
- 503 when a dependency (the database) is unreachable.
"""
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache


@never_cache
def health_check(request):
    """Report application + database health."""
    checks = {}
    healthy = True

    # ── Database connectivity ──
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        checks['database'] = 'ok'
    except Exception as exc:  # pragma: no cover - defensive
        checks['database'] = f'error: {exc.__class__.__name__}'
        healthy = False

    payload = {
        'status': 'healthy' if healthy else 'unhealthy',
        'time': timezone.now().isoformat(),
        'checks': checks,
    }
    return JsonResponse(payload, status=200 if healthy else 503)
