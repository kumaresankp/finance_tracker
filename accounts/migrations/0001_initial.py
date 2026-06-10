# Generated migration file for accounts app

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('account_type', models.CharField(choices=[('savings', 'Savings'), ('current', 'Current'), ('salary', 'Salary'), ('cash', 'Cash'), ('credit', 'Credit Card'), ('upi', 'UPI Wallet'), ('investment', 'Investment'), ('other', 'Other')], default='savings', max_length=20)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=15)),
                ('color', models.CharField(default='#6366f1', max_length=7)),
                ('icon', models.CharField(choices=[('bi-bank', 'Bank'), ('bi-cash-stack', 'Cash'), ('bi-credit-card', 'Credit Card'), ('bi-phone', 'UPI/Mobile'), ('bi-wallet2', 'Wallet'), ('bi-piggy-bank', 'Piggy Bank'), ('bi-currency-dollar', 'Investment'), ('bi-building', 'Building')], default='bi-bank', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
