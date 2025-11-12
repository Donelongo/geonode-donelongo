# my_geonode/info_hub/urls.py (Ensure this is EXACTLY what you have)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api


app_name = 'info_hub' # <--- CRITICAL: Make sure this line is present and correct

router = DefaultRouter()
router.register(r'advisories', views.AdvisoryMessageViewSet, basename='advisorymessage')
router.register(r'diseases', views.DiseaseViewSet, basename='disease')

urlpatterns = [
    path('', include(router.urls)),
    # This line is the key for the PDF download:
    path('advisory/<int:advisory_id>/pdf/', views.download_advisory_pdf, name='advisory_pdf'),
    # API endpoint for WMS layer list
    path('api/wms-layers', api.wms_layers_api_view, name='wms-layers-api'),
    # API endpoint to get distinct attribute values for a layer (server-side WFS proxy)
    path('api/layer-attributes', api.layer_attributes_api_view, name='layer-attributes-api'),

]