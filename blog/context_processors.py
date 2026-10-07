"""
Context processors — inject site-wide data into every template.
"""

from django.conf import settings

from .models import Post


def popular_posts(request):
    """Top published posts by view count, available in all templates.

    Kept small (5) and lightweight. Skips the admin to avoid unnecessary
    queries there.
    """
    if request.path.startswith("/admin"):
        return {}
    return {
        "popular_posts": (
            Post.published.select_related("category")
            .order_by("-view_count")[:5]
        )
    }


def adsense(request):
    """Expose AdSense config to all templates.

    `adsense_client_id` is empty until configured, so ads stay off by default.
    """
    if request.path.startswith("/admin"):
        return {}
    return {
        "adsense_client_id": settings.ADSENSE_CLIENT_ID,
        "adsense_slots": settings.ADSENSE_SLOTS,
    }
