from django.contrib import admin, messages
import zipfile
from pathlib import PurePath

from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.conf import settings

from .admin_site import admin_site
from .forms import LibraryImageBulkReplaceForm, LibraryImageBulkUploadForm
from .models import (
    AIContentGenerationLog,
    BlogCategory,
    BlogComment,
    BlogPost,
    BlogTag,
    City,
    CityServicePage,
    ConversionEvent,
    Lead,
    LibraryImage,
    MediaFolder,
    NavigationItem,
    Page,
    PageMedia,
    Project,
    ProjectImage,
    ContactNumber,
    Service,
    SiteSettings,
    SiteVerification,
    SearchConsoleQuery,
    SEOReportIssue,
    SEOAutomationRun,
    LegacyRedirect,
    Testimonial,
)
from .views import default_alt_for, default_category_for, default_title_for, default_usage_group_for


try:
    admin_site.register(get_user_model(), UserAdmin)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin_site.register(Group, GroupAdmin)
except admin.sites.AlreadyRegistered:
    pass


class SafeChangelistAdmin(admin.ModelAdmin):
    changelist_error_message = "تعذر تحميل القائمة بسبب عدم توافق قاعدة البيانات. نفّذ migrate ثم أعد المحاولة."

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context=extra_context)
        except (OperationalError, ProgrammingError):
            self.message_user(request, self.changelist_error_message, level=messages.ERROR)
            return redirect("admin:index")


class SingletonAdmin(SafeChangelistAdmin):
    def has_add_permission(self, request):
        try:
            if self.model.objects.exists():
                return False
        except (OperationalError, ProgrammingError):
            return False
        return super().has_add_permission(request)


class SeoAdmin(SafeChangelistAdmin):
    search_fields = ("meta_title", "meta_description", "meta_keywords")


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


class ContactNumberInline(admin.TabularInline):
    model = ContactNumber
    extra = 1
    fields = ("label", "phone", "is_primary", "enable_whatsapp", "is_active", "sort_order")


def duplicate_pages(modeladmin, request, queryset):
    for obj in queryset:
        obj.pk = None
        obj.slug = f"{obj.slug}-copy"
        obj.title = f"{obj.title} - نسخة"
        obj.save()
    messages.success(request, "تم إنشاء نسخ من الصفحات المحددة.")


duplicate_pages.short_description = "نسخ الصفحات المحددة"


@admin.register(SiteSettings, site=admin_site)
class SiteSettingsAdmin(SingletonAdmin):
    list_display = ("site_name", "contact_phone", "whatsapp_number", "email", "updated_at")
    inlines = [ContactNumberInline]
    fieldsets = (
        ("بيانات الموقع", {"fields": ("site_name", "tagline", "footer_text")}),
        ("التواصل", {"fields": ("contact_phone", "whatsapp_number", "email", "address")}),
        ("LocalBusiness Schema", {"fields": ("business_type", "legal_name", "street_address", "address_locality", "address_region", "postal_code", "address_country", "latitude", "longitude", "opening_hours", "area_served", "same_as_links")}),
        ("خيارات المحتوى", {"fields": ("service_highlights",)}),
        ("الشبكات الاجتماعية", {"fields": ("facebook_url", "instagram_url", "x_url", "linkedin_url")}),
        ("خلفية هيرو الرئيسية", {"fields": ("homepage_hero_background", "homepage_hero_background_url")}),
        ("خلفية هيرو المدونة", {"fields": ("blog_hero_background", "blog_hero_background_url")}),
        ("ألوان الموقع", {"fields": ("primary_color", "secondary_color", "accent_color", "background_color", "text_color")}),
        ("SEO الصفحة الرئيسية", {"fields": ("homepage_meta_title", "homepage_meta_description")}),
        ("SEO عام", {"fields": ("seo_default_keywords", "seo_default_description", "seo_twitter_handle", "default_og_image", "default_og_image_url")}),
        ("Google Search Console", {"fields": ("google_search_console_property", "google_service_account_json")}),
        ("أتمتة SEO بالذكاء الاصطناعي", {"fields": ("ai_seo_enabled", "ai_seo_auto_apply", "ai_seo_research_queries")}),
    )


@admin.register(SiteVerification, site=admin_site)
class SiteVerificationAdmin(SafeChangelistAdmin):
    list_display = ("provider", "name", "is_active", "updated_at")
    list_filter = ("provider", "is_active")
    search_fields = ("name", "content", "raw_html")


