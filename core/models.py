import mimetypes
from pathlib import PurePath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import models
from django.templatetags.static import static

from .image_utils import optimize_uploaded_image


def normalize_image_field_name(name, upload_prefix):
    if not name:
        return name

    clean_name = str(name).replace("\\", "/").lstrip("/")
    media_prefix = settings.MEDIA_URL.strip("/")
    if media_prefix and clean_name.startswith(f"{media_prefix}/"):
        clean_name = clean_name[len(media_prefix) + 1 :]

    upload_prefix = upload_prefix.strip("/")
    repeated_prefix = f"{upload_prefix}/{upload_prefix}/"
    while clean_name.startswith(repeated_prefix):
        clean_name = f"{upload_prefix}/{clean_name[len(repeated_prefix):]}"

    return clean_name


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SeoFields(models.Model):
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)

    class Meta:
        abstract = True


class SiteSettings(TimeStampedModel):
    site_name = models.CharField(max_length=200, default="لاندسكيب المملكة")
    contact_phone = models.CharField(max_length=20, default="0507555824")
    whatsapp_number = models.CharField(max_length=20, default="0507555824")
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    tagline = models.CharField(max_length=255, default="خدمات متكاملة في جميع مدن السعودية")
    homepage_meta_title = models.CharField(
        max_length=255,
        default="لاندسكيب وتنسيق حدائق وأشجار ونخيل في السعودية",
    )
    homepage_meta_description = models.TextField(
        default="شركة سعودية متخصصة في تصميم الحدائق وتنفيذ اللاندسكيب وزراعة الأشجار والنخيل وأنظمة الري في جميع مدن المملكة."
    )
    homepage_hero_background = models.ImageField(upload_to="site-settings/", blank=True, null=True)
    homepage_hero_background_url = models.URLField(blank=True)
    blog_hero_background = models.ImageField(upload_to="site-settings/", blank=True, null=True)
    blog_hero_background_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default="#83643b")
    secondary_color = models.CharField(max_length=7, default="#0f5b54")
    accent_color = models.CharField(max_length=7, default="#c6a56d")
    background_color = models.CharField(max_length=7, default="#f7f1e8")
    text_color = models.CharField(max_length=7, default="#1c1915")
    footer_text = models.TextField(blank=True)
    service_highlights = models.TextField(
        default="تصميم حدائق\nلاندسكيب\nأشجار ونخيل\nشبوك\nمظلات",
        help_text="أدخل خدمة في كل سطر لتظهر في محتوى الموقع وتهيئة SEO.",
    )
    seo_default_keywords = models.CharField(
        max_length=500,
        blank=True,
        default="لاندسكيب, تصميم حدائق, تنسيق حدائق, أشجار, نخيل, مظلات, شبوك, السعودية",
        help_text="كلمات مفتاحية افتراضية مفصولة بفواصل.",
    )
    seo_default_description = models.TextField(
        blank=True,
        default="شركة متخصصة في خدمات اللاندسكيب وتنسيق الحدائق والأشجار والنخيل والمظلات والشبوك في السعودية.",
    )
    seo_twitter_handle = models.CharField(
        max_length=50,
        blank=True,
        help_text="مثال: @yourbrand",
    )
    default_og_image = models.ImageField(upload_to="site-settings/", blank=True, null=True)
    default_og_image_url = models.URLField(blank=True)
    business_type = models.CharField(max_length=80, default="LocalBusiness")
    legal_name = models.CharField(max_length=220, blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    address_locality = models.CharField(max_length=120, blank=True)
    address_region = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=40, blank=True)
    address_country = models.CharField(max_length=2, default="SA")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    opening_hours = models.TextField(blank=True, help_text="سطر لكل يوم بصيغة schema.org مثل Mo-Sa 08:00-20:00")
    area_served = models.TextField(blank=True, help_text="سطر لكل مدينة أو منطقة خدمة")
    same_as_links = models.TextField(blank=True, help_text="سطر لكل رابط اجتماعي أو ملف تعريفي خارجي")
    google_search_console_property = models.URLField(blank=True, help_text="مثال: https://example.com/ أو sc-domain:example.com")
    google_service_account_json = models.TextField(blank=True, help_text="JSON لحساب الخدمة الخاص بـ Google Search Console. احفظه فقط في بيئة موثوقة.")
    ai_seo_enabled = models.BooleanField(default=True, help_text="تشغيل منظومة تحسين SEO اليومية.")
    ai_seo_auto_apply = models.BooleanField(default=False, help_text="تطبيق تعديلات الذكاء الاصطناعي تلقائيًا عند تشغيل أمر الأتمتة.")
    ai_seo_research_queries = models.TextField(
        blank=True,
        help_text="استعلامات بحث إضافية، سطر لكل استعلام. تستخدمها الأتمتة اليومية مع Search Console.",
    )
    class Meta:
        verbose_name = "إعدادات الموقع"
        verbose_name_plural = "إعدادات الموقع"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        if self.homepage_hero_background:
            optimize_uploaded_image(self.homepage_hero_background, max_size=(2200, 1600))
        if self.blog_hero_background:
            optimize_uploaded_image(self.blog_hero_background, max_size=(2200, 1600))
        if self.default_og_image:
            optimize_uploaded_image(self.default_og_image, max_size=(2200, 1600))
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    @property
    def homepage_hero_background_resolved(self):
        if self.homepage_hero_background:
            return self.homepage_hero_background.url
        return self.homepage_hero_background_url

    @property
    def blog_hero_background_resolved(self):
        if self.blog_hero_background:
            return self.blog_hero_background.url
        return self.blog_hero_background_url

    @property
    def default_og_image_resolved(self):
        if self.default_og_image:
            return self.default_og_image.url
        return self.default_og_image_url

    @property
    def service_highlights_list(self):
        return [item.strip() for item in (self.service_highlights or "").splitlines() if item.strip()]

    @property
    def opening_hours_list(self):
        return [item.strip() for item in (self.opening_hours or "").splitlines() if item.strip()]

    @property
    def area_served_list(self):
        return [item.strip() for item in (self.area_served or "").splitlines() if item.strip()]

    @property
    def same_as_list(self):
        links = [self.instagram_url, self.facebook_url, self.x_url, self.linkedin_url]
        links += [item.strip() for item in (self.same_as_links or "").splitlines() if item.strip()]
        seen = set()
        output = []
        for link in links:
            if link and link not in seen:
                seen.add(link)
                output.append(link)
        return output


