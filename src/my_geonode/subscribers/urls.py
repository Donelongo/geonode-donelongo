# subscribers/urls.py
from django.urls import path
from .views import SubscribeAPIView
from . import views

app_name = 'subscribers' # <--- THIS LINE IS MISSING! Add this.

urlpatterns = [
    path('subscribe/', SubscribeAPIView.as_view(), name='subscribe'),
    path('unsubscribe/<int:subscriber_id>/<str:token>/', views.unsubscribe_view, name='unsubscribe'),
]   