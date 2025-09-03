#src/my_geonode/info_hub/api.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from geonode.layers.models import Dataset
from urllib.parse import urljoin


@require_GET
def wms_layers_api_view(request):
    """Return a JSON list of published GeoNode layers for WMS display.

    Shape each item for the frontend:
      - id: numeric Layer id
      - title: display title
      - wms_url: GeoServer WMS base URL
      - layer_name: GeoServer published layer name (typename)
      - bbox: [minx, miny, maxx, maxy]
    """
    # Filter published datasets; avoid non-public
    qs = Dataset.objects.filter(is_published=True)

    # Derive WMS base URL from settings; prefer GEOSERVER_PUBLIC_LOCATION
    wms_base = getattr(settings, 'GEOSERVER_PUBLIC_LOCATION', None)
    try:
        if not wms_base:
            wms_base = settings.OGC_SERVER['default'].get('PUBLIC_LOCATION') or settings.OGC_SERVER['default'].get('LOCATION')
    except Exception:
        pass
    if not wms_base:
        # Last-resort sensible default under SITEURL
        wms_base = urljoin(getattr(settings, 'SITEURL', '/'), 'geoserver/')
    # Ensure trailing slash then join 'wms'
    if not wms_base.endswith('/'):
        wms_base += '/'
    wms_url = urljoin(getattr(settings, 'SITEURL', '/'), 'geoserver/wms')
    items = []
    for ds in qs:
        # Prefer fully qualified typename; fall back to alternate or name
        layer_name = getattr(ds, "typename", None) or getattr(ds, "alternate", None) or getattr(ds, "name", None)
        items.append({
            "id": ds.id,
            "title": ds.title,
            "wms_url": wms_url,
            "layer_name": layer_name,
            "bbox": [
                ds.bbox_x0,
                ds.bbox_y0,
                ds.bbox_x1,
                ds.bbox_y1,
            ],
        })

    return JsonResponse(items, safe=False)
