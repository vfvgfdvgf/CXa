from pathlib import Path
from datetime import timezone as datetime_timezone

from django.conf import settings
from django.db import models
from django.core.cache import cache
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import reverse
from django.db.utils import OperationalError, ProgrammingError
from django.utils.encoding import iri_to_uri
from django.utils import timezone
from xml.sax.saxutils import escape

from .data import (
    BLOG_POSTS,
    CITIES,
    PHONE_NUMBER,
    PORTFOLIO_ITEMS,
    SERVICE_SLUGS,
    SITE_NAME,
    TESTIMONIALS,
    build_quote_message,
    get_city,
    get_post,
    get_service,
)
from .context_processors import build_theme_css
from .forms import BlogCommentForm
from .models import ConversionEvent, Lead, LibraryImage, PageMedia, SiteSettings
from .models import BlogCategory, BlogComment, BlogPost, BlogTag, City as CityModel, CityServicePage, Page, Project, Service as ServiceModel, Testimonial
from .text_utils import fix_arabic_text, fix_payload_text


UI_TEXT = {
    "ar": {
        "home": "الرئيسية",
        "about": "من نحن",
        "services": "الخدمات",
        "projects": "المشاريع",
        "cities": "المدن",
        "blog": "المدونة",
        "contact": "اتصل بنا",
        "quote": "اطلب عرض سعر",
        "call_now": "اتصل الآن",
        "whatsapp": "واتساب",
        "hero_badge": "لاندسكيب وتنسيق حدائق في جميع مدن السعودية",
    },
}

STATIC_IMAGE_FILES = tuple(sorted(path.name for path in (settings.BASE_DIR / "imge").glob("*") if path.is_file()))

IMAGE_METADATA = {
    "WhatsApp Image 2026-03-21 at 6.34.14 PM (1).jpeg": {"category": "traditional", "title": "سقف مجلس تراثي بخوص وجذوع", "alt": "سقف مجلس تراثي سعودي"},
    "WhatsApp Image 2026-03-21 at 6.34.14 PM (2).jpeg": {"category": "traditional", "title": "قاعة تراثية سعودية بتفاصيل داخلية", "alt": "قاعة مجلس تراثي"},
    "WhatsApp Image 2026-03-21 at 6.34.14 PM.jpeg": {"category": "shades", "title": "تنفيذ هيكل مظلة خارجية", "alt": "تركيب هيكل مظلة"},
    "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg": {"category": "palm", "title": "توريد وزراعة نخيل للمزارع", "alt": "صف نخيل مزروع حديثا"},
    "WhatsApp Image 2026-03-21 at 6.39.47 PM.jpeg": {"category": "shades", "title": "مظلة سيارات خارجية", "alt": "مظلة سيارات أمام منزل"},
    "WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg": {"category": "traditional", "title": "واجهة مبنى تراثي سعودي", "alt": "بناء تراثي سعودي"},
    "WhatsApp Image 2026-03-21 at 6.39.49 PM.jpeg": {"category": "fencing", "title": "بوابة شبوك للمزارع", "alt": "بوابة شبوك مجلفنة"},
    "WhatsApp Image 2026-03-21 at 6.39.54 PM.jpeg": {"category": "fencing", "title": "بوابة شبوك بساتر خصوصية", "alt": "بوابة سياج بساتر"},
    "WhatsApp Image 2026-03-21 at 6.39.55 PM.jpeg": {"category": "fencing", "title": "شبوك حماية بساتر جانبي", "alt": "سياج بساتر جانبي"},
    "WhatsApp Image 2026-03-21 at 6.39.56 PM (1).jpeg": {"category": "traditional", "title": "مبنى تراثي بطابع نجدي", "alt": "واجهة مبنى تراثي نجدي"},
    "WhatsApp Image 2026-03-21 at 6.39.56 PM.jpeg": {"category": "fencing", "title": "شبوك أراض صحراوية", "alt": "شبوك للأراضي في الصحراء"},
    "WhatsApp Image 2026-03-21 at 6.39.57 PM.jpeg": {"category": "fencing", "title": "سياج حماية بساتر ممتد", "alt": "سياج بساتر طويل"},
    "WhatsApp Image 2026-03-21 at 6.40.01 PM.jpeg": {"category": "shades", "title": "تركيب مظلة جلسات وسيارات", "alt": "تركيب مظلة خارجية"},
    "WhatsApp Image 2026-03-21 at 6.40.02 PM (1).jpeg": {"category": "traditional", "title": "مجلس تراثي خارجي", "alt": "مجلس تراثي من الخارج"},
    "WhatsApp Image 2026-03-21 at 6.40.02 PM (2).jpeg": {"category": "traditional", "title": "نوافذ وأبواب تراثية داخلية", "alt": "تفاصيل نوافذ تراثية"},
    "WhatsApp Image 2026-03-21 at 6.40.02 PM.jpeg": {"category": "traditional", "title": "سور حجري تراثي", "alt": "سور حجري بطابع تراثي"},
    "WhatsApp Image 2026-03-21 at 6.40.03 PM (1).jpeg": {"category": "shades", "title": "مظلة سيارات جاهزة", "alt": "مظلة سيارات بعد التنفيذ"},
    "WhatsApp Image 2026-03-21 at 6.40.03 PM.jpeg": {"category": "traditional", "title": "مجلس سعودي تراثي من الداخل", "alt": "ديكور مجلس تراثي سعودي"},
    "WhatsApp Image 2026-03-21 at 6.40.04 PM (1).jpeg": {"category": "shades", "title": "تفاصيل مظلة سيارات من الداخل", "alt": "تفاصيل سقف مظلة سيارات"},
    "WhatsApp Image 2026-03-21 at 6.40.04 PM (2).jpeg": {"category": "shades", "title": "تنفيذ مظلة سيارات كبيرة", "alt": "تركيب مظلة سيارات كبيرة"},
    "WhatsApp Image 2026-03-21 at 6.40.04 PM.jpeg": {"category": "shades", "title": "مظلة سيارات قماشية جاهزة", "alt": "مظلة سيارات قماشية"},
    "WhatsApp Image 2026-03-21 at 6.40.05 PM (1).jpeg": {"category": "traditional", "title": "سقف تراثي بجذوع طبيعية", "alt": "تشطيب سقف تراثي"},
    "WhatsApp Image 2026-03-21 at 6.40.05 PM.jpeg": {"category": "traditional", "title": "تشطيب سقف مجلس تراثي", "alt": "تفاصيل سقف مجلس سعودي"},
    "WhatsApp Image 2026-03-21 at 6.40.06 PM (1).jpeg": {"category": "fencing", "title": "بوابة شبوك مجلفنة", "alt": "بوابة سياج مجلفن"},
    "WhatsApp Image 2026-03-21 at 6.40.06 PM (2).jpeg": {"category": "fencing", "title": "شبوك مجلفنة للأراضي", "alt": "شبوك مجلفنة خارجية"},
    "WhatsApp Image 2026-03-21 at 6.40.06 PM.jpeg": {"category": "fencing", "title": "سياج حماية بساتر صلب", "alt": "سياج بساتر صلب"},
    "WhatsApp Image 2026-03-21 at 6.40.07 PM (1).jpeg": {"category": "fencing", "title": "شبوك خارجية ممتدة", "alt": "شبوك طويلة للأراضي"},
    "WhatsApp Image 2026-03-21 at 6.40.07 PM (2).jpeg": {"category": "traditional", "title": "مظلة تراثية بسقف طبيعي", "alt": "سقف تراثي بجذوع وخوص"},
    "WhatsApp Image 2026-03-21 at 6.40.07 PM (3).jpeg": {"category": "fencing", "title": "تركيب شبوك بساتر", "alt": "تنفيذ سياج بساتر"},
    "WhatsApp Image 2026-03-21 at 6.40.07 PM.jpeg": {"category": "fencing", "title": "شبوك مجلفنة بعزل", "alt": "سياج مجلفن طويل"},
    "WhatsApp Image 2026-03-21 at 6.40.08 PM (1).jpeg": {"category": "fencing", "title": "شبوك خضراء بساتر", "alt": "شبوك بساتر أخضر"},
    "WhatsApp Image 2026-03-21 at 6.40.08 PM.jpeg": {"category": "fencing", "title": "سياج بساتر للمزارع", "alt": "شبوك بساتر للمزارع"},
    "WhatsApp Image 2026-03-21 at 6.40.09 PM (1).jpeg": {"category": "fencing", "title": "شبوك حماية طويلة", "alt": "شبوك حماية على امتداد طويل"},
    "WhatsApp Image 2026-03-21 at 6.40.09 PM (2).jpeg": {"category": "fencing", "title": "شبوك بساتر للخصوصية", "alt": "سياج بساتر للخصوصية"},
    "WhatsApp Image 2026-03-21 at 6.40.09 PM (3).jpeg": {"category": "fencing", "title": "شبوك جانبية للأراضي", "alt": "شبوك جانبية للأراضي"},
    "WhatsApp Image 2026-03-21 at 6.40.09 PM (4).jpeg": {"category": "fencing", "title": "شبوك بساتر ممتدة", "alt": "شبوك بساتر ممتدة"},
    "WhatsApp Image 2026-03-21 at 6.40.09 PM.jpeg": {"category": "fencing", "title": "سياج بساتر طويل", "alt": "سياج طويل بساتر"},
    "WhatsApp Image 2026-03-21 at 6.40.10 PM (1).jpeg": {"category": "fencing", "title": "أعمدة شبوك تحت التنفيذ", "alt": "تركيب أعمدة سياج"},
    "WhatsApp Image 2026-03-21 at 6.40.10 PM (2).jpeg": {"category": "fencing", "title": "شبوك مجلفنة جاهزة", "alt": "شبوك مجلفنة جاهزة"},
    "WhatsApp Image 2026-03-21 at 6.40.10 PM.jpeg": {"category": "fencing", "title": "شبوك بساتر خارجية", "alt": "سياج بساتر خارجي"},
    "WhatsApp Image 2026-03-21 at 6.40.11 PM (1).jpeg": {"category": "fencing", "title": "سياج شبوك طويل", "alt": "سياج شبوك طويل"},
    "WhatsApp Image 2026-03-21 at 6.40.11 PM.jpeg": {"category": "fencing", "title": "شبوك حماية للأراضي", "alt": "شبوك حماية مجلفنة"},
}