@admin.register(SearchConsoleQuery, site=admin_site)
class SearchConsoleQueryAdmin(SafeChangelistAdmin):
    list_display = ("query", "page", "clicks", "impressions", "ctr", "position", "date_from", "date_to")
    list_filter = ("country", "device", "date_to")
    search_fields = ("query", "page")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SEOReportIssue, site=admin_site)
class SEOReportIssueAdmin(SafeChangelistAdmin):
    list_display = ("title", "issue_type", "severity", "status", "page_url", "detected_at")
    list_filter = ("severity", "status", "issue_type")
    search_fields = ("title", "page_url", "details", "suggested_fix")
    actions = ["mark_fixed", "mark_ignored"]

    @admin.action(description="تعليم المحدد كتم إصلاحه")
    def mark_fixed(self, request, queryset):
        queryset.update(status="fixed")

    @admin.action(description="تجاهل المحدد")
    def mark_ignored(self, request, queryset):
        queryset.update(status="ignored")


@admin.register(SEOAutomationRun, site=admin_site)
class SEOAutomationRunAdmin(SafeChangelistAdmin):
    list_display = ("started_at", "status", "issues_before", "issues_after", "ai_requested", "ai_applied", "finished_at")
    list_filter = ("status", "ai_requested", "ai_applied", "started_at")
    search_fields = ("summary", "error_message")
    readonly_fields = (
        "started_at",
        "finished_at",
        "status",
        "search_console_result",
        "local_seo_result",
        "redirects_result",
        "issues_before",
        "issues_after",
        "ai_requested",
        "ai_applied",
        "ai_result",
        "summary",
        "error_message",
        "created_at",
        "updated_at",
    )


@admin.register(LegacyRedirect, site=admin_site)
class LegacyRedirectAdmin(SafeChangelistAdmin):
    list_display = ("old_path", "target_path", "is_permanent", "is_active", "hit_count", "updated_at")
    list_filter = ("is_permanent", "is_active")
    search_fields = ("old_path", "target_path", "note")


@admin.register(MediaFolder, site=admin_site)
class MediaFolderAdmin(SafeChangelistAdmin):
    list_display = ("name", "parent", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PageMedia, site=admin_site)
class PageMediaAdmin(SafeChangelistAdmin):
    list_display = ("title", "page", "section", "folder", "sort_order", "is_active", "preview")
    list_filter = ("page", "section", "is_active", "folder")
    search_fields = ("title", "alt_text", "external_url")
    ordering = ("page", "section", "sort_order")

    def preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="height:44px;border-radius:8px;" />', obj.image_url)
        return "-"


@admin.action(description="مزامنة صور مجلد imge")
def sync_library_images(modeladmin, request, queryset):
    image_dir = settings.BASE_DIR / "imge"
    created_count = 0
    for path in sorted(image_dir.glob("*")):
        if not path.is_file():
            continue
        _, created = LibraryImage.objects.get_or_create(
            source_name=path.name,
            defaults={
                "title": default_title_for(path.name),
                "alt_text": default_alt_for(path.name),
                "category": default_category_for(path.name),
                "usage_group": default_usage_group_for(path.name),
            },
        )
        if created:
            created_count += 1
    messages.success(request, f"تمت مزامنة الصور. العناصر الجديدة: {created_count}")


ALLOWED_LIBRARY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}


def _safe_uploaded_image_name(name):
    return PurePath(name).name.replace("\\", "").replace("/", "")


def _is_supported_library_image(name):
    return PurePath(name).suffix.lower() in ALLOWED_LIBRARY_IMAGE_EXTENSIONS


