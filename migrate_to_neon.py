import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SQLITE_DB = "users.db"
NEON_DB_URL = os.getenv("DATABASE_URL")

def migrate():
    if not NEON_DB_URL:
        print("❌ Lỗi: Chưa cấu hình DATABASE_URL trong file .env")
        return

    print("🚀 Bắt đầu chuyển đổi dữ liệu từ SQLite sang Neon...")

    # Kết nối SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_curr = sqlite_conn.cursor()

    # Kết nối Neon (Postgres)
    try:
        pg_conn = psycopg2.connect(NEON_DB_URL)
        pg_curr = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Lỗi kết nối Neon: {e}")
        return

    # 1. Tạo các bảng trên Neon (nếu chưa có)
    print("--- Đang tạo cấu trúc bảng trên Neon ---")
    pg_curr.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            class_name TEXT
        );
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
            sender TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chat_stats (
            id SERIAL PRIMARY KEY,
            username TEXT,
            question TEXT,
            matched_keys TEXT
        );
    ''')
    pg_conn.commit()

    # 2. Di chuyển dữ liệu bảng 'users'
    print("--- Đang di chuyển bảng: users ---")
    sqlite_curr.execute("SELECT id, username, password, is_admin, class_name FROM users")
    users = sqlite_curr.fetchall()
    for user in users:
        pg_curr.execute(
            "INSERT INTO users (id, username, password, is_admin, class_name) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            user
        )

    # 3. Di chuyển dữ liệu bảng 'chat_sessions'
    print("--- Đang di chuyển bảng: chat_sessions ---")
    sqlite_curr.execute("SELECT id, user_id, name, created_at FROM chat_sessions")
    sessions = sqlite_curr.fetchall()
    for session in sessions:
        pg_curr.execute(
            "INSERT INTO chat_sessions (id, user_id, name, created_at) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            session
        )

    # 4. Di chuyển dữ liệu bảng 'chat_messages'
    print("--- Đang di chuyển bảng: chat_messages ---")
    sqlite_curr.execute("SELECT id, session_id, sender, message, timestamp FROM chat_messages")
    messages = sqlite_curr.fetchall()
    for msg in messages:
        pg_curr.execute(
            "INSERT INTO chat_messages (id, session_id, sender, message, timestamp) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            msg
        )

    # 5. Di chuyển dữ liệu bảng 'chat_stats'
    print("--- Đang di chuyển bảng: chat_stats ---")
    sqlite_curr.execute("SELECT id, username, question, matched_keys FROM chat_stats")
    stats = sqlite_curr.fetchall()
    for s in stats:
        pg_curr.execute(
            "INSERT INTO chat_stats (id, username, question, matched_keys) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            s
        )

    pg_conn.commit()
    print("✅ Chuyển đổi dữ liệu THÀNH CÔNG!")

    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