IMAGE_GROUPS = {
    "home_hero": ["WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.47 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg"],
    "home_gallery": ["WhatsApp Image 2026-03-21 at 6.40.03 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.40.06 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.34.14 PM (2).jpeg", "WhatsApp Image 2026-03-21 at 6.40.08 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.40.02 PM (2).jpeg", "WhatsApp Image 2026-03-21 at 6.40.04 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.56 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.14 PM (1).jpeg"],
    "home_banners": ["WhatsApp Image 2026-03-21 at 6.40.01 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.09 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.02 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg"],
    "about": ["WhatsApp Image 2026-03-21 at 6.34.14 PM (2).jpeg", "WhatsApp Image 2026-03-21 at 6.40.02 PM (2).jpeg", "WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.14 PM (1).jpeg"],
    "services": ["WhatsApp Image 2026-03-21 at 6.39.47 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.56 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.03 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.40.08 PM (1).jpeg"],
    "portfolio": ["WhatsApp Image 2026-03-21 at 6.40.01 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.04 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.02 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.40.06 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg"],
    "cities": ["WhatsApp Image 2026-03-21 at 6.40.03 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.40.06 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.09 PM.jpeg"],
    "blog": ["WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.03 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.39.56 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg"],
    "blog_post": ["WhatsApp Image 2026-03-21 at 6.40.02 PM (2).jpeg", "WhatsApp Image 2026-03-21 at 6.40.04 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.06 PM (1).jpeg"],
    "contact": ["WhatsApp Image 2026-03-21 at 6.39.47 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.40.02 PM (1).jpeg"],
    "city": ["WhatsApp Image 2026-03-21 at 6.40.03 PM (1).jpeg", "WhatsApp Image 2026-03-21 at 6.39.56 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.39.48 PM.jpeg", "WhatsApp Image 2026-03-21 at 6.34.15 PM.jpeg"],
}

SERVICE_CATEGORY_MAP = {"shades": "shades", "fencing": "fencing", "palm-trees": "palm", "traditional": "traditional"}


def detect_language(request):
    return "ar"


def safe_static(path):
    try:
        return iri_to_uri(static(path))
    except Exception:
        return iri_to_uri(f"/static/{str(path).lstrip('/')}")


def build_seo(title, description, request, image="", keywords=""):
    return {
        "title": title,
        "description": description,
        "canonical": request.build_absolute_uri(request.path),
        "image": request.build_absolute_uri(image) if image and image.startswith("/") else image,
        "keywords": keywords,
    }


def get_service_highlights(settings_obj):
    if settings_obj and settings_obj.service_highlights_list:
        return [fix_arabic_text(item) for item in settings_obj.service_highlights_list]
    return ["لاندسكيب", "تصميم حدائق", "أشجار ونخيل", "شبوك", "مظلات"]


def highlights_phrase(settings_obj, limit=4):
    return "، ".join(get_service_highlights(settings_obj)[:limit])


def build_base_context(request):
    language = detect_language(request)
    settings_obj = None
    try:
        settings_obj = SiteSettings.load()
    except (OperationalError, ProgrammingError):
        settings_obj = None

    return fix_payload_text({
        "lang_code": language,
        "is_rtl": language != "en",
        "ui": UI_TEXT[language],
        "services_map": SERVICE_SLUGS,
        "cities_data": CITIES,
        "settings_obj": settings_obj,
        "theme_css_vars": build_theme_css(settings_obj=settings_obj),
    })


def render_clean(request, template_name, context, **kwargs):
    return render(request, template_name, fix_payload_text(context), **kwargs)


def build_library_image(filename, title="", alt=""):
    return {
        "filename": filename,
        "image_url": safe_static(filename),
        "title": fix_arabic_text(title or "صورة من أعمالنا"),
        "display_alt": fix_arabic_text(alt or title or "صورة من أعمال الشركة"),
    }


def get_library_images(start=0, count=None):
    files = STATIC_IMAGE_FILES[start:] if count is None else STATIC_IMAGE_FILES[start : start + count]
    return [
        build_library_image(
            filename,
            title=f"صورة مشروع {index + 1}",
            alt=f"صورة مشروع {index + 1}",
        )
        for index, filename in enumerate(files, start=start)
    ]


def get_page_image_block(page_slug):
    page_slices = {
        "home_hero": (0, 3),
        "home_gallery": (3, 8),
        "home_banners": (11, 4),
        "about": (15, 4),
        "services": (19, 6),
        "portfolio": (25, 6),
        "cities": (31, 5),
        "blog": (36, 4),
        "blog_post": (8, 3),
        "contact": (39, 3),
        "city": (5, 4),
        "city_service": (9, 4),
    }
    start, count = page_slices.get(page_slug, (0, 4))
    return get_library_images(start, count)


def with_fallback_media(items, fallback_items):
    return items or fallback_items


def serialize_library_item(item):
    if isinstance(item, dict):
        return {
            "filename": item.get("source_name", ""),
            "image_url": item.get("image_url", ""),
            "title": fix_arabic_text(item.get("title", "")),
            "display_alt": fix_arabic_text(item.get("display_alt") or item.get("alt_text", "") or item.get("title", "")),
            "category": item.get("category", "general"),
        }
    return {
        "filename": item.source_name,
        "image_url": item.image_url,
        "title": fix_arabic_text(item.title),
        "display_alt": fix_arabic_text(item.display_alt),
        "category": item.category,
    }


def default_usage_group_for(filename):
    for usage_group, filenames in IMAGE_GROUPS.items():
        if filename in filenames:
            return usage_group
    return "home_gallery"


def default_category_for(filename):
    metadata = IMAGE_METADATA.get(filename, {})
    return metadata.get("category", "general")


def default_title_for(filename):
    return "صورة من مشاريع اللاندسكيب"


def default_alt_for(filename):
    return "صورة تنسيق حدائق ولاندسكيب"


def get_library_records():
    cached_records = cache.get("library:records")
    if cached_records is not None:
        return cached_records

    try:
        existing = set(LibraryImage.objects.values_list("source_name", flat=True))
        missing = []
        for filename in STATIC_IMAGE_FILES:
            if filename not in existing:
                missing.append(
                    LibraryImage(
                        source_name=filename,
                        title=default_title_for(filename),
                        alt_text=default_alt_for(filename),
                        category=default_category_for(filename),
                        usage_group=default_usage_group_for(filename),
                        sort_order=0,
                        is_active=True,
                    )
                )
        if missing:
            LibraryImage.objects.bulk_create(missing)
        records = []
        for item in (
            LibraryImage.objects.filter(is_active=True)
            .defer("image_data")
            .only(
                "id",
                "source_name",
                "title",
                "alt_text",
                "category",
                "usage_group",
                "image",
                "image_stored",
                "image_filename",
                "external_url",
                "sort_order",
            )
        ):
            records.append(
                {
                    "id": item.pk,
                    "source_name": item.source_name,
                    "title": item.title,
                    "alt_text": item.alt_text,
                    "display_alt": item.display_alt,
                    "category": item.category,
                    "usage_group": item.usage_group,
                    "sort_order": item.sort_order,
                    "image_url": item.image_url,
                }
            )
        cache.set("library:records", records, 300)
        return records
    except (OperationalError, ProgrammingError):
        return []


def assign_service_fallback_images(services):
    fallback_images = get_library_images(0, max(len(services), 4))
    output = []
    for index, service in enumerate(services):
        updated = dict(service)
        if not updated.get("image") and index < len(fallback_images):
            updated["image"] = fallback_images[index]["image_url"]
        output.append(updated)
    return output


def assign_project_fallback_images(projects):
    fallback_images = get_library_images(11, max(len(projects), 6))
    output = []
    for index, project in enumerate(projects):
        updated = dict(project)
        if not updated.get("image_url") and index < len(fallback_images):
            updated["image_url"] = fallback_images[index]["image_url"]
        output.append(updated)
    return output


def build_library_image(filename, title="", alt=""):
    records = get_library_records()
    matched = next((item for item in records if item.get("source_name") == filename), None)
    if matched:
        return serialize_library_item(matched)
    return {
        "filename": filename,
        "image_url": safe_static(filename),
        "title": fix_arabic_text(title or "صورة من مشاريع اللاندسكيب"),
        "display_alt": fix_arabic_text(alt or title or "صورة تنسيق حدائق ولاندسكيب"),
        "category": default_category_for(filename),
    }


def get_page_image_block(page_slug):
    records = [serialize_library_item(item) for item in get_library_records() if item.get("usage_group") == page_slug]
    if records:
        return records
    filenames = IMAGE_GROUPS.get(page_slug)
    if filenames:
        return [build_library_image(filename) for filename in filenames]
    return get_library_images(0, 4)


def get_images_by_category(category, limit=4):
    records = [serialize_library_item(item) for item in get_library_records() if item.get("category") == category]
    if records:
        return records[:limit]
    matches = [filename for filename in STATIC_IMAGE_FILES if IMAGE_METADATA.get(filename, {}).get("category") == category]
    return [build_library_image(filename) for filename in matches[:limit]]


def resolve_service_category(service_slug):
    return SERVICE_CATEGORY_MAP.get(service_slug, "shades")


def assign_service_fallback_images(services):
    output = []
    for service in services:
        updated = dict(service)
        service_category = resolve_service_category(updated.get("slug", "shades"))
        fallback_images = get_images_by_category(service_category, 3)
        if not updated.get("image") and fallback_images:
            updated["image"] = fallback_images[0]["image_url"]
        output.append(updated)
    return output


