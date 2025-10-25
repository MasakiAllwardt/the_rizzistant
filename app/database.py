"""Database operations for date summaries"""
import sqlite3
from datetime import datetime
from typing import Optional
from app.config import DB_PATH


def init_database():
    """Initialize the SQLite database and create the table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS date_summaries (
            uid TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_previous_summary(uid: str) -> Optional[str]:
    """Retrieve the previous date summary for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM date_summaries WHERE uid = ?", (uid,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def save_summary(uid: str, summary: str):
    """Save or replace the date summary for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO date_summaries (uid, summary, created_at)
        VALUES (?, ?, ?)
    """, (uid, summary, datetime.now()))
    conn.commit()
    conn.close()
