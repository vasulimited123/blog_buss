"""
Root URL configuration.

Admin panel is mounted at /admin/.
CKEditor 5 upload endpoints at /ckeditor5/.
The public website URLs live in the blog app and are added in a later step.
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from blog.sitemaps import sitemaps
from blog.views import robots_txt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),

    # SEO endpoints
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),

    # Public site URLs (blog app).
    path("", include("blog.urls")),
]

# Serve uploaded media during development only.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
