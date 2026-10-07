"""
Admin configuration — the content creation panel writers and editors use.

Goals:
- Writing an article should feel organized, not like a raw database form.
- Fields grouped into logical sections (content, SEO, workflow, safety).
- Easy filtering by status/category, search, and bulk publish actions.
- Rich text editor (CKEditor 5) for the article body.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Author,
    Category,
    MedicalReviewer,
    NewsletterSubscriber,
    Post,
    Tag,
)


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
admin.site.site_header = "Elevate Life — Content Panel"
admin.site.site_title = "Elevate Life Admin"
admin.site.index_title = "Manage your content"


# ---------------------------------------------------------------------------
# Author
# ---------------------------------------------------------------------------
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "credentials", "user", "post_count")
    search_fields = ("name", "credentials")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Identity", {"fields": ("name", "slug", "credentials", "user")}),
        ("Profile", {"fields": ("bio", "photo")}),
        ("Links", {"fields": ("website", "twitter", "linkedin")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


# ---------------------------------------------------------------------------
# Medical reviewer
# ---------------------------------------------------------------------------
@admin.register(MedicalReviewer)
class MedicalReviewerAdmin(admin.ModelAdmin):
    list_display = ("name", "credentials", "verification_url")
    search_fields = ("name", "credentials")


# ---------------------------------------------------------------------------
# Category & Tag
# ---------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "post_count")
    list_filter = ("parent",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
    )

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


# ---------------------------------------------------------------------------
# Post — the main creation screen
# ---------------------------------------------------------------------------
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status_badge",
        "category",
        "author",
        "post_type",
        "sensitivity",
        "published_at",
        "seo_score",
    )
    list_filter = ("status", "post_type", "sensitivity", "category", "created_at")
    search_fields = ("title", "excerpt", "focus_keyword")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "medical_reviewer")
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    list_per_page = 25
    readonly_fields = ("seo_score", "view_count", "created_at", "updated_at", "image_preview")
    actions = ("make_published", "make_draft", "submit_for_medical_review")

    fieldsets = (
        ("Content", {
            "fields": (
                "title", "slug", "excerpt", "editor_note", "body",
                "featured_image", "image_preview", "featured_image_alt",
            ),
        }),
        ("Classification", {
            "fields": ("category", "tags", "author", "post_type"),
        }),
        ("Workflow", {
            "fields": ("status", "published_at", "notify_subscribers"),
        }),
        ("Trust & sources (E-E-A-T)", {
            "fields": ("medical_reviewer", "reviewed_at", "sources"),
            "description": "Health content should be reviewed and cite reputable sources.",
        }),
        ("Safety", {
            "fields": ("sensitivity", "content_warning"),
        }),
        ("SEO", {
            "fields": (
                "meta_title", "meta_description", "focus_keyword",
                "canonical_url", "seo_score",
            ),
            "classes": ("collapse",),
        }),
        ("Engagement & housekeeping", {
            "fields": ("allow_comments", "view_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # -- Display helpers --
    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "draft": "#9ca3af",
            "in_review": "#f59e0b",
            "medical_review": "#8b5cf6",
            "scheduled": "#3b82f6",
            "published": "#10b981",
        }
        color = colors.get(obj.status, "#9ca3af")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height:150px;border-radius:6px;" />',
                obj.featured_image.url,
            )
        return "No image uploaded yet."

    # -- Bulk actions --
    @admin.action(description="Publish selected posts now")
    def make_published(self, request, queryset):
        count = 0
        for post in queryset:
            post.status = Post.Status.PUBLISHED
            if post.published_at is None:
                post.published_at = timezone.now()
            post.save()
            count += 1
        self.message_user(request, f"{count} post(s) published.")

    @admin.action(description="Move selected posts back to draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"{updated} post(s) moved to draft.")

    @admin.action(description="Send selected posts to medical review")
    def submit_for_medical_review(self, request, queryset):
        updated = queryset.update(status=Post.Status.MEDICAL_REVIEW)
        self.message_user(request, f"{updated} post(s) sent to medical review.")


# ---------------------------------------------------------------------------
# Newsletter subscribers
# ---------------------------------------------------------------------------
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "source", "subscribed_at")
    list_filter = ("is_active", "subscribed_at")
    search_fields = ("email",)
    readonly_fields = ("subscribed_at",)
