# yourapp/urls.py
from django.urls import path
from .views import MyDataAPIView

urlpatterns = [
    path('ym-data/<str:start_date>/<str:end_date>/<str:month>/', MyDataAPIView.as_view(), name='ym-data'),
]