def assign_project_fallback_images(projects):
    fallback_images = get_page_image_block("portfolio")
    output = []
    for index, project in enumerate(projects):
        updated = dict(project)
        if not updated.get("image_url") and index < len(fallback_images):
            updated["image_url"] = fallback_images[index]["image_url"]
        output.append(updated)
    return output


def service_cards():
    try:
        services = list(ServiceModel.objects.filter(is_visible=True).prefetch_related("cities"))
        if services:
            return assign_service_fallback_images([
                {
                    "slug": service.slug,
                    "name": fix_arabic_text(service.title),
                    "short_name": fix_arabic_text(service.short_title or service.title),
                    "description": fix_arabic_text(service.description),
                    "benefits": [fix_arabic_text(item) for item in service.benefits_list],
                    "image": service.resolved_image,
                }
                for service in services
            ])
    except (OperationalError, ProgrammingError):
        pass
    return assign_service_fallback_images([{"slug": slug, **service} for slug, service in SERVICE_SLUGS.items()])


def get_page_media(page, section=None):
    try:
        queryset = PageMedia.objects.filter(page=page, is_active=True)
        if section:
            queryset = queryset.filter(section=section)
        return list(queryset)
    except (OperationalError, ProgrammingError):
        return []


def get_managed_page(page_slug=None, template_key=None):
    try:
        queryset = Page.objects.filter(is_visible=True)
        if page_slug:
            return queryset.filter(models.Q(custom_url=page_slug) | models.Q(slug=page_slug)).first()
        if template_key:
            return queryset.filter(template_key=template_key).first()
    except Exception:
        return None
    return None


def get_cities_data():
    try:
        cities = list(CityModel.objects.filter(is_active=True))
        if cities:
            return [
                {
                    "slug": city.slug,
                    "name": fix_arabic_text(city.name),
                    "region": fix_arabic_text(city.region),
                    "description": fix_arabic_text(city.short_description or city.content),
                    "content": fix_arabic_text(city.content),
                    "hero_title": fix_arabic_text(city.hero_title),
                }
                for city in cities
            ]
    except (OperationalError, ProgrammingError):
        pass
    return CITIES


def get_projects_data():
    try:
        projects = list(Project.objects.filter(is_visible=True).select_related("city"))
        if projects:
            return assign_project_fallback_images([
                {
                    "title": fix_arabic_text(project.title),
                    "category": fix_arabic_text(project.get_category_display()),
                    "image_url": project.image_url,
                    "description": fix_arabic_text(project.description),
                }
                for project in projects
            ])
    except (OperationalError, ProgrammingError):
        pass
    return assign_project_fallback_images([
        {
            "title": item["title"],
            "category": item["category"],
            "image_url": f"/static/{item['image']}",
            "description": item.get("description", ""),
        }
        for item in PORTFOLIO_ITEMS
    ])


def get_testimonials_data():
    try:
        items = list(Testimonial.objects.filter(is_visible=True))
        if items:
            return [
                {
                    "name": fix_arabic_text(f"{item.name} - {item.city_name}".strip(" -")),
                    "quote": fix_arabic_text(item.review),
                    "rating": item.rating,
                }
                for item in items
            ]
    except (OperationalError, ProgrammingError):
        pass
    return TESTIMONIALS


def get_posts_data():
    try:
        posts = list(
            BlogPost.objects.filter(status="published")
            .filter(models.Q(publish_at__lte=timezone.now()) | models.Q(publish_at__isnull=True))
            .select_related("category")
            .prefetch_related("tags")
        )
        if posts:
            return posts
    except (OperationalError, ProgrammingError):
        pass
    return BLOG_POSTS


def get_blog_sidebar_data():
    cache_key = "blog-sidebar-data"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        categories = list(BlogCategory.objects.all())
        tags = list(BlogTag.objects.all()[:20])
        popular_posts = list(BlogPost.objects.filter(status="published").order_by("-view_count", "-publish_at")[:5])
    except (OperationalError, ProgrammingError):
        categories, tags, popular_posts = [], [], []

    payload = {"categories": categories, "tags": tags, "popular_posts": popular_posts}
    cache.set(cache_key, payload, 300)
    return payload


def home(request):
    context = build_base_context(request)
    settings_obj = context.get("settings_obj")
    site_name = fix_arabic_text(settings_obj.site_name) if settings_obj else SITE_NAME
    highlights_text = highlights_phrase(settings_obj)
    managed_page = get_managed_page(template_key="home")
    context.update(
        {
            "seo": build_seo(
                f"{site_name} | {(settings_obj.homepage_meta_title if settings_obj else 'لاندسكيب وتنسيق حدائق في السعودية')}",
                settings_obj.homepage_meta_description if settings_obj else f"شركة سعودية متخصصة في {highlights_text} مع تنفيذ احترافي في جميع المدن.",
                request,
                image=settings_obj.default_og_image_resolved if settings_obj else "",
                keywords=settings_obj.seo_default_keywords if settings_obj else "",
            ),
            "hero_title": fix_arabic_text(managed_page.hero_title) if managed_page and managed_page.hero_title else "حلول لاندسكيب متكاملة تعزز جمال المساحات الخارجية",
            "hero_text": fix_arabic_text(managed_page.intro_text) if managed_page and managed_page.intro_text else "نصمم وننفذ الحدائق ونوفر حلولًا متكاملة بجودة عالية وسرعة استجابة.",
            "hero_background": settings_obj.homepage_hero_background_resolved if settings_obj else "",
            "services": service_cards(),
            "portfolio_items": get_projects_data(),
            "testimonials": get_testimonials_data(),
            "featured_cities": get_cities_data()[:8],
            "hero_media": with_fallback_media(get_page_media("home", "hero"), get_page_image_block("home_hero")),
            "home_gallery": with_fallback_media(get_page_media("home", "gallery"), get_page_image_block("home_gallery")),
            "home_banners": get_page_image_block("home_banners"),
            "latest_posts": get_posts_data()[:3],
            "stats": [
                {"value": "+12", "label": "مدينة رئيسية نخدمها يوميًا"},
                {"value": "+250", "label": "مشروعًا بين سكني وتجاري وزراعي"},
                {"value": "24/7", "label": "سرعة رد على الاتصالات والواتساب"},
            ],
        }
    )
    return render_clean(request, "pages/home.html", context)


def managed_page(request, page_slug):
    page = get_managed_page(page_slug=page_slug)
    if not page:
        raise Http404("Page not found")
    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                page.meta_title or f"{page.title} | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                page.meta_description or page.intro_text,
                request,
            ),
            "page_obj": page,
            "page_images": with_fallback_media(
                get_page_media(page.template_key if page.template_key != "custom" else "home"),
                get_page_image_block(page.template_key if page.template_key != "custom" else "about"),
            ),
        }
    )
    return render_clean(request, "pages/managed_page.html", context)


def about(request):
    context = build_base_context(request)
    context["seo"] = build_seo(
        f"من نحن | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
        "تعرف على خبرة شركتنا السعودية في تصميم الحدائق وتنفيذ اللاندسكيب وزراعة الأشجار والنخيل.",
        request,
    )
    context["page_images"] = with_fallback_media(get_page_media("about"), get_page_image_block("about"))
    return render_clean(request, "pages/about.html", context)


def services(request):
    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                f"خدماتنا | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                "استعرض خدمات تصميم الحدائق وتنفيذ اللاندسكيب وزراعة الأشجار والنخيل وأنظمة الري في السعودية.",
                request,
            ),
            "services": service_cards(),
            "page_images": with_fallback_media(get_page_media("services"), get_page_image_block("services")),
        }
    )
    return render_clean(request, "pages/services.html", context)


def service_detail(request, service_slug):
    context = build_base_context(request)
    service_obj = None
    try:
        service_obj = ServiceModel.objects.filter(slug=service_slug, is_visible=True).first()
    except (OperationalError, ProgrammingError):
        service_obj = None

    if service_obj:
        service = {
            "slug": service_obj.slug,
            "name": fix_arabic_text(service_obj.title),
            "short_name": fix_arabic_text(service_obj.short_title or service_obj.title),
            "keyword": fix_arabic_text(service_obj.short_title or service_obj.title),
            "description": fix_arabic_text(service_obj.description),
            "benefits": [fix_arabic_text(item) for item in service_obj.benefits_list],
            "image": service_obj.resolved_image,
            "meta_title": fix_arabic_text(service_obj.meta_title),
            "meta_description": fix_arabic_text(service_obj.meta_description),
            "meta_keywords": fix_arabic_text(service_obj.meta_keywords),
        }
        updated_at = service_obj.updated_at
    else:
        raw_service = SERVICE_SLUGS.get(service_slug)
        if not raw_service:
            raise Http404("Service not found")
        service = {
            "slug": service_slug,
            "name": fix_arabic_text(raw_service["name"]),
            "short_name": fix_arabic_text(raw_service.get("short_name", raw_service["name"])),
            "keyword": fix_arabic_text(raw_service.get("keyword", raw_service["name"])),
            "description": fix_arabic_text(raw_service.get("description", "")),
            "benefits": [fix_arabic_text(item) for item in raw_service.get("benefits", [])],
            "image": "",
            "meta_title": "",
            "meta_description": "",
            "meta_keywords": "",
        }
        updated_at = timezone.now()

    cities_data = get_cities_data()
    city_links = []
    for city in cities_data:
        try:
            url = reverse("city_service_detail", kwargs={"city_slug": city["slug"], "service_slug": service["slug"]})
        except Exception:
            url = reverse("city_detail", kwargs={"city_slug": city["slug"]})
        city_links.append({"name": city["name"], "url": url})

    service_text = f"{service['name']} في السعودية"
    context.update(
        {
            "seo": build_seo(
                service["meta_title"] or f"{service_text} | توريد وتنفيذ احترافي",
                service["meta_description"]
                or f"خدمة {service_text} للرياض وجميع مدن السعودية مع معاينة، توريد، تنفيذ، ري، وصيانة حسب احتياج الموقع.",
                request,
                image=service.get("image", ""),
                keywords=service["meta_keywords"]
                or f"{service['name']}, توريد نخيل, تكريب نخيل, تشذيب نخيل, لاندسكيب, تنسيق حدائق, شبوك, مظلات",
            ),
            "service": service,
            "cities": city_links,
            "page_images": with_fallback_media(get_page_media("services"), get_images_by_category(resolve_service_category(service["slug"]), 6)),
            "updated_at": updated_at,
        }
    )
    return render_clean(request, "pages/service_detail.html", context)


