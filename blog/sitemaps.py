"""
XML sitemaps for search engines.

Django's sitemap framework paginates automatically at 50,000 URLs per file
and generates a sitemap index — so this scales to thousands of posts without
extra work.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Post, Tag


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Post.published.all()

    def lastmod(self, obj):
        return obj.updated_at

    # location() uses obj.get_absolute_url() by default.


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Category.objects.all()


class TagSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.4
    protocol = "https"

    def items(self):
        return Tag.objects.all()


class StaticViewSitemap(Sitemap):
    """Static informational pages."""
    changefreq = "monthly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return [
            "blog:home",
            "blog:category_index",
            "blog:about",
            "blog:contact",
            "blog:privacy",
            "blog:terms",
            "blog:disclaimer",
            "blog:affiliate_disclosure",
        ]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "posts": PostSitemap,
    "categories": CategorySitemap,
    "tags": TagSitemap,
    "static": StaticViewSitemap,
}
