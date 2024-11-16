from django.urls import path
from . import views

app_name = 'nomina_app'

urlpatterns = [
    path('', views.process_excel, name='process_excel'),
]