def portfolio(request):
    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                f"المشاريع والأعمال | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                "معرض أعمال لمشاريع اللاندسكيب وتنسيق الحدائق والتشجير المنفذة في مختلف مدن السعودية.",
                request,
            ),
            "portfolio_items": get_projects_data(),
            "page_images": with_fallback_media(get_page_media("portfolio"), get_page_image_block("portfolio")),
        }
    )
    return render_clean(request, "pages/portfolio.html", context)


def cities(request):
    context = build_base_context(request)
    city_data = get_cities_data()
    context["seo"] = build_seo(
        f"المدن التي نخدمها | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
        "تغطية شاملة لجميع مدن السعودية مع صفحات مخصصة للرياض وجدة والدمام ومكة والمدينة والقصيم وأبها وتبوك وحائل وجازان.",
        request,
    )
    context["page_images"] = with_fallback_media(get_page_media("cities"), get_page_image_block("cities"))
    context["cities_data"] = city_data
    return render_clean(request, "pages/cities.html", context)


def blog_index(request):
    context = build_base_context(request)
    settings_obj = context.get("settings_obj")
    posts = get_posts_data()
    query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()

    if query:
        if posts and hasattr(posts[0], "title"):
            posts = [post for post in posts if query.lower() in post.title.lower() or query.lower() in post.content.lower()]
        else:
            posts = [post for post in posts if query.lower() in post["title"].lower()]

    if category_filter:
        if posts and hasattr(posts[0], "category_id"):
            posts = [post for post in posts if post.category and post.category.slug == category_filter]

    featured_posts = [post for post in posts if hasattr(post, "is_featured") and post.is_featured][:3]
    sidebar = get_blog_sidebar_data()
    context.update(
        {
            "seo": build_seo(
                f"مدونة الأعمال والخدمات | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                "مقالات SEO عربية عن تصميم الحدائق وتكلفة اللاندسكيب وأنواع الأشجار والنخيل وأنظمة الري في السعودية.",
                request,
            ),
            "posts": posts,
            "featured_posts": featured_posts,
            "search_query": query,
            "active_category": category_filter,
            "categories": sidebar["categories"],
            "tags_cloud": sidebar["tags"],
            "popular_posts": sidebar["popular_posts"],
            "blog_hero_background": settings_obj.blog_hero_background_resolved if settings_obj else "",
            "page_images": with_fallback_media(get_page_media("blog"), get_page_image_block("blog")),
        }
    )
    return render_clean(request, "blog/index.html", context)


def blog_category(request, category_slug):
    category = BlogCategory.objects.filter(slug=category_slug).first()
    if not category:
        raise Http404("Category not found")
    posts = list(
        BlogPost.objects.filter(status="published", category=category)
        .filter(models.Q(publish_at__lte=timezone.now()) | models.Q(publish_at__isnull=True))
        .select_related("category")
        .prefetch_related("tags")
    )
    context = build_base_context(request)
    settings_obj = context.get("settings_obj")
    sidebar = get_blog_sidebar_data()
    context.update(
        {
            "seo": build_seo(
                category.meta_title or f"مقالات {category.name} | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                category.meta_description or category.description,
                request,
            ),
            "posts": posts,
            "featured_posts": [],
            "search_query": "",
            "active_category": category.slug,
            "current_taxonomy_title": f"تصنيف: {category.name}",
            "categories": sidebar["categories"],
            "tags_cloud": sidebar["tags"],
            "popular_posts": sidebar["popular_posts"],
            "blog_hero_background": settings_obj.blog_hero_background_resolved if settings_obj else "",
            "page_images": with_fallback_media(get_page_media("blog"), get_page_image_block("blog")),
        }
    )
    return render_clean(request, "blog/index.html", context)


def blog_tag(request, tag_slug):
    tag = BlogTag.objects.filter(slug=tag_slug).first()
    if not tag:
        raise Http404("Tag not found")
    posts = list(
        BlogPost.objects.filter(status="published", tags=tag)
        .filter(models.Q(publish_at__lte=timezone.now()) | models.Q(publish_at__isnull=True))
        .select_related("category")
        .prefetch_related("tags")
        .distinct()
    )
    context = build_base_context(request)
    settings_obj = context.get("settings_obj")
    sidebar = get_blog_sidebar_data()
    context.update(
        {
            "seo": build_seo(
                tag.meta_title or f"وسم: {tag.name} | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                tag.meta_description or f"مقالات مرتبطة بوسم {tag.name}",
                request,
            ),
            "posts": posts,
            "featured_posts": [],
            "search_query": "",
            "active_category": "",
            "current_taxonomy_title": f"وسم: {tag.name}",
            "categories": sidebar["categories"],
            "tags_cloud": sidebar["tags"],
            "popular_posts": sidebar["popular_posts"],
            "blog_hero_background": settings_obj.blog_hero_background_resolved if settings_obj else "",
            "page_images": with_fallback_media(get_page_media("blog"), get_page_image_block("blog")),
        }
    )
    return render_clean(request, "blog/index.html", context)


def blog_detail(request, post_slug):
    try:
        post = (
            BlogPost.objects.filter(status="published", slug=post_slug)
            .filter(models.Q(publish_at__lte=timezone.now()) | models.Q(publish_at__isnull=True))
            .select_related("category")
            .prefetch_related("tags", "comments")
            .first()
        )
    except (OperationalError, ProgrammingError):
        post = None
    if not post:
        post = get_post(post_slug)
    if not post:
        raise Http404("Post not found")

    approved_comments = []
    related_posts = []
    comment_form = BlogCommentForm()

    if hasattr(post, "pk"):
        BlogPost.objects.filter(pk=post.pk).update(view_count=models.F("view_count") + 1)
        if request.method == "POST":
            comment_form = BlogCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.save()
                comment_form = BlogCommentForm()
        approved_comments = list(post.comments.filter(is_approved=True, is_spam=False))
        related_posts = list(
            BlogPost.objects.filter(status="published")
            .exclude(pk=post.pk)
            .filter(
                models.Q(category=post.category) | models.Q(tags__in=post.tags.all())
            )
            .filter(models.Q(publish_at__lte=timezone.now()) | models.Q(publish_at__isnull=True))
            .distinct()
            .select_related("category")[:4]
        )

    # Prepare SEO image and keywords for the article (prefer featured image)
    seo_image = ""
    if hasattr(post, "featured_image") and getattr(post, "featured_image"):
        try:
            seo_image = post.featured_image.url
        except Exception:
            seo_image = getattr(post, "featured_image_url", "") or getattr(post, "image_url", "")
    else:
        seo_image = getattr(post, "featured_image_url", "") or getattr(post, "image_url", "")
    seo_keywords = getattr(post, "meta_keywords", "") or ""

    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                f"{post.title if hasattr(post, 'title') else post['title']} | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                post.meta_description if hasattr(post, "meta_description") else post["meta_description"],
                request,
                image=seo_image,
                keywords=seo_keywords,
            ),
            "post": post,
            "article_intro": post.excerpt if hasattr(post, "excerpt") else post["intro"],
            "article_sections": getattr(post, "sections", None),
            "comment_form": comment_form,
            "approved_comments": approved_comments,
            "related_posts": related_posts,
            "share_url": request.build_absolute_uri(request.path),
            "page_images": with_fallback_media(get_page_media("blog_post"), get_page_image_block("blog_post")),
        }
    )
    return render_clean(request, "blog/detail.html", context)


def blog_track_read(request, post_slug):
    seconds = request.GET.get("seconds", "0")
    try:
        seconds = int(seconds)
    except ValueError:
        seconds = 0

    if 1 <= seconds <= 3600:
        BlogPost.objects.filter(slug=post_slug).update(total_read_seconds=models.F("total_read_seconds") + seconds)
    return HttpResponse("ok", content_type="text/plain; charset=utf-8")


def capture_lead(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)

    name = (request.POST.get("name") or "زائر الموقع").strip()[:120]
    phone = (request.POST.get("phone") or request.POST.get("mobile") or "").strip()[:20]
    city = (request.POST.get("city") or "").strip()[:120]
    service = (request.POST.get("service") or "").strip()
    details = (request.POST.get("details") or request.POST.get("message") or "").strip()
    page_url = (request.POST.get("page_url") or request.META.get("HTTP_REFERER") or "").strip()

    if not phone:
        phone = "واتساب"

    message_parts = []
    if service:
        message_parts.append(f"الخدمة: {service}")
    if details:
        message_parts.append(f"التفاصيل: {details}")
    if page_url:
        message_parts.append(f"صفحة الطلب: {page_url}")
    message = "\n".join(message_parts) or "طلب سريع من الموقع"

    try:
        lead = Lead.objects.create(name=name, phone=phone, city_name=city, message=message)
        return JsonResponse({"ok": True, "lead_id": lead.pk})
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "database_unavailable"}, status=503)


def track_conversion(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)

    event_type = (request.POST.get("event_type") or "").strip()
    allowed = {choice[0] for choice in ConversionEvent.EVENT_CHOICES}
    if event_type not in allowed:
        return JsonResponse({"ok": False, "error": "invalid_event"}, status=400)

    try:
        event = ConversionEvent.objects.create(
            event_type=event_type,
            label=(request.POST.get("label") or "").strip()[:160],
            page_url=(request.POST.get("page_url") or request.META.get("HTTP_REFERER") or "").strip(),
            metadata={
                "city": request.POST.get("city", ""),
                "service": request.POST.get("service", ""),
            },
        )
        return JsonResponse({"ok": True, "event_id": event.pk})
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "database_unavailable"}, status=503)


