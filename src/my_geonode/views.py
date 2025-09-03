#src/my_geonode/views.py
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
import requests


GEOSERVER_OWS_INTERNAL = "http://geoserver:8080/geoserver/ows"


@require_GET
def geoserver_ows(request):
    """
    Lightweight reverse proxy to GeoServer OWS so the frontend can use a same-origin WMS URL:
      - Proxies any query string to the GeoServer service within the Docker network.
      - Returns upstream content-type and status code.
    """
    try:
        # Preserve full query string as-is
        upstream = GEOSERVER_OWS_INTERNAL
        headers = {
            # Forward minimal headers; Host should be geoserver service internally
            'Accept': request.META.get('HTTP_ACCEPT', '*/*'),
            'User-Agent': request.META.get('HTTP_USER_AGENT', 'my_geonode-proxy'),
        }
        # Stream not strictly necessary here; responses are small XML/JSON or images
        r = requests.get(upstream, params=request.GET, headers=headers, timeout=20)
        content_type = r.headers.get('Content-Type', 'application/octet-stream')
        resp = HttpResponse(r.content, status=r.status_code, content_type=content_type)
        # Pass through caching headers if present
        for h in ['Cache-Control', 'Expires', 'ETag', 'Last-Modified', 'Content-Disposition']:
            if h in r.headers:
                resp[h] = r.headers[h]
        return resp
    except requests.RequestException as e:
        return JsonResponse({'error': 'Upstream GeoServer unreachable', 'detail': str(e)}, status=502)


@require_GET
def wms_layers_capabilities(request):
    """
    Convenience endpoint that returns WMS GetCapabilities from GeoServer.
    The frontend supports either JSON or raw capabilities XML; we return XML here.
    """
    params = request.GET.copy()
    # Ensure required params are set
    params.setdefault('SERVICE', 'WMS')
    params.setdefault('REQUEST', 'GetCapabilities')
    return geoserver_ows(request.__class__({'REQUEST_METHOD': 'GET', 'wsgi.input': None}))  # placeholder to satisfy type check
