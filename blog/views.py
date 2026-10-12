"""
Public-facing views (server-rendered Django templates, no API/React).

All public post queries go through Post.published so drafts and
scheduled-but-not-yet-live posts never leak to visitors.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Author, Category, NewsletterSubscriber, Post, Tag

POSTS_PER_PAGE = 12


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------
def home(request):
    live_posts = Post.published.select_related("author", "category")

    context = {
        "featured_posts": live_posts[:5],
        "latest_posts": live_posts[:9],
        "trending_posts": live_posts.order_by("-view_count")[:5],
        "categories": Category.objects.filter(parent__isnull=True),
    }
    return render(request, "blog/home.html", context)


# ---------------------------------------------------------------------------
# Post detail
# ---------------------------------------------------------------------------
def post_detail(request, category, slug):
    post = get_object_or_404(
        Post.published.select_related("author", "category", "medical_reviewer"),
        slug=slug,
        category__slug=category,
    )

    # Count a view (atomic; avoids race conditions).
    Post.published.filter(pk=post.pk).update(view_count=F("view_count") + 1)

    # Related posts: same category, excluding this one.
    related_posts = (
        Post.published.filter(category=post.category)
        .exclude(pk=post.pk)
        .select_related("author", "category")[:4]
    )

    context = {
        "post": post,
        "related_posts": related_posts,
    }
    # Choose template by post type, with a safe fallback to standard.
    return render(request, [post.template_name, "blog/post_types/standard.html"], context)


# ---------------------------------------------------------------------------
# Category archive
# ---------------------------------------------------------------------------
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    post_list = (
        Post.published.filter(category=category)
        .select_related("author", "category")
    )
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "category": category,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
    }
    return render(request, "blog/category.html", context)


# ---------------------------------------------------------------------------
# Tag archive
# ---------------------------------------------------------------------------
def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    post_list = (
        Post.published.filter(tags=tag)
        .select_related("author", "category")
    )
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "tag": tag,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
    }
    return render(request, "blog/tag.html", context)


# ---------------------------------------------------------------------------
# Author profile
# ---------------------------------------------------------------------------
def author_detail(request, slug):
    author = get_object_or_404(Author, slug=slug)
    post_list = (
        Post.published.filter(author=author)
        .select_related("author", "category")
    )
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "author": author,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
    }
    return render(request, "blog/author.html", context)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def search(request):
    query = (request.GET.get("q") or "").strip()
    results = Post.published.none()

    if query:
        results = (
            Post.published.filter(
                Q(title__icontains=query)
                | Q(excerpt__icontains=query)
                | Q(body__icontains=query)
                | Q(tags__name__icontains=query)
            )
            .select_related("author", "category")
            .distinct()
        )

    paginator = Paginator(results, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "query": query,
        "page_obj": page_obj,
        "posts": page_obj.object_list,
        "result_count": paginator.count,
    }
    return render(request, "blog/search.html", context)


# ---------------------------------------------------------------------------
# All categories index
# ---------------------------------------------------------------------------
def category_index(request):
    context = {
        "categories": Category.objects.filter(parent__isnull=True),
    }
    return render(request, "blog/category_index.html", context)


# ---------------------------------------------------------------------------
# Newsletter subscribe
# ---------------------------------------------------------------------------
@require_POST
def newsletter_subscribe(request):
    email = (request.POST.get("email") or "").strip().lower()
    source = request.POST.get("source", "")

    if not email:
        messages.error(request, "Please enter a valid email address.")
        return redirect(request.META.get("HTTP_REFERER", "blog:home"))

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={"source": source},
    )
    if created:
        messages.success(request, "Thanks for subscribing! Check your inbox.")
    else:
        messages.info(request, "You're already subscribed.")

    return redirect("blog:subscribed")


def subscribed(request):
    return render(request, "blog/subscribed.html")


# ---------------------------------------------------------------------------
# Static informational pages
# ---------------------------------------------------------------------------
def about(request):
    return render(request, "blog/pages/about.html")


def contact(request):
    return render(request, "blog/pages/contact.html")


def privacy(request):
    return render(request, "blog/pages/privacy.html")


def terms(request):
    return render(request, "blog/pages/terms.html")


def disclaimer(request):
    return render(request, "blog/pages/disclaimer.html")


def affiliate_disclosure(request):
    return render(request, "blog/pages/affiliate_disclosure.html")


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------
def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /ckeditor5/",
        "Disallow: /search/",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# ---------------------------------------------------------------------------
# ads.txt — declares authorized ad sellers (Google AdSense requirement).
# Serves a valid line only once your AdSense publisher ID is configured.
# ---------------------------------------------------------------------------
def ads_txt(request):
    from django.conf import settings

    client_id = settings.ADSENSE_CLIENT_ID  # e.g. "ca-pub-1234567890123456"
    if client_id:
        # Strip the "ca-" prefix for the ads.txt publisher id, per Google's format.
        pub_id = client_id.replace("ca-", "", 1)
        content = f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"
    else:
        content = "# ads.txt — add your AdSense publisher line after approval.\n"
    return HttpResponse(content, content_type="text/plain")
