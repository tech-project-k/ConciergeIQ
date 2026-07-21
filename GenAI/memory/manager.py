# =====================================================================
# Why it exists:
# Saves and loads conversation messages between the traveler and the AI.
# =====================================================================

import sqlite3
import json
import os
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger("memory_manager")

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "conciergeiq_genai_memory.db")
)

class MemoryManager:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guest_preferences (
                session_id TEXT PRIMARY KEY,
                preferences_json TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.commit()
        conn.close()

    def get_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    def save_preferences(self, session_id: str, preferences_dict: Dict[str, Any]) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO guest_preferences (session_id, preferences_json) VALUES (?, ?)",
            (session_id, json.dumps(preferences_dict))
        )
        conn.commit()
        conn.close()

    def get_preferences(self, session_id: str) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT preferences_json FROM guest_preferences WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else {}

    def clear_session(self, session_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM guest_preferences WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

memory_manager = MemoryManager()