@admin.register(LibraryImage, site=admin_site)
class LibraryImageAdmin(SafeChangelistAdmin):
    change_list_template = "admin/core/libraryimage/change_list.html"
    list_display = ("title", "category", "usage_group", "source_name", "sort_order", "is_active", "preview")
    list_filter = ("category", "usage_group", "is_active")
    search_fields = ("title", "alt_text", "source_name", "external_url")
    ordering = ("usage_group", "sort_order", "title")
    actions = [sync_library_images]
    fieldsets = (
        ("بيانات الصورة", {"fields": ("title", "alt_text", "category", "usage_group", "sort_order", "is_active")}),
        ("المصدر الأصلي", {"fields": ("source_name",)}),
        ("استبدال الصورة", {"fields": ("image", "external_url")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).defer("image_data")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("bulk-upload/", self.admin_site.admin_view(self.bulk_upload_view), name="core_libraryimage_bulk_upload"),
            path("bulk-replace/", self.admin_site.admin_view(self.bulk_replace_view), name="core_libraryimage_bulk_replace"),
        ]
        return custom_urls + urls

    def _read_uploaded_library_files(self, request):
        replacements = []
        for uploaded in request.FILES.getlist("images"):
            if _is_supported_library_image(uploaded.name):
                uploaded.seek(0)
                replacements.append((_safe_uploaded_image_name(uploaded.name), uploaded))

        zip_file = request.FILES.get("zip_file")
        if zip_file:
            with zipfile.ZipFile(zip_file) as archive:
                for member in sorted(archive.namelist()):
                    if member.endswith("/") or "__MACOSX" in member:
                        continue
                    filename = _safe_uploaded_image_name(member)
                    if not filename or not _is_supported_library_image(filename):
                        continue
                    replacements.append((filename, ContentFile(archive.read(member), name=filename)))
        return replacements

    def _read_replacement_files(self, request):
        return self._read_uploaded_library_files(request)

    def _unique_source_name(self, filename):
        safe_name = _safe_uploaded_image_name(filename) or "library-image.jpg"
        stem = PurePath(safe_name).stem or "library-image"
        suffix = PurePath(safe_name).suffix or ".jpg"
        candidate = safe_name
        counter = 1
        while LibraryImage.objects.filter(source_name=candidate).exists():
            candidate = f"{stem}-{counter}{suffix}"
            counter += 1
        return candidate

    def _next_sort_order(self, usage_group, offsets):
        if usage_group not in offsets:
            latest = (
                LibraryImage.objects.filter(usage_group=usage_group)
                .order_by("-sort_order")
                .values_list("sort_order", flat=True)
                .first()
            )
            offsets[usage_group] = (latest or 0) + 10
        value = offsets[usage_group]
        offsets[usage_group] += 10
        return value

    def _create_uploaded_library_images(self, uploads, distribution_mode, usage_group, category, activate_now):
        created = []
        usage_groups = [choice[0] for choice in LibraryImage.USAGE_GROUP_CHOICES]
        sort_offsets = {}
        for index, (filename, file_obj) in enumerate(uploads):
            target_group = usage_group if distribution_mode == "single" else usage_groups[index % len(usage_groups)]
            source_name = self._unique_source_name(filename)
            item = LibraryImage(
                source_name=source_name,
                title=default_title_for(source_name),
                alt_text=default_alt_for(source_name),
                category=category or default_category_for(source_name),
                usage_group=target_group,
                sort_order=self._next_sort_order(target_group, sort_offsets),
                is_active=activate_now,
            )
            file_obj.seek(0)
            item.image.save(source_name, file_obj, save=False)
            item.save()
            created.append(item)
        return created

    def bulk_upload_view(self, request):
        form = LibraryImageBulkUploadForm(request.POST or None, request.FILES or None)

        if request.method == "POST" and form.is_valid():
            uploads = self._read_uploaded_library_files(request)
            if not uploads:
                messages.error(request, "لم يتم العثور على صور صالحة للرفع. الصيغ المدعومة: JPG, PNG, WebP, AVIF, GIF.")
            else:
                created = self._create_uploaded_library_images(
                    uploads,
                    form.cleaned_data["distribution_mode"],
                    form.cleaned_data.get("usage_group") or "",
                    form.cleaned_data.get("category") or "general",
                    form.cleaned_data["activate_now"],
                )
                messages.success(request, f"تم رفع {len(created)} صورة جديدة وتوزيعها داخل مكتبة الموقع.")
                return redirect("admin:core_libraryimage_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": "رفع صور جديدة وتوزيعها على الموقع",
            "opts": self.model._meta,
            "form": form,
            "supported_extensions": ", ".join(sorted(ALLOWED_LIBRARY_IMAGE_EXTENSIONS)),
        }
        return TemplateResponse(request, "admin/core/libraryimage/bulk_upload.html", context)

    def _target_queryset_for_bulk_replace(self, scope):
        queryset = LibraryImage.objects.all()
        if scope == "active":
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("usage_group", "sort_order", "title", "pk")

    def _replace_library_images(self, targets, replacements, match_mode, clear_external_url):
        replaced = []
        skipped = []
        if match_mode == "source_name":
            by_name = {name.lower(): (name, file_obj) for name, file_obj in replacements}
            for item in targets:
                keys = [item.source_name.lower()] if item.source_name else []
                keys.append(PurePath(item.source_name or "").name.lower())
                match = next((by_name[key] for key in keys if key and key in by_name), None)
                if not match:
                    skipped.append(item)
                    continue
                filename, file_obj = match
                item.image.save(filename, file_obj, save=False)
                if clear_external_url:
                    item.external_url = ""
                item.save()
                replaced.append(item)
        else:
            for item, (filename, file_obj) in zip(targets, replacements):
                item.image.save(filename, file_obj, save=False)
                if clear_external_url:
                    item.external_url = ""
                item.save()
                replaced.append(item)
            skipped = list(targets[len(replaced) :])
        return replaced, skipped

    def bulk_replace_view(self, request):
        form = LibraryImageBulkReplaceForm(request.POST or None, request.FILES or None)
        targets = self._target_queryset_for_bulk_replace((request.POST or None) and request.POST.get("scope") or "active")
        target_count = targets.count()

        if request.method == "POST" and form.is_valid():
            replacements = self._read_replacement_files(request)
            if not replacements:
                messages.error(request, "لم يتم العثور على صور صالحة للاستبدال. الصيغ المدعومة: JPG, PNG, WebP, AVIF, GIF.")
            else:
                targets_list = list(self._target_queryset_for_bulk_replace(form.cleaned_data["scope"]))
                replaced, skipped = self._replace_library_images(
                    targets_list,
                    replacements,
                    form.cleaned_data["match_mode"],
                    form.cleaned_data["clear_external_url"],
                )
                messages.success(request, f"تم استبدال {len(replaced)} صورة مع الحفاظ على العناوين والأوصاف والتصنيفات السابقة.")
                if skipped:
                    messages.warning(request, f"لم يتم استبدال {len(skipped)} صورة لعدم وجود صورة مقابلة لها.")
                if len(replacements) > len(replaced):
                    messages.info(request, f"تم تجاهل {len(replacements) - len(replaced)} صورة زائدة عن عناصر المكتبة.")
                return redirect("admin:core_libraryimage_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": "استبدال صور مكتبة الموقع دفعة واحدة",
            "opts": self.model._meta,
            "form": form,
            "target_count": target_count,
            "supported_extensions": ", ".join(sorted(ALLOWED_LIBRARY_IMAGE_EXTENSIONS)),
        }
        return TemplateResponse(request, "admin/core/libraryimage/bulk_replace.html", context)

    def changelist_view(self, request, extra_context=None):
        image_dir = settings.BASE_DIR / "imge"
        for path in sorted(image_dir.glob("*")):
            if path.is_file():
                LibraryImage.objects.get_or_create(
                    source_name=path.name,
                    defaults={
                        "title": default_title_for(path.name),
                        "alt_text": default_alt_for(path.name),
                        "category": default_category_for(path.name),
                        "usage_group": default_usage_group_for(path.name),
                    },
                )
        return super().changelist_view(request, extra_context=extra_context)

    def preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="height:44px;border-radius:8px;" />', obj.image_url)
        return "-"


@admin.register(Page, site=admin_site)
class PageAdmin(SeoAdmin):
    list_display = ("title", "template_key", "resolved_path", "show_in_menu", "is_visible", "menu_order")
    list_filter = ("template_key", "show_in_menu", "is_visible")
    search_fields = ("title", "slug", "hero_title", "body")
    prepopulated_fields = {"slug": ("title",)}
    actions = [duplicate_pages]


@admin.register(City, site=admin_site)
class CityAdmin(SeoAdmin):
    list_display = ("name", "region", "is_active", "auto_generate_service_pages", "updated_at")
    list_filter = ("region", "is_active", "auto_generate_service_pages")
    search_fields = ("name", "slug", "short_description", "content")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("بيانات المدينة", {"fields": ("name", "slug", "region", "hero_title", "short_description", "content")}),
        ("ألوان المدينة", {"fields": ("primary_color", "secondary_color", "accent_color", "background_color")}),
        ("إعدادات الظهور", {"fields": ("is_active", "auto_generate_service_pages")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "meta_keywords")}),
    )


