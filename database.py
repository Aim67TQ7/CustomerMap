
import sqlite3
import hashlib
from typing import Optional

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def validate_bunting_email(email: str) -> bool:
    return email.endswith('@buntingmagnetics.com')

def register_user(username: str, password: str, is_admin: bool = False) -> bool:
    if not validate_bunting_email(username):
        return False
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                 (username, hash_password(password), is_admin))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username: str, password: str) -> Optional[dict]:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?',
             (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {'id': user[0], 'username': user[1], 'is_admin': user[3]}
    return None
