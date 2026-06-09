from app.database import get_db


def list_suppliers():
    with get_db() as conn:
        return conn.execute('SELECT * FROM suppliers ORDER BY id DESC').fetchall()


def get_supplier(supplier_id):
    with get_db() as conn:
        return conn.execute('SELECT * FROM suppliers WHERE id=?', (supplier_id,)).fetchone()


def create_supplier(name, email):
    with get_db() as conn:
        conn.execute('INSERT INTO suppliers (name, email) VALUES (?, ?)', (name, email))


def update_supplier(supplier_id, name, email):
    with get_db() as conn:
        conn.execute('UPDATE suppliers SET name=?, email=? WHERE id=?', (name, email, supplier_id))


def delete_supplier(supplier_id):
    with get_db() as conn:
        conn.execute('DELETE FROM suppliers WHERE id=?', (supplier_id,))
