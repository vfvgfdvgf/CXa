from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .local_seo import ensure_local_service_pages, seed_default_cities_and_services


@override_settings(DEBUG=True, ALLOWED_HOSTS=["localhost", "testserver"], SECURE_SSL_REDIRECT=False)
class PublicPageSmokeTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        seed_default_cities_and_services()
        ensure_local_service_pages()

    def test_public_pages_load(self):
        urls = [
            reverse("home"),
            reverse("about"),
            reverse("services"),
            reverse("portfolio"),
            reverse("cities"),
            reverse("blog"),
            reverse("contact"),
            reverse("robots_txt"),
            reverse("sitemap_xml"),
            reverse("city_detail", kwargs={"city_slug": "riyadh"}),
            reverse(
                "city_service_detail",
                kwargs={"city_slug": "riyadh", "service_slug": "landscaping"},
            ),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)


class ProjectConfigurationTests(SimpleTestCase):
    def test_sqlite_is_the_local_fallback_database(self):
        self.assertEqual(settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3")

    def test_root_image_assets_are_available_to_staticfiles(self):
        sample_image = "WhatsApp Image 2026-03-21 at 6.34.14 PM.jpeg"
        self.assertIsNotNone(finders.find(sample_image))
