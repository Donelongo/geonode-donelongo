from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

EXEMPT_DATA_PATHS = {
    '/data/account/login/',
    '/data/account/logout/',
    '/data/account/signup/',
    '/data/api/o/token/',
}

class RequireLoginForDataMiddleware:
    """(Deprecated) Was used for /data/ prefix variant."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/data/') and path not in EXEMPT_DATA_PATHS:
            if not request.user.is_authenticated:
                login_url = reverse('account_login') if 'account_login' in settings.ROOT_URLCONF else '/data/account/login/'
                return redirect(f"{login_url}?next={path}")
        return self.get_response(request)


PUBLIC_REACT_PATHS = {
    '/', '/advisory', '/disease', '/suitability-map', '/risk-map', '/about', '/contact', '/terms-and-conditions'
}

CORE_GEONODE_PREFIXES = [
    '/layers', '/maps', '/documents', '/datasets', '/catalogue', '/people', '/groups', '/services', '/geoapps', '/admin'
]

class RequireLoginForProtectedGeoNode:
    """Protect core GeoNode functional areas while leaving React portal pages public.
    If anonymous and requesting a path that starts with a GeoNode core prefix, redirect to login with next=.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip('/') or '/'
        if path not in PUBLIC_REACT_PATHS and any(path.startswith(p) for p in CORE_GEONODE_PREFIXES):
            if not request.user.is_authenticated:
                return redirect(f"/account/login/?next={request.path}")
        return self.get_response(request)
