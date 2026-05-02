from django.core.cache import cache
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect


class LegacyRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import LegacyRedirect

        path = request.path
        normalized = path.rstrip("/") or "/"
        candidates = {path, normalized, f"{normalized}/"}
        cache_key = f"legacy_redirect:{path}"
        cached_redirect = cache.get(cache_key)

        if cached_redirect is None:
            try:
                redirect = (
                    LegacyRedirect.objects.filter(is_active=True, old_path__in=candidates)
                    .order_by("-is_permanent", "-updated_at")
                    .only("target_path", "is_permanent")
                    .first()
                )
                cached_redirect = (redirect.target_path, redirect.is_permanent) if redirect else False
            except (OperationalError, ProgrammingError):
                cached_redirect = False
            cache.set(cache_key, cached_redirect, 300)

        if cached_redirect:
            target_path, is_permanent = cached_redirect
            if target_path and target_path != path:
                response_class = HttpResponsePermanentRedirect if is_permanent else HttpResponseRedirect
                return response_class(target_path)
        return self.get_response(request)
