from PIL import Image, UnidentifiedImageError
import json
from pathlib import Path
from flask import url_for
from werkzeug.utils import secure_filename
from app.config import BASE_DIR, PRODUCT_IMAGES_DIR, PRODUCT_JSON_DIR, ALLOWED_IMAGE_EXTENSIONS, DISPLAY_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE
from app.repositories import product_repo
from app.validators import validate_product_form, ValidationError


def product_json_path_for(product_id):
    return PRODUCT_JSON_DIR / f'product_{product_id}.json'


def product_images_folder_for(product_id):
    return PRODUCT_IMAGES_DIR / f'product_{product_id}'


def load_product(row):
    path = BASE_DIR / row['card_json_url']
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    product = {**dict(row), **data}
    product['discount'] = int(product.get('discount') or 0)
    product['in_assortment'] = int(product.get('in_assortment') if product.get('in_assortment') is not None else 1)
    product['is_new'] = int(product.get('is_new') or 0)
    product['discounted_price'] = max(0, round(product['price'] * (100 - product['discount']) / 100)) if product['discount'] else product['price']
    # Backward compatibility for product JSON files created before nutrition fields were added.
    product['proteins'] = product.get('proteins', '')
    product['fats'] = product.get('fats', '')
    product['carbohydrates'] = product.get('carbohydrates', '')
    product['kcal'] = product.get('kcal') or product.get('calories', '')
    folder = product.get('images_folder', '')
    images_path = BASE_DIR / folder
    images = []
    if images_path.exists():
        for image in sorted(images_path.iterdir()):
            if image.is_file() and image.suffix.lower() in DISPLAY_IMAGE_EXTENSIONS:
                images.append('/' + str(image.relative_to(BASE_DIR)).replace('\\', '/'))
    product['images'] = images
    product['main_image'] = images[0] if images else url_for('static', filename='img/product-placeholder.svg')
    return product


def all_products(include_hidden=False, sort='id-asc'):
    return [load_product(r) for r in product_repo.list_product_rows(include_hidden=include_hidden, sort=sort)]


def get_product(product_id, include_hidden=False):
    row = product_repo.get_product_row(product_id, include_hidden=include_hidden)
    return load_product(row) if row else None


def save_product_json(product_id, data):
    PRODUCT_JSON_DIR.mkdir(exist_ok=True)
    payload = {k: data[k] for k in ['name', 'short_description', 'full_description', 'composition', 'weight', 'proteins', 'fats', 'carbohydrates', 'kcal', 'type']}
    payload['calories'] = data['kcal']
    payload['images_folder'] = f'static/img/products/product_{product_id}'
    product_json_path_for(product_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def _is_safe_image(file_storage, suffix):
    if suffix == '.svg':
        return False

    allowed_formats = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.webp': 'WEBP',
    }

    expected_format = allowed_formats.get(suffix)
    if not expected_format:
        return False

    pos = file_storage.stream.tell()
    try:
        file_storage.stream.seek(0)
        with Image.open(file_storage.stream) as image:
            image.verify()
            detected_format = image.format
    except (UnidentifiedImageError, OSError, ValueError):
        return False
    finally:
        file_storage.stream.seek(pos)

    return detected_format == expected_format


def save_uploaded_images(product_id, files):
    folder = product_images_folder_for(product_id).resolve()
    folder.mkdir(parents=True, exist_ok=True)

    files = [file for file in files if file and file.filename]
    if not files:
        return

    existing_count = len([p for p in folder.iterdir() if p.is_file()])
    saved_count = 0

    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError('Недопустимый формат изображения')

        file.stream.seek(0, 2)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > MAX_IMAGE_SIZE:
            raise ValidationError('Изображение больше 5 МБ')
        if not _is_safe_image(file, suffix):
            raise ValidationError('Файл не похож на безопасное изображение')

        original_name = secure_filename(Path(file.filename).stem) or 'image'
        number = existing_count + saved_count + 1
        target = (folder / f'{number:02d}_{original_name}{suffix}').resolve()

        if not str(target).startswith(str(folder)):
            raise ValidationError('Недопустимое имя файла')

        counter = 1
        while target.exists():
            target = (folder / f'{number:02d}_{original_name}_{counter}{suffix}').resolve()
            counter += 1

        file.save(target)
        saved_count += 1


def create_product_from_form(form, files):
    data = validate_product_form(form)
    if product_repo.product_name_exists(data['name']):
        raise ValidationError('Товар с таким названием уже существует')
    product_id = product_repo.create_product(data['name'], data['quantity'], data['price'], data['in_assortment'], data['is_new'], data['discount'])
    save_product_json(product_id, data)
    save_uploaded_images(product_id, files)
    return product_id


def update_product_from_form(product_id, form, files):
    data = validate_product_form(form)
    if product_repo.product_name_exists(data['name'], exclude_id=product_id):
        raise ValidationError('Товар с таким названием уже существует')
    product_repo.update_product(product_id, data['name'], data['quantity'], data['price'], data['in_assortment'], data['is_new'], data['discount'])
    save_product_json(product_id, data)
    save_uploaded_images(product_id, files)


def update_product_flags(product_id, in_assortment, is_new):
    product_repo.update_product_flags(product_id, in_assortment, is_new)


def delete_product(product_id):
    product_repo.delete_product(product_id)
    path = product_json_path_for(product_id)
    if path.exists():
        path.unlink()


def delete_product_image(product_id, image):
    folder = product_images_folder_for(product_id).resolve()
    target = (BASE_DIR / image.lstrip('/')).resolve()
    if str(target).startswith(str(folder)) and target.exists() and target.is_file():
        target.unlink()
        return True
    return False
