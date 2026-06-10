from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse


def settings_view(request):
    context = {
        'page_title': 'Settings',
    }
    return render(request, 'settings_app/settings.html', context)


def seed_data(request):
    """Seed sample data for demonstration"""
    if request.method == 'POST':
        from accounts.models import BankAccount
        from transactions.models import Category, Transaction
        from django.utils import timezone
        from datetime import date, timedelta
        import random
        from decimal import Decimal

        # Create accounts
        accounts_data = [
            {'name': 'SBI Savings', 'account_type': 'savings', 'balance': 50000, 'color': '#3b82f6', 'icon': 'bi-bank'},
            {'name': 'HDFC Salary', 'account_type': 'salary', 'balance': 35000, 'color': '#10b981', 'icon': 'bi-credit-card'},
            {'name': 'Cash Wallet', 'account_type': 'cash', 'balance': 5000, 'color': '#f59e0b', 'icon': 'bi-cash-stack'},
            {'name': 'UPI Wallet', 'account_type': 'upi', 'balance': 2000, 'color': '#8b5cf6', 'icon': 'bi-phone'},
        ]

        created_accounts = []
        for acc_data in accounts_data:
            acc, created = BankAccount.objects.get_or_create(
                name=acc_data['name'],
                defaults=acc_data
            )
            created_accounts.append(acc)

        # Create categories
        expense_cats = [
            ('Food & Dining', '#ef4444', 'bi-cup-hot'),
            ('Transport', '#f97316', 'bi-car-front'),
            ('Shopping', '#a855f7', 'bi-cart'),
            ('Entertainment', '#ec4899', 'bi-film'),
            ('Health', '#06b6d4', 'bi-heart-pulse'),
            ('Utilities', '#6366f1', 'bi-lightning'),
            ('Education', '#14b8a6', 'bi-mortarboard'),
            ('Groceries', '#84cc16', 'bi-basket'),
        ]
        income_cats = [
            ('Salary', '#10b981', 'bi-briefcase'),
            ('Freelance', '#3b82f6', 'bi-laptop'),
            ('Business', '#f59e0b', 'bi-building'),
            ('Investment Returns', '#8b5cf6', 'bi-graph-up'),
        ]

        exp_category_objs = []
        for name, color, icon in expense_cats:
            cat, _ = Category.objects.get_or_create(
                name=name, category_type='expense',
                defaults={'color': color, 'icon': icon}
            )
            exp_category_objs.append(cat)

        inc_category_objs = []
        for name, color, icon in income_cats:
            cat, _ = Category.objects.get_or_create(
                name=name, category_type='income',
                defaults={'color': color, 'icon': icon}
            )
            inc_category_objs.append(cat)

        # Create sample transactions (last 3 months)
        today = date.today()
        notes_expense = [
            'Lunch at restaurant', 'Grocery shopping', 'Bus ticket',
            'Movie tickets', 'Medicine', 'Electricity bill', 'Online course',
            'Petrol', 'Coffee', 'Dinner', 'Metro card recharge',
        ]
        notes_income = [
            'Monthly salary', 'Freelance project', 'Bonus', 'Client payment'
        ]

        transactions_created = 0
        for days_back in range(90):
            t_date = today - timedelta(days=days_back)

            # Monthly salary on 1st
            if t_date.day == 1 and not Transaction.objects.filter(
                transaction_date=t_date, transaction_type='income',
                category=inc_category_objs[0]
            ).exists():
                Transaction.objects.create(
                    transaction_type='income',
                    bank_account=created_accounts[1],
                    category=inc_category_objs[0],
                    amount=Decimal('45000'),
                    note='Monthly salary credit',
                    transaction_date=t_date,
                )
                transactions_created += 1

            # 1-3 random expenses per day (sometimes)
            if random.random() > 0.3:
                num_exp = random.randint(1, 3)
                for _ in range(num_exp):
                    cat = random.choice(exp_category_objs)
                    amount = Decimal(str(round(random.uniform(50, 2000), 2)))
                    acc = random.choice(created_accounts)
                    if not Transaction.objects.filter(
                        transaction_date=t_date, bank_account=acc,
                        category=cat, amount=amount
                    ).exists():
                        Transaction.objects.create(
                            transaction_type='expense',
                            bank_account=acc,
                            category=cat,
                            amount=amount,
                            note=random.choice(notes_expense),
                            transaction_date=t_date,
                        )
                        transactions_created += 1

        messages.success(
            request,
            f'Sample data created! {transactions_created} transactions added.'
        )
        return redirect('dashboard:dashboard')

    return redirect('settings_app:settings')


def clear_data(request):
    """Clear all data"""
    if request.method == 'POST':
        from transactions.models import Transaction, Category
        from accounts.models import BankAccount

        Transaction.objects.all().delete()
        Category.objects.all().delete()
        BankAccount.objects.all().delete()

        messages.success(request, 'All data cleared successfully.')
        return redirect('settings_app:settings')

    return redirect('settings_app:settings')