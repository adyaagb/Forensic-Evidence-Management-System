
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import query

# Ensure users table with role
query(
    """
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(100) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      role ENUM('admin','readonly') DEFAULT 'readonly'
    )
    """,
    params=None,
    fetch=None
)

class User(UserMixin):
    def __init__(self, id, username, password_hash, role='readonly'):
        self.id = str(id)
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def by_id(user_id):
        row = query("SELECT * FROM users WHERE id=%s", (user_id,), fetch="one")
        return User(row['id'], row['username'], row['password_hash'], row['role']) if row else None

    @staticmethod
    def by_username(username):
        row = query("SELECT * FROM users WHERE username=%s", (username,), fetch="one")
        return User(row['id'], row['username'], row['password_hash'], row['role']) if row else None

    @staticmethod
    def create_admin_if_missing(username, password):
        row = query("SELECT id FROM users WHERE username=%s", (username,), fetch="one")
        if not row:
            ph = generate_password_hash(password)
            query("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'admin')",
                  (username, ph), fetch=None)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
