from app.database import get_db


def dashboard_stats():
    with get_db() as conn:
        return {
            'products': conn.execute('SELECT COUNT(*) FROM assortment').fetchone()[0],
            'suppliers': conn.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0],
            'clients': conn.execute('SELECT COUNT(*) FROM clients').fetchone()[0],
            'orders': conn.execute('SELECT COUNT(DISTINCT order_id) FROM orders').fetchone()[0],
        }


def cleanup_old_orders():
    with get_db() as conn:
        conn.execute("DELETE FROM orders WHERE date(order_date) < date('now','-6 months')")


def product_table_stats():
    with get_db() as conn:
        return {
            'total': conn.execute('SELECT COUNT(*) FROM assortment').fetchone()[0],
            'in_assortment': conn.execute('SELECT COUNT(*) FROM assortment WHERE in_assortment=1').fetchone()[0],
            'new': conn.execute('SELECT COUNT(*) FROM assortment WHERE is_new=1').fetchone()[0],
            'out_of_stock': conn.execute('SELECT COUNT(*) FROM assortment WHERE quantity=0').fetchone()[0],
        }
