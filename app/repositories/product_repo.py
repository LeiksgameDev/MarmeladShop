from app.database import get_db


SORT_SQL = {
    'id-asc': 'id ASC',
    'id-desc': 'id DESC',
    'name-asc': 'name COLLATE NOCASE ASC',
    'name-desc': 'name COLLATE NOCASE DESC',
    'price-asc': 'price ASC',
    'price-desc': 'price DESC',
    'quantity-asc': 'quantity ASC',
    'quantity-desc': 'quantity DESC',
    'discount-desc': 'discount DESC',
    'discount-asc': 'discount ASC',
    'new-first': 'is_new DESC, id DESC',
    'new-last': 'is_new ASC, id DESC',
    'assortment-first': 'in_assortment DESC, id ASC',
    'assortment-last': 'in_assortment ASC, id ASC',
}


def list_product_rows(include_hidden=False, sort='id-asc'):
    order_by = SORT_SQL.get(sort, SORT_SQL['id-asc'])
    with get_db() as conn:
        if include_hidden:
            return conn.execute(f'SELECT * FROM assortment ORDER BY {order_by}').fetchall()
        return conn.execute(f'SELECT * FROM assortment WHERE in_assortment=1 ORDER BY {order_by}').fetchall()


def get_product_row(product_id, include_hidden=False):
    with get_db() as conn:
        if include_hidden:
            return conn.execute('SELECT * FROM assortment WHERE id=?', (product_id,)).fetchone()
        return conn.execute('SELECT * FROM assortment WHERE id=? AND in_assortment=1', (product_id,)).fetchone()


def create_product(name, quantity, price, in_assortment=1, is_new=0, discount=0):
    with get_db() as conn:
        cur = conn.execute(
            'INSERT INTO assortment (name, card_json_url, quantity, price, in_assortment, is_new, discount) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, '', quantity, price, in_assortment, is_new, discount)
        )
        product_id = cur.lastrowid
        conn.execute('UPDATE assortment SET card_json_url=? WHERE id=?', (f'products_json/product_{product_id}.json', product_id))
        return product_id


def update_product(product_id, name, quantity, price, in_assortment=1, is_new=0, discount=0):
    with get_db() as conn:
        conn.execute(
            'UPDATE assortment SET name=?, quantity=?, price=?, in_assortment=?, is_new=?, discount=? WHERE id=?',
            (name, quantity, price, in_assortment, is_new, discount, product_id)
        )


def update_product_flags(product_id, in_assortment, is_new):
    with get_db() as conn:
        conn.execute(
            'UPDATE assortment SET in_assortment=?, is_new=? WHERE id=?',
            (1 if in_assortment else 0, 1 if is_new else 0, product_id)
        )


def delete_product(product_id):
    with get_db() as conn:
        conn.execute('DELETE FROM assortment WHERE id=?', (product_id,))


def product_name_exists(name, exclude_id=None):
    with get_db() as conn:
        if exclude_id:
            row = conn.execute(
                'SELECT id FROM assortment WHERE LOWER(name)=LOWER(?) AND id<>?',
                (name, exclude_id)
            ).fetchone()
        else:
            row = conn.execute(
                'SELECT id FROM assortment WHERE LOWER(name)=LOWER(?)',
                (name,)
            ).fetchone()
        return row is not None
