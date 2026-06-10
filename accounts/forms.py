from django import forms
from .models import BankAccount


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'account_type', 'balance', 'color', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SBI Savings Account',
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color',
                'type': 'color',
            }),
            'icon': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_balance(self):
        balance = self.cleaned_data.get('balance')
        if balance is None:
            balance = 0
        return balance