class ContactNumber(TimeStampedModel):
    site_settings = models.ForeignKey(
        SiteSettings,
        on_delete=models.CASCADE,
        related_name="contact_numbers",
        default=1,
    )
    label = models.CharField(max_length=80, default="رقم التواصل")
    phone = models.CharField(max_length=20)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    enable_whatsapp = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "رقم تواصل"
        verbose_name_plural = "أرقام التواصل"
        ordering = ["-is_primary", "sort_order", "id"]

    def __str__(self):
        return f"{self.label} - {self.phone}"

    @property
    def whatsapp_digits(self):
        digits = "".join(char for char in (self.phone or "") if char.isdigit())
        if digits.startswith("0"):
            digits = f"966{digits[1:]}"
        return digits


class PageMedia(models.Model):
    PAGE_CHOICES = [
        ("home", "الرئيسية"),
        ("about", "من نحن"),
        ("services", "الخدمات"),
        ("portfolio", "المشاريع"),
        ("cities", "المدن"),
        ("contact", "اتصل بنا"),
        ("blog", "المدونة"),
        ("blog_post", "تفاصيل المقال"),
        ("city", "صفحة المدينة"),
        ("city_service", "صفحة خدمة داخل مدينة"),
    ]

    page = models.CharField(max_length=30, choices=PAGE_CHOICES)
    section = models.CharField(
        max_length=50,
        default="hero",
        help_text="مثال: hero, gallery, secondary",
    )
    folder = models.ForeignKey(
        "MediaFolder",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="images",
    )
    title = models.CharField(max_length=150)
    alt_text = models.CharField(max_length=180, blank=True)
    image = models.ImageField(upload_to="site-media/", blank=True, null=True)
    external_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "صورة صفحة"
        verbose_name_plural = "صور الصفحات"
        ordering = ["page", "section", "sort_order", "-created_at"]

    def __str__(self):
        return f"{self.get_page_display()} - {self.title}"

    def clean(self):
        if not self.image and not self.external_url:
            raise ValidationError("يجب رفع صورة من الجهاز أو إدخال رابط صورة خارجي.")

    def save(self, *args, **kwargs):
        if self.image:
            optimize_uploaded_image(self.image)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return self.external_url

    @property
    def display_alt(self):
        return self.alt_text or self.title


