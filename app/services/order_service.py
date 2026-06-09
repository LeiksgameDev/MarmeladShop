from datetime import datetime
from app.database import get_db
from app.validators import clean_int, ValidationError


def profile_orders(uid):
    with get_db() as conn:
        return conn.execute('''
            SELECT o.order_id, o.order_status, o.order_date,
                   SUM(o.quantity * ROUND(a.price * (100 - COALESCE(a.discount,0)) / 100.0)) total,
                   GROUP_CONCAT(a.name || ' — ' || o.quantity || ' шт.', '||') items
            FROM orders o JOIN assortment a ON a.id=o.product_id
            WHERE o.client_id=? AND date(o.order_date) >= date('now','-6 months')
            GROUP BY o.order_id, o.order_status, o.order_date
            ORDER BY o.order_date DESC, o.order_id DESC
        ''', (uid,)).fetchall()


def order_details(uid, order_id):
    with get_db() as conn:
        rows = conn.execute('''SELECT o.*, a.name, a.price, COALESCE(a.discount,0) discount, ROUND(a.price * (100 - COALESCE(a.discount,0)) / 100.0) effective_price FROM orders o JOIN assortment a ON a.id=o.product_id
                               WHERE o.client_id=? AND o.order_id=? ORDER BY o.id''', (uid, order_id)).fetchall()
    total = sum(int(r['effective_price']) * r['quantity'] for r in rows)
    return rows, total


def create_order(uid, cart):
    if not isinstance(cart, list) or not cart:
        raise ValidationError('Корзина пустая')
    normalized = []
    for item in cart:
        product_id = clean_int(item.get('id'), 'ID товара', 1)
        qty = clean_int(item.get('qty'), 'Количество', 1, 100)
        normalized.append((product_id, qty))
    with get_db() as conn:
        order_id = int(datetime.now().strftime('%y%m%d%H%M%S'))
        for product_id, qty in normalized:
            product = conn.execute('SELECT quantity, in_assortment FROM assortment WHERE id=?', (product_id,)).fetchone()
            if not product or not product['in_assortment'] or product['quantity'] < qty:
                raise ValidationError('Недостаточно товара на складе')
        for product_id, qty in normalized:
            conn.execute('UPDATE assortment SET quantity=quantity-? WHERE id=?', (qty, product_id))
            conn.execute('''INSERT INTO orders (client_id, order_id, product_id, quantity, order_status, order_date, pickup_store)
                            VALUES (?, ?, ?, ?, ?, date('now'), ?)''',
                         (uid, order_id, product_id, qty, 'принят', 'г.Киров, ул.Воровского 31'))
    return order_id


def cancel_order(uid, order_id):
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM orders WHERE client_id=? AND order_id=?', (uid, order_id)).fetchall()
        if not rows:
            raise ValidationError('Заказ не найден')
        if rows[0]['order_status'] in ('получен', 'отменен'):
            raise ValidationError('Этот заказ уже нельзя отменить')
        for row in rows:
            conn.execute('UPDATE assortment SET quantity=quantity+? WHERE id=?', (row['quantity'], row['product_id']))
        conn.execute('UPDATE orders SET order_status=? WHERE client_id=? AND order_id=?', ('отменен', uid, order_id))
