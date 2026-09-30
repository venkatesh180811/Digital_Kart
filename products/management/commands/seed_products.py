import io
import itertools
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from PIL import Image, ImageDraw, ImageFont

from categories.models import Category, SubCategory, Brand
from products.models import Product, ProductImage

User = get_user_model()

# Deterministic randomness so re-running (without --flush) gives consistent, idempotent results.
random.seed(42)

CATEGORY_DEFS = {
    "Mobiles": {
        "icon": "fa-solid fa-mobile-screen",
        "color": (27, 31, 59),       # ink navy
        "subcats": ["Smartphones", "Feature Phones"],
        "adjectives": ["Nova", "Pulse", "Edge", "Air", "Max", "Prime", "Flex", "Spark", "Volt", "Zen",
                       "Comet", "Halo", "Drift", "Blaze", "Aria", "Ion", "Nexa"],
        "noun": "Smartphone",
        "mrp_range": (8999, 54999),
        "discount_range": (10, 30),
        "specs": lambda: {
            "Display": random.choice(["6.1\" AMOLED", "6.5\" AMOLED, 120Hz", "6.7\" AMOLED, 120Hz"]),
            "RAM": random.choice(["4GB", "6GB", "8GB", "12GB"]),
            "Storage": random.choice(["64GB", "128GB", "256GB"]),
            "Battery": random.choice(["4500mAh", "5000mAh", "5500mAh"]),
            "Camera": random.choice(["48MP Dual", "50MP Triple", "64MP Triple"]),
        },
    },
    "Laptops": {
        "icon": "fa-solid fa-laptop",
        "color": (38, 43, 82),       # ink-700
        "subcats": ["Ultrabooks", "Gaming Laptops"],
        "adjectives": ["AeroBook", "StrikeForce", "CoreLine", "SwiftEdge", "TitanBook", "FlexPro",
                       "ProBook", "UltraLite", "PowerRun", "SteelBook", "ClearView", "RapidBook",
                       "SlimTech", "WorkMate", "EdgeRunner", "CoreMax", "ByteLine"],
        "noun": "Laptop",
        "mrp_range": (42999, 139999),
        "discount_range": (10, 25),
        "specs": lambda: {
            "Processor": random.choice(["6-core", "8-core", "12-core", "16-core"]),
            "RAM": random.choice(["8GB", "16GB", "32GB"]),
            "Storage": random.choice(["256GB SSD", "512GB SSD", "1TB SSD"]),
            "Display": random.choice(["13.3\" FHD", "14\" FHD IPS", "15.6\" FHD", "15.6\" 165Hz"]),
            "Weight": random.choice(["1.2kg", "1.4kg", "1.8kg", "2.1kg"]),
        },
    },
    "Audio": {
        "icon": "fa-solid fa-headphones",
        "color": (0, 168, 145),      # teal-600
        "subcats": ["Headphones", "Speakers"],
        "adjectives": ["BassPro", "EchoDot", "SoundWave", "AuraBeat", "ClearTone", "PulseBeat", "SonicX",
                       "DeepBass", "TrueSound", "AirBeat", "LoopSound", "VividTone", "EchoMax", "BoomBeat",
                       "CrispSound", "AmpLite", "ResoWave"],
        "noun": "Audio Device",
        "mrp_range": (1499, 12999),
        "discount_range": (15, 45),
        "specs": lambda: {
            "Battery Life": random.choice(["12 hours", "24 hours", "30 hours", "40 hours"]),
            "Connectivity": random.choice(["Bluetooth 5.0", "Bluetooth 5.2", "Bluetooth 5.3", "Wi-Fi + Bluetooth"]),
            "ANC": random.choice(["Yes", "No"]),
        },
    },
    "Fashion": {
        "icon": "fa-solid fa-shirt",
        "color": (255, 93, 93),      # coral-500
        "subcats": ["Men's Footwear", "Women's Footwear"],
        "adjectives": ["TrailRunner", "Elegance", "UrbanStep", "CloudWalk", "ClassicFit", "FlexSole",
                       "StrideOne", "GraceHeel", "MetroWalk", "ComfortLine", "SwiftStep", "PrimeStride",
                       "EasyStep", "BoldWalk", "LightFoot", "PaceMaker", "TrueFit"],
        "noun": "Footwear",
        "mrp_range": (1499, 5999),
        "discount_range": (20, 50),
        "specs": lambda: {
            "Material": random.choice(["Breathable Mesh", "Synthetic Leather", "Genuine Leather", "Canvas"]),
            "Sole": random.choice(["EVA Cushioned", "Rubber", "Memory Foam"]),
            "Sizes": random.choice(["UK 3-8", "UK 6-11", "UK 5-10"]),
        },
    },
    "Home & Kitchen": {
        "icon": "fa-solid fa-blender",
        "color": (232, 156, 0),      # amber-600
        "subcats": ["Appliances", "Cookware"],
        "adjectives": ["ChefPro", "NonStick", "QuickCook", "HomeStyle", "KitchenLite", "FreshMix",
                       "SteamMaster", "GrillMate", "BrewPoint", "CrispAir", "PurePress", "WarmServe",
                       "EasyCook", "DailyChef", "PrepPro", "CookEase", "TasteMate"],
        "noun": "Kitchen Essential",
        "mrp_range": (1299, 8999),
        "discount_range": (15, 40),
        "specs": lambda: {
            "Power": random.choice(["800W", "1000W", "1400W", "1800W"]),
            "Capacity": random.choice(["1.5L", "2.5L", "4.5L", "6L"]),
            "Warranty": random.choice(["1 Year", "2 Years"]),
        },
    },
    "Watches": {
        "icon": "fa-solid fa-clock",
        "color": (18, 20, 43),       # ink-900
        "subcats": ["Smartwatches", "Analog Watches"],
        "adjectives": ["PulseFit", "Heritage", "ChronoLite", "ActiveTrack", "TimeCraft", "FitLoop",
                       "ClassicHour", "SmartBeat", "UrbanTime", "VitalTrack", "EliteHour", "SwiftTrack",
                       "DailyTrack", "MetroTime", "CoreBeat", "PulseHour", "TrueTime"],
        "noun": "Watch",
        "mrp_range": (1999, 8999),
        "discount_range": (20, 45),
        "specs": lambda: {
            "Display": random.choice(["1.4\" AMOLED", "1.8\" AMOLED", "Analog Dial"]),
            "Battery Life": random.choice(["2 days", "7 days", "14 days", "N/A (Analog)"]),
            "Water Resistance": random.choice(["3 ATM", "5 ATM", "10 ATM"]),
        },
    },
}