def library_image_from_database(request, pk, filename):
    item = get_object_or_404(
        LibraryImage.objects.only("image_data", "image_content_type", "image_filename", "is_active"),
        pk=pk,
        is_active=True,
    )
    if not item.image_data:
        raise Http404

    response = HttpResponse(bytes(item.image_data), content_type=item.image_content_type or "image/jpeg")
    response["Cache-Control"] = "public, max-age=86400"
    response["Content-Disposition"] = f'inline; filename="{item.image_filename or filename}"'
    return response


def contact(request):
    context = build_base_context(request)
    settings_obj = context.get("settings_obj")
    context.update(
        {
            "seo": build_seo(
                f"اتصل بنا | {settings_obj.site_name if settings_obj else SITE_NAME}",
                settings_obj.seo_default_description if settings_obj and settings_obj.seo_default_description else f"تواصل معنا الآن لطلب عرض سعر سريع لخدمات {highlights_phrase(settings_obj)} في السعودية.",
                request,
                image=settings_obj.default_og_image_resolved if settings_obj else "",
                keywords=settings_obj.seo_default_keywords if settings_obj else "",
            ),
            "phone": context.get("contact_phone") or PHONE_NUMBER,
            "page_images": with_fallback_media(get_page_media("contact"), get_page_image_block("contact")),
        }
    )
    return render_clean(request, "pages/contact.html", context)


CALCULATOR_PAGES = {
    "landscape": {
        "title": "حاسبة تكلفة اللاندسكيب",
        "service": "لاندسكيب وتنسيق حدائق",
        "description": "تقدير تكلفة تصميم وتنفيذ اللاندسكيب للفلل والاستراحات والمشاريع.",
        "unit": "متر مربع",
        "min_rate": 180,
        "max_rate": 360,
        "tips": ["يشمل التقدير الزراعة والتوزيع العام.", "تزيد التكلفة مع الجلسات والممرات والإضاءة.", "المعاينة تحدد احتياج التربة والري."],
        "keywords": "حاسبة تكلفة لاندسكيب, تكلفة تنسيق حدائق, سعر اللاندسكيب",
    },
    "palm-supply": {
        "title": "حاسبة تكلفة توريد النخيل",
        "service": "توريد نخيل",
        "description": "تقدير تكلفة توريد النخيل حسب العدد والمقاس والنوع.",
        "unit": "نخلة",
        "min_rate": 450,
        "max_rate": 1800,
        "tips": ["السعر يتغير حسب نوع النخيل والمقاس.", "النقل والزراعة قد تحسب منفصلة.", "نخيل المداخل يحتاج اختيار مقاس متناسق."],
        "keywords": "حاسبة تكلفة توريد نخيل, سعر نخيل الرياض, تكلفة نخيل واشنطني",
    },
    "palm-pruning": {
        "title": "حاسبة تكلفة تكريب وتشذيب النخيل",
        "service": "تكريب أو تشذيب نخيل",
        "description": "تقدير تكلفة تنظيف وتكريب وتشذيب النخيل حسب العدد والارتفاع.",
        "unit": "نخلة",
        "min_rate": 45,
        "max_rate": 180,
        "tips": ["الارتفاع وكثافة السعف تؤثر على السعر.", "تنظيف المخلفات قد يضاف للتكلفة.", "التكريب الدوري يحسن الشكل ويقلل المخاطر."],
        "keywords": "حاسبة تكلفة تكريب نخيل, سعر تشذيب نخيل, تكلفة تنظيف نخيل",
    },
    "washingtonia-palm": {
        "title": "حاسبة تكلفة نخيل واشنطني",
        "service": "نخيل واشنطني",
        "description": "تقدير تكلفة توريد وزراعة نخيل واشنطني للمداخل والطرق.",
        "unit": "نخلة",
        "min_rate": 600,
        "max_rate": 2200,
        "tips": ["المقاس هو العامل الأكبر في السعر.", "يفضل للمداخل والطرق والمساحات المفتوحة.", "يحتاج ري منتظم بعد الزراعة."],
        "keywords": "حاسبة تكلفة نخيل واشنطني, سعر نخيل واشنطني, توريد نخيل واشنطنيا",
    },
    "royal-palm": {
        "title": "حاسبة تكلفة نخيل ملوكي",
        "service": "نخيل ملوكي",
        "description": "تقدير تكلفة توريد وزراعة النخيل الملوكي للواجهات الفاخرة.",
        "unit": "نخلة",
        "min_rate": 900,
        "max_rate": 3200,
        "tips": ["يناسب الفلل والواجهات الرسمية.", "يحتاج توزيع متناسق ومسافات واضحة.", "اختيار المقاس يغير التكلفة بشكل كبير."],
        "keywords": "حاسبة تكلفة نخيل ملوكي, سعر نخيل ملوكي, توريد نخيل ملوكي",
    },
    "natural-grass": {
        "title": "حاسبة تكلفة الثيل الطبيعي",
        "service": "ثيل طبيعي",
        "description": "تقدير تكلفة توريد وزراعة الثيل الطبيعي مع التسوية والري.",
        "unit": "متر مربع",
        "min_rate": 35,
        "max_rate": 95,
        "tips": ["جودة التربة والتسوية تؤثر على النتيجة.", "الثيل الطبيعي يحتاج ري وقص وصيانة.", "المساحات الكبيرة تخفض متوسط التكلفة."],
        "keywords": "حاسبة تكلفة ثيل طبيعي, سعر الثيل الطبيعي, زراعة ثيل طبيعي",
    },
    "artificial-grass": {
        "title": "حاسبة تكلفة العشب الصناعي",
        "service": "عشب صناعي",
        "description": "تقدير تكلفة تركيب العشب الصناعي للحدائق والجلسات والأسطح.",
        "unit": "متر مربع",
        "min_rate": 45,
        "max_rate": 140,
        "tips": ["السعر يتغير حسب سماكة وجودة العشب.", "تجهيز الأرضية مهم لطول عمر التركيب.", "مناسب لتقليل الصيانة واستهلاك الماء."],
        "keywords": "حاسبة تكلفة عشب صناعي, سعر العشب الصناعي, تركيب عشب صناعي",
    },
    "irrigation": {
        "title": "حاسبة تكلفة شبكات الري",
        "service": "شبكات ري",
        "description": "تقدير تكلفة شبكة الري للحدائق والنخيل والثيل.",
        "unit": "متر مربع",
        "min_rate": 25,
        "max_rate": 85,
        "tips": ["نوع الري يختلف بين التنقيط والرش.", "التحكم الآلي يزيد التكلفة ويحسن التشغيل.", "توزيع المناطق يقلل هدر الماء."],
        "keywords": "حاسبة تكلفة شبكات ري, سعر شبكة ري, ري بالتنقيط للنخيل",
    },
    "tree-supply": {
        "title": "حاسبة تكلفة توريد الأشجار",
        "service": "توريد أشجار",
        "description": "تقدير تكلفة توريد وزراعة أشجار ظل وزينة ومثمرة.",
        "unit": "شجرة",
        "min_rate": 120,
        "max_rate": 850,
        "tips": ["نوع الشجرة وحجمها يغيران السعر.", "أشجار الظل الكبيرة تحتاج نقل وزراعة بعناية.", "اختيار أشجار مناسبة للمناخ يقلل الصيانة."],
        "keywords": "حاسبة تكلفة توريد أشجار, سعر أشجار ظل, تكلفة زراعة أشجار",
    },
    "soil-preparation": {
        "title": "حاسبة تكلفة تجهيز التربة",
        "service": "تجهيز تربة زراعية",
        "description": "تقدير تكلفة تحسين وتجهيز التربة قبل الزراعة واللاندسكيب.",
        "unit": "متر مربع",
        "min_rate": 18,
        "max_rate": 60,
        "tips": ["قد تشمل إزالة تربة قديمة أو إضافة تربة محسنة.", "التسميد والخلطات ترفع الجودة والتكلفة.", "تجهيز التربة يحسن نجاح الزراعة."],
        "keywords": "حاسبة تكلفة تجهيز تربة, سعر تربة زراعية, تحسين تربة حدائق",
    },
    "fencing": {
        "title": "حاسبة تكلفة الشبوك",
        "service": "شبوك وسياجات",
        "description": "تقدير تكلفة تركيب الشبوك والسياجات للمزارع والاستراحات.",
        "unit": "متر طولي",
        "min_rate": 55,
        "max_rate": 180,
        "tips": ["الارتفاع ونوع الشبك يغيران السعر.", "الأعمدة والبوابات تحسب ضمن التفاصيل.", "الشبوك مناسبة للحماية والخصوصية."],
        "keywords": "حاسبة تكلفة شبوك, سعر تركيب شبوك, شبوك مزارع",
    },
    "shades": {
        "title": "حاسبة تكلفة المظلات",
        "service": "مظلات خارجية",
        "description": "تقدير تكلفة مظلات السيارات والجلسات والمداخل.",
        "unit": "متر مربع",
        "min_rate": 130,
        "max_rate": 380,
        "tips": ["نوع القماش أو المعدن يؤثر على السعر.", "المساحة والارتفاع وطريقة التثبيت مهمة.", "المظلات تكمل اللاندسكيب وتزيد الاستخدام."],
        "keywords": "حاسبة تكلفة مظلات, سعر مظلات سيارات, تركيب مظلات خارجية",
    },
}


