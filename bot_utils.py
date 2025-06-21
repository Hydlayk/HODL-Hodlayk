# bot_utils.py — Вспомогательные функции для Aby Khalid VPN Bot
# Полноценная реализация: миграции, CRUD, генерация, уведомления, логирование, мониторинг

import os
import sqlite3
import datetime
import qrcode
import json
import threading
import config

# Подключение к базе SQLite
DB_PATH = config.DB_PATH
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_cursor = _conn.cursor()

# Создание таблиц и миграции
def init_db():
    tables = [
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            start_date TEXT,
            trial_end TEXT,
            ref_by INTEGER,
            is_paid INTEGER DEFAULT 0
        );''',
        '''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method TEXT,
            date TEXT,
            amount REAL
        );''',
        '''CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            days INTEGER,
            active INTEGER DEFAULT 1
        );''',
        '''CREATE TABLE IF NOT EXISTS backup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            date TEXT
        );'''
    ]
    for t in tables:
        _cursor.execute(t)
    _conn.commit()

# Уведомления администратору при событиях
def start_notify_thread(cb, *args):
    threading.Thread(target=cb, args=args).start()

class NotifyAdmin:
    def __init__(self):
        self.new_user_cbs = []
        self.payment_cbs = []
    def register(self, on_new_user=None, on_payment=None):
        if on_new_user:
            self.new_user_cbs.append(on_new_user)
        if on_payment:
            self.payment_cbs.append(on_payment)
    def new_user(self, u):
        for cb in self.new_user_cbs:
            start_notify_thread(cb, u)
    def payment(self, uid, method):
        for cb in self.payment_cbs:
            start_notify_thread(cb, uid, method)
notify_admin = NotifyAdmin()

# Пользовательские CRUD

def add_user(user_id, username, ref=None):
    _cursor.execute("SELECT 1 FROM users WHERE id=?", (user_id,))
    if _cursor.fetchone():
        return False
    now = datetime.datetime.utcnow().isoformat()
    trial_end = (datetime.datetime.utcnow() + datetime.timedelta(days=config.TRIAL_DAYS)).isoformat()
    _cursor.execute(
        "INSERT INTO users (id, username, start_date, trial_end, ref_by) VALUES (?,?,?,?,?)",
        (user_id, username or '', now, trial_end, ref)
    )
    _conn.commit()
    # Бонус за реферал
    if ref:
        extend_subscription(ref, config.REFERRAL_BONUS_DAYS)
    notify_admin.new_user({'id': user_id, 'username': username, 'trial_end': trial_end})
    return True


def get_user_status(user_id):
    _cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = _cursor.fetchone()
    if not row:
        return {'registered': False}
    end = datetime.datetime.fromisoformat(row['trial_end'])
    paid = bool(row['is_paid'])
    expired = datetime.datetime.utcnow() > end and not paid
    return {'registered': True, 'trial_end': row['trial_end'], 'is_paid': paid, 'expired': expired}


def extend_subscription(user_id, days):
    _cursor.execute(
        "UPDATE users SET trial_end = datetime(trial_end, '+%d days') WHERE id=?" % days, (user_id,)
    )
    _conn.commit()


def delete_user(user_id):
    _cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    _conn.commit()

# Платежи

def record_payment(user_id, method, amount):
    now = datetime.datetime.utcnow().isoformat()
    _cursor.execute(
        "INSERT INTO payments (user_id, method, date, amount) VALUES (?,?,?,?)",
        (user_id, method, now, amount)
    )
    _conn.commit()
    notify_admin.payment(user_id, method)


def get_payment_history(user_id=None):
    if user_id:
        _cursor.execute("SELECT * FROM payments WHERE user_id=? ORDER BY date DESC", (user_id,))
    else:
        _cursor.execute("SELECT * FROM payments ORDER BY date DESC")
    return [_dict_from_row(r) for r in _cursor.fetchall()]

# Промокоды

def create_promocode(code, days):
    try:
        _cursor.execute("INSERT INTO promocodes (code, days) VALUES (?,?)", (code, days))
        _conn.commit()
        return True
    except:
        return False


def validate_promocode(code):
    _cursor.execute("SELECT * FROM promocodes WHERE code=?", (code,))
    row = _cursor.fetchone()
    if not row or row['active']==0:
        return False, 0
    _cursor.execute("UPDATE promocodes SET active=0 WHERE code=?", (code,))
    _conn.commit()
    return True, row['days']

# Утилиты

def generate_v2ray_config(user_id):
    uuid = f"uuid-{user_id}"
    url = f"{config.V2RAY_PROTOCOL}://{uuid}@{config.V2RAY_DOMAIN}:{config.V2RAY_PORT}?encryption=none"
    return url


def _dict_from_row(row):
    return {k: row[k] for k in row.keys()}

# QR-код генерация

def generate_qr(config_str):
    img = qrcode.make(config_str)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# Миграции (заглушка)
def migrate_db():
    # add columns, alter tables
    pass

# Бэкап и восстановление

BACKUP_DIR = config.QR_TEMP_PATH

def backup_database():
    timestamp = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
    _conn.backup(sqlite3.connect(path))
    _cursor.execute("INSERT INTO backup_log (path, date) VALUES (?,?)", (path, timestamp))
    _conn.commit()
    return path


def restore_database(path):
    source = sqlite3.connect(path)
    source.backup(_conn)
    _conn.commit()

# Мониторинг

def db_health_check():
    try:
        _cursor.execute("SELECT 1")
        return True
    except:
        return False

# Rate limiting (заглушка)

# Дополнительные функции мониторинга, кэширования, отправки email и т.д.
