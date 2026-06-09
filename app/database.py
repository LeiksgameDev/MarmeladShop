import json
import sqlite3
from app.config import DB_PATH, PRODUCT_JSON_DIR, SEED_PRODUCTS


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with get_db() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assortment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            card_json_url TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            price INTEGER NOT NULL CHECK(price >= 0),
            in_assortment INTEGER NOT NULL DEFAULT 1,
            is_new INTEGER NOT NULL DEFAULT 0,
            discount INTEGER NOT NULL DEFAULT 0 CHECK(discount >= 0 AND discount <= 90)
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            order_status TEXT NOT NULL,
            order_date TEXT NOT NULL,
            pickup_store TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(product_id) REFERENCES assortment(id)
        );
        ''')

        columns = {row['name'] for row in conn.execute("PRAGMA table_info(assortment)").fetchall()}
        if 'in_assortment' not in columns:
            conn.execute('ALTER TABLE assortment ADD COLUMN in_assortment INTEGER NOT NULL DEFAULT 1')
        if 'is_new' not in columns:
            conn.execute('ALTER TABLE assortment ADD COLUMN is_new INTEGER NOT NULL DEFAULT 0')
        if 'discount' not in columns:
            conn.execute('ALTER TABLE assortment ADD COLUMN discount INTEGER NOT NULL DEFAULT 0')
        if conn.execute('SELECT COUNT(*) FROM assortment').fetchone()[0] == 0:
            for file in sorted(PRODUCT_JSON_DIR.glob('product_*.json'), key=lambda x: int(x.stem.split('_')[1])):
                data = json.loads(file.read_text(encoding='utf-8'))
                file_product_id = int(file.stem.split('_')[1])
                product_id = conn.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM assortment').fetchone()[0]
                seed = SEED_PRODUCTS.get(file_product_id, {'quantity': 0, 'price': 0})
                conn.execute('INSERT INTO assortment (id, name, card_json_url, quantity, price, in_assortment, is_new, discount) VALUES (?, ?, ?, ?, ?, 1, 0, 0)',
                             (product_id, data['name'], f'products_json/{file.name}', seed['quantity'], seed['price']))
        if conn.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0] == 0:
            conn.executemany('INSERT INTO suppliers (name, email) VALUES (?, ?)', [
                ('Сладкая фабрика Вятка', 'supply@vyatka-sweets.ru'),
                ('Шоколадный дом', 'orders@choco-house.ru'),
                ('Мармеладные линии', 'mail@marmelines.ru')
            ])
        conn.execute("DELETE FROM orders WHERE date(order_date) < date('now','-6 months')")
