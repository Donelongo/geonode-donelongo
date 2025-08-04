from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriberViewSet, unsubscribe_view

app_name = 'subscribers'

router = DefaultRouter()
router.register(r'', SubscriberViewSet, basename='subscriber')

urlpatterns = [
    path('', include(router.urls)),  # handles /api/subscribers/
    path('unsubscribe/<int:subscriber_id>/<str:token>/', unsubscribe_view, name='unsubscribe'),
]
