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
from django.urls import re_path
from django.shortcuts import redirect
from django.conf import settings
from .meta_views import meta_json
from django.views.generic import TemplateView, RedirectView
from geonode.urls import urlpatterns as geonode_core_urlpatterns
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView
from django.http import HttpResponse, Http404
from django.contrib.staticfiles import finders
from my_geonode.views import geoserver_ows
import os

# CRA entrypoint redirect
def react_app(request):
    # Serve the built CRA index.html directly so the URL stays at /app/
    rel = 'frontend/index.html'
    path = finders.find(rel)
    if path and os.path.exists(path):
        with open(path, 'rb') as f:
            return HttpResponse(f.read(), content_type='text/html; charset=utf-8')
    raise Http404('React build not found')

"""
Order matters: place SPA entrypoints before GeoNode's core URLs so hard refreshes
on React pages resolve to the SPA instead of GeoNode templates.
"""

# SPA patterns
spa_urlpatterns = [
    # /app base + deep links
    path('app/', react_app, name='react_app'),
    re_path(r'^app/.*$', react_app, name='react_app_catchall'),
]

# API and Core endpoints
api_urlpatterns = [
    # Mount info_hub at /info_hub for API endpoints like /info_hub/api/wms-layers
    path('info_hub/', include('info_hub.urls')),
    path('api/info_hub/', include('info_hub.urls')),
    path('api/subscribers/', include('subscribers.urls')),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path('api/contact/', include('contact.urls')),
    path('geoserver_proxy/ows', geoserver_ows),
]

# Specific SPA Toplevel routes (lower priority than APIs)
spa_toplevel_urlpatterns = [
    re_path(r'^advisory(?:/.*)?$', react_app, name='advisory'),
    re_path(r'^disease(?:/.*)?$', react_app, name='disease'),
    re_path(r'^suitability-map(?:/.*)?$', react_app, name='suitability_map'),
    re_path(r'^risk-map(?:/.*)?$', react_app, name='risk_map'),
    re_path(r'^about(?:/.*)?$', react_app, name='about'),
    re_path(r'^about-us(?:/.*)?$', react_app, name='about_us'),
    re_path(r'^contact(?:/.*)?$', react_app, name='contact'),
    re_path(r'^contact-us(?:/.*)?$', react_app, name='contact_us_dash'),
    re_path(r'^contactus(?:/.*)?$', react_app, name='contact_us'),
    re_path(r'^terms-and-conditions(?:/.*)?$', react_app, name='terms_and_conditions'),
]

urlpatterns = api_urlpatterns + spa_urlpatterns + spa_toplevel_urlpatterns + geonode_core_urlpatterns

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
    # Mount info_hub at /info_hub for API endpoints like /info_hub/api/wms-layers
    path('info_hub/', include('info_hub.urls')),
    path('api/info_hub/', include('info_hub.urls')),
    path('api/subscribers/', include('subscribers.urls')),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path('api/contact/', include('contact.urls')),
    # Backwards-compatible / plural forms redirect to singular (avoid React "No routes matched" warning)
    path('advisories', RedirectView.as_view(url='/advisory', permanent=False)),
    path('diseases', RedirectView.as_view(url='/disease', permanent=False)),
    path('meta.json', meta_json, name='meta_json'),
    path('geoserver_proxy/ows', geoserver_ows),
]

print("✅ Custom URL patterns loaded (GeoNode at root; React pages added; middleware protects GeoNode core)")

# ---------------------------

# No need to add admin/ here, GeoNode's geonode.urls already includes it.
# No need to add static/media serving here, Nginx handles it in Docker setup.

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
