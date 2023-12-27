# yourapp/urls.py
from django.urls import path
from .views import Customer_DataAPIView, QSR_View

urlpatterns = [
    path('cm_data/<str:start_date>/<str:end_date>/<str:month>/', Customer_DataAPIView.as_view(), name='customer-data'),
    path('qsr/<str:ads>/<str:dc>/', QSR_View.as_view(), name='QSR-data'),
]
