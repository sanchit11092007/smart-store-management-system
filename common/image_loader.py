import os
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Folder to keep product photos
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Color themes for categories
CATEGORY_COLORS = {
    "Grocery & Staples": "#fef3c7",
    "Fruits & Vegetables": "#dcfce7",
    "Dairy & Eggs": "#e0f2fe",
    "Beverages": "#ffedd5",
    "Snacks & Munchies": "#fee2e2",
    "Personal Care": "#f3e8ff",
    "Household Essentials": "#e2e8f0",
    "Bakery & Sweets": "#fce7f3",
    "Instant Food": "#fef9c3",
}

CATEGORY_ICONS = {
    "Grocery & Staples": "🌾",
    "Fruits & Vegetables": "🍎",
    "Dairy & Eggs": "🥛",
    "Beverages": "🥤",
    "Snacks & Munchies": "🍿",
    "Personal Care": "🧼",
    "Household Essentials": "🧹",
    "Bakery & Sweets": "🍞",
    "Instant Food": "🍜",
}


def get_product_image(item_id, item_name, category, size=(160, 110)):
    """
    Returns a Tkinter PhotoImage for any product.
    1. Checks if a real photo exists in assets/products/{item_id}.png.
    2. If not found, creates a clean image card with category color and icon.
    """
    # 1. Check for real image file
    real_file = os.path.join(ASSETS_DIR, f"{item_id}.png")
    if os.path.exists(real_file):
        try:
            img = Image.open(real_file).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass

    # 2. Automatically generate a clean product picture card
    bg_color = CATEGORY_COLORS.get(category, "#f1f5f9")
    img = Image.new("RGBA", size, color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=1)

    # Pick icon
    icon = CATEGORY_ICONS.get(category, "🛒")

    # Short product text
    short_title = item_name[:16] + ".." if len(item_name) > 16 else item_name

    # Draw simple text
    draw.text((size[0] // 2, 38), icon, fill="#0f172a", anchor="mm", font=None)
    draw.text((size[0] // 2, 75), short_title, fill="#334155", anchor="mm", font=None)

    return ImageTk.PhotoImage(img)