from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # Main transaction types
    path('expense/', views.expense_view, name='expense'),
    path('income/', views.income_view, name='income'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('list/', views.transaction_list, name='list'),

    # Transaction CRUD
    path('<int:pk>/edit/', views.transaction_edit, name='edit'),
    path('<int:pk>/delete/', views.transaction_delete, name='delete'),

    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Import / Export
    path('import-export/', views.import_export_view, name='import_export'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('import/excel/', views.import_excel, name='import_excel'),
    path('backup/', views.backup_database, name='backup'),
    path('restore/', views.restore_database, name='restore'),
]