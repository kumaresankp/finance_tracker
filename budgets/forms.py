from django import forms
from transactions.models import Category
from .models import Budget, BudgetGroup


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['budget_type', 'category', 'group', 'amount',
                  'alert_threshold', 'is_active', 'note']
        widgets = {
            'budget_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_budget_type'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '0.00',
                'step': '0.01', 'min': '0',
            }),
            'alert_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '1', 'max': '100',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Optional note about this budget',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only expense categories can carry a spending budget.
        self.fields['category'].queryset = Category.objects.filter(
            category_type='expense'
        )
        self.fields['category'].required = False
        self.fields['group'].required = False
        self.fields['group'].empty_label = 'No group'

    def clean(self):
        cleaned = super().clean()
        budget_type = cleaned.get('budget_type')
        category = cleaned.get('category')
        is_active = cleaned.get('is_active')

        if budget_type == 'category':
            if not category:
                self.add_error('category', 'Select a category for a category budget.')
            else:
                dup = Budget.objects.filter(
                    budget_type='category', category=category, is_active=True
                ).exclude(pk=self.instance.pk)
                if is_active and dup.exists():
                    self.add_error(
                        'category',
                        f'An active budget for "{category.name}" already exists.'
                    )
        elif budget_type == 'overall':
            cleaned['category'] = None
            dup = Budget.objects.filter(
                budget_type='overall', is_active=True
            ).exclude(pk=self.instance.pk)
            if is_active and dup.exists():
                raise forms.ValidationError(
                    'An active overall monthly budget already exists. '
                    'Edit the existing one instead.'
                )
        return cleaned


class BudgetGroupForm(forms.ModelForm):
    class Meta:
        model = BudgetGroup
        fields = ['name', 'color', 'icon', 'monthly_limit', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g., Essentials',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color', 'type': 'color',
            }),
            'icon': forms.Select(attrs={'class': 'form-select'}),
            'monthly_limit': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Optional shared cap',
                'step': '0.01', 'min': '0',
            }),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
