from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import LibraryImage, normalize_image_field_name


class Command(BaseCommand):
    help = "Normalize duplicated LibraryImage media paths stored in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving updates.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        fixed_count = 0

        for item in LibraryImage.objects.exclude(image="").exclude(image__isnull=True).iterator():
            current_name = item.image.name
            normalized_name = normalize_image_field_name(current_name, "library-images")
            if current_name == normalized_name:
                continue

            fixed_count += 1
            self.stdout.write(f"{current_name} -> {normalized_name}")
            if not dry_run:
                LibraryImage.objects.filter(pk=item.pk).update(
                    image=normalized_name,
                    updated_at=timezone.now(),
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run complete. Paths to fix: {fixed_count}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Library image paths fixed: {fixed_count}"))