def cost_calculator(request):
    context = build_base_context(request)
    calculators = [
        {"slug": slug, **calculator}
        for slug, calculator in CALCULATOR_PAGES.items()
    ]
    context.update(
        {
            "seo": build_seo(
                "حاسبة تكلفة اللاندسكيب والنخيل والثيل | تقدير سريع",
                "احسب تكلفة تقريبية لخدمات اللاندسكيب، توريد وزراعة النخيل، الثيل الطبيعي والعشب الصناعي وشبكات الري قبل طلب عرض السعر.",
                request,
                keywords="حاسبة تكلفة لاندسكيب, تكلفة توريد نخيل, تكلفة الثيل, تكلفة تنسيق حدائق",
            ),
            "calculators": calculators,
            "calculator": CALCULATOR_PAGES["landscape"],
            "calculator_slug": "landscape",
            "page_images": with_fallback_media(get_page_media("services"), get_page_image_block("services")),
        }
    )
    return render_clean(request, "pages/cost_calculator.html", context)


def cost_calculator_detail(request, calculator_slug):
    calculator = CALCULATOR_PAGES.get(calculator_slug)
    if not calculator:
        raise Http404("Calculator not found")
    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                f"{calculator['title']} | تقدير تكلفة سريع",
                calculator["description"],
                request,
                keywords=calculator["keywords"],
            ),
            "calculators": [{"slug": slug, **item} for slug, item in CALCULATOR_PAGES.items()],
            "calculator": calculator,
            "calculator_slug": calculator_slug,
            "page_images": with_fallback_media(get_page_media("services"), get_page_image_block("services")),
        }
    )
    return render_clean(request, "pages/cost_calculator.html", context)


COMPARISON_PAGES = {
    "washingtonia-vs-royal-palm": {
        "title": "نخيل واشنطني أم نخيل ملوكي؟",
        "description": "مقارنة عملية بين نخيل واشنطني والنخيل الملوكي من حيث الشكل والاستخدام والصيانة والأنسب للفلل والمداخل.",
        "left": "نخيل واشنطني",
        "right": "نخيل ملوكي",
        "left_points": ["مناسب للطرق والمداخل الواسعة", "يعطي ارتفاعًا واضحًا وسريع الحضور", "اختيار عملي للمشاريع الخارجية"],
        "right_points": ["مظهر فاخر ومنظم", "مناسب للفلل والواجهات الراقية", "يفضل عند التركيز على الهوية البصرية"],
        "recommendation": "إذا كان الهدف تغطية مداخل وطرق ومساحات كبيرة فالنخيل الواشنطني خيار عملي، أما إذا كان الهدف واجهة فاخرة ومظهر رسمي فالنخيل الملوكي غالبًا أفضل.",
        "keywords": "نخيل واشنطني, نخيل ملوكي, الفرق بين نخيل واشنطني وملوكي",
    },
    "natural-vs-artificial-grass": {
        "title": "ثيل طبيعي أم عشب صناعي؟",
        "description": "مقارنة بين الثيل الطبيعي والعشب الصناعي للحدائق والاستراحات من حيث الشكل والصيانة والري والتكلفة.",
        "left": "ثيل طبيعي",
        "right": "عشب صناعي",
        "left_points": ["مظهر طبيعي وملمس حي", "يحتاج ري وقص وصيانة", "مناسب لمن يريد حديقة خضراء حقيقية"],
        "right_points": ["صيانة أقل واستهلاك ماء شبه معدوم", "مناسب للممرات والجلسات والأسطح", "يحافظ على الشكل في الاستخدام اليومي"],
        "recommendation": "الثيل الطبيعي أفضل لعشاق المساحات الحية مع صيانة منتظمة، والعشب الصناعي أفضل إذا كانت الأولوية قلة الصيانة وتوفير الماء.",
        "keywords": "ثيل طبيعي, عشب صناعي, الفرق بين الثيل الطبيعي والصناعي",
    },
}


def comparison_detail(request, comparison_slug):
    comparison = COMPARISON_PAGES.get(comparison_slug)
    if not comparison:
        raise Http404("Comparison not found")
    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                f"{comparison['title']} | مقارنة لاختيار الأنسب",
                comparison["description"],
                request,
                keywords=comparison["keywords"],
            ),
            "comparison": comparison,
            "page_images": with_fallback_media(get_page_media("services"), get_page_image_block("services")),
        }
    )
    return render_clean(request, "pages/comparison_detail.html", context)


def city_detail(request, city_slug):
    try:
        city_obj = CityModel.objects.filter(is_active=True, slug=city_slug).first()
    except (OperationalError, ProgrammingError):
        city_obj = None

    if city_obj:
        city = {"slug": city_obj.slug, "name": city_obj.name, "region": city_obj.region, "description": city_obj.short_description or city_obj.content}
        city_pages = CityServicePage.objects.filter(city=city_obj, is_active=True).select_related("service")
        service_links = [
            {
                "slug": item.custom_slug or item.service.slug,
                "name": item.service.title,
                "description": item.content,
                "image": (get_images_by_category(resolve_service_category(item.service.slug), 1) or [{}])[0].get("image_url", ""),
                "url": reverse("city_service_detail", kwargs={"city_slug": city_slug, "service_slug": item.custom_slug or item.service.slug}),
            }
            for item in city_pages
        ]
    else:
        city = get_city(city_slug)
        if not city:
            raise Http404("City not found")
        service_links = [
            {
                "slug": service_slug,
                "name": service["name"],
                "description": service["description"],
                "image": (get_images_by_category(resolve_service_category(service_slug), 1) or [{}])[0].get("image_url", ""),
                "url": reverse("city_service_detail", kwargs={"city_slug": city_slug, "service_slug": service_slug}),
            }
            for service_slug, service in SERVICE_SLUGS.items()
        ]

    context = build_base_context(request)
    context.update(
        {
            "seo": build_seo(
                f"لاندسكيب وحدائق في {city['name']} | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                f"تنفيذ لاندسكيب متكامل في {city['name']} يشمل تصميم الحدائق، زراعة الأشجار والنخيل، وأنظمة الري مع خدمة سريعة وجودة عالية.",
                request,
            ),
            "city": city,
            "service_links": service_links,
            "quote_message": build_quote_message(city_name=city["name"]),
            "page_images": with_fallback_media(get_page_media("city"), get_page_image_block("city")),
            "theme_css_vars": build_theme_css(settings_obj=context.get("settings_obj"), city=city_obj),
        }
    )
    return render_clean(request, "cities/detail.html", context)


def city_service_detail(request, city_slug, service_slug):
    try:
        city_obj = CityModel.objects.filter(is_active=True, slug=city_slug).first()
        city_service_obj = None
        if city_obj:
            city_service_obj = CityServicePage.objects.filter(
                city=city_obj,
                is_active=True,
            ).select_related("service").filter(custom_slug=service_slug).first() or CityServicePage.objects.filter(
                city=city_obj,
                is_active=True,
                service__slug=service_slug,
            ).select_related("service").first()
        else:
            city_service_obj = None
    except (OperationalError, ProgrammingError):
        city_obj = None
        city_service_obj = None

    if city_service_obj:
        city = {"slug": city_obj.slug, "name": city_obj.name}
        service = {
            "name": city_service_obj.service.title,
            "keyword": city_service_obj.hero_title or city_service_obj.service.title,
            "description": city_service_obj.content,
            "benefits": city_service_obj.benefits_list or city_service_obj.service.benefits_list,
        }
        related_services = [
            {
                "name": item.service.title,
                "url": reverse("city_service_detail", kwargs={"city_slug": city_slug, "service_slug": item.custom_slug or item.service.slug}),
            }
            for item in CityServicePage.objects.filter(city=city_obj, is_active=True).exclude(pk=city_service_obj.pk).select_related("service")
        ]
    else:
        city = get_city(city_slug)
        service = get_service(service_slug)
        if not city or not service:
            raise Http404("Page not found")
        related_services = [
            {
                "name": related["name"],
                "url": reverse(
                    "city_service_detail",
                    kwargs={"city_slug": city_slug, "service_slug": related_slug},
                ),
            }
            for related_slug, related in SERVICE_SLUGS.items()
            if related_slug != service_slug
        ]

    service_category = resolve_service_category(service_slug)
    context = build_base_context(request)
    service_keyword = service["keyword"]
    page_phrase = service_keyword if city["name"] in service_keyword else f"{service_keyword} في {city['name']}"
    context.update(
        {
            "seo": build_seo(
                f"{page_phrase} | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
                f"{page_phrase} بخامات ممتازة وتنفيذ سريع وأسعار تنافسية مع معاينة واتساب واتصال مباشر.",
                request,
            ),
            "city": city,
            "service": service,
            "quote_message": build_quote_message(city_name=city["name"], service_name=service["name"]),
            "related_services": related_services,
            "page_images": with_fallback_media(get_page_media("city_service"), get_images_by_category(service_category, 4)),
            "theme_css_vars": build_theme_css(settings_obj=context.get("settings_obj"), city=city_obj),
        }
    )
    return render_clean(request, "cities/service_detail.html", context)


def robots_txt(request):
    site_base = getattr(settings, "SITE_URL", None) or request.build_absolute_uri("/").rstrip("/")
    sitemap_url = site_base + reverse("sitemap_xml")
    host = site_base.replace("https://", "").replace("http://", "")
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /__debug__/",
        "Allow: /",
        "Allow: /archive/",
        f"Host: {host}",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def _archive_static_pages():
    return [
        {"title": "الرئيسية", "url": reverse("home"), "kind": "صفحة رئيسية"},
        {"title": "من نحن", "url": reverse("about"), "kind": "صفحة تعريفية"},
        {"title": "الخدمات", "url": reverse("services"), "kind": "فهرس خدمات"},
        {"title": "الأعمال", "url": reverse("portfolio"), "kind": "معرض أعمال"},
        {"title": "المدن", "url": reverse("cities"), "kind": "فهرس مدن"},
        {"title": "المدونة", "url": reverse("blog"), "kind": "فهرس مقالات"},
        {"title": "اتصل بنا", "url": reverse("contact"), "kind": "تواصل"},
        {"title": "شبكة الأرشفة", "url": reverse("archive_network"), "kind": "فهرس بوتات"},
        {"title": "فهرس الخدمات", "url": reverse("archive_services"), "kind": "فهرس بوتات"},
        {"title": "فهرس المدن", "url": reverse("archive_cities"), "kind": "فهرس بوتات"},
        {"title": "فهرس المقالات", "url": reverse("archive_articles"), "kind": "فهرس بوتات"},
    ]