BRAND_NAMES = [
    "Zenfone", "Nimbus", "Orbit", "Kraft", "Velora", "Pulse",
    "Meridian", "Solace", "Aether", "Northline",
]

PRODUCTS_PER_CATEGORY = 17  # 6 categories x 17 = 102 total -> every brand still lands on 10+


def _text_color_for_background(rgb):
    """Pick black or white text depending on background brightness for readability."""
    r, g, b = rgb
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return (20, 20, 30) if brightness > 150 else (255, 255, 255)


def generate_placeholder_image(product_name, brand_name, bg_rgb, size=(600, 600)):
    """
    Generates an original, generated-from-scratch placeholder image (solid brand-colored
    card + wrapped product name). No external/copyrighted imagery is used or fetched.
    """
    img = Image.new("RGB", size, bg_rgb)
    draw = ImageDraw.Draw(img)
    text_color = _text_color_for_background(bg_rgb)

    try:
        title_font = ImageFont.load_default(size=34)
        brand_font = ImageFont.load_default(size=22)
    except TypeError:
        # Older Pillow without the `size` kwarg on load_default
        title_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    # Simple word-wrap for the product name within the canvas width
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

    # Thin border accent
    draw.rectangle([(0, 0), (size[0] - 1, size[1] - 1)], outline=text_color, width=2)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


