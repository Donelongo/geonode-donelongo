# agro_advisory_system/info_hub/urls.py (Ensure this is EXACTLY what you have)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'info_hub' # <--- CRITICAL: Make sure this line is present and correct

router = DefaultRouter()
router.register(r'advisories', views.AdvisoryMessageViewSet, basename='advisorymessage')
router.register(r'diseases', views.DiseaseViewSet, basename='disease')

urlpatterns = [
    path('', include(router.urls)),
    # This line is the key for the PDF download:
    path('advisories/<int:advisory_id>/download/pdf/', views.download_advisory_pdf, name='download_advisory_pdf'),
]