@admin.register(Service, site=admin_site)
class ServiceAdmin(SeoAdmin):
    list_display = ("title", "slug", "is_visible", "display_order", "updated_at")
    list_filter = ("is_visible",)
    search_fields = ("title", "slug", "description")
    filter_horizontal = ("cities",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CityServicePage, site=admin_site)
class CityServicePageAdmin(SeoAdmin):
    list_display = ("service", "city", "is_active", "updated_at")
    list_filter = ("is_active", "city", "service")
    search_fields = ("service__title", "city__name", "hero_title", "content")
    autocomplete_fields = ("city", "service")


@admin.register(BlogCategory, site=admin_site)
class BlogCategoryAdmin(SafeChangelistAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogTag, site=admin_site)
class BlogTagAdmin(SafeChangelistAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost, site=admin_site)
class BlogPostAdmin(SeoAdmin):
    list_display = ("title", "category", "status", "is_featured", "publish_at", "seo_indicator", "view_count")
    list_filter = ("status", "is_featured", "category", "tags")
    search_fields = ("title", "slug", "excerpt", "content")
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "publish_at"
    readonly_fields = ("seo_indicator", "view_count", "total_read_seconds", "reading_time_display")
    fieldsets = (
        ("المقال", {"fields": ("title", "slug", "category", "tags", "status", "is_featured", "publish_at")}),
        ("المحتوى", {"fields": ("excerpt", "content")}),
        ("الصورة الرئيسية", {"fields": ("featured_image", "featured_image_url")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "meta_keywords", "seo_indicator")}),
        ("التحليلات", {"fields": ("view_count", "total_read_seconds", "reading_time_display")}),
    )

    class Media:
        js = ("js/admin-blog-autosave.js",)

    def seo_indicator(self, obj):
        color = "#2e7d32" if obj.seo_score >= 70 else "#c62828"
        return format_html('<strong style="color:{};">{}%</strong>', color, obj.seo_score)

    seo_indicator.short_description = "تقييم SEO"

    def reading_time_display(self, obj):
        return f"{obj.reading_time_minutes} دقيقة"

    reading_time_display.short_description = "وقت القراءة"

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context=extra_context)
        except (OperationalError, ProgrammingError):
            self.message_user(
                request,
                "تعذر تحميل قائمة المقالات بسبب عدم توافق قاعدة البيانات. نفّذ migrate ثم أعد المحاولة.",
                level=messages.ERROR,
            )
            return redirect("admin:index")


