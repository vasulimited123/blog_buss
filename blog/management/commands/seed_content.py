"""
Seed the site with the real, full-length launch content.

Article data lives in _content_batch1.py, _content_batch2.py, ... — this
command imports every batch it can find and loads them all. Re-running is
safe (update_or_create keyed on slug refreshes existing posts).

    python manage.py seed_content

Options:
    --list    Show what would be seeded (titles + categories) without writing.

NOTE: These are strong, ad-safe DRAFTS for a YMYL health niche. Have a
qualified professional review and personalise before publishing publicly.
"""

import importlib

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Author, Category, MedicalReviewer, Post, Tag

from ._content_helpers import render_body, DEFAULT_SOURCES, STANDARD_WARNING


# Category name -> description (created if missing).
CATEGORY_DESCRIPTIONS = {
    "Men's Health": "Physical and mental wellbeing topics relevant to men.",
    "Women's Health": "Physical and mental wellbeing topics relevant to women.",
    "Relationship & Intimacy": "Building and maintaining closeness in relationships.",
    "Sexual Wellness": "Evidence-based education on sexual health and wellbeing.",
    "Relationship Psychology": "The psychology behind attraction, desire, and connection.",
    "Marriage & Long-term": "Navigating intimacy and connection in long-term partnerships.",
}

# Author name -> credentials.
AUTHOR_CREDENTIALS = {
    "Dr. Ananya Rao": "PhD, Clinical Psychologist",
    "Dr. Vikram Mehta": "MD, Family Medicine",
}

REVIEWER = ("Dr. Sunita Kapoor", "MD, Psychiatrist & Certified Sex Therapist")

# Batch modules to load, in order. Add new batches here as they're created.
BATCH_MODULES = [
    "blog.management.commands._content_batch1",
    "blog.management.commands._content_batch2",
    "blog.management.commands._content_batch3",
    "blog.management.commands._content_batch4",
    "blog.management.commands._content_batch5",
    "blog.management.commands._content_batch6",
]


def load_all_articles():
    """Import every available batch module and concatenate its ARTICLES."""
    articles = []
    for mod_path in BATCH_MODULES:
        try:
            mod = importlib.import_module(mod_path)
        except ModuleNotFoundError:
            continue  # batch not created yet — skip silently
        articles.extend(getattr(mod, "ARTICLES", []))
    return articles


class Command(BaseCommand):
    help = "Seed the site with the real, full-length launch content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--list", action="store_true",
            help="List articles that would be seeded, without writing.",
        )

    def handle(self, *args, **options):
        articles = load_all_articles()

        if options["list"]:
            self.stdout.write(f"{len(articles)} article(s) available:")
            for a in articles:
                self.stdout.write(f"  [{a['category']}] {a['title']}")
            return

        if not articles:
            self.stdout.write(self.style.WARNING("No article batches found."))
            return

        # Ensure categories.
        categories = {}
        for name, desc in CATEGORY_DESCRIPTIONS.items():
            c, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})
            categories[name] = c

        # Ensure authors.
        authors = {}
        for name, creds in AUTHOR_CREDENTIALS.items():
            a, _ = Author.objects.get_or_create(name=name, defaults={"credentials": creds})
            authors[name] = a

        reviewer, _ = MedicalReviewer.objects.get_or_create(
            name=REVIEWER[0], defaults={"credentials": REVIEWER[1]}
        )

        created = updated = 0
        for a in articles:
            category = categories.get(a["category"])
            if category is None:
                category, _ = Category.objects.get_or_create(name=a["category"])
                categories[a["category"]] = category

            author = authors.get(a["author"])
            if author is None:
                author, _ = Author.objects.get_or_create(name=a["author"])
                authors[a["author"]] = author

            body_html = render_body(a["body"])

            post, was_created = Post.objects.update_or_create(
                slug=a["slug"],
                defaults={
                    "title": a["title"],
                    "excerpt": a["excerpt"],
                    "body": body_html,
                    "author": author,
                    "category": category,
                    "post_type": a.get("post_type", "standard"),
                    "status": Post.Status.PUBLISHED,
                    "published_at": timezone.now(),
                    "medical_reviewer": reviewer,
                    "reviewed_at": timezone.now().date(),
                    "sensitivity": a.get("sensitivity", "mature"),
                    "content_warning": a.get("content_warning", STANDARD_WARNING),
                    "focus_keyword": a.get("focus_keyword", ""),
                    "meta_title": a.get("meta_title", "")[:70],
                    "meta_description": a.get("meta_description", a["excerpt"])[:160],
                    "featured_image_alt": a["title"],
                    "sources": a.get("sources", DEFAULT_SOURCES),
                },
            )

            # Tags
            for tag_name in a.get("tags", []):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                post.tags.add(tag)

            if was_created:
                created += 1
            else:
                updated += 1

        total = Post.published.count()
        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, updated {updated}. "
            f"{total} published post(s) total."
        ))
        # Per-category summary
        for name, cat in categories.items():
            self.stdout.write(f"  {name}: {cat.posts.count()} post(s)")
