from django.shortcuts import render
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
import json
import calendar
from decimal import Decimal

from .models import Budget, BudgetGroup
from .forms import BudgetForm, BudgetGroupForm
from .services import (
    get_budget_status,
    get_overall_budget_status,
    get_group_status,
    get_budget_alerts,
    get_budget_history,
    get_budget_summary,
)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


# ── Overview ─────────────────────────────────────────────────────────────

def budget_overview(request):
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

    summary = get_budget_summary(year, month)
    category_budgets = get_budget_status(year, month)
    overall = get_overall_budget_status(year, month)
    groups = get_group_status(year, month)
    alerts = get_budget_alerts(year, month)
    history = get_budget_history(months=6, year=year, month=month)

    chart_data = {'history': history}

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(now.year - 3, now.year + 2))

    context = {
        'summary': summary,
        'category_budgets': category_budgets,
        'overall': overall,
        'groups': groups,
        'alerts': alerts,
        'has_budgets': bool(category_budgets or overall or groups),
        'chart_data_json': json.dumps(chart_data, default=decimal_default),
        'selected_year': year,
        'selected_month': month,
        'months': months,
        'years': years,
        'page_title': 'Budgets',
    }
    return render(request, 'budgets/budget_overview.html', context)


# ── Budget CRUD ──────────────────────────────────────────────────────────

class BudgetCreateView(CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:overview')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Budget for "{self.object.display_name}" created.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Budget'
        context['btn_text'] = 'Create Budget'
        return context


class BudgetUpdateView(UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:overview')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Budget for "{self.object.display_name}" updated.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Budget'
        context['btn_text'] = 'Update Budget'
        return context


class BudgetDeleteView(DeleteView):
    model = Budget
    template_name = 'budgets/budget_confirm_delete.html'
    success_url = reverse_lazy('budgets:overview')

    def form_valid(self, form):
        name = self.get_object().display_name
        response = super().form_valid(form)
        messages.success(self.request, f'Budget for "{name}" deleted.')
        return response


# ── Budget group CRUD ────────────────────────────────────────────────────

class BudgetGroupCreateView(CreateView):
    model = BudgetGroup
    form_class = BudgetGroupForm
    template_name = 'budgets/budget_group_form.html'
    success_url = reverse_lazy('budgets:overview')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Group "{self.object.name}" created.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Budget Group'
        context['btn_text'] = 'Create Group'
        return context


class BudgetGroupUpdateView(UpdateView):
    model = BudgetGroup
    form_class = BudgetGroupForm
    template_name = 'budgets/budget_group_form.html'
    success_url = reverse_lazy('budgets:overview')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Group "{self.object.name}" updated.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Budget Group'
        context['btn_text'] = 'Update Group'
        return context


class BudgetGroupDeleteView(DeleteView):
    model = BudgetGroup
    template_name = 'budgets/budget_confirm_delete.html'
    success_url = reverse_lazy('budgets:overview')

    def form_valid(self, form):
        name = self.get_object().name
        response = super().form_valid(form)
        messages.success(self.request, f'Group "{name}" deleted.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_group'] = True
        return context
