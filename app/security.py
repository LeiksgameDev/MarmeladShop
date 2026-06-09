import hmac
import os
import secrets
from functools import wraps
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from flask import abort, current_app, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

fernet = None

def init_security(app):
    global fernet
    data_key = os.getenv('DATA_KEY')
    if not data_key:
        key_file = Path(app.instance_path) / 'data.key'
        if key_file.exists():
            data_key = key_file.read_text().strip()
        else:
            data_key = Fernet.generate_key().decode()
            key_file.write_text(data_key)
    fernet = Fernet(data_key.encode())


def encrypt(value):
    return fernet.encrypt((value or '').encode()).decode()


def decrypt(value):
    if not value:
        return ''
    try:
        return fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        return ''


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def validate_csrf():
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        sent = request.form.get('_csrf_token') or request.headers.get('X-CSRFToken')
        expected = session.get('_csrf_token')
        if not expected or not sent or not hmac.compare_digest(expected, sent):
            abort(400, description='CSRF token is missing or invalid')


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_auth'):
            flash('Введите пароль администратора')
            return redirect(url_for('admin.admin_login'))
        return fn(*args, **kwargs)
    return wrapper


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from app.services.auth_service import current_user
        if not current_user():
            flash('Войдите или зарегистрируйтесь для продолжения')
            return redirect(url_for('public.auth'))
        return fn(*args, **kwargs)
    return wrapper
