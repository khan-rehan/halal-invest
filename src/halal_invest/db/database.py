"""SQLite database initialization and connection."""

import sqlite3
from pathlib import Path

DB_DIR = Path.home() / ".halal-invest"
DB_PATH = DB_DIR / "portfolio.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating the DB and tables if needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    init_tables(conn)
    return conn


def init_tables(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('buy', 'sell')),
            shares REAL NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            target_buy_price REAL,
            target_sell_price REAL,
            notes TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS purification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            impure_percentage REAL NOT NULL,
            dividend_amount REAL NOT NULL,
            purification_amount REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
