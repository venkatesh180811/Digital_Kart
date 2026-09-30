import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from products.models import Product, ProductImage
from categories.models import Category


CATEGORY_COLORS = {
    "Mobiles": (27, 31, 59),
    "Laptops": (38, 43, 82),
    "Audio": (0, 168, 145),
    "Fashion": (255, 93, 93),
    "Home & Kitchen": (232, 156, 0),
    "Watches": (18, 20, 43),
}


def _text_color_for_background(rgb):
    r, g, b = rgb
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return (20, 20, 30) if brightness > 150 else (255, 255, 255)


def generate_placeholder_image(product_name, brand_name, bg_rgb, size=(600, 600)):
    img = Image.new("RGB", size, bg_rgb)
    draw = ImageDraw.Draw(img)
    text_color = _text_color_for_background(bg_rgb)

    try:
        title_font = ImageFont.load_default(size=34)
        brand_font = ImageFont.load_default(size=22)
    except TypeError:
        title_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    max_width = size[0] - 80
    words = product_name.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=title_font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    line_height = 44
    total_text_height = len(lines) * line_height
    y = (size[1] - total_text_height) / 2 - 20

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        draw.text(((size[0] - w) / 2, y), line, fill=text_color, font=title_font)
        y += line_height

    brand_text = brand_name.upper()
    bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    w = bbox[2] - bbox[0]
    draw.text(((size[0] - w) / 2, size[1] - 70), brand_text, fill=text_color, font=brand_font)

    draw.rectangle([(0, 0), (size[0] - 1, size[1] - 1)], outline=text_color, width=2)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


class Command(BaseCommand):
    help = "Generates placeholder images for products that don't have any."

    def handle(self, *args, **options):
        products = Product.objects.filter(images__isnull=True)
        count = products.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("All products already have images."))
            return

        self.stdout.write(f"Found {count} products without images. Generating placeholders...")

        for product in products:
            color = CATEGORY_COLORS.get(product.category.name, (100, 100, 100))
            brand_name = product.brand.name if product.brand else "DigitalKart"
            image_bytes = generate_placeholder_image(product.name, brand_name, color)
            filename = f"{product.slug}.png"
            product_image = ProductImage(
                product=product,
                alt_text=product.name,
                is_primary=True,
                sort_order=0,
            )
            product_image.image.save(filename, ContentFile(image_bytes), save=True)

        self.stdout.write(self.style.SUCCESS(f"Done. Added placeholder images to {count} products."))
