#src/my_geonode/info_hub/api.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from geonode.layers.models import Dataset
from urllib.parse import urljoin
import json
try:
    import requests
except Exception:
    requests = None


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

        # Prefer the model helper method which returns tag names (authoritative)
        keywords = None
        try:
            if hasattr(ds, 'keyword_list'):
                _kw = ds.keyword_list()
                if _kw:
                    keywords = [str(k) for k in _kw]
        except Exception:
            keywords = None

        # Fallback to inspect common attributes if the helper returned nothing
        if not keywords:
            for field in ('keywords', 'subjects', 'tags'):
                if hasattr(ds, field):
                    val = getattr(ds, field)
                    try:
                        if hasattr(val, 'all'):
                            keywords = [str(k) for k in val.all()]
                        else:
                            if isinstance(val, str):
                                keywords = [s.strip() for s in val.split(',') if s.strip()]
                            else:
                                keywords = list(val)
                    except Exception:
                        keywords = None
                    break

        # Ensure bbox ordering (minx, miny, maxx, maxy)
        bbox = [None, None, None, None]
        try:
            bbox = [ds.bbox_x0, ds.bbox_y0, ds.bbox_x1, ds.bbox_y1]
        except Exception:
            bbox = [None, None, None, None]

        items.append({
            "id": ds.id,
            "title": ds.title,
            "wms_url": wms_url,
            "layer_name": layer_name,
            "bbox": bbox,
            "keywords": keywords or [],
        })

    return JsonResponse(items, safe=False)


@require_GET
def layer_attributes_api_view(request):
    """Return distinct attribute values for a given layer by proxying a WFS attributes-only request.

    Query params:
      - layer: required, the GeoServer typename (workspace:layer)
      - props: optional, comma-separated property names to return (defaults used if omitted)

    This view runs server-side WFS requests (same-origin) so the frontend doesn't need to fetch large GeoJSON or deal with CORS.
    """
    layer = request.GET.get('layer')
    props = request.GET.get('props')
    if not layer:
        return JsonResponse({'error': 'missing layer parameter'}, status=400)

    # default properties to inspect
    default_props = ['scenario', 'timeframe', 'season', 'crop', 'crop_type', 'suitability']
    if props:
        prop_list = [p.strip() for p in props.split(',') if p.strip()]
        if not prop_list:
            prop_list = default_props
    else:
        prop_list = default_props

    # Derive a WFS endpoint like in wms_layers_api_view
    wfs_base = getattr(settings, 'GEOSERVER_PUBLIC_LOCATION', None)
    try:
        if not wfs_base:
            wfs_base = settings.OGC_SERVER['default'].get('PUBLIC_LOCATION') or settings.OGC_SERVER['default'].get('LOCATION')
    except Exception:
        wfs_base = None
    if not wfs_base:
        wfs_base = urljoin(getattr(settings, 'SITEURL', '/'), 'geoserver/')
    if not wfs_base.endswith('/'):
        wfs_base += '/'
    # make sure it points to wfs
    try:
        u = urljoin(wfs_base, 'wfs')
        wfs_url = u
    except Exception:
        wfs_url = urljoin(getattr(settings, 'SITEURL', '/'), 'geoserver/wfs')

    params = {
        'service': 'WFS', 'version': '1.0.0', 'request': 'GetFeature',
        'typeName': layer, 'outputFormat': 'application/json', 'propertyName': ','.join(prop_list), 'maxFeatures': '5000'
    }

    # Server-side fetch to GeoServer WFS
    try:
        if requests:
            resp = requests.get(wfs_url, params=params, timeout=15)
            if resp.status_code != 200:
                return JsonResponse({'error': f'wfs request failed {resp.status_code}'}, status=502)
            j = resp.json()
        else:
            # fallback to urllib
            from urllib.request import urlopen
            from urllib.parse import urlencode
            url = f"{wfs_url}?{urlencode(params)}"
            with urlopen(url, timeout=15) as f:
                j = json.load(f)
    except Exception as e:
        return JsonResponse({'error': 'failed fetching WFS attributes', 'detail': str(e)}, status=502)

    # Aggregate distinct values
    out = {p: [] for p in prop_list}
    try:
        features = j.get('features', []) if isinstance(j, dict) else []
        sets = {p: set() for p in prop_list}
        for f in features:
            props_obj = f.get('properties') or {}
            for p in prop_list:
                v = props_obj.get(p)
                if v is None or v == '':
                    continue
                # normalize booleans/numbers/strings to strings
                try:
                    s = str(v)
                    sets[p].add(s)
                except Exception:
                    continue
        for p in prop_list:
            out[p] = sorted(list(sets[p]))
    except Exception as e:
        return JsonResponse({'error': 'failed processing WFS response', 'detail': str(e)}, status=500)

    return JsonResponse({'attributes': out})
