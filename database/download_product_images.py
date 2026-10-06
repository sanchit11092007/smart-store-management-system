import os
import math
from PIL import Image, ImageDraw, ImageFont

# Root assets directory: d:\smart_store_project\assets\products
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Rich curated color themes for categories
PALETTES = {
    "Grocery & Staples": ("#d97706", "#fef3c7", "#78350f"),
    "Dairy, Milk & Paneer": ("#0284c7", "#e0f2fe", "#075985"),
    "Fresh Vegetables & Greens": ("#15803d", "#dcfce7", "#14532d"),
    "Fresh Fruits & Berries": ("#b91c1c", "#fee2e2", "#7f1d1d"),
    "Bakery & Breakfast": ("#c2410c", "#ffedd5", "#7c2d12"),
    "Snacks, Chips & Namkeen": ("#ca8a04", "#fef9c3", "#713f12"),
    "Chocolates, Sweets & Biscuits": ("#be185d", "#fce7f3", "#831843"),
    "Tea, Coffee & Beverages": ("#0369a1", "#e0f2fe", "#0c4a6e"),
    "Personal Care & Grooming": ("#7e22ce", "#f3e8ff", "#581c87"),
    "Girls Accessories & Makeup": ("#be123c", "#ffe4e6", "#881337"),
    "Tech & Mobile Accessories": ("#1d4ed8", "#dbeafe", "#1e3a8a"),
    "Health, Wellness & Supplements": ("#0f766e", "#ccfbf1", "#134e4a"),
    "All Medicines & First Aid": ("#c026d3", "#fae8ff", "#701a75"),
    "Household & Cleaning": ("#475569", "#f1f5f9", "#0f172a"),
    "Home & Kitchenware": ("#0369a1", "#e0f2fe", "#0c4a6e"),
    "Stationery & Office Supplies": ("#a16207", "#fef9c3", "#713f12"),
    "Clothing & Fashion": ("#be185d", "#fce7f3", "#831843"),
    "Seasonal, Pooja & Festival": ("#c2410c", "#ffedd5", "#7c2d12"),
    "Ready to Eat": ("#b45309", "#fef3c7", "#78350f"),
    "Sports & Fitness": ("#15803d", "#dcfce7", "#14532d"),
}


def generate_category_assets():
    """
    Generates vibrant visual background cards for each product department.
    Saves them to assets/products/{category_slug}.png
    """
    for cat_name, (primary, bg_soft, text_dark) in PALETTES.items():
        slug = cat_name.lower().replace(" ", "_").replace("&", "and").replace(",", "")
        file_path = os.path.join(ASSETS_DIR, f"{slug}.png")

        img = Image.new("RGBA", (320, 180), color=bg_soft)
        draw = ImageDraw.Draw(img)

        # Draw decorative background patterns
        draw.rectangle([0, 0, 319, 179], outline=primary, width=2)
        draw.rectangle([0, 0, 319, 12], fill=primary)

        # Abstract geometric circles/shapes for modern card look
        draw.ellipse([210, 30, 330, 150], outline=primary, width=2)
        draw.ellipse([230, 50, 310, 130], fill=primary)

        # Draw category title on left
        display_name = cat_name[:24]
        draw.text((20, 45), display_name, fill=text_dark)
        draw.text((20, 85), "SnapKart Quality Assured", fill=primary)

        img.save(file_path)
        print(f"Generated category image asset: {file_path}")


if __name__ == "__main__":
    generate_category_assets()