class LibraryImage(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("shades", "تصميم حدائق"),
        ("fencing", "لاندسكيب صلب"),
        ("palm", "أشجار ونخيل"),
        ("traditional", "أنظمة ري وصيانة"),
        ("general", "عام"),
    ]
    USAGE_GROUP_CHOICES = [
        ("home_hero", "هيرو الرئيسية"),
        ("home_gallery", "معرض الرئيسية"),
        ("home_banners", "بنرات الرئيسية"),
        ("about", "من نحن"),
        ("services", "الخدمات"),
        ("portfolio", "الأعمال"),
        ("cities", "المدن"),
        ("blog", "المدونة"),
        ("blog_post", "تفاصيل المقال"),
        ("contact", "اتصل بنا"),
        ("city", "صفحة المدينة"),
        ("city_service", "خدمة داخل مدينة"),
    ]

    source_name = models.CharField(max_length=255, unique=True, blank=True, help_text="اسم الملف الأصلي داخل مجلد imge")
    title = models.CharField(max_length=180)
    alt_text = models.CharField(max_length=220, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    usage_group = models.CharField(max_length=30, choices=USAGE_GROUP_CHOICES, default="home_gallery")
    image = models.ImageField(upload_to="library-images/", blank=True, null=True)
    image_data = models.BinaryField(blank=True, null=True, editable=False)
    image_content_type = models.CharField(max_length=80, blank=True, editable=False)
    image_filename = models.CharField(max_length=255, blank=True, editable=False)
    external_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "صورة مكتبة الموقع"
        verbose_name_plural = "صور مكتبة الموقع"
        ordering = ["usage_group", "sort_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image:
            self.image.name = normalize_image_field_name(self.image.name, "library-images")
            optimize_uploaded_image(self.image)
            self.store_image_in_database()
        super().save(*args, **kwargs)

    def store_image_in_database(self):
        if not self.image:
            return

        data = b""
        try:
            self.image.open("rb")
            data = self.image.read()
            self.image.close()
        except Exception:
            try:
                with default_storage.open(self.image.name, "rb") as image_file:
                    data = image_file.read()
            except Exception:
                data = b""

        if not data:
            return

        filename = PurePath(self.image.name).name or self.source_name or "library-image.jpg"
        content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
        self.image_data = data
        self.image_filename = filename
        self.image_content_type = content_type

    @property
    def image_url(self):
        if self.image_data and self.pk:
            filename = self.image_filename or PurePath(self.image.name or self.source_name or "image.jpg").name
            return f"/media-db/library-images/{self.pk}/{filename}"
        if self.image:
            return self.image.url
        if self.external_url:
            return self.external_url
        if self.source_name:
            return static(self.source_name)
        return ""

    @property
    def display_alt(self):
        return self.alt_text or self.title


class MediaFolder(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name="children")

    class Meta:
        verbose_name = "مجلد وسائط"
        verbose_name_plural = "مجلدات الوسائط"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Page(TimeStampedModel, SeoFields):
    TEMPLATE_CHOICES = [
        ("home", "الرئيسية"),
        ("about", "من نحن"),
        ("services", "الخدمات"),
        ("portfolio", "الأعمال"),
        ("cities", "المدن"),
        ("blog", "المدونة"),
        ("contact", "اتصل بنا"),
        ("custom", "صفحة مخصصة"),
    ]

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    menu_title = models.CharField(max_length=120, blank=True)
    hero_title = models.CharField(max_length=255, blank=True)
    intro_text = models.TextField(blank=True)
    body = models.TextField(blank=True)
    template_key = models.CharField(max_length=30, choices=TEMPLATE_CHOICES, default="custom")
    custom_url = models.CharField(max_length=180, blank=True, help_text="مثال: offers أو about-us")
    is_visible = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True)
    menu_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "صفحة"
        verbose_name_plural = "الصفحات"
        ordering = ["menu_order", "title"]

    def __str__(self):
        return self.title

    @property
    def resolved_path(self):
        return self.custom_url or self.slug


class City(TimeStampedModel, SeoFields):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    region = models.CharField(max_length=120, blank=True)
    short_description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    hero_title = models.CharField(max_length=255, blank=True)
    primary_color = models.CharField(max_length=7, blank=True)
    secondary_color = models.CharField(max_length=7, blank=True)
    accent_color = models.CharField(max_length=7, blank=True)
    background_color = models.CharField(max_length=7, blank=True)
    is_active = models.BooleanField(default=True)
    auto_generate_service_pages = models.BooleanField(default=True)

    class Meta:
        verbose_name = "مدينة"
        verbose_name_plural = "المدن"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(TimeStampedModel, SeoFields):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=140, unique=True)
    short_title = models.CharField(max_length=180, blank=True)
    description = models.TextField()
    benefits = models.TextField(blank=True, help_text="أدخل ميزة في كل سطر")
    image = models.ImageField(upload_to="services/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    cities = models.ManyToManyField(City, blank=True, related_name="services")
    is_visible = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "خدمة"
        verbose_name_plural = "الخدمات"
        ordering = ["display_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image:
            optimize_uploaded_image(self.image)
        super().save(*args, **kwargs)

    @property
    def benefits_list(self):
        return [item.strip() for item in self.benefits.splitlines() if item.strip()]

    @property
    def resolved_image(self):
        if self.image:
            return self.image.url
        return self.image_url


class CityServicePage(TimeStampedModel, SeoFields):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="city_services")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="city_pages")
    hero_title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    benefits = models.TextField(blank=True, help_text="أدخل ميزة في كل سطر")
    is_active = models.BooleanField(default=True)
    custom_slug = models.SlugField(max_length=160, blank=True)

    class Meta:
        verbose_name = "خدمة داخل مدينة"
        verbose_name_plural = "الخدمات داخل المدن"
        unique_together = ("city", "service")
        ordering = ["city__name", "service__title"]

    def __str__(self):
        return f"{self.service.title} - {self.city.name}"

    def save(self, *args, **kwargs):
        if not self.hero_title:
            self.hero_title = f"{self.service.title} في {self.city.name}"
        if not self.custom_slug:
            self.custom_slug = self.service.slug
        super().save(*args, **kwargs)

    @property
    def benefits_list(self):
        return [item.strip() for item in self.benefits.splitlines() if item.strip()]


