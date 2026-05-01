from django.db.models.signals import post_save
from django.dispatch import receiver

from .local_seo import build_city_service_seo
from .models import City, CityServicePage, Service


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
    if instance.is_active and instance.auto_generate_service_pages:
        _create_missing_pages_for(city=instance)


@receiver(post_save, sender=Service)
def create_pages_after_service_save(sender, instance, **kwargs):
    if instance.is_visible:
        _create_missing_pages_for(service=instance)
