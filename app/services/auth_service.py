from datetime import datetime
from flask import session
from app.database import get_db
from app.security import decrypt, encrypt, hash_password, verify_password
from app.validators import clean_email, clean_password, clean_phone, clean_text, ValidationError


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    with get_db() as conn:
        user = conn.execute('SELECT * FROM clients WHERE id=?', (uid,)).fetchone()
    if not user:
        session.clear()
        return None
    return {'id': user['id'], 'name': decrypt(user['name']), 'phone': decrypt(user['phone']), 'email': decrypt(user['email'])}


def register_user(form):
    name = clean_text(form.get('name'), 'ФИО', max_len=120)
    phone = clean_phone(form.get('phone'))
    email = clean_email(form.get('email'))
    password = clean_password(form.get('password'))
    with get_db() as conn:
        rows = conn.execute('SELECT id, phone, email FROM clients').fetchall()
        for row in rows:
            if decrypt(row['phone']) == phone or decrypt(row['email']) == email:
                raise ValidationError('Пользователь с таким телефоном или почтой уже есть')
        cur = conn.execute('INSERT INTO clients (name, phone, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)',
                           (encrypt(name), encrypt(phone), encrypt(email), hash_password(password), datetime.now().isoformat(timespec='seconds')))
        session['user_id'] = cur.lastrowid


def login_user(form):
    login = clean_text(form.get('login'), 'Логин', max_len=120).lower()
    password = form.get('password', '')
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM clients').fetchall()
    for row in rows:
        if decrypt(row['phone']).lower() == login or decrypt(row['email']).lower() == login:
            if verify_password(row['password_hash'], password):
                session['user_id'] = row['id']
                return
    raise ValidationError('Неверный логин или пароль')


def list_clients():
    clients = []
    with get_db() as conn:
        rows = conn.execute('SELECT id, name, phone, email, created_at FROM clients ORDER BY id DESC').fetchall()
    for row in rows:
        clients.append({'id': row['id'], 'name': decrypt(row['name']), 'phone': decrypt(row['phone']), 'email': decrypt(row['email']), 'created_at': row['created_at']})
    return clients
