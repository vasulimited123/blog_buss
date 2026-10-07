"""
Remove the 26 earlier generic articles (from seed_content), leaving only the
10 flagship story-driven articles (from seed_powerful) and their categories,
authors, tags, and reviewer.

    python manage.py remove_generic          # shows what would be deleted
    python manage.py remove_generic --confirm   # actually deletes

Works by deleting the exact slugs the seed_content batches created, so it can
never touch the flagship posts.
"""

import importlib

from django.core.management.base import BaseCommand

from blog.models import Post

SEED_CONTENT_BATCHES = [
    "blog.management.commands._content_batch1",
    "blog.management.commands._content_batch2",
    "blog.management.commands._content_batch3",
    "blog.management.commands._content_batch4",
    "blog.management.commands._content_batch5",
    "blog.management.commands._content_batch6",
]


def generic_slugs():
    slugs = []
    for mod_path in SEED_CONTENT_BATCHES:
        try:
            mod = importlib.import_module(mod_path)
        except ModuleNotFoundError:
            continue
        for a in getattr(mod, "ARTICLES", []):
            slugs.append(a["slug"])
    return slugs


class Command(BaseCommand):
    help = "Remove the earlier generic seed_content articles."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true",
                            help="Actually delete (otherwise dry-run).")

    def handle(self, *args, **options):
        slugs = generic_slugs()
        qs = Post.objects.filter(slug__in=slugs)
        count = qs.count()

        if not options["confirm"]:
            self.stdout.write(f"DRY RUN — would delete {count} generic post(s):")
            for p in qs:
                self.stdout.write(f"  - {p.slug}")
            self.stdout.write("\nRun again with --confirm to delete.")
            return

        deleted, _ = qs.delete()
        remaining = Post.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {count} generic post(s). {remaining} post(s) remain."
        ))
