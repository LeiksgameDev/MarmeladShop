import hmac
import os
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from app.security import admin_required
from app.services.admin_service import dashboard_stats, product_table_stats
from app.services.auth_service import list_clients
from app.services.product_service import all_products, create_product_from_form, delete_product, delete_product_image, get_product, update_product_flags, update_product_from_form
from app.services.supplier_service import create_supplier_from_form, delete_supplier, get_supplier, list_suppliers, update_supplier_from_form
from app.validators import ValidationError

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin43')
        if hmac.compare_digest(password, admin_password):
            session['admin_auth'] = True
            return redirect(url_for('admin.admin_dashboard'))
        flash('Неверный пароль администратора')
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_auth', None)
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', stats=dashboard_stats())

@admin_bp.route('/admin/products')
@admin_required
def admin_products():
    sort = request.args.get('sort', 'id-asc')
    return render_template('admin_products.html', products=all_products(include_hidden=True, sort=sort), sort=sort, table_stats=product_table_stats())

@admin_bp.route('/admin/products/new', methods=['GET', 'POST'])
@admin_required
def admin_product_new():
    if request.method == 'POST':
        try:
            create_product_from_form(request.form, request.files.getlist('images'))
            flash('Товар добавлен')
            return redirect(url_for('admin.admin_products'))
        except ValidationError as exc:
            flash(str(exc))
    product = {'id': None, 'name': '', 'short_description': '', 'full_description': '', 'composition': '', 'weight': '', 'proteins': '', 'fats': '', 'carbohydrates': '', 'kcal': '', 'type': 'Мармелад', 'quantity': 0, 'price': 0, 'in_assortment': 1, 'is_new': 0, 'discount': 0, 'images': []}
    return render_template('admin_product_form.html', product=product, action='Добавить')

@admin_bp.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(product_id):
    product = get_product(product_id, include_hidden=True)
    if not product:
        abort(404)
    if request.method == 'POST':
        try:
            update_product_from_form(product_id, request.form, request.files.getlist('images'))
            flash('Товар обновлен')
            return redirect(url_for('admin.admin_products'))
        except ValidationError as exc:
            flash(str(exc))
    return render_template('admin_product_form.html', product=product, action='Сохранить')

@admin_bp.route('/admin/products/<int:product_id>/flags', methods=['POST'])
@admin_required
def admin_product_flags(product_id):
    data = request.get_json(silent=True) or request.form

    if hasattr(data, 'get') and 'in_assortment' in data:
        in_assortment = data.get('in_assortment') in (True, 'true', '1', 'on', 1)
    else:
        in_assortment = request.form.get('in_assortment') == 'on'

    if hasattr(data, 'get') and 'is_new' in data:
        is_new = data.get('is_new') in (True, 'true', '1', 'on', 1)
    else:
        is_new = request.form.get('is_new') == 'on'

    update_product_flags(product_id, in_assortment, is_new)

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True, 'message': 'Флажки сохранены'})

    flash('Флажки товара обновлены')
    return redirect(url_for('admin.admin_products', sort=request.form.get('sort', 'id-asc')))

@admin_bp.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def admin_product_delete(product_id):
    delete_product(product_id)
    flash('Товар удален')
    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/admin/products/<int:product_id>/images/delete', methods=['POST'])
@admin_required
def admin_product_image_delete(product_id):
    if delete_product_image(product_id, request.form.get('image', '')):
        flash('Фото удалено')
    return redirect(url_for('admin.admin_product_edit', product_id=product_id))

@admin_bp.route('/admin/suppliers')
@admin_required
def admin_suppliers():
    return render_template('admin_suppliers.html', suppliers=list_suppliers())

@admin_bp.route('/admin/suppliers/new', methods=['GET', 'POST'])
@admin_required
def admin_supplier_new():
    if request.method == 'POST':
        try:
            create_supplier_from_form(request.form)
            flash('Поставщик добавлен')
            return redirect(url_for('admin.admin_suppliers'))
        except ValidationError as exc:
            flash(str(exc))
    return render_template('admin_supplier_form.html', supplier=None, action='Добавить')

@admin_bp.route('/admin/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_supplier_edit(supplier_id):
    supplier = get_supplier(supplier_id)
    if not supplier:
        abort(404)
    if request.method == 'POST':
        try:
            update_supplier_from_form(supplier_id, request.form)
            flash('Поставщик обновлен')
            return redirect(url_for('admin.admin_suppliers'))
        except ValidationError as exc:
            flash(str(exc))
    return render_template('admin_supplier_form.html', supplier=supplier, action='Сохранить')

@admin_bp.route('/admin/suppliers/<int:supplier_id>/delete', methods=['POST'])
@admin_required
def admin_supplier_delete(supplier_id):
    delete_supplier(supplier_id)
    flash('Поставщик удален')
    return redirect(url_for('admin.admin_suppliers'))

@admin_bp.route('/admin/clients')
@admin_required
def admin_clients():
    return render_template('admin_clients.html', clients=list_clients())