class BlogCategory(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        verbose_name = "تصنيف مقال"
        verbose_name_plural = "تصنيفات المقالات"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogTag(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        verbose_name = "وسم"
        verbose_name_plural = "الوسوم"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogPost(TimeStampedModel, SeoFields):
    STATUS_CHOICES = [
        ("draft", "مسودة"),
        ("published", "منشور"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to="blog/", blank=True, null=True)
    featured_image_url = models.URLField(blank=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name="posts")
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_featured = models.BooleanField(default=False)
    publish_at = models.DateTimeField(blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    total_read_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "مقال"
        verbose_name_plural = "المقالات"
        ordering = ["-publish_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.featured_image:
            optimize_uploaded_image(self.featured_image)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.featured_image:
            return self.featured_image.url
        return self.featured_image_url

    @property
    def is_published(self):
        return self.status == "published"

    @property
    def reading_time_minutes(self):
        words = len((self.content or "").split())
        return max(1, round(words / 200))

    @property
    def seo_score(self):
        score = 0
        if self.meta_title:
            score += 30
        if self.meta_description:
            score += 25
        if self.meta_keywords:
            score += 15
        if len((self.content or "").split()) > 300:
            score += 20
        if self.featured_image or self.featured_image_url:
            score += 10
        return min(score, 100)

    @property
    def avg_read_seconds(self):
        return self.total_read_seconds // self.view_count if self.view_count else 0


class BlogComment(TimeStampedModel):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=120)
    author_email = models.EmailField(blank=True)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)

    class Meta:
        verbose_name = "تعليق"
        verbose_name_plural = "التعليقات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} - {self.post.title}"

    def save(self, *args, **kwargs):
        text = (self.content or "").lower()
        if text.count("http") > 1 or text.count("www.") > 1:
            self.is_spam = True
            self.is_approved = False
        super().save(*args, **kwargs)


class Project(TimeStampedModel, SeoFields):
    CATEGORY_CHOICES = [
        ("shades", "تصميم حدائق"),
        ("fencing", "لاندسكيب صلب"),
        ("palm", "أشجار ونخيل"),
        ("traditional", "أنظمة ري وصيانة"),
    ]

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name="projects")
    description = models.TextField()
    featured_image = models.ImageField(upload_to="projects/", blank=True, null=True)
    featured_image_url = models.URLField(blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "مشروع"
        verbose_name_plural = "المشاريع"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.featured_image:
            optimize_uploaded_image(self.featured_image)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.featured_image:
            return self.featured_image.url
        return self.featured_image_url


class ProjectImage(TimeStampedModel):
    TYPE_CHOICES = [
        ("before", "قبل"),
        ("after", "بعد"),
        ("gallery", "معرض"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="gallery")
    title = models.CharField(max_length=150, blank=True)
    image_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="gallery")
    image = models.ImageField(upload_to="projects/gallery/", blank=True, null=True)
    external_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "صورة مشروع"
        verbose_name_plural = "صور المشاريع"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title or f"صورة {self.project.title}"

    def save(self, *args, **kwargs):
        if self.image:
            optimize_uploaded_image(self.image)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return self.external_url


class Lead(TimeStampedModel):
    STATUS_CHOICES = [
        ("new", "جديد"),
        ("contacted", "تم التواصل"),
        ("closed", "مغلق"),
    ]

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    city_name = models.CharField(max_length=120, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "طلب عميل"
        verbose_name_plural = "طلبات العملاء"
        ordering = ["status", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.phone}"


class ConversionEvent(TimeStampedModel):
    EVENT_CHOICES = [
        ("whatsapp", "واتساب"),
        ("call", "اتصال"),
        ("calculator", "حاسبة تكلفة"),
        ("exit_intent", "نافذة خروج"),
    ]

    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    page_url = models.URLField(blank=True)
    label = models.CharField(max_length=160, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "حدث تحويل"
        verbose_name_plural = "تتبع التحويلات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at:%Y-%m-%d %H:%M}"


class Testimonial(TimeStampedModel):
    name = models.CharField(max_length=120)
    city_name = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    review = models.TextField()
    source = models.CharField(max_length=120, blank=True, help_text="مثال: Google Business Profile أو عميل مباشر")
    source_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "تقييم عميل"
        verbose_name_plural = "تقييمات العملاء"
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.name


class NavigationItem(TimeStampedModel):
    label = models.CharField(max_length=120)
    route_name = models.CharField(max_length=80, blank=True, help_text="مثل home أو contact")
    external_url = models.URLField(blank=True)
    linked_page = models.ForeignKey(Page, on_delete=models.SET_NULL, blank=True, null=True, related_name="nav_items")
    sort_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)

    class Meta:
        verbose_name = "عنصر قائمة"
        verbose_name_plural = "عناصر القائمة"
        ordering = ["sort_order", "label"]

    def __str__(self):
        return self.label

    def clean(self):
        targets = [bool(self.route_name), bool(self.external_url), bool(self.linked_page)]
        if sum(targets) == 0:
            raise ValidationError("يجب تحديد رابط داخلي أو خارجي أو صفحة مرتبطة.")


class AIContentGenerationLog(TimeStampedModel):
    CONTENT_TYPE_CHOICES = [
        ("blog_post", "مقال"),
        ("service", "خدمة"),
        ("city", "مدينة"),
        ("page", "صفحة"),
        ("city_service", "خدمة داخل مدينة"),
    ]
    MODE_CHOICES = [
        ("create", "إنشاء"),
        ("update", "تحديث"),
    ]
    STATUS_CHOICES = [
        ("pending", "قيد التنفيذ"),
        ("completed", "مكتمل"),
        ("failed", "فشل"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="ai_content_logs")
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPE_CHOICES)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="create")
    prompt = models.TextField()
    title_hint = models.CharField(max_length=255, blank=True)
    image_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    input_payload = models.JSONField(default=dict, blank=True)
    generated_payload = models.JSONField(default=dict, blank=True)
    target_object_type = models.CharField(max_length=100, blank=True)
    target_object_id = models.PositiveIntegerField(blank=True, null=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "سجل إنشاء محتوى بالذكاء الاصطناعي"
        verbose_name_plural = "سجلات إنشاء المحتوى بالذكاء الاصطناعي"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_content_type_display()} - {self.get_mode_display()} - {self.created_at:%Y-%m-%d %H:%M}"


class SiteVerification(TimeStampedModel):
    PROVIDER_CHOICES = [
        ("google", "Google Search Console"),
        ("bing", "Bing Webmaster Tools"),
        ("yandex", "Yandex"),
        ("custom", "كود مخصص"),
    ]
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default="google")
    name = models.CharField(max_length=120, default="google-site-verification")
    content = models.CharField(max_length=500, blank=True)
    raw_html = models.TextField(blank=True, help_text="استخدمه فقط لكود meta كامل موثوق.")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "كود تحقق"
        verbose_name_plural = "أكواد التحقق"
        ordering = ["provider", "name"]

    def __str__(self):
        return f"{self.get_provider_display()} - {self.name}"


class SearchConsoleQuery(TimeStampedModel):
    query = models.CharField(max_length=500)
    page = models.URLField(blank=True)
    country = models.CharField(max_length=10, blank=True)
    device = models.CharField(max_length=30, blank=True)
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    ctr = models.FloatField(default=0)
    position = models.FloatField(default=0)
    date_from = models.DateField(blank=True, null=True)
    date_to = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "كلمة من Search Console"
        verbose_name_plural = "كلمات Search Console"
        ordering = ["-impressions", "position"]
        indexes = [models.Index(fields=["query", "page"])]

    def __str__(self):
        return f"{self.query} - {self.impressions}"


class SEOReportIssue(TimeStampedModel):
    SEVERITY_CHOICES = [("high", "مرتفع"), ("medium", "متوسط"), ("low", "منخفض")]
    STATUS_CHOICES = [("open", "مفتوح"), ("fixed", "تم الإصلاح"), ("ignored", "متجاهل")]
    page_url = models.CharField(max_length=500)
    title = models.CharField(max_length=255)
    issue_type = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    details = models.TextField(blank=True)
    suggested_fix = models.TextField(blank=True)
    detected_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مشكلة SEO"
        verbose_name_plural = "تقرير SEO اليومي"
        ordering = ["status", "-severity", "-detected_at"]

    def __str__(self):
        return f"{self.title} - {self.page_url}"


class LegacyRedirect(TimeStampedModel):
    old_path = models.CharField(max_length=255, unique=True, help_text="مثال: /riyadh/shades/")
    target_path = models.CharField(max_length=255, help_text="مثال: /riyadh/landscaping/")
    is_permanent = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    hit_count = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "تحويل رابط قديم"
        verbose_name_plural = "تحويلات الروابط القديمة"
        ordering = ["old_path"]

    def __str__(self):
        return f"{self.old_path} -> {self.target_path}"


class SEOAutomationRun(TimeStampedModel):
    STATUS_CHOICES = [
        ("running", "قيد التشغيل"),
        ("completed", "مكتمل"),
        ("failed", "فشل"),
        ("skipped", "متجاوز"),
    ]
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    search_console_result = models.JSONField(default=dict, blank=True)
    local_seo_result = models.JSONField(default=dict, blank=True)
    redirects_result = models.JSONField(default=dict, blank=True)
    issues_before = models.PositiveIntegerField(default=0)
    issues_after = models.PositiveIntegerField(default=0)
    ai_requested = models.BooleanField(default=False)
    ai_applied = models.BooleanField(default=False)
    ai_result = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "تشغيل أتمتة SEO"
        verbose_name_plural = "تشغيلات أتمتة SEO"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.get_status_display()} - {self.started_at:%Y-%m-%d %H:%M}"
