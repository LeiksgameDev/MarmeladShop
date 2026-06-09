import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / os.getenv('DATABASE', 'instance/shop.db')
PRODUCT_JSON_DIR = BASE_DIR / 'products_json'
PRODUCT_IMAGES_DIR = BASE_DIR / 'static' / 'img' / 'products'
# Existing seeded product images may include SVG files.
# SVG is allowed only for displaying trusted bundled product images, not for uploads.
DISPLAY_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.svg'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
SEED_PRODUCTS = {
    1:{'quantity':80,'price':240},2:{'quantity':60,'price':290},3:{'quantity':45,'price':420},4:{'quantity':120,'price':190},5:{'quantity':25,'price':990},
    6:{'quantity':70,'price':260},7:{'quantity':50,'price':360},8:{'quantity':90,'price':230},9:{'quantity':35,'price':650},10:{'quantity':55,'price':310}
}
