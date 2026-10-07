"""
Seed the 10 flagship, story-driven articles.

These are crafted to be human, warm, and genuinely useful — the opposite of
generic AI filler. Each includes an `editor_note` placeholder: a prompt in
[[ ]] brackets telling YOU what personal reflection to add. Replace each
placeholder with your own real words in the admin to make it authentic.

    python manage.py seed_powerful

Idempotent (update_or_create on slug).
"""

import importlib

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Author, Category, Post, Tag
from ._content_helpers import render_body


CATEGORY_DESCRIPTIONS = {
    "Men's Health": "Physical and mental wellbeing topics relevant to men.",
    "Women's Health": "Physical and mental wellbeing topics relevant to women.",
    "Relationship & Intimacy": "Building and maintaining closeness in relationships.",
    "Sexual Wellness": "Evidence-based education on sexual health and wellbeing.",
    "Relationship Psychology": "The psychology behind attraction, desire, and connection.",
    "Marriage & Long-term": "Navigating intimacy and connection in long-term partnerships.",
    "Chronic Health": "Living well with long-term health conditions like diabetes and arthritis.",
}

# Single real author — the founder of Elevate Life.
# Credentials intentionally left blank for now (user will add later).
AUTHOR_NAME = "Dr. R.S. Agrawal"
AUTHOR_CREDENTIALS = ""
AUTHOR_BIO = (
    "Dr. R.S. Agrawal is the founder of Elevate Life. He writes to make honest, "
    "compassionate guidance on relationships, intimacy, and emotional wellbeing "
    "accessible to everyone — without shame or judgment."
)

# No medical reviewer is attributed until a real professional is in place.
REVIEWER = None

BATCH_MODULES = [
    "blog.management.commands._powerful_batch1",
    "blog.management.commands._powerful_batch2",
    "blog.management.commands._powerful_batch3",
    "blog.management.commands._powerful_batch4",
    "blog.management.commands._powerful_batch5",
]


def load_all_articles():
    articles = []
    for mod_path in BATCH_MODULES:
        try:
            mod = importlib.import_module(mod_path)
        except ModuleNotFoundError:
            continue
        articles.extend(getattr(mod, "ARTICLES", []))
    return articles


class Command(BaseCommand):
    help = "Seed the 10 flagship, story-driven articles."

    def add_arguments(self, parser):
        parser.add_argument("--list", action="store_true", help="List without writing.")

    def handle(self, *args, **options):
        articles = load_all_articles()

        if options["list"]:
            self.stdout.write(f"{len(articles)} flagship article(s):")
            for a in articles:
                self.stdout.write(f"  [{a['category']}] {a['title']}")
            return

        if not articles:
            self.stdout.write(self.style.WARNING("No flagship batches found yet."))
            return

        categories = {}
        for name, desc in CATEGORY_DESCRIPTIONS.items():
            c, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})
            categories[name] = c

        # Single real author for all content.
        author, _ = Author.objects.get_or_create(
            name=AUTHOR_NAME,
            defaults={"credentials": AUTHOR_CREDENTIALS, "bio": AUTHOR_BIO},
        )
        # Keep the bio/credentials current on re-runs.
        author.credentials = AUTHOR_CREDENTIALS
        author.bio = AUTHOR_BIO
        author.save()

        created = updated = 0
        for a in articles:
            category = categories[a["category"]]
            post, was_created = Post.objects.update_or_create(
                slug=a["slug"],
                defaults={
                    "title": a["title"],
                    "excerpt": a["excerpt"],
                    "editor_note": a.get("editor_note", ""),
                    "body": render_body(a["body"]),
                    "author": author,
                    "category": category,
                    "post_type": a.get("post_type", "story"),
                    "status": Post.Status.PUBLISHED,
                    "published_at": timezone.now(),
                    "medical_reviewer": None,
                    "sensitivity": a.get("sensitivity", "mature"),
                    "content_warning": a.get("content_warning",
                        "This article discusses adult relationship and wellbeing topics."),
                    "focus_keyword": a.get("focus_keyword", ""),
                    "meta_title": a.get("meta_title", "")[:70],
                    "meta_description": a.get("meta_description", a["excerpt"])[:160],
                    "featured_image_alt": a["title"],
                    "sources": a.get("sources", []),
                },
            )
            for tag_name in a.get("tags", []):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                post.tags.add(tag)
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, updated {updated}. "
            f"{Post.published.count()} published post(s) total."
        ))
        self.stdout.write("\nEditor notes are written and ready. You can refine any of "
                          "them in your own words later via the admin.")
