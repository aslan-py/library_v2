from django.urls import path

from .views import FundOptimizationView

app_name = 'analytics'

urlpatterns = [
    path('', FundOptimizationView.as_view(), name='optimization'),
]
