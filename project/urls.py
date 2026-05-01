from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from core import views as core_views
from core.admin_site import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("core.urls")),
]

handler404 = core_views.custom_404

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
