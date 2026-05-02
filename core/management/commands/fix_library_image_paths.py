from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.cache import cache
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
        stored_count = 0

        for item in LibraryImage.objects.exclude(image="").exclude(image__isnull=True).iterator():
            current_name = item.image.name
            normalized_name = normalize_image_field_name(current_name, "library-images")
            source_name = normalize_image_field_name(f"library-images/{item.source_name}", "library-images") if item.source_name else ""
            if source_name and not default_storage.exists(normalized_name) and default_storage.exists(source_name):
                normalized_name = source_name

            changed_path = current_name != normalized_name

            if changed_path:
                fixed_count += 1
                self.stdout.write(f"{current_name} -> {normalized_name}")

            item.image.name = normalized_name
            if not item.image_data:
                item.store_image_in_database()
                if item.image_data:
                    stored_count += 1

            if not changed_path and not item.image_data:
                continue

            if not dry_run:
                LibraryImage.objects.filter(pk=item.pk).update(
                    image=normalized_name,
                    image_data=item.image_data,
                    image_stored=bool(item.image_data),
                    image_content_type=item.image_content_type,
                    image_filename=item.image_filename,
                    updated_at=timezone.now(),
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run complete. Paths to fix: {fixed_count}. Images to store in database: {stored_count}"))
        else:
            cache.delete("library:records")
            self.stdout.write(self.style.SUCCESS(f"Library image paths fixed: {fixed_count}. Images stored in database: {stored_count}"))
