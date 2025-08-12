# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.urls import include, path  # Ensure 'include' and 'path' are imported
from django.views.generic import TemplateView, RedirectView
from geonode.urls import urlpatterns as geonode_core_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView

urlpatterns = geonode_core_urlpatterns

# You can register your own urlpatterns here
# Example of adding a custom homepage (uncomment and modify if needed):
# from my_geonode.views import homepage # Assuming you have a homepage view in your custom project
# urlpatterns = [
#     path('', homepage, name='home'),
# ] + urlpatterns

# --- Your Custom App URLs ---
# It's highly recommended to prefix your custom API endpoints
# to avoid conflicts with GeoNode's existing URLs.
urlpatterns += [
    path('api/info_hub/', include('info_hub.urls')),
    path('api/subscribers/', include('subscribers.urls')),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path('api/contact/', include('contact.urls')),
    # React embedded pages – align Django entrypoints with React Router paths (singular)
    path('advisory', TemplateView.as_view(template_name='frontend/app.html'), name='advisory'),  # React
    path('disease', TemplateView.as_view(template_name='frontend/app.html'), name='disease'),
    # Backwards-compatible / plural forms redirect to singular (avoid React "No routes matched" warning)
    path('advisories', RedirectView.as_view(url='/advisory', permanent=False)),
    path('diseases', RedirectView.as_view(url='/disease', permanent=False)),
    # Other React top-level pages (allow hard refresh / direct access)
    path('suitability-map', TemplateView.as_view(template_name='frontend/app.html'), name='suitability_map'),
    path('risk-map', TemplateView.as_view(template_name='frontend/app.html'), name='risk_map'),
    path('about', TemplateView.as_view(template_name='frontend/app.html'), name='about'),
    path('contact', TemplateView.as_view(template_name='frontend/app.html'), name='contact'),
    path('terms-and-conditions', TemplateView.as_view(template_name='frontend/app.html'), name='terms_and_conditions'),

]

print("✅ Custom URL patterns loaded (GeoNode at root; React pages added; middleware protects GeoNode core)")

# ---------------------------

# No need to add admin/ here, GeoNode's geonode.urls already includes it.
# No need to add static/media serving here, Nginx handles it in Docker setup.

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
