from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect


class LegacyRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import LegacyRedirect

        path = request.path
        normalized = path.rstrip("/") or "/"
        candidates = {path, normalized, f"{normalized}/"}
        redirect = (
            LegacyRedirect.objects.filter(is_active=True, old_path__in=candidates)
            .order_by("-is_permanent", "-updated_at")
            .first()
        )
        if redirect and redirect.target_path and redirect.target_path != path:
            redirect.hit_count += 1
            redirect.save(update_fields=["hit_count", "updated_at"])
            response_class = HttpResponsePermanentRedirect if redirect.is_permanent else HttpResponseRedirect
            return response_class(redirect.target_path)
        return self.get_response(request)