def _archive_services():
    services = []
    try:
        queryset = ServiceModel.objects.filter(is_visible=True).order_by("display_order", "title")
        for service in queryset:
            services.append({
                "title": fix_arabic_text(service.title),
                "description": fix_arabic_text(service.meta_description or service.description),
                "url": reverse("service_detail", kwargs={"service_slug": service.slug}),
                "slug": service.slug,
                "updated_at": service.updated_at,
            })
    except (OperationalError, ProgrammingError):
        services = []

    if not services:
        for slug, service in SERVICE_SLUGS.items():
            services.append({
                "title": fix_arabic_text(service["name"]),
                "description": fix_arabic_text(service.get("description", "")),
                "url": reverse("service_detail", kwargs={"service_slug": slug}),
                "slug": slug,
                "updated_at": timezone.now(),
            })
    return services


def _archive_cities():
    cities = []
    try:
        queryset = CityModel.objects.filter(is_active=True).order_by("region", "name")
        for city in queryset:
            cities.append({
                "title": fix_arabic_text(city.name),
                "description": fix_arabic_text(city.meta_description or city.short_description or city.content),
                "url": reverse("city_detail", kwargs={"city_slug": city.slug}),
                "slug": city.slug,
                "region": fix_arabic_text(city.region),
                "updated_at": city.updated_at,
            })
    except (OperationalError, ProgrammingError):
        cities = []

    if not cities:
        for city in CITIES:
            cities.append({
                "title": fix_arabic_text(city["name"]),
                "description": fix_arabic_text(city.get("description", "")),
                "url": reverse("city_detail", kwargs={"city_slug": city["slug"]}),
                "slug": city["slug"],
                "region": fix_arabic_text(city.get("region", "")),
                "updated_at": timezone.now(),
            })
    return cities


def _archive_articles():
    articles = []
    categories = []
    tags = []
    try:
        posts = (
            BlogPost.objects.filter(status="published")
            .filter(models.Q(publish_at__lte=timezone.now()) | models.Q(publish_at__isnull=True))
            .select_related("category")
            .order_by("-publish_at", "-updated_at")
        )
        for post in posts:
            articles.append({
                "title": fix_arabic_text(post.title),
                "description": fix_arabic_text(post.meta_description or post.excerpt),
                "url": reverse("blog_detail", kwargs={"post_slug": post.slug}),
                "updated_at": post.updated_at,
            })
        categories = [
            {"title": fix_arabic_text(item.name), "url": reverse("blog_category", kwargs={"category_slug": item.slug})}
            for item in BlogCategory.objects.order_by("name")
        ]
        tags = [
            {"title": fix_arabic_text(item.name), "url": reverse("blog_tag", kwargs={"tag_slug": item.slug})}
            for item in BlogTag.objects.order_by("name")
        ]
    except (OperationalError, ProgrammingError):
        articles = []

    if not articles:
        for post in BLOG_POSTS:
            articles.append({
                "title": fix_arabic_text(post["title"]),
                "description": fix_arabic_text(post.get("meta_description", "")),
                "url": reverse("blog_detail", kwargs={"post_slug": post["slug"]}),
                "updated_at": timezone.now(),
            })
    return articles, categories, tags


def _archive_city_service_links(limit=None):
    links = []
    try:
        queryset = (
            CityServicePage.objects.filter(is_active=True)
            .select_related("city", "service")
            .order_by("city__name", "service__display_order", "service__title")
        )
        if limit:
            queryset = queryset[:limit]
        for item in queryset:
            links.append({
                "title": fix_arabic_text(item.hero_title or f"{item.service.title} في {item.city.name}"),
                "description": fix_arabic_text(item.meta_description),
                "url": reverse("city_service_detail", kwargs={"city_slug": item.city.slug, "service_slug": item.custom_slug or item.service.slug}),
                "city": fix_arabic_text(item.city.name),
                "service": fix_arabic_text(item.service.title),
            })
    except (OperationalError, ProgrammingError):
        links = []

    if not links:
        for city in CITIES:
            for service_slug, service in SERVICE_SLUGS.items():
                links.append({
                    "title": f"{fix_arabic_text(service['name'])} في {fix_arabic_text(city['name'])}",
                    "description": fix_arabic_text(service.get("description", "")),
                    "url": reverse("city_service_detail", kwargs={"city_slug": city["slug"], "service_slug": service_slug}),
                    "city": fix_arabic_text(city["name"]),
                    "service": fix_arabic_text(service["name"]),
                })
                if limit and len(links) >= limit:
                    return links
    return links


def archive_network(request):
    context = build_base_context(request)
    services = _archive_services()
    cities = _archive_cities()
    articles, categories, tags = _archive_articles()
    city_services = _archive_city_service_links(limit=None)
    context.update({
        "seo": build_seo(
            "شبكة أرشفة الموقع | كل الخدمات والمدن والمقالات",
            "فهرس HTML يساعد محركات البحث على اكتشاف صفحات الخدمات والمدن والمقالات وصفحات النخيل واللاندسكيب والشبوك والمظلات.",
            request,
            keywords="فهرس الموقع, خريطة الموقع, خدمات النخيل, لاندسكيب, توريد أشجار, شبوك, مظلات",
        ),
        "archive_title": "شبكة أرشفة الموقع",
        "archive_intro": "صفحة مركزية تجمع أهم روابط الموقع وتوجه روبوتات البحث إلى فهارس تفصيلية لكل نوع محتوى.",
        "static_pages": _archive_static_pages(),
        "services": services[:60],
        "calculators": [{"slug": slug, **item} for slug, item in CALCULATOR_PAGES.items()],
        "cities": cities,
        "articles": articles[:40],
        "categories": categories,
        "tags": tags,
        "city_services": city_services[:120],
        "counts": {
            "services": len(services),
            "cities": len(cities),
            "articles": len(articles),
            "city_services": len(city_services),
        },
    })
    return render_clean(request, "pages/archive_network.html", context)


def archive_services(request):
    context = build_base_context(request)
    services = _archive_services()
    context.update({
        "seo": build_seo(
            "فهرس خدمات النخيل واللاندسكيب والشبوك والمظلات",
            "كل صفحات الخدمات المتخصصة في توريد النخيل، تكريب وتشذيب النخيل، اللاندسكيب، الأشجار، الثيل، الري، الشبوك والمظلات.",
            request,
        ),
        "archive_title": "فهرس الخدمات",
        "archive_intro": "روابط مباشرة لكل صفحة خدمة حتى تصل لها محركات البحث والزوار بسهولة.",
        "items": services,
        "item_kind": "خدمة",
    })
    return render_clean(request, "pages/archive_list.html", context)


def archive_cities(request):
    context = build_base_context(request)
    context.update({
        "seo": build_seo(
            "فهرس المدن وصفحات الخدمات المحلية",
            "فهرس HTML لكل المدن وصفحات الخدمة داخل كل مدينة لتحسين اكتشاف صفحات الرياض وجدة والدمام وباقي المدن.",
            request,
        ),
        "archive_title": "فهرس المدن والخدمات المحلية",
        "archive_intro": "روابط المدن وروابط الخدمة داخل المدينة، وهي الصفحات الأهم للاستهداف المحلي في Google.",
        "cities": _archive_cities(),
        "city_services": _archive_city_service_links(limit=None),
    })
    return render_clean(request, "pages/archive_cities.html", context)


def archive_articles(request):
    context = build_base_context(request)
    articles, categories, tags = _archive_articles()
    context.update({
        "seo": build_seo(
            "فهرس مقالات النخيل واللاندسكيب",
            "كل مقالات الموقع عن توريد النخيل وتكريب النخيل واللاندسكيب وتوريد الأشجار والثيل والري والشبوك والمظلات.",
            request,
        ),
        "archive_title": "فهرس المقالات والتصنيفات",
        "archive_intro": "روابط المقالات والتصنيفات والوسوم حتى تكتشف محركات البحث المحتوى التحريري بوضوح.",
        "articles": articles,
        "categories": categories,
        "tags": tags,
    })
    return render_clean(request, "pages/archive_articles.html", context)


def _sitemap_base(request):
    return getattr(settings, "SITE_URL", None) or request.build_absolute_uri("/").rstrip("/")


def _sitemap_absolute(request, url):
    site_base = _sitemap_base(request)
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        return site_base + url
    return site_base + "/" + url


def _sitemap_iso(dt):
    return dt.astimezone(datetime_timezone.utc).isoformat() if dt else None


def _sitemap_image_sets(request):
    return {
        "home_gallery": [{"loc": _sitemap_absolute(request, item["image_url"]), "title": item.get("title", "")} for item in get_page_image_block("home_gallery")[:4]],
        "services": [{"loc": _sitemap_absolute(request, item["image_url"]), "title": item.get("title", "")} for item in get_page_image_block("services")[:2]],
        "city": [{"loc": _sitemap_absolute(request, item["image_url"]), "title": item.get("title", "")} for item in get_page_image_block("city")[:3]],
        "city_service": [{"loc": _sitemap_absolute(request, item["image_url"]), "title": item.get("title", "")} for item in get_page_image_block("city_service")[:2]],
        "blog_post": [{"loc": _sitemap_absolute(request, item["image_url"]), "title": item.get("title", "")} for item in get_page_image_block("blog_post")[:1]],
    }


def _unique_sitemap_images(images):
    seen = set()
    output = []
    for image in images:
        loc = image.get("loc")
        if not loc or loc in seen:
            continue
        seen.add(loc)
        output.append(image)
    return output


