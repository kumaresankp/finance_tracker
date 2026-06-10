from django import forms
from django.utils import timezone
from .models import Transaction, Category
from accounts.models import BankAccount


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'bank_account', 'transaction_date', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg amount-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True,
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'bank_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a note (optional)...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(category_type='expense')
        self.fields['bank_account'].queryset = BankAccount.objects.filter(is_active=True)
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['transaction_type'] = 'expense'
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.transaction_type = 'expense'
        if commit:
            instance.save()
        return instance


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'bank_account', 'transaction_date', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg amount-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True,
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'bank_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a note (optional)...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(category_type='income')
        self.fields['bank_account'].queryset = BankAccount.objects.filter(is_active=True)
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now().date()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.transaction_type = 'income'
        if commit:
            instance.save()
        return instance


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['bank_account', 'target_account', 'amount', 'transaction_date', 'note']
        widgets = {
            'bank_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'target_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg amount-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True,
            }),
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Transfer note (optional)...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_account'].queryset = BankAccount.objects.filter(is_active=True)
        self.fields['target_account'].queryset = BankAccount.objects.filter(is_active=True)
        self.fields['bank_account'].label = 'From Account'
        self.fields['target_account'].label = 'To Account'
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('bank_account')
        target = cleaned_data.get('target_account')
        amount = cleaned_data.get('amount')

        if source and target and source == target:
            raise forms.ValidationError("Source and destination accounts cannot be the same.")

        if source and amount:
            if amount > source.balance:
                raise forms.ValidationError(
                    f"Insufficient balance. Available: ₹{source.balance}"
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.transaction_type = 'transfer'
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name',
            }),
            'category_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color',
                'type': 'color',
            }),
            'icon': forms.Select(attrs={
                'class': 'form-select',
            }),
        }


class TransactionFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search transactions...',
        })
    )
    transaction_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types'), ('income', 'Income'), ('expense', 'Expense'), ('transfer', 'Transfer')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    account = forms.ModelChoiceField(
        required=False,
        queryset=BankAccount.objects.filter(is_active=True),
        empty_label='All Accounts',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )