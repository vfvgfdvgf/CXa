from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image


def _save_variant(image, original_name, extension, image_format, quality=78):
    variant_name = f"{Path(original_name).with_suffix('')}.{extension}"
    buffer = BytesIO()
    save_kwargs = {"format": image_format, "quality": quality}
    if image_format == "WEBP":
        save_kwargs["method"] = 6
    try:
        image.save(buffer, **save_kwargs)
    except Exception:
        return ""
    try:
        if default_storage.exists(variant_name):
            default_storage.delete(variant_name)
        default_storage.save(variant_name, ContentFile(buffer.getvalue()))
        return variant_name
    except Exception:
        return ""


def optimize_uploaded_image(image_field, quality=82, max_size=(1600, 1600)):
    if not image_field:
        return

    try:
        image = Image.open(image_field)
    except Exception:
        return

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    try:
        image.thumbnail(max_size, Image.LANCZOS)
    except Exception:
        return

    buffer = BytesIO()
    try:
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
    except Exception:
        return

    upload_dir = str(Path(image_field.name).parent)
    stem = Path(image_field.name).stem if image_field.name else "image"
    name = f"{stem}.jpg" if upload_dir in ("", ".") else f"{upload_dir}/{stem}.jpg"
    image_field.save(name, ContentFile(buffer.getvalue()), save=False)
    _save_variant(image, name, "webp", "WEBP")
    _save_variant(image, name, "avif", "AVIF", quality=62)
