"""
Blog data models.

Design goals (from the planning docs):
- Editorial workflow: draft -> in review -> medical review -> scheduled -> published
- SEO fields on every post (meta title/description, canonical)
- E-E-A-T signals: named Author + optional MedicalReviewer, cited sources
- Sensitivity levels + content warnings (health/wellness niche)
- Post "type" so different kinds of posts can use different templates
- Newsletter subscriber capture
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from django_ckeditor_5.fields import CKEditor5Field


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def unique_slugify(instance, value, slug_field="slug", max_length=None):
    """Generate a slug for `instance` that is unique for its model.

    Two different names can slugify to the same value (e.g. "Marriage & Intimacy"
    and "Marriage Intimacy" both -> "marriage-intimacy"). This appends -2, -3, …
    until the slug is unique, avoiding IntegrityError on the unique slug column.
    """
    base = slugify(value) or "item"
    if max_length:
        base = base[:max_length]
    ModelClass = instance.__class__
    slug = base
    n = 2
    qs = ModelClass.objects.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(**{slug_field: slug}).exists():
        suffix = f"-{n}"
        trimmed = base[: (max_length - len(suffix))] if max_length else base
        slug = f"{trimmed}{suffix}"
        n += 1
    return slug


# ---------------------------------------------------------------------------
# Managers
# ---------------------------------------------------------------------------
class PublishedPostManager(models.Manager):
    """Returns only posts that are live (published and past their publish time)."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status="published", published_at__lte=timezone.now())
        )


# ---------------------------------------------------------------------------
# Author (public-facing writer profile) and Medical Reviewer (E-E-A-T)
# ---------------------------------------------------------------------------
class Author(models.Model):
    """A public byline. Optionally linked to a login (User) account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="author_profile",
        help_text="Optional: link this byline to a login account.",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    credentials = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. 'Certified Sex Therapist', 'MA Psychology'.",
    )
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="authors/", blank=True, null=True)

    # Social / trust links
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=170)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:author", kwargs={"slug": self.slug})


class MedicalReviewer(models.Model):
    """A qualified professional who reviews/approves health content.

    Kept separate from Author because a reviewer signs off on accuracy
    but is usually not the person who wrote the article.
    """

    name = models.CharField(max_length=150)
    credentials = models.CharField(
        max_length=200,
        help_text="e.g. 'MD, Urologist', 'MBBS, DPM Psychiatry'.",
    )
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="reviewers/", blank=True, null=True)
    verification_url = models.URLField(
        blank=True,
        help_text="Link to their clinic/practice/registration for verification.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Medical reviewer"
        verbose_name_plural = "Medical reviewers"

    def __str__(self):
        return f"{self.name} ({self.credentials})"


# ---------------------------------------------------------------------------
# Taxonomy: Category (nestable) and Tag
# ---------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        help_text="Optional parent for a nested category.",
    )
    # SEO for the category archive page
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=120)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:category", kwargs={"slug": self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=80)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag", kwargs={"slug": self.slug})


# ---------------------------------------------------------------------------
# Post — the core content model
# ---------------------------------------------------------------------------
class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "in_review", "In review (editor)"
        MEDICAL_REVIEW = "medical_review", "Medical review"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"

    class PostType(models.TextChoices):
        STANDARD = "standard", "Standard article"
        LISTICLE = "listicle", "Listicle"
        STORY = "story", "Personal story"
        COMPARISON = "comparison", "Comparison"
        QUIZ = "quiz", "Quiz"

    class Sensitivity(models.TextChoices):
        GENERAL = "general", "General audience"
        MATURE = "mature", "Mature (18+ recommended)"
        SENSITIVE = "sensitive", "Sensitive topic (trigger warning)"

    # --- Core content ---
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short summary shown in listings and used as a fallback meta description.",
    )
    editor_note = models.TextField(
        blank=True,
        help_text="A short, personal 'note from the editor' shown in a highlighted box "
                  "at the top of the article. Your authentic voice — a real reflection, "
                  "observation, or reassurance. This is what makes the piece human.",
    )
    body = CKEditor5Field(config_name="article", blank=True)
    featured_image = models.ImageField(upload_to="posts/%Y/%m/", blank=True, null=True)
    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Describe the image for accessibility and SEO.",
    )

    # --- Relationships ---
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")

    # --- Post type (drives which template renders it) ---
    post_type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        default=PostType.STANDARD,
    )

    # --- Editorial workflow ---
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the post goes/went live. For scheduled posts, a future time.",
    )

    # --- E-E-A-T / trust (health niche) ---
    medical_reviewer = models.ForeignKey(
        MedicalReviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_posts",
    )
    reviewed_at = models.DateField(null=True, blank=True)
    sources = models.JSONField(
        default=list,
        blank=True,
        help_text="List of citation URLs backing the claims in this article.",
    )

    # --- Sensitivity / safety ---
    sensitivity = models.CharField(
        max_length=20,
        choices=Sensitivity.choices,
        default=Sensitivity.GENERAL,
    )
    content_warning = models.CharField(max_length=300, blank=True)

    # --- SEO ---
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="Overrides the title in search results. 50-60 chars ideal.",
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Search snippet. 150-160 chars ideal.",
    )
    canonical_url = models.URLField(
        blank=True,
        help_text="Set only if this content also lives at another URL.",
    )
    focus_keyword = models.CharField(
        max_length=100,
        blank=True,
        help_text="Main keyword this article targets (used by the SEO scorer later).",
    )
    seo_score = models.PositiveSmallIntegerField(default=0)

    # --- Engagement / housekeeping ---
    view_count = models.PositiveIntegerField(default=0)
    allow_comments = models.BooleanField(default=True)
    notify_subscribers = models.BooleanField(
        default=False,
        help_text="Email subscribers when this post is published.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()          # default: all posts (admin, drafts)
    published = PublishedPostManager()  # only live posts (public views)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title, max_length=220)
        # When marked published without an explicit time, stamp it now.
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            kwargs={"category": self.category.slug, "slug": self.slug},
        )

    @property
    def is_live(self):
        """True if the post should be visible to the public right now."""
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    @property
    def template_name(self):
        """Template used to render this post, based on its type."""
        return f"blog/post_types/{self.post_type}.html"


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Where they subscribed from (e.g. post slug, homepage).",
    )

    class Meta:
        ordering = ["-subscribed_at"]
        verbose_name = "Newsletter subscriber"

    def __str__(self):
        return self.email
