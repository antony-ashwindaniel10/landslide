import hashlib
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(BASE_DIR, "data", "runtime")
DB_PATH = os.path.join(RUNTIME_DIR, "auth.sqlite")

_LOCK = threading.Lock()
_SESSION_DAYS = 7

DEMO_ACCOUNTS = (
    {
        "username": "admin",
        "password": "admin123",
        "display_name": "District Admin",
        "role": "admin",
    },
    {
        "username": "user",
        "password": "user123",
        "display_name": "Field Officer",
        "role": "user",
    },
)


def _connect():
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return digest.hex()


def init_auth():
    with _LOCK:
        connection = _connect()
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            now = datetime.now(timezone.utc).isoformat()
            for account in DEMO_ACCOUNTS:
                existing = connection.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (account["username"],),
                ).fetchone()
                if existing:
                    continue
                salt = secrets.token_hex(16)
                connection.execute(
                    """
                    INSERT INTO users
                    (username, display_name, role, salt, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        account["username"],
                        account["display_name"],
                        account["role"],
                        salt,
                        _hash_password(account["password"], salt),
                        now,
                    ),
                )
            connection.commit()
        finally:
            connection.close()


def _public_user(row):
    return {
        "username": row["username"],
        "display_name": row["display_name"],
        "role": row["role"],
    }


def register_user(username: str, password: str, display_name: str):
    username = (username or "").strip().lower()
    display_name = (display_name or "").strip()
    if len(username) < 3 or len(username) > 32:
        raise ValueError("Username must be 3–32 characters.")
    if not username.replace("_", "").isalnum():
        raise ValueError("Username can use letters, numbers, and underscores.")
    if len(password or "") < 6:
        raise ValueError("Password must be at least 6 characters.")
    if len(display_name) < 2:
        raise ValueError("Enter the name people should see on reports.")

    salt = secrets.token_hex(16)
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        connection = _connect()
        try:
            try:
                connection.execute(
                    """
                    INSERT INTO users
                    (username, display_name, role, salt, password_hash, created_at)
                    VALUES (?, ?, 'user', ?, ?, ?)
                    """,
                    (
                        username,
                        display_name,
                        salt,
                        _hash_password(password, salt),
                        now,
                    ),
                )
                connection.commit()
            except sqlite3.IntegrityError as error:
                raise ValueError("That username is already in use.") from error
        finally:
            connection.close()
    return login(username, password)


def login(username: str, password: str):
    username = (username or "").strip().lower()
    with _LOCK:
        connection = _connect()
        try:
            row = connection.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row is None:
                return None
            digest = _hash_password(password or "", row["salt"])
            if not secrets.compare_digest(digest, row["password_hash"]):
                return None
            token = secrets.token_urlsafe(32)
            expires = (
                datetime.now(timezone.utc) + timedelta(days=_SESSION_DAYS)
            ).isoformat()
            connection.execute(
                "INSERT INTO sessions (token, username, expires_at) VALUES (?, ?, ?)",
                (token, row["username"], expires),
            )
            connection.commit()
            return {"token": token, "user": _public_user(row)}
        finally:
            connection.close()


def user_from_token(token: str):
    if not token:
        return None
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        connection = _connect()
        try:
            row = connection.execute(
                """
                SELECT users.username, users.display_name, users.role, sessions.expires_at
                FROM sessions
                JOIN users ON users.username = sessions.username
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()
            if row is None or row["expires_at"] < now:
                if row is not None:
                    connection.execute(
                        "DELETE FROM sessions WHERE token = ?",
                        (token,),
                    )
                    connection.commit()
                return None
            return _public_user(row)
        finally:
            connection.close()


def logout(token: str):
    if not token:
        return
    with _LOCK:
        connection = _connect()
        try:
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
            connection.commit()
        finally:
            connection.close()
