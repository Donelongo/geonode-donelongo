#src/my_geonode/info_hub/api.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from geonode.layers.models import Dataset
from urllib.parse import urljoin
import json
import logging
import xml.etree.ElementTree as ET
try:
    import requests
except Exception:
    requests = None

logger = logging.getLogger(__name__)


def _guess_keywords(layer_name, layer_title):
    text = f"{layer_name or ''} {layer_title or ''}".lower()
    out = []
    if "risk" in text:
        out.append("risk")
    if "suitability" in text:
        out.append("suitability")
    return out


def _tag_endswith(elem, suffix):
    try:
        return elem.tag.endswith(suffix)
    except Exception:
        return False


def _find_child_text(layer_elem, suffix):
    for child in list(layer_elem):
        if _tag_endswith(child, suffix):
            return (child.text or "").strip()
    return ""


def _extract_bbox_from_layer(layer_elem):
    # WMS 1.3.0: EX_GeographicBoundingBox
    for child in list(layer_elem):
        if _tag_endswith(child, "EX_GeographicBoundingBox"):
            vals = {}
            for n in list(child):
                k = n.tag.split("}")[-1]
                vals[k] = (n.text or "").strip()
            try:
                return [
                    float(vals.get("westBoundLongitude")),
                    float(vals.get("southBoundLatitude")),
                    float(vals.get("eastBoundLongitude")),
                    float(vals.get("northBoundLatitude")),
                ]
            except Exception:
                pass

    # WMS 1.1.1 fallback: LatLonBoundingBox attributes
    for child in list(layer_elem):
        if _tag_endswith(child, "LatLonBoundingBox"):
            try:
                return [
                    float(child.attrib.get("minx")),
                    float(child.attrib.get("miny")),
                    float(child.attrib.get("maxx")),
                    float(child.attrib.get("maxy")),
                ]
            except Exception:
                pass

    return [None, None, None, None]


def _fallback_layers_from_capabilities():
    """Fallback source for layers when GeoNode Dataset ORM is not usable."""
    siteurl = getattr(settings, "SITEURL", "/")
    public_wms_url = urljoin(siteurl, "geoserver/wms")

    # Prefer internal GeoServer URL for server-side fetch
    try:
        base = settings.OGC_SERVER["default"].get("LOCATION") or "http://geoserver:8080/geoserver/"
    except Exception:
        base = "http://geoserver:8080/geoserver/"
    if not base.endswith("/"):
        base += "/"
    internal_wms_url = urljoin(base, "wms")

    caps_params = {"service": "WMS", "request": "GetCapabilities"}
    xml_text = None
    try:
        if requests:
            resp = requests.get(internal_wms_url, params=caps_params, timeout=20)
            resp.raise_for_status()
            xml_text = resp.text
        else:
            from urllib.request import urlopen
            from urllib.parse import urlencode
            with urlopen(f"{internal_wms_url}?{urlencode(caps_params)}", timeout=20) as f:
                xml_text = f.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning("WMS capabilities fallback failed: %s", e)
        return []

    if not xml_text:
        return []

    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        logger.warning("Invalid WMS capabilities XML: %s", e)
        return []

    items = []
    idx = 1
    for layer in root.iter():
        if not _tag_endswith(layer, "Layer"):
            continue
        name = _find_child_text(layer, "Name")
        if not name:
            continue
        title = _find_child_text(layer, "Title") or name
        items.append(
            {
                "id": idx,
                "title": title,
                "wms_url": public_wms_url,
                "layer_name": name,
                "bbox": _extract_bbox_from_layer(layer),
                "keywords": _guess_keywords(name, title),
            }
        )
        idx += 1

    return items


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
    items = []
    siteurl = getattr(settings, "SITEURL", "/")
    wms_url = urljoin(siteurl, "geoserver/wms")

    # Primary source: GeoNode datasets (when model/db schema are aligned).
    try:
        qs = Dataset.objects.filter(is_published=True)
        for ds in qs:
            layer_name = getattr(ds, "typename", None) or getattr(ds, "alternate", None) or getattr(ds, "name", None)
            keywords = None
            try:
                if hasattr(ds, "keyword_list"):
                    _kw = ds.keyword_list()
                    if _kw:
                        keywords = [str(k) for k in _kw]
            except Exception:
                keywords = None
            bbox = [None, None, None, None]
            try:
                bbox = [ds.bbox_x0, ds.bbox_y0, ds.bbox_x1, ds.bbox_y1]
            except Exception:
                bbox = [None, None, None, None]
            items.append(
                {
                    "id": ds.id,
                    "title": ds.title,
                    "wms_url": wms_url,
                    "layer_name": layer_name,
                    "bbox": bbox,
                    "keywords": keywords or _guess_keywords(layer_name, getattr(ds, "title", "")),
                }
            )
    except Exception as e:
        logger.warning("Dataset ORM path failed for wms-layers; using capabilities fallback: %s", e)

    # Fallback source: GeoServer GetCapabilities.
    if not items:
        items = _fallback_layers_from_capabilities()

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
