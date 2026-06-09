from flask import Blueprint, jsonify, request, session, url_for
from app.services.auth_service import current_user
from app.services.order_service import cancel_order, create_order
from app.services.product_service import all_products
from app.validators import ValidationError

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/cart/products', methods=['POST'])
def cart_products():
    payload = request.get_json(silent=True) or {}
    ids = []
    for value in payload.get('ids', []):
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            return jsonify({'ok': False, 'message': 'Некорректный ID товара'}), 400
    result = [p for p in all_products() if p['id'] in set(ids)]
    return jsonify(result)

@api_bp.route('/order', methods=['POST'])
def order_create():
    if not current_user():
        return jsonify({'ok': False, 'message': 'Нужно войти или зарегистрироваться'}), 401
    payload = request.get_json(silent=True) or {}
    try:
        order_id = create_order(session['user_id'], payload.get('cart', []))
    except ValidationError as exc:
        return jsonify({'ok': False, 'message': str(exc)}), 400
    return jsonify({'ok': True, 'order_id': order_id, 'url': url_for('public.order', order_id=order_id)})

@api_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
def order_cancel(order_id):
    if not current_user():
        return jsonify({'ok': False, 'message': 'Нужно войти или зарегистрироваться'}), 401
    try:
        cancel_order(session['user_id'], order_id)
    except ValidationError as exc:
        status = 404 if 'не найден' in str(exc).lower() else 400
        return jsonify({'ok': False, 'message': str(exc)}), status
    return jsonify({'ok': True, 'message': 'Заказ отменен'})