@admin.register(BlogComment, site=admin_site)
class BlogCommentAdmin(SafeChangelistAdmin):
    list_display = ("author_name", "post", "is_approved", "is_spam", "created_at")
    list_filter = ("is_approved", "is_spam", "created_at")
    search_fields = ("author_name", "author_email", "content", "post__title")
    autocomplete_fields = ("post",)


@admin.register(Project, site=admin_site)
class ProjectAdmin(SeoAdmin):
    list_display = ("title", "category", "city", "is_visible", "updated_at")
    list_filter = ("category", "city", "is_visible")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProjectImageInline]


@admin.register(Lead, site=admin_site)
class LeadAdmin(SafeChangelistAdmin):
    list_display = ("name", "phone", "city_name", "status", "created_at")
    list_filter = ("status", "city_name")
    search_fields = ("name", "phone", "city_name", "message")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ConversionEvent, site=admin_site)
class ConversionEventAdmin(SafeChangelistAdmin):
    list_display = ("event_type", "label", "page_url", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("label", "page_url")
    readonly_fields = ("event_type", "label", "page_url", "metadata", "created_at", "updated_at")


@admin.register(Testimonial, site=admin_site)
class TestimonialAdmin(SafeChangelistAdmin):
    list_display = ("name", "city_name", "rating", "source", "is_verified", "is_visible", "display_order")
    list_filter = ("rating", "is_verified", "is_visible", "source")
    search_fields = ("name", "city_name", "review", "source")


@admin.register(NavigationItem, site=admin_site)
class NavigationItemAdmin(SafeChangelistAdmin):
    list_display = ("label", "route_name", "linked_page", "sort_order", "is_visible")
    list_filter = ("is_visible", "open_in_new_tab")
    search_fields = ("label", "route_name", "external_url")


@admin.register(AIContentGenerationLog, site=admin_site)
class AIContentGenerationLogAdmin(SafeChangelistAdmin):
    list_display = ("content_type", "mode", "status", "image_count", "target_object_type", "target_object_id", "created_at")
    list_filter = ("content_type", "mode", "status", "created_at")
    search_fields = ("prompt", "title_hint", "target_object_type", "error_message")
    readonly_fields = (
        "user",
        "content_type",
        "mode",
        "prompt",
        "title_hint",
        "image_count",
        "status",
        "input_payload",
        "generated_payload",
        "target_object_type",
        "target_object_id",
        "error_message",
        "created_at",
        "updated_at",
    )
