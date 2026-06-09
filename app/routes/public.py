from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from app.security import login_required
from app.services.auth_service import current_user, login_user, register_user
from app.services.order_service import order_details, profile_orders
from app.services.product_service import all_products, get_product
from app.validators import ValidationError

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    return render_template('index.html', products=all_products()[:4])

@public_bp.route('/catalog')
def catalog():
    q = request.args.get('q', '').strip().lower()[:80]
    category = request.args.get('category', 'all')
    sort = request.args.get('sort', 'default')
    products = all_products()
    if q:
        products = [p for p in products if q in p['name'].lower()]
    if category != 'all':
        products = [p for p in products if p['type'] == category]
    if sort == 'price-asc':
        products.sort(key=lambda p: p['discounted_price'])
    elif sort == 'price-desc':
        products.sort(key=lambda p: p['discounted_price'], reverse=True)
    return render_template('catalog.html', products=products, q=q, category=category, sort=sort)

@public_bp.route('/product/<int:product_id>')
def product(product_id):
    item = get_product(product_id)
    if not item:
        abort(404)
    return render_template('product.html', product=item)

@public_bp.route('/about')
def about():
    return render_template('about.html')

@public_bp.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@public_bp.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        try:
            if request.form.get('action') == 'register':
                register_user(request.form)
                return redirect(url_for('public.profile'))
            login_user(request.form)
            return redirect(url_for('public.profile'))
        except ValidationError as exc:
            flash(str(exc))
    return render_template('auth.html')

@public_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('public.index'))

@public_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', orders=profile_orders(session['user_id']))

@public_bp.route('/order/<int:order_id>')
@login_required
def order(order_id):
    rows, total = order_details(session['user_id'], order_id)
    if not rows:
        abort(404)
    return render_template('order.html', rows=rows, total=total)
