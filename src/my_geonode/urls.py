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

from django.urls import include, path # Ensure 'include' and 'path' are imported
from geonode.urls import urlpatterns as geonode_urlpatterns # Rename GeoNode's urlpatterns to avoid conflict

# Start with GeoNode's default URL patterns
urlpatterns = geonode_urlpatterns

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
]
print("✅ Custom URL patterns loaded: info_hub and subscribers")

# ---------------------------

# No need to add admin/ here, GeoNode's geonode.urls already includes it.
# No need to add static/media serving here, Nginx handles it in Docker setup.