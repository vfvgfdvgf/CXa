from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .local_seo import build_city_service_seo
from .models import City, CityServicePage, ContactNumber, LegacyRedirect, NavigationItem, Page, Service, SiteSettings, SiteVerification, Testimonial


def clear_site_cache():
    cache.delete_many(["site:defaults", "site:navigation_items"])


def _create_missing_pages_for(city=None, service=None):
    cities = City.objects.filter(is_active=True, auto_generate_service_pages=True)
    services = Service.objects.filter(is_visible=True)
    if city is not None:
        cities = cities.filter(pk=city.pk)
    if service is not None:
        services = services.filter(pk=service.pk)

    for city_obj in cities:
        for service_obj in services:
            payload = build_city_service_seo(city_obj, service_obj)
            CityServicePage.objects.get_or_create(
                city=city_obj,
                service=service_obj,
                defaults={
                    "hero_title": payload["hero_title"],
                    "content": payload["content"],
                    "benefits": payload["benefits"],
                    "custom_slug": payload["custom_slug"],
                    "meta_title": payload["meta_title"],
                    "meta_description": payload["meta_description"],
                    "meta_keywords": payload["meta_keywords"],
                    "is_active": True,
                },
            )


@receiver(post_save, sender=City)
def create_pages_after_city_save(sender, instance, **kwargs):
    clear_site_cache()
    if instance.is_active and instance.auto_generate_service_pages:
        _create_missing_pages_for(city=instance)


@receiver(post_save, sender=Service)
def create_pages_after_service_save(sender, instance, **kwargs):
    clear_site_cache()
    if instance.is_visible:
        _create_missing_pages_for(service=instance)


@receiver(post_save, sender=SiteSettings)
@receiver(post_save, sender=SiteVerification)
@receiver(post_save, sender=ContactNumber)
@receiver(post_save, sender=NavigationItem)
@receiver(post_save, sender=Page)
@receiver(post_save, sender=Testimonial)
def clear_cached_site_defaults(sender, instance, **kwargs):
    clear_site_cache()


@receiver(post_save, sender=LegacyRedirect)
def clear_cached_legacy_redirect(sender, instance, **kwargs):
    if not instance.old_path:
        return
    normalized = instance.old_path.rstrip("/") or "/"
    cache.delete_many([
        f"legacy_redirect:{instance.old_path}",
        f"legacy_redirect:{normalized}",
        f"legacy_redirect:{normalized}/",
    ])
