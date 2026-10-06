import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Assets directory directly in root folder: d:\smart_store_project\assets\products
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Color palettes for department categories
CATEGORY_COLORS = {
    "Grocery & Staples": ("#fef3c7", "#d97706"),
    "Dairy, Milk & Paneer": ("#dcfce7", "#16a34a"),
    "Fresh Vegetables & Greens": ("#ecfdf5", "#059669"),
    "Fresh Fruits & Berries": ("#fef2f2", "#dc2626"),
    "Bakery & Breakfast": ("#fff7ed", "#ea580c"),
    "Snacks, Chips & Namkeen": ("#fef9c3", "#ca8a04"),
    "Chocolates, Sweets & Biscuits": ("#fce7f3", "#db2777"),
    "Tea, Coffee & Beverages": ("#e0f2fe", "#0284c7"),
    "Personal Care & Grooming": ("#f3e8ff", "#9333ea"),
    "Girls Accessories & Makeup": ("#fce7f3", "#e11d48"),
    "Tech & Mobile Accessories": ("#dbeafe", "#2563eb"),
    "Health, Wellness & Supplements": ("#d1fae5", "#0d9488"),
    "All Medicines & First Aid": ("#fee2e2", "#e11d48"),
    "Household & Cleaning": ("#e2e8f0", "#475569"),
    "Home & Kitchenware": ("#f0f9ff", "#0369a1"),
    "Stationery & Office Supplies": ("#fef9c3", "#a16207"),
    "Clothing & Fashion": ("#fce4ec", "#c2185b"),
    "Seasonal, Pooja & Festival": ("#fff3e0", "#e65100"),
    "Ready to Eat": ("#fff8e1", "#f57f17"),
    "Sports & Fitness": ("#e8f5e9", "#2e7d32"),
}

CATEGORY_EMOJIS = {
    "Grocery & Staples": "🌾",
    "Dairy, Milk & Paneer": "🥛",
    "Fresh Vegetables & Greens": "🥦",
    "Fresh Fruits & Berries": "🍎",
    "Bakery & Breakfast": "🍞",
    "Snacks, Chips & Namkeen": "🍟",
    "Chocolates, Sweets & Biscuits": "🍫",
    "Tea, Coffee & Beverages": "🥤",
    "Personal Care & Grooming": "🧼",
    "Girls Accessories & Makeup": "💄",
    "Tech & Mobile Accessories": "🔌",
    "Health, Wellness & Supplements": "💊",
    "All Medicines & First Aid": "🩹",
    "Household & Cleaning": "🧹",
    "Home & Kitchenware": "🍳",
    "Stationery & Office Supplies": "✏️",
    "Clothing & Fashion": "👕",
    "Seasonal, Pooja & Festival": "🎉",
    "Ready to Eat": "🍜",
    "Sports & Fitness": "⚽",
}

# Image Cache to keep PhotoImage instances alive in Tkinter
_TK_IMAGE_CACHE = {}


def get_product_image(item_id, item_name, category, size=(210, 105)):
    """
    Returns a Tkinter PhotoImage for any product ID.
    1. Checks if a real saved photo exists in assets/products/{item_id}.png.
    2. If not found, checks for assets/products/cat_{category_slug}.png.
    3. Generates and saves a crisp high-quality product photo card in assets/products/{item_id}.png.
    """
    cache_key = f"{item_id}_{size[0]}x{size[1]}"
    if cache_key in _TK_IMAGE_CACHE:
        return _TK_IMAGE_CACHE[cache_key]

    # 1. Check for item-specific photo
    real_file = os.path.join(ASSETS_DIR, f"{item_id}.png")
    if os.path.exists(real_file):
        try:
            pil_img = Image.open(real_file).convert("RGBA")
            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
            tk_photo = ImageTk.PhotoImage(pil_img)
            _TK_IMAGE_CACHE[cache_key] = tk_photo
            return tk_photo
        except Exception:
            pass

    # 2. Check for category default image
    cat_slug = category.lower().replace(" ", "_").replace("&", "and").replace(",", "")
    cat_file = os.path.join(ASSETS_DIR, f"cat_{cat_slug}.png")
    if os.path.exists(cat_file):
        try:
            pil_img = Image.open(cat_file).convert("RGBA")
            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
            tk_photo = ImageTk.PhotoImage(pil_img)
            _TK_IMAGE_CACHE[cache_key] = tk_photo
            return tk_photo
        except Exception:
            pass

    # 3. Dynamically generate and save product picture card into assets/products/
    bg_color, accent_color = CATEGORY_COLORS.get(category, ("#f1f5f9", "#334155"))
    pil_img = Image.new("RGBA", size, color=bg_color)
    draw = ImageDraw.Draw(pil_img)

    # Outer border
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=1)

    # Top accent strip
    draw.rectangle([0, 0, size[0] - 1, 6], fill=accent_color)

    # Veg Symbol Badge (Green Circle inside Square)
    draw.rectangle([10, 12, 24, 26], outline="#16a34a", width=1)
    draw.ellipse([14, 16, 20, 22], fill="#16a34a")

    # Short product title
    display_title = item_name[:22] + ".." if len(item_name) > 22 else item_name
    draw.text((32, 14), display_title, fill="#0f172a")

    # Category & Emoji Badge
    emoji = CATEGORY_EMOJIS.get(category, "🛒")
    draw.text((size[0] // 2, 50), emoji, fill="#0f172a", anchor="mm")
    draw.text((size[0] // 2, 82), f"100% Veg • {category[:18]}", fill=accent_color, anchor="mm")

    # Save to assets/products/{item_id}.png so it persists in root directory
    try:
        pil_img.save(real_file)
    except Exception:
        pass

    tk_photo = ImageTk.PhotoImage(pil_img)
    _TK_IMAGE_CACHE[cache_key] = tk_photo
    return tk_photo