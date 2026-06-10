from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from .models import BankAccount
from .forms import BankAccountForm
from transactions.models import Transaction


class AccountListView(ListView):
    model = BankAccount
    template_name = 'accounts/account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return BankAccount.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_balance'] = BankAccount.objects.filter(
            is_active=True
        ).aggregate(total=Sum('balance'))['total'] or 0
        context['inactive_accounts'] = BankAccount.objects.filter(is_active=False)
        return context


class AccountCreateView(CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'partials/success_message.html', {
                'message': f'Account "{self.object.name}" created successfully!'
            })
        messages.success(self.request, f'Account "{self.object.name}" created successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Account'
        context['btn_text'] = 'Create Account'
        return context


class AccountUpdateView(UpdateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Account "{self.object.name}" updated successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Account'
        context['btn_text'] = 'Update Account'
        return context


class AccountDeleteView(DeleteView):
    model = BankAccount
    template_name = 'accounts/account_confirm_delete.html'
    success_url = reverse_lazy('accounts:list')

    def form_valid(self, form):
        account = self.get_object()
        name = account.name
        response = super().form_valid(form)
        messages.success(self.request, f'Account "{name}" deleted successfully!')
        return response


def account_detail(request, pk):
    account = get_object_or_404(BankAccount, pk=pk)
    transactions = Transaction.objects.filter(
        Q(bank_account=account) | Q(target_account=account)
    ).order_by('-transaction_date', '-created_at')[:50]

    context = {
        'account': account,
        'transactions': transactions,
        'total_income': account.get_total_income(),
        'total_expense': account.get_total_expense(),
    }
    return render(request, 'accounts/account_detail.html', context)


def get_accounts_json(request):
    """API endpoint for HTMX dropdowns"""
    accounts = BankAccount.objects.filter(is_active=True).values(
        'id', 'name', 'account_type', 'balance', 'color', 'icon'
    )
    return JsonResponse({'accounts': list(accounts)})