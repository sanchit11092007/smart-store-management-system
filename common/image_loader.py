import os
from PIL import Image, ImageDraw, ImageTk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

_TK_IMAGE_CACHE = {}


def get_product_image(item_id, item_name, category, size=(210, 110)):
    """
    Returns a high-quality Tkinter PhotoImage for any product using real downloaded web photography.
    Caches resized images in memory for high-performance fluid rendering.
    """
    # Check memory cache first
    slug = category.lower().replace(" ", "_").replace("&", "and").replace(",", "").strip()
    cache_key = f"{slug}_{size[0]}x{size[1]}"
    if cache_key in _TK_IMAGE_CACHE:
        return _TK_IMAGE_CACHE[cache_key]

    # Check for item-specific photo first
    item_file = os.path.join(ASSETS_DIR, f"{item_id}.png")
    cat_file = os.path.join(ASSETS_DIR, f"{slug}.png")

    target_file = item_file if os.path.exists(item_file) else cat_file

    if os.path.exists(target_file):
        try:
            pil_img = Image.open(target_file).convert("RGBA")
            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)

            # Add subtle elegant card border to frame the product photograph
            draw = ImageDraw.Draw(pil_img)
            draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#e2e8f0", width=1)

            tk_photo = ImageTk.PhotoImage(pil_img)
            _TK_IMAGE_CACHE[cache_key] = tk_photo
            return tk_photo
        except Exception as e:
            print(f"Error rendering photo for category {slug}: {e}")

    # Fallback modern placeholder if image file not found
    pil_img = Image.new("RGBA", size, color="#f8fafc")
    draw = ImageDraw.Draw(pil_img)
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=1)
    draw.text((15, 45), category[:24], fill="#475569")

    tk_photo = ImageTk.PhotoImage(pil_img)
    _TK_IMAGE_CACHE[cache_key] = tk_photo
    return tk_photo