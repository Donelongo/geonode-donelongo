from django.http import JsonResponse
from django.conf import settings
import pkg_resources


def meta_json(request):
    """Return lightweight app metadata for clients expecting /meta.json."""
    try:
        geonode_version = pkg_resources.get_distribution('geonode').version
    except Exception:
        geonode_version = None
    return JsonResponse({
        "app": getattr(settings, 'SITENAME', 'GeoNode'),
        "geonode_version": geonode_version,
        "siteurl": getattr(settings, 'SITEURL', ''),
    })
