from pathlib import Path

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders

register = template.Library()


def _variant_url(url, ext):
    if not url or "://" in url or url.startswith("data:"):
        return ""
    path = Path(url)
    if not path.suffix:
        return ""
    return str(path.with_suffix(f".{ext}")).replace("\\", "/")


def _url_exists(url):
    if not url or "://" in url or url.startswith("data:"):
        return False
    if url.startswith(settings.MEDIA_URL):
        relative = url[len(settings.MEDIA_URL) :].lstrip("/")
        return (settings.MEDIA_ROOT / relative).exists()
    if url.startswith(settings.STATIC_URL):
        relative = url[len(settings.STATIC_URL) :].lstrip("/")
        return finders.find(relative) is not None
    return False


@register.simple_tag
def image_srcset(url):
    items = []
    for ext, width in (("avif", 1600), ("webp", 1200)):
        variant = _variant_url(url, ext)
        if variant and _url_exists(variant):
            items.append(f"{variant} {width}w")
    if url:
        items.append(f"{url} 800w")
    return ", ".join(items)
