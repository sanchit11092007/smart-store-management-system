import os
from PIL import Image, ImageDraw, ImageTk

# Assets directory directly in root folder: d:\smart_store_project\assets\products
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Color palettes for department categories
CATEGORY_PALETTES = {
    "Grocery & Staples": ("#fef3c7", "#d97706"),
    "Dairy, Milk & Paneer": ("#e0f2fe", "#0284c7"),
    "Fresh Vegetables & Greens": ("#dcfce7", "#15803d"),
    "Fresh Fruits & Berries": ("#fee2e2", "#b91c1c"),
    "Bakery & Breakfast": ("#ffedd5", "#c2410c"),
    "Snacks, Chips & Namkeen": ("#fef9c3", "#ca8a04"),
    "Chocolates, Sweets & Biscuits": ("#fce7f3", "#be185d"),
    "Tea, Coffee & Beverages": ("#e0f2fe", "#0369a1"),
    "Personal Care & Grooming": ("#f3e8ff", "#7e22ce"),
    "Girls Accessories & Makeup": ("#ffe4e6", "#be123c"),
    "Tech & Mobile Accessories": ("#dbeafe", "#1d4ed8"),
    "Health, Wellness & Supplements": ("#ccfbf1", "#0f766e"),
    "All Medicines & First Aid": ("#fae8ff", "#c026d3"),
    "Household & Cleaning": ("#f1f5f9", "#475569"),
    "Home & Kitchenware": ("#e0f2fe", "#0369a1"),
    "Stationery & Office Supplies": ("#fef9c3", "#a16207"),
    "Clothing & Fashion": ("#fce7f3", "#be185d"),
    "Seasonal, Pooja & Festival": ("#ffedd5", "#c2410c"),
    "Ready to Eat": ("#fef3c7", "#b45309"),
    "Sports & Fitness": ("#dcfce7", "#15803d"),
}

# Image Cache to keep PhotoImage instances alive in Tkinter
_TK_IMAGE_CACHE = {}


def get_product_image(item_id, item_name, category, size=(210, 105)):
    """
    Returns a Tkinter PhotoImage for any product ID.
    1. Checks if an item-specific photo exists in assets/products/{item_id}.png.
    2. Checks if a category photo exists in assets/products/{category_slug}.png.
    3. Dynamically generates and caches a high-quality product photo card into assets/products/{item_id}.png.
    """
    cache_key = f"{item_id}_{size[0]}x{size[1]}"
    if cache_key in _TK_IMAGE_CACHE:
        return _TK_IMAGE_CACHE[cache_key]

    # 1. Check for item-specific saved photo
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

    # 2. Check for category default asset file
    slug = category.lower().replace(" ", "_").replace("&", "and").replace(",", "")
    cat_file = os.path.join(ASSETS_DIR, f"{slug}.png")
    if os.path.exists(cat_file):
        try:
            pil_img = Image.open(cat_file).convert("RGBA")
            # Overlay product name on top of category template card
            draw = ImageDraw.Draw(pil_img)
            draw.rectangle([10, 120, 310, 170], fill="#0f172a")
            short_name = item_name[:24] + ".." if len(item_name) > 24 else item_name
            draw.text((20, 135), short_name, fill="#ffffff")

            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
            pil_img.save(real_file)  # Cache for item_id

            tk_photo = ImageTk.PhotoImage(pil_img)
            _TK_IMAGE_CACHE[cache_key] = tk_photo
            return tk_photo
        except Exception:
            pass

    # 3. Fallback card generation
    bg_color, accent_color = CATEGORY_PALETTES.get(category, ("#f1f5f9", "#334155"))
    pil_img = Image.new("RGBA", size, color=bg_color)
    draw = ImageDraw.Draw(pil_img)

    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=1)
    draw.rectangle([0, 0, size[0] - 1, 6], fill=accent_color)

    display_title = item_name[:22] + ".." if len(item_name) > 22 else item_name
    draw.text((15, 20), display_title, fill="#0f172a")
    draw.text((15, 50), f"SnapKart • {category[:18]}", fill=accent_color)

    try:
        pil_img.save(real_file)
    except Exception:
        pass

    tk_photo = ImageTk.PhotoImage(pil_img)
    _TK_IMAGE_CACHE[cache_key] = tk_photo
    return tk_photo