class Command(BaseCommand):
    help = "Seeds DigitalKart with 10+ products per category AND 10+ products per brand, each with a generated placeholder image."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-images", action="store_true",
            help="Skip generating placeholder images (faster, text-only seed).",
        )

    def handle(self, *args, **options):
        skip_images = options["skip_images"]

        seller, created = User.objects.get_or_create(
            email="demo-seller@digitalkart.example",
            defaults={"username": "demo_seller", "is_seller": True, "is_email_verified": True},
        )
        if created:
            seller.set_password("DemoSeller@123")
            seller.save()
            self.stdout.write(self.style.SUCCESS("Created demo seller account (demo-seller@digitalkart.example / DemoSeller@123)"))
        elif not seller.is_seller:
            seller.is_seller = True
            seller.save(update_fields=["is_seller"])

        # ---------------- Categories & Subcategories ----------------
        categories = {}
        subcats_by_category = {}
        for name, meta in CATEGORY_DEFS.items():
            cat, _ = Category.objects.get_or_create(name=name, defaults={"icon": meta["icon"]})
            categories[name] = cat
            subcats_by_category[name] = []
            for sub_name in meta["subcats"]:
                sub, _ = SubCategory.objects.get_or_create(category=cat, name=sub_name)
                subcats_by_category[name].append(sub)

        # ---------------- Brands ----------------
        brands = {}
        for b in BRAND_NAMES:
            brand, _ = Brand.objects.get_or_create(name=b)
            brands[b] = brand

        # Cycle brands so every brand gets an (almost) equal share across the whole catalog.
        brand_cycle = itertools.cycle(BRAND_NAMES)

        created_count = 0
        skipped_count = 0
        images_created = 0

        for cat_name, meta in CATEGORY_DEFS.items():
            category = categories[cat_name]
            subcats = subcats_by_category[cat_name]

            for i in range(PRODUCTS_PER_CATEGORY):
                adjective = meta["adjectives"][i % len(meta["adjectives"])]
                brand_name = next(brand_cycle)
                brand = brands[brand_name]
                subcategory = subcats[i % len(subcats)]

                name = f"{brand_name} {adjective} {meta['noun']}"

                mrp = random.randint(*meta["mrp_range"])
                discount_pct = random.randint(*meta["discount_range"])
                price = round(mrp * (100 - discount_pct) / 100, -1) or mrp
                stock = random.choice([0, 5, 12, 20, 35, 50, 80])
                is_featured = i % 4 == 0
                is_best_seller = i % 3 == 0

                product, was_created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        "seller": seller, "category": category, "subcategory": subcategory, "brand": brand,
                        "description": (
                            f"The {name} combines dependable performance with everyday practicality — "
                            f"a solid pick in the {subcategory.name.lower()} lineup."
                        ),
                        "specifications": meta["specs"](),
                        "mrp": mrp, "price": price, "stock": stock,
                        "is_active": True, "is_featured": is_featured, "is_best_seller": is_best_seller,
                    },
                )
                if was_created:
                    created_count += 1
                else:
                    skipped_count += 1

                if not skip_images and not product.images.exists():
                    image_bytes = generate_placeholder_image(name, brand_name, meta["color"])
                    filename = f"{product.slug}.png"
                    product_image = ProductImage(product=product, alt_text=name, is_primary=True, sort_order=0)
                    product_image.image.save(filename, ContentFile(image_bytes), save=True)
                    images_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {len(categories)} categories, {len(brands)} brands. "
            f"{created_count} new products created, {skipped_count} already existed and were left untouched. "
            f"{images_created} placeholder images generated."
        ))

        self.stdout.write("")
        self.stdout.write("Products per category:")
        for cat_name, cat in categories.items():
            self.stdout.write(f"  {cat_name}: {Product.objects.filter(category=cat).count()}")

        self.stdout.write("")
        self.stdout.write("Products per brand:")
        for brand_name, brand in brands.items():
            self.stdout.write(f"  {brand_name}: {Product.objects.filter(brand=brand).count()}")

        if skip_images:
            self.stdout.write(self.style.WARNING(
                "\nImages were skipped (--skip-images). Add real product photos later via /admin/, "
                "or re-run without --skip-images to backfill placeholders for any product missing one."
            ))
        else:
            self.stdout.write(
                "\nPlaceholder images are generated locally (brand-colored cards with the product name) — "
                "no external or copyrighted images were downloaded. Swap them for real photos any time via "
                "/admin/ under Products > (select product) > Product images."
            )
