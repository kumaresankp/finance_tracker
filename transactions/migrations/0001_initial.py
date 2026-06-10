# Generated migration file for transactions app

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('category_type', models.CharField(choices=[('income', 'Income'), ('expense', 'Expense')], max_length=10)),
                ('color', models.CharField(default='#6366f1', max_length=7)),
                ('icon', models.CharField(default='bi-three-dots', max_length=50)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('income', 'Income'), ('expense', 'Expense'), ('transfer', 'Transfer')], max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('note', models.TextField(blank=True, default='')),
                ('transaction_date', models.DateField(default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='accounts.bankaccount')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='transactions.category')),
                ('target_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incoming_transfers', to='accounts.bankaccount')),
            ],
            options={
                'ordering': ['-transaction_date', '-created_at'],
            },
        ),
    ]
