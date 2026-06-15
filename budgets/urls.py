from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.budget_overview, name='overview'),
    path('create/', views.BudgetCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='delete'),
    path('groups/create/', views.BudgetGroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/edit/', views.BudgetGroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', views.BudgetGroupDeleteView.as_view(), name='group_delete'),
]
