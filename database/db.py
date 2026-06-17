import sqlite3
from typing import Optional

class Database:
    def __init__(self, db_path: str = "hydration_bot.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    weight_kg REAL,
                    activity TEXT,
                    interval_minutes INTEGER,
                    start_time TEXT,
                    end_time TEXT,
                    daily_goal REAL,
                    consumed_ml REAL DEFAULT 0,
                    last_reminder_time TEXT,
                    is_active INTEGER DEFAULT 0,
                    channel_id INTEGER
                )
            """)
            conn.commit()

    def save_user_plan(self, user_id: int, weight: float, activity: str, interval: int, start: str, end: str, goal: float, channel_id: int):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, weight_kg, activity, interval_minutes, start_time, end_time, daily_goal, consumed_ml, is_active, channel_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            """, (user_id, weight, activity, interval, start, end, goal, channel_id))
            conn.commit()

    def get_user(self, user_id: int):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()

    def update_consumption(self, user_id: int, amount: float):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET consumed_ml = consumed_ml + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()

    def stop_plan(self, user_id: int):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()

    def get_active_plans(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE is_active = 1")
            return cursor.fetchall()

    def update_last_reminder(self, user_id: int, timestamp: str):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET last_reminder_time = ? WHERE user_id = ?", (timestamp, user_id))
            conn.commit()
