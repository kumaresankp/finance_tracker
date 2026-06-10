from django.urls import path
from . import views

app_name = 'settings_app'

urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('seed/', views.seed_data, name='seed_data'),
    path('clear/', views.clear_data, name='clear_data'),
]