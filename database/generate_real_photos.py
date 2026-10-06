import os
import glob
import urllib.request
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "products")
os.makedirs(ASSETS_DIR, exist_ok=True)

# High quality royalty-free real image URLs for all categories
CATEGORY_PHOTO_URLS = {
    "grocery_and_staples": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&auto=format&fit=crop&q=80",
    "dairy_milk_and_paneer": "https://images.unsplash.com/photo-1628088062854-d1870b4553da?w=400&auto=format&fit=crop&q=80",
    "fresh_vegetables_and_greens": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&auto=format&fit=crop&q=80",
    "fresh_fruits_and_berries": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&auto=format&fit=crop&q=80",
    "bakery_and_breakfast": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&auto=format&fit=crop&q=80",
    "snacks_chips_and_namkeen": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&auto=format&fit=crop&q=80",
    "chocolates_sweets_and_biscuits": "https://images.unsplash.com/photo-1511381939415-e44015466834?w=400&auto=format&fit=crop&q=80",
    "tea_coffee_and_beverages": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=400&auto=format&fit=crop&q=80",
    "personal_care_and_grooming": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400&auto=format&fit=crop&q=80",
    "girls_accessories_and_makeup": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&auto=format&fit=crop&q=80",
    "tech_and_mobile_accessories": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&auto=format&fit=crop&q=80",
    "health_wellness_and_supplements": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&auto=format&fit=crop&q=80",
    "all_medicines_and_first_aid": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&auto=format&fit=crop&q=80",
    "household_and_cleaning": "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=400&auto=format&fit=crop&q=80",
    "home_and_kitchenware": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=400&auto=format&fit=crop&q=80",
    "stationery_and_office_supplies": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&auto=format&fit=crop&q=80",
    "clothing_and_fashion": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&auto=format&fit=crop&q=80",
    "seasonal_pooja_and_festival": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&auto=format&fit=crop&q=80",
    "ready_to_eat": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&auto=format&fit=crop&q=80",
    "sports_and_fitness": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=400&auto=format&fit=crop&q=80",
}


def download_and_generate_photos():
    # Clear old cached product item photos so new real photos display
    png_files = glob.glob(os.path.join(ASSETS_DIR, "*.png"))
    for f in png_files:
        try:
            os.remove(f)
        except Exception:
            pass

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for slug, url in CATEGORY_PHOTO_URLS.items():
        file_path = os.path.join(ASSETS_DIR, f"{slug}.png")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                img = Image.open(response).convert("RGBA")
                img = img.resize((320, 180), Image.Resampling.LANCZOS)
                img.save(file_path)
                print(f"Downloaded real photo for category: {slug}")
        except Exception as e:
            print(f"Could not download photo for {slug}: {e}")


if __name__ == "__main__":
    download_and_generate_photos()
