from django.db import transaction
from django.utils.text import slugify

from .data import CITIES, SERVICE_SLUGS
from .models import City, CityServicePage, Service
from .text_utils import fix_arabic_text, fix_payload_text


DEFAULT_SERVICE_ALIASES = {
    "shades": "landscaping",
    "fencing": "hardscape",
    "palm-trees": "palm-trees",
    "traditional": "irrigation-maintenance",
}


def clean_slug(value, fallback):
    slug = slugify((value or "").strip())
    return slug or fallback


def service_public_slug(service):
    return DEFAULT_SERVICE_ALIASES.get(service.slug, service.slug)


def build_city_seo(city):
    city_name = fix_arabic_text(city.name)
    highlights = "تصميم الحدائق، اللاندسكيب، التشجير، النخيل، وأنظمة الري"
    return {
        "hero_title": city.hero_title or f"خدمات لاندسكيب وتنسيق حدائق في {city_name}",
        "short_description": city.short_description
        or f"نقدم في {city_name} حلول {highlights} للمنازل والفلل والاستراحات والمشاريع التجارية بجودة تنفيذ عالية.",
        "content": city.content
        or (
            f"نوفر خدمات لاندسكيب متكاملة في {city_name} تشمل دراسة المساحة، اختيار النباتات المناسبة، "
            "تنفيذ الجلسات والممرات، وتركيب أنظمة ري تساعد على تقليل الهدر والمحافظة على جمال الحديقة طوال العام."
        ),
        "meta_title": city.meta_title or f"لاندسكيب وتنسيق حدائق في {city_name} | خدمات حدائق ونخيل",
        "meta_description": city.meta_description
        or f"تنفيذ لاندسكيب وتنسيق حدائق في {city_name}: تصميم، زراعة أشجار ونخيل، ري وصيانة، ومشاريع خارجية بجودة عالية.",
        "meta_keywords": city.meta_keywords
        or f"لاندسكيب {city_name}, تنسيق حدائق {city_name}, تصميم حدائق {city_name}, زراعة نخيل {city_name}",
    }


def build_service_seo(service):
    title = fix_arabic_text(service.title)
    return {
        "short_title": service.short_title or title,
        "meta_title": service.meta_title or f"{title} في السعودية | تنفيذ احترافي",
        "meta_description": service.meta_description
        or f"خدمة {title} للمنازل والفلل والمشاريع التجارية مع تنفيذ منظم وخامات مناسبة لبيئة السعودية.",
        "meta_keywords": service.meta_keywords or f"{title}, لاندسكيب, تنسيق حدائق, السعودية",
    }


def build_city_service_seo(city, service):
    city_name = fix_arabic_text(city.name)
    service_title = fix_arabic_text(service.short_title or service.title)
    benefits = service.benefits_list or [
        "معاينة للموقع وتحديد الاحتياج بدقة",
        "اقتراح مواد ونباتات مناسبة للمدينة",
        "تنفيذ منظم مع متابعة بعد التسليم",
    ]
    return {
        "hero_title": f"{service_title} في {city_name}",
        "custom_slug": service_public_slug(service),
        "content": (
            f"إذا كنت تبحث عن {service_title} في {city_name} فنحن نقدم خدمة متكاملة تبدأ من فهم احتياج الموقع "
            "وتنتهي بتنفيذ عملي يحافظ على الشكل الجمالي وسهولة الصيانة. نراعي طبيعة المناخ، مساحة المشروع، "
            "طريقة الاستخدام اليومية، والميزانية المناسبة قبل اقتراح الحل النهائي.\n\n"
            f"تشمل الخدمة في {city_name} التخطيط، اختيار المواد أو النباتات المناسبة، التنفيذ، وتجهيز توصيات "
            "الصيانة حتى تبقى النتيجة مستقرة ومناسبة للاستخدام السكني أو التجاري."
        ),
        "benefits": "\n".join(benefits),
        "meta_title": f"{service_title} في {city_name} | تنفيذ لاندسكيب احترافي",
        "meta_description": (
            f"خدمة {service_title} في {city_name} للمنازل والفلل والمشاريع: معاينة، تصميم، تنفيذ، "
            "وتوصيات صيانة بجودة عالية وسرعة تواصل."
        ),
        "meta_keywords": f"{service_title} {city_name}, لاندسكيب {city_name}, تنسيق حدائق {city_name}",
    }


@transaction.atomic
def seed_default_cities_and_services():
    created = {"cities": 0, "services": 0}

    for raw_city in fix_payload_text(CITIES):
        defaults = {
            "name": raw_city["name"],
            "region": raw_city.get("region", ""),
            "short_description": raw_city.get("description", ""),
            "content": raw_city.get("description", ""),
            "is_active": True,
            "auto_generate_service_pages": True,
        }
        city, was_created = City.objects.get_or_create(slug=raw_city["slug"], defaults=defaults)
        if was_created:
            seo = build_city_seo(city)
            for field, value in seo.items():
                setattr(city, field, value)
            city.save()
            created["cities"] += 1

    for index, (raw_slug, raw_service) in enumerate(fix_payload_text(SERVICE_SLUGS).items(), start=1):
        slug = DEFAULT_SERVICE_ALIASES.get(raw_slug, raw_slug)
        defaults = {
            "title": raw_service["name"],
            "short_title": raw_service.get("short_name", raw_service["name"]),
            "description": raw_service.get("description", ""),
            "benefits": "\n".join(raw_service.get("benefits", [])),
            "display_order": index,
            "is_visible": True,
        }
        service, was_created = Service.objects.get_or_create(slug=slug, defaults=defaults)
        if was_created:
            seo = build_service_seo(service)
            for field, value in seo.items():
                setattr(service, field, value)
            service.save()
            created["services"] += 1

    return created


@transaction.atomic
def ensure_local_service_pages(overwrite=False):
    created = 0
    updated = 0
    cities = City.objects.filter(is_active=True, auto_generate_service_pages=True)
    services = Service.objects.filter(is_visible=True)

    for city in cities:
        city_seo = build_city_seo(city)
        changed_city = False
        for field, value in city_seo.items():
            if not getattr(city, field):
                setattr(city, field, value)
                changed_city = True
        if changed_city:
            city.save()

        for service in services:
            service.cities.add(city)
            payload = build_city_service_seo(city, service)
            page, was_created = CityServicePage.objects.get_or_create(
                city=city,
                service=service,
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
            if was_created:
                created += 1
            elif overwrite:
                for field, value in payload.items():
                    setattr(page, field, value)
                page.is_active = True
                page.save()
                updated += 1
            else:
                changed = False
                for field, value in payload.items():
                    if not getattr(page, field):
                        setattr(page, field, value)
                        changed = True
                if changed:
                    page.save()
                    updated += 1

    return {"created": created, "updated": updated}
