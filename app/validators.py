import re
from email.utils import parseaddr

CATEGORIES = {'Конфеты', 'Мармелад', 'Шоколад', 'Наборы', 'Печенье/пряники'}

class ValidationError(ValueError):
    pass


def clean_text(value, field='Поле', min_len=1, max_len=255):
    value = (value or '').strip()
    if len(value) < min_len:
        raise ValidationError(f'{field}: заполните значение')
    if len(value) > max_len:
        raise ValidationError(f'{field}: слишком длинное значение')
    return value


def clean_email(value):
    value = clean_text(value, 'Почта', max_len=120).lower()
    if parseaddr(value)[1] != value or '@' not in value:
        raise ValidationError('Введите корректную почту')
    return value


def clean_phone(value):
    value = clean_text(value, 'Телефон', max_len=32)
    digits = re.sub(r'\D+', '', value)
    if len(digits) < 10:
        raise ValidationError('Введите корректный телефон')
    return value


def clean_password(value):
    if not value or len(value) < 6:
        raise ValidationError('Пароль должен быть не короче 6 символов')
    if len(value) > 128:
        raise ValidationError('Пароль слишком длинный')
    return value


def clean_int(value, field, min_value=0, max_value=1_000_000):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'{field}: должно быть число')
    if number < min_value or number > max_value:
        raise ValidationError(f'{field}: значение вне допустимого диапазона')
    return number


def validate_product_form(form):
    category = clean_text(form.get('type', 'Мармелад'), 'Категория', max_len=40)
    if category not in CATEGORIES:
        raise ValidationError('Недопустимая категория товара')
    return {
        'name': clean_text(form.get('name'), 'Название', max_len=120),
        'short_description': clean_text(form.get('short_description'), 'Краткое описание', max_len=300),
        'full_description': clean_text(form.get('full_description'), 'Описание', max_len=3000),
        'composition': clean_text(form.get('composition'), 'Состав', max_len=1000),
        'weight': clean_text(form.get('weight'), 'Вес товара', max_len=60),
        'proteins': clean_text(form.get('proteins'), 'Белки', max_len=60),
        'fats': clean_text(form.get('fats'), 'Жиры', max_len=60),
        'carbohydrates': clean_text(form.get('carbohydrates'), 'Углеводы', max_len=60),
        'kcal': clean_text(form.get('kcal'), 'Ккал', max_len=60),
        'type': category,
        'quantity': clean_int(form.get('quantity'), 'Остаток', 0, 100000),
        'price': clean_int(form.get('price'), 'Цена', 0, 1000000),
        'in_assortment': 1 if form.get('in_assortment') == 'on' else 0,
        'is_new': 1 if form.get('is_new') == 'on' else 0,
        'discount': clean_int(form.get('discount', 0), 'Скидка', 0, 90),
    }


def validate_supplier_form(form):
    return {'name': clean_text(form.get('name'), 'Наименование', max_len=160), 'email': clean_email(form.get('email'))}