def _all_sitemap_images(request):
    images = []

    for group in ("home_hero", "home_gallery", "home_banners", "about", "services", "portfolio", "cities", "blog", "blog_post", "contact", "city", "city_service"):
        for item in get_page_image_block(group):
            if item.get("image_url"):
                images.append({
                    "loc": _sitemap_absolute(request, item["image_url"]),
                    "title": item.get("title", "") or item.get("display_alt", ""),
                })

    try:
        for item in PageMedia.objects.filter(is_active=True):
            if item.image_url:
                images.append({"loc": _sitemap_absolute(request, item.image_url), "title": item.title})
        for item in LibraryImage.objects.filter(is_active=True).defer("image_data"):
            if item.image_url:
                images.append({"loc": _sitemap_absolute(request, item.image_url), "title": item.title})
        for service in ServiceModel.objects.filter(is_visible=True):
            if service.resolved_image:
                images.append({"loc": _sitemap_absolute(request, service.resolved_image), "title": service.title})
        for project in Project.objects.filter(is_visible=True):
            if project.image_url:
                images.append({"loc": _sitemap_absolute(request, project.image_url), "title": project.title})
        for post in BlogPost.objects.filter(status="published"):
            if post.image_url:
                images.append({"loc": _sitemap_absolute(request, post.image_url), "title": post.title})
    except (OperationalError, ProgrammingError):
        pass

    return _unique_sitemap_images(images)


def _render_sitemap_urlset(items):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for item in items:
        xml.append("<url>")
        xml.append(f"<loc>{escape(item['loc'])}</loc>")
        if item.get("lastmod"):
            xml.append(f"<lastmod>{escape(item['lastmod'])}</lastmod>")
        if item.get("changefreq"):
            xml.append(f"<changefreq>{escape(item['changefreq'])}</changefreq>")
        if item.get("priority"):
            xml.append(f"<priority>{escape(item['priority'])}</priority>")
        for image in item.get("images", []) or []:
            if image.get("loc"):
                xml.append("<image:image>")
                xml.append(f"<image:loc>{escape(image['loc'])}</image:loc>")
                if image.get("title"):
                    xml.append(f"<image:title>{escape(image['title'])}</image:title>")
                xml.append("</image:image>")
        xml.append("</url>")
    xml.append("</urlset>")
    return HttpResponse("".join(xml), content_type="application/xml; charset=utf-8")


def _render_sitemap_index(request, sitemaps):
    now = _sitemap_iso(timezone.now())
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for sitemap in sitemaps:
        xml.append("<sitemap>")
        xml.append(f"<loc>{escape(_sitemap_absolute(request, sitemap['loc']))}</loc>")
        xml.append(f"<lastmod>{escape(sitemap.get('lastmod') or now)}</lastmod>")
        xml.append("</sitemap>")
    xml.append("</sitemapindex>")
    return HttpResponse("".join(xml), content_type="application/xml; charset=utf-8")


def _sitemap_collector(request):
    urls = []
    seen_locations = set()

    def add_url(location, lastmod=None, changefreq="weekly", priority="0.5", images=None):
        final_location = _sitemap_absolute(request, location)
        if final_location in seen_locations:
            return
        seen_locations.add(final_location)
        urls.append({
            "loc": final_location,
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority,
            "images": images or [],
        })

    return urls, add_url


def sitemap_pages_xml(request):
    urls, add_url = _sitemap_collector(request)

    add_url(
        reverse("home"),
        lastmod=_sitemap_iso(timezone.now()),
        changefreq="daily",
        priority="1.0",
    )

    static_pages = {
        "about": "about",
        "services": "services",
        "portfolio": "portfolio",
        "cities": "cities",
        "blog": "blog",
        "contact": "contact",
        "cost_calculator": "services",
        "archive_network": "services",
        "archive_services": "services",
        "archive_cities": "cities",
        "archive_articles": "blog",
    }
    for name, block_name in static_pages.items():
        add_url(
            reverse(name),
            lastmod=_sitemap_iso(timezone.now()),
            changefreq="monthly",
            priority="0.8",
        )

    for comparison_slug in COMPARISON_PAGES:
        add_url(
            reverse("comparison_detail", kwargs={"comparison_slug": comparison_slug}),
            lastmod=_sitemap_iso(timezone.now()),
            changefreq="monthly",
            priority="0.75",
        )

    for calculator_slug in CALCULATOR_PAGES:
        add_url(
            reverse("cost_calculator_detail", kwargs={"calculator_slug": calculator_slug}),
            lastmod=_sitemap_iso(timezone.now()),
            changefreq="monthly",
            priority="0.78",
        )

    return _render_sitemap_urlset(urls)


def sitemap_services_xml(request):
    urls, add_url = _sitemap_collector(request)

    for service_slug in SERVICE_SLUGS:
        add_url(
            reverse("service_detail", kwargs={"service_slug": service_slug}),
            lastmod=_sitemap_iso(timezone.now()),
            changefreq="weekly",
            priority="0.85",
        )

    try:
        for service in ServiceModel.objects.filter(is_visible=True):
            add_url(
                reverse("service_detail", kwargs={"service_slug": service.slug}),
                lastmod=_sitemap_iso(getattr(service, "updated_at", None)),
                changefreq="weekly",
                priority="0.85",
            )
    except (OperationalError, ProgrammingError):
        pass

    return _render_sitemap_urlset(urls)


def sitemap_cities_xml(request):
    urls, add_url = _sitemap_collector(request)

    for city in CITIES:
        add_url(
            reverse("city_detail", kwargs={"city_slug": city["slug"]}),
            lastmod=_sitemap_iso(timezone.now()),
            changefreq="weekly",
            priority="0.9",
        )

    try:
        for city in CityModel.objects.filter(is_active=True):
            add_url(
                reverse("city_detail", kwargs={"city_slug": city.slug}),
                lastmod=_sitemap_iso(getattr(city, "updated_at", None)),
                changefreq="weekly",
                priority="0.9",
            )
    except (OperationalError, ProgrammingError):
        pass

    return _render_sitemap_urlset(urls)


def sitemap_local_services_xml(request):
    urls, add_url = _sitemap_collector(request)

    for city in CITIES:
        for service_slug in SERVICE_SLUGS:
            add_url(
                reverse("city_service_detail", kwargs={"city_slug": city["slug"], "service_slug": service_slug}),
                lastmod=_sitemap_iso(timezone.now()),
                changefreq="monthly",
                priority="0.7",
            )

    try:
        for item in CityServicePage.objects.filter(is_active=True).select_related("city", "service"):
            add_url(
                reverse(
                    "city_service_detail",
                    kwargs={"city_slug": item.city.slug, "service_slug": item.custom_slug or item.service.slug},
                ),
                lastmod=_sitemap_iso(getattr(item, "updated_at", None)),
                changefreq="monthly",
                priority="0.75",
            )
    except (OperationalError, ProgrammingError):
        pass

    return _render_sitemap_urlset(urls)


def sitemap_blog_xml(request):
    urls, add_url = _sitemap_collector(request)

    for post in BLOG_POSTS:
        add_url(
            reverse("blog_detail", kwargs={"post_slug": post["slug"]}),
            lastmod=_sitemap_iso(timezone.now()),
            changefreq="monthly",
            priority="0.6",
        )

    try:
        for category in BlogCategory.objects.all():
            add_url(reverse("blog_category", kwargs={"category_slug": category.slug}), lastmod=_sitemap_iso(getattr(category, "updated_at", None)), changefreq="monthly", priority="0.5")
        for tag in BlogTag.objects.all():
            add_url(reverse("blog_tag", kwargs={"tag_slug": tag.slug}), lastmod=_sitemap_iso(getattr(tag, "updated_at", None)), changefreq="monthly", priority="0.4")
        for post in BlogPost.objects.filter(status="published"):
            lastmod_dt = getattr(post, "publish_at", None) or getattr(post, "updated_at", None) or getattr(post, "created_at", None)
            add_url(reverse("blog_detail", kwargs={"post_slug": post.slug}), lastmod=_sitemap_iso(lastmod_dt), changefreq="monthly", priority="0.6")
    except (OperationalError, ProgrammingError):
        pass

    return _render_sitemap_urlset(urls)


def sitemap_images_xml(request):
    urls, add_url = _sitemap_collector(request)
    all_images = _all_sitemap_images(request)

    page_targets = [
        (reverse("home"), "daily", "0.9"),
        (reverse("services"), "weekly", "0.8"),
        (reverse("portfolio"), "weekly", "0.7"),
        (reverse("cities"), "weekly", "0.7"),
        (reverse("blog"), "weekly", "0.6"),
        (reverse("archive_network"), "weekly", "0.6"),
    ]
    chunk_size = 500
    for index, (page_url, changefreq, priority) in enumerate(page_targets):
        chunk = all_images[index * chunk_size : (index + 1) * chunk_size]
        if chunk:
            add_url(
                page_url,
                lastmod=_sitemap_iso(timezone.now()),
                changefreq=changefreq,
                priority=priority,
                images=chunk,
            )

    return _render_sitemap_urlset(urls)


def sitemap_xml(request):
    return _render_sitemap_index(
        request,
        [
            {"loc": reverse("sitemap_pages_xml")},
            {"loc": reverse("sitemap_services_xml")},
            {"loc": reverse("sitemap_cities_xml")},
            {"loc": reverse("sitemap_local_services_xml")},
            {"loc": reverse("sitemap_blog_xml")},
            {"loc": reverse("sitemap_images_xml")},
        ],
    )


def custom_404(request, exception=None):
    context = build_base_context(request)
    context["seo"] = build_seo(
        f"الصفحة غير موجودة | {context.get('settings_obj').site_name if context.get('settings_obj') else SITE_NAME}",
        "عذرًا، الصفحة المطلوبة غير موجودة. يمكنك العودة إلى الرئيسية أو تصفح الخدمات والمدن والمشاريع.",
        request,
    )
    return render_clean(request, "404.html", context, status=404)
