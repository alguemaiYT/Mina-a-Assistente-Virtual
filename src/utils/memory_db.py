import sqlite3
import os
from typing import List, Tuple
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "memory.db")

def init_db():
    """Initialize the SQLite memories database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            keypoint TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Memories database initialized at %s", DB_PATH)

def save_memory(username: str, keypoint: str):
    """Save a new memory keypoint."""
    init_db()  # Ensure DB is created
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if exact keypoint already exists for user to avoid redundancy
    cursor.execute("SELECT id FROM memories WHERE username = ? AND keypoint = ?", (username, keypoint))
    if cursor.fetchone():
        conn.close()
        return
    cursor.execute("INSERT INTO memories (username, keypoint) VALUES (?, ?)", (username, keypoint))
    conn.commit()
    conn.close()
    logger.info("Saved memory: [%s] -> %s", username, keypoint)

def get_all_memories() -> List[Tuple[str, str]]:
    """Retrieve all saved memories."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, keypoint FROM memories ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as exc:
        logger.error("Failed to retrieve memories: %s", exc)
        return []
