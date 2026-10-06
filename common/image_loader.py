import os
from PIL import Image, ImageDraw, ImageTk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

_TK_IMAGE_CACHE = {}


def get_product_image(item_id, item_name, category, size=(210, 105)):
    """
    Returns a Tkinter PhotoImage for any product ID using real downloaded web photos.
    1. Checks if item-specific image exists in assets/products/{item_id}.png.
    2. If not, loads the real downloaded web photo for the category: assets/products/{category_slug}.png.
    3. Crops & resizes the real web photo, adds a clean product title overlay, and saves it into assets/products/{item_id}.png.
    """
    cache_key = f"{item_id}_{size[0]}x{size[1]}"
    if cache_key in _TK_IMAGE_CACHE:
        return _TK_IMAGE_CACHE[cache_key]

    # 1. Check for item-specific image
    item_file = os.path.join(ASSETS_DIR, f"{item_id}.png")
    if os.path.exists(item_file):
        try:
            pil_img = Image.open(item_file).convert("RGBA")
            if pil_img.size != size:
                pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
            tk_photo = ImageTk.PhotoImage(pil_img)
            _TK_IMAGE_CACHE[cache_key] = tk_photo
            return tk_photo
        except Exception:
            pass

    # 2. Load real downloaded category photo from assets/products/
    slug = category.lower().replace(" ", "_").replace("&", "and").replace(",", "")
    cat_file = os.path.join(ASSETS_DIR, f"{slug}.png")

    if os.path.exists(cat_file):
        try:
            pil_img = Image.open(cat_file).convert("RGBA")
            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)

            # Draw clean product title overlay at bottom of real web photo
            overlay = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            draw.rectangle([0, size[1] - 32, size[0], size[1]], fill=(15, 23, 42, 220))

            short_name = item_name[:24] + ".." if len(item_name) > 24 else item_name
            draw.text((10, size[1] - 24), short_name, fill="#ffffff")

            pil_img = Image.alpha_composite(pil_img, overlay)
            pil_img.save(item_file)

            tk_photo = ImageTk.PhotoImage(pil_img)
            _TK_IMAGE_CACHE[cache_key] = tk_photo
            return tk_photo
        except Exception as e:
            print(f"Error rendering real photo for item {item_id}: {e}")

    # 3. Fallback clean image
    pil_img = Image.new("RGBA", size, color="#f1f5f9")
    draw = ImageDraw.Draw(pil_img)
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=1)
    draw.text((10, 30), item_name[:22], fill="#0f172a")

    try:
        pil_img.save(item_file)
    except Exception:
        pass

    tk_photo = ImageTk.PhotoImage(pil_img)
    _TK_IMAGE_CACHE[cache_key] = tk_photo
    return tk_photo