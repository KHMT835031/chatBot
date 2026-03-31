from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import requests
import json
import sqlite3
import psycopg2
from psycopg2 import extras
import os
from datetime import timedelta
from dotenv import load_dotenv
from functools import wraps

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
MAX_TOKEN_ENV = int(os.getenv("MAX_TOKEN", 2048))
app_secret_key = os.getenv("SECRET_KEY", "supersecretkey")
DATABASE_URL = os.getenv("DATABASE_URL") # Tham số mới cho Neon/Postgres

# The URL will be constructed when needed to ensure the latest API_KEY is used
def get_gemini_url(api_key):
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

app = Flask(__name__)
app.secret_key = app_secret_key
# Cấu hình thời gian tự động đăng xuất (ví dụ: 30 phút)
app.permanent_session_lifetime = timedelta(minutes=30)

DB_PATH = "users.db"
DATA_PATH = "informatics9.json"
CONFIG_PATH = "config.json"
LOG_PATH = "error.log"
STATS_PATH = "chat_stats.json"

def get_db_connection():
    if DATABASE_URL:
        # Connect to Postgres (Neon)
        conn = psycopg2.connect(DATABASE_URL)
        return conn, "%s"
    else:
        # Connect to SQLite (Local)
        conn = sqlite3.connect(DB_PATH)
        return conn, "?"

def init_db():
    conn, p = get_db_connection()
    c = conn.cursor()
    
    # SQLite và Postgres có cú pháp tạo bảng hơi khác nhau
    if DATABASE_URL:
        # PostgreSQL syntax
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            class_name TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
            sender TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_stats (
            id SERIAL PRIMARY KEY,
            username TEXT,
            question TEXT,
            matched_keys TEXT
        )''')
        # Thêm bảng cấu hình hệ thống
        c.execute('''CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
    else:
        # SQLite syntax
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            class_name TEXT
        )''')
        try:
            c.execute("ALTER TABLE users ADD COLUMN class_name TEXT")
        except sqlite3.OperationalError:
            pass # Cột đã tồn tại
        c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            sender TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            question TEXT,
            matched_keys TEXT
        )''')
        # Thêm bảng cấu hình hệ thống cho SQLite
        c.execute('''CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')

    # Tạo tài khoản admin mẫu nếu chưa có
    c.execute(f"SELECT * FROM users WHERE username={p}", ("admin",))
    if not c.fetchone():
        c.execute(f"INSERT INTO users (username, password, is_admin) VALUES ({p}, {p}, 1)", ("admin", "admin123"))
    
    conn.commit()
    conn.close()

init_db()

def get_user(username):
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"SELECT id, username, password, is_admin, class_name FROM users WHERE username={p}", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "password": user[2], "is_admin": user[3], "class_name": user[4]}
    return None

def add_user(username, password, class_name=None, is_admin=0):
    conn, p = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(f"INSERT INTO users (username, password, class_name, is_admin) VALUES ({p}, {p}, {p}, {p})", (username, password, class_name, is_admin))
        conn.commit()
        return True
    except (sqlite3.IntegrityError, psycopg2.IntegrityError):
        return False
    finally:
        conn.close()

def get_all_users():
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin, class_name FROM users")
    users = [{"id": row[0], "username": row[1], "is_admin": bool(row[2]), "class_name": row[3]} for row in c.fetchall()]
    conn.close()
    return users

def set_admin(user_id):
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE users SET is_admin=1 WHERE id={p}", (user_id,))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM users WHERE id={p}", (user_id,))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def load_lessons():
    path = get_current_data_path()
    if not os.path.exists(path):
        # Create an empty dict if the file is missing
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_lessons(lessons):
    path = get_current_data_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

def load_config():
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM system_config")
    rows = c.fetchall()
    conn.close()

    if not rows:
        # Nếu chưa có trong DB, trả về config mặc định
        return {
            "API_KEY": API_KEY, 
            "MAX_TOKEN": MAX_TOKEN_ENV,
            "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
            "OPENROUTER_MODEL": OPENROUTER_MODEL,
            "CURRENT_GRADE": "Tin học 9",
            "DATA_FILE": "informatics9.json"
        }
    
    config = {row[0]: row[1] for row in rows}
    # Chuyển MAX_TOKEN sang số nguyên
    if "MAX_TOKEN" in config:
        config["MAX_TOKEN"] = int(config["MAX_TOKEN"])
    return config

def save_config(config):
    conn, p = get_db_connection()
    c = conn.cursor()
    for key, value in config.items():
        if DATABASE_URL:
            # Postgres: UPSERT style
            c.execute(f"INSERT INTO system_config (key, value) VALUES ({p}, {p}) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (key, str(value)))
        else:
            # SQLite: UPSERT style
            c.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_current_data_path():
    config = load_config()
    return config.get("DATA_FILE", "informatics9.json")

def get_current_grade_name():
    config = load_config()
    return config.get("CURRENT_GRADE", "Tin học 9")

@app.context_processor
def inject_grade_name():
    return dict(get_current_grade_name=get_current_grade_name)

def log_error(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def openrouter_generate_content(prompt):
    if not OPENROUTER_API_KEY:
        return "❌ Lỗi: Chưa cấu hình OpenRouter API Key."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Informatics 9 ChatBot"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    url = "https://openrouter.ai/api/v1/chat/completions"
    try:
        resp = requests.post(url, headers=headers, json=data)
        result = resp.json()
        if "error" in result:
            log_error(f"OpenRouter API error: {result['error']}")
            return "❌ Lỗi khi gọi OpenRouter API."
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log_error(f"OpenRouter Exception: {str(e)}")
        return "❌ Lỗi khi gọi OpenRouter API."

def gemini_generate_content(prompt):
    config = load_config()
    api_key = config.get("API_KEY", API_KEY)
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    url = get_gemini_url(api_key)
    try:
        resp = requests.post(url, headers=headers, json=data)
        result = resp.json()
        # Nếu Gemini trả về lỗi, thử qua OpenRouter
        if "error" in result:
            log_error(f"Gemini API error (fallback to OR): {result['error']}")
            return openrouter_generate_content(prompt)
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        log_error(f"Gemini Exception (fallback to OR): {str(e)}")
        # Trường hợp ngoại lệ (mạng, API down), thử qua OpenRouter
        return openrouter_generate_content(prompt)

def find_lesson_by_content(user_msg, lessons):
    user_msg_lower = user_msg.lower()
    matched_lessons = []
    for bai in lessons.values():
        for k, v in bai.items():
            if k != "ten":
                if user_msg_lower in v.lower():
                    matched_lessons.append((bai, v))
                    break # Chỉ cần khớp 1 phần trong bài là được
    return matched_lessons

def log_chat_stat(username, question, matched_keys):
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(
        f"INSERT INTO chat_stats (username, question, matched_keys) VALUES ({p}, {p}, {p})",
        (username or "guest", question, json.dumps(matched_keys, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

def get_stats():
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, question, matched_keys FROM chat_stats")
    rows = c.fetchall()
    conn.close()
    stats = []
    for row in rows:
        username, question, matched_keys = row
        try:
            matched_keys = json.loads(matched_keys)
        except Exception:
            matched_keys = []
        stats.append({
            "username": username,
            "question": question,
            "matched_keys": matched_keys,
        })
    return stats

@app.route("/")
def index():
    lessons = load_lessons()
    # Lấy ra 2 tên chủ đề đầu tiên làm ví dụ
    example_topics = [v['ten'] for v in list(lessons.values())[:2]]
    return render_template("index.html", 
                           user=session.get("user"), 
                           is_admin=session.get("is_admin"),
                           example_topics=example_topics)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        class_name = request.form.get("class_name", "").strip()
        if not username or not password:
            flash("Vui lòng nhập đầy đủ thông tin.")
            return redirect(url_for("register"))
        if add_user(username, password, class_name):
            flash("Đăng ký thành công. Vui lòng đăng nhập.")
            return redirect(url_for("login"))
        else:
            flash("Tên đăng nhập đã tồn tại.")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = get_user(username)
        if user and user["password"] == password:
            session.permanent = True  # Kích hoạt thời gian hết hạn session đã cấu hình
            session["user"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            class_info = f" ({user['class_name']})" if user.get("class_name") else ""
            flash(f"Đăng nhập thành công. Chào mừng {user['username']}{class_info}!")
            return redirect(url_for("index"))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu.")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất.")
    return redirect(url_for("login"))

def save_message(session_id, sender, message):
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"INSERT INTO chat_messages (session_id, sender, message) VALUES ({p}, {p}, {p})", (session_id, sender, message))
    conn.commit()
    conn.close()

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    session_id = request.json.get("session_id")

    if not user_msg:
        return jsonify({"reply": "❌ Câu hỏi không hợp lệ."}), 400

    user_msg_lower = user_msg.lower()
    lessons = load_lessons()
    matched_lessons = find_lesson_by_content(user_msg_lower, lessons)

    matched_keys = []
    for bai, _ in matched_lessons:
        for key, value in lessons.items():
            if value is bai:
                matched_keys.append(key)
                break

    log_chat_stat(session.get("user"), user_msg_lower, matched_keys)

    # Lưu tin nhắn của người dùng nếu đã đăng nhập và có session_id
    if session.get("user") and session_id:
        save_message(session_id, "user", user_msg)

    grade_name = get_current_grade_name()
    if matched_lessons:
        related_content = "\n".join(content for _, content in matched_lessons)
        prompt = (
            f"Bạn là trợ lý học tập {grade_name}. Dưới đây là các nội dung yêu cầu cần đạt của chương trình {grade_name}:\n"
            f"{related_content}\n\n"
            f"Câu hỏi của người dùng: \"{user_msg}\"\n"
            "Yêu cầu:\n"
            f"- Trả lời trực tiếp câu hỏi của người dùng dựa trên các nội dung liên quan ở trên, ngắn gọn, đúng trọng tâm, dễ hiểu, phù hợp với trình độ {grade_name}.\n"
            "- Nếu có công thức hoặc đoạn mã, hãy đặt trong khối code markdown phù hợp (ví dụ: ```excel ... ```).\n"
            "- Không sử dụng màu nền, biểu tượng, hoặc các ký hiệu đặc biệt ngoài markdown cơ bản."
        )
        reply = gemini_generate_content(prompt)
    else:
        grade_name = get_current_grade_name()
        suggest_prompt = (
            f"Bạn là trợ lý học tập {grade_name}. Dưới đây là các nội dung yêu cầu cần đạt của chương trình {grade_name}:\n"
            + "\n".join(
                v for bai in lessons.values() for k, v in bai.items() if k != "ten"
            ) +
            f"\n\nCâu hỏi của người dùng: \"{user_msg}\"\n"
            "Yêu cầu:\n"
            f"- Nếu không có nội dung nào liên quan để trả lời, hãy đối thoại thân thiện với người dùng và gợi ý một hoặc một vài nội dung/chủ đề trong chương trình {grade_name} mà bạn nghĩ người dùng có thể quan tâm hoặc nên hỏi tiếp."
        )
        reply = gemini_generate_content(suggest_prompt)

    # Lưu trả lời của bot
    if session.get("user") and session_id:
        save_message(session_id, "bot", reply)

    return jsonify({"reply": reply})


@app.route("/admin")
@admin_required
def admin_dashboard():
    lessons = load_lessons()
    users = get_all_users()
    return render_template("admin_dashboard.html", lessons=lessons, users=users)

@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def admin_add():
    if request.method == "POST":
        lessons = load_lessons()
        key = request.form["key"].strip()
        ten = request.form["ten"].strip()
        
        # Lấy các cặp key-value nội dung động
        custom_keys = request.form.getlist("custom_key[]")
        custom_vals = request.form.getlist("custom_val[]")
        
        if not key or not ten:
            flash("Vui lòng nhập đầy đủ thông tin.")
            return redirect(url_for("admin_add"))
        if key in lessons:
            flash("Chủ đề đã tồn tại.")
            return redirect(url_for("admin_add"))
        
        lessons[key] = {"ten": ten}
        for ck, cv in zip(custom_keys, custom_vals):
            if ck.strip() and cv.strip():
                lessons[key][ck.strip()] = cv.strip()
        
        save_lessons(lessons)
        flash("Đã thêm chủ đề mới.")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add.html")

@app.route("/admin/edit/<key>", methods=["GET", "POST"])
@admin_required
def admin_edit(key):
    lessons = load_lessons()
    if key not in lessons:
        flash("Không tìm thấy chủ đề.")
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        ten = request.form["ten"].strip()
        custom_keys = request.form.getlist("custom_key[]")
        custom_vals = request.form.getlist("custom_val[]")
        
        lessons[key] = {"ten": ten}
        for ck, cv in zip(custom_keys, custom_vals):
            if ck.strip() and cv.strip():
                lessons[key][ck.strip()] = cv.strip()
                
        save_lessons(lessons)
        flash("Đã cập nhật chủ đề.")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_edit.html", key=key, lesson=lessons[key])

@app.route("/admin/delete/<key>", methods=["POST"])
@admin_required
def admin_delete(key):
    lessons = load_lessons()
    if key in lessons:
        del lessons[key]
        save_lessons(lessons)
        flash("Đã xóa chủ đề.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/set_admin/<int:user_id>", methods=["POST"])
@admin_required
def admin_set_admin(user_id):
    set_admin(user_id)
    flash("Đã cấp quyền admin cho tài khoản.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    # Không cho phép admin tự xóa chính mình
    user = get_user(session["user"])
    if user and user[0] == user_id:
        flash("Không thể xóa tài khoản admin đang đăng nhập.")
        return redirect(url_for("admin_dashboard"))
    delete_user(user_id)
    flash("Đã xóa tài khoản.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/change_password/<int:user_id>", methods=["POST"])
@admin_required
def admin_change_password(user_id):
    new_password = request.form.get("new_password", "").strip()
    if not new_password:
        flash("Mật khẩu mới không được để trống.")
        return redirect(url_for("admin_dashboard"))
    
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE users SET password={p} WHERE id={p}", (new_password, user_id))
    conn.commit()
    conn.close()
    
    flash("Đã cập nhật mật khẩu mới.")
    return redirect(url_for("admin_dashboard"))

def update_password(username, new_password):
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE users SET password={p} WHERE username={p}", (new_password, username))
    conn.commit()
    conn.close()

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"].strip()
        new_password = request.form["new_password"]
        user = get_user(username)
        if not user:
            flash("Không tìm thấy tài khoản.")
            return redirect(url_for("forgot_password"))
        update_password(username, new_password)
        flash("Đặt lại mật khẩu thành công. Vui lòng đăng nhập.")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/admin/config", methods=["GET", "POST"])
@admin_required
def admin_config():
    config = load_config()
    # Lấy danh sách các file .json trong thư mục để người dùng chọn
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and f != 'package-lock.json' and f != 'package.json']
    
    if request.method == "POST":
        api_key = request.form.get("API_KEY", "").strip()
        max_token = request.form.get("MAX_TOKEN", "").strip()
        or_api_key = request.form.get("OPENROUTER_API_KEY", "").strip()
        or_model = request.form.get("OPENROUTER_MODEL", "").strip()
        current_grade = request.form.get("CURRENT_GRADE", "Tin học 9").strip()
        data_file = request.form.get("DATA_FILE", "informatics9.json").strip()
        
        if not api_key or not max_token.isdigit():
            flash("Vui lòng nhập đầy đủ và hợp lệ.")
            return redirect(url_for("admin_config"))
        
        config["API_KEY"] = api_key
        config["MAX_TOKEN"] = int(max_token)
        config["OPENROUTER_API_KEY"] = or_api_key
        config["OPENROUTER_MODEL"] = or_model
        config["CURRENT_GRADE"] = current_grade
        config["DATA_FILE"] = data_file
        save_config(config)
        flash("Đã cập nhật cấu hình hệ thống.")
        return redirect(url_for("admin_config"))
    return render_template("admin_config.html", config=config, json_files=json_files)

@app.route("/admin/logs")
@admin_required
def admin_logs():
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as f:
            logs = f.readlines()[-100:]  # Hiển thị tối đa 100 dòng cuối
    return render_template("admin_logs.html", logs=logs)

@app.route("/admin/stats")
@admin_required
def admin_stats():
    stats = get_stats()
    lessons = load_lessons()
    lesson_keys = list(lessons.keys())
    # Thống kê số lượng câu hỏi theo user
    user_count = {}
    for s in stats:
        user = s["username"]
        user_count[user] = user_count.get(user, 0) + 1

    # Thống kê chủ đề được hỏi nhiều nhất (kết hợp matched_keys và Gemini API)
    topic_count = {}
    config = load_config()
    api_key = config.get("API_KEY", API_KEY)
    headers = {"Content-Type": "application/json"}
    url = get_gemini_url(api_key)

    def gemini_classify_topic(question):
        config = load_config()
        api_key = config.get("API_KEY", API_KEY)
        or_api_key = config.get("OPENROUTER_API_KEY", OPENROUTER_API_KEY)
        or_model = config.get("OPENROUTER_MODEL", OPENROUTER_MODEL)
        grade_name = get_current_grade_name()
        
        prompt = (
            f"Bạn là trợ lý {grade_name}. Dưới đây là các chủ đề chương trình {grade_name}:\n"
            + "\n".join([f"- {k}: {lessons[k]['ten']}" for k in lesson_keys]) +
            f"\n\nCâu hỏi: \"{question}\"\n"
            "Hãy trả lời duy nhất bằng key chủ đề phù hợp nhất trong danh sách trên (ví dụ: chu_de_1, chu_de_2, ...). Nếu không rõ thì trả về 'unknown'."
        )
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        url = get_gemini_url(api_key)
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=8)
            result = resp.json()
            if "candidates" in result:
                text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                key = text.split()[0]
                if key in lesson_keys:
                    return key
            
            # Nếu Gemini lỗi, thử OpenRouter
            if or_api_key:
                headers_or = {
                    "Authorization": f"Bearer {or_api_key}",
                    "Content-Type": "application/json"
                }
                data_or = {
                    "model": or_model,
                    "messages": [{"role": "user", "content": prompt}]
                }
                resp_or = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers_or, json=data_or, timeout=8)
                result_or = resp_or.json()
                if "choices" in result_or:
                    text = result_or["choices"][0]["message"]["content"].strip()
                    key = text.split()[0]
                    if key in lesson_keys:
                        return key
            return "unknown"
        except Exception as e:
            log_error(f"Classify error (fallback to OR if available): {str(e)}")
            return "unknown"

    for s in stats:
        matched = s.get("matched_keys", [])
        if matched:
            for key in matched:
                topic_count[key] = topic_count.get(key, 0) + 1
        else:
            # Dùng Gemini API để phân loại chủ đề nếu chưa có matched_keys
            key = gemini_classify_topic(s["question"])
            if key != "unknown":
                topic_count[key] = topic_count.get(key, 0) + 1

    user_count_sorted = sorted(user_count.items(), key=lambda x: x[1], reverse=True)
    topic_count_sorted = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
    return render_template("admin_stats.html",
        user_count=user_count_sorted,
        topic_count=topic_count_sorted,
        lessons=lessons,
        total=len(stats)
    )

@app.route("/session/create", methods=["POST"])
@login_required
def create_session():
    name = request.json.get("name", "Chưa đặt tên")
    user = get_user(session["user"])
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"INSERT INTO chat_sessions (user_id, name) VALUES ({p}, {p}) RETURNING id", (user["id"], name))
    if DATABASE_URL:
        new_id = c.fetchone()[0]
    else:
        # SQLite doesn't support RETURNING, use lastrowid
        c.execute(f"SELECT last_insert_rowid()")
        new_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"session_id": new_id})

@app.route("/session/rename", methods=["POST"])
@login_required
def rename_session():
    session_id = request.json.get("session_id")
    new_name = request.json.get("name")
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE chat_sessions SET name={p} WHERE id={p} AND user_id=(SELECT id FROM users WHERE username={p})",
              (new_name, session_id, session["user"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/session/delete", methods=["POST"])
@login_required
def delete_session():
    session_id = request.json.get("session_id")
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM chat_messages WHERE session_id={p}", (session_id,))
    c.execute(f"DELETE FROM chat_sessions WHERE id={p} AND user_id=(SELECT id FROM users WHERE username={p})",
              (session_id, session["user"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/session/list", methods=["GET"])
@login_required
def list_sessions():
    user = get_user(session["user"])
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"SELECT id, name, created_at FROM chat_sessions WHERE user_id={p} ORDER BY created_at DESC", (user["id"],))
    sessions = [
        {"id": row[0], "name": row[1], "created_at": str(row[2])} for row in c.fetchall()
    ]
    conn.close()
    return jsonify({"sessions": sessions})

@app.route("/session/messages", methods=["POST"])
@login_required
def get_session_messages():
    session_id = request.json.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    conn, p = get_db_connection()
    c = conn.cursor()
    c.execute(f"SELECT sender, message, timestamp FROM chat_messages WHERE session_id={p} ORDER BY timestamp ASC", (session_id,))
    messages = [
        {"sender": row[0], "message": row[1], "timestamp": str(row[2])} for row in c.fetchall()
    ]
    conn.close()
    return jsonify({"messages": messages})

if __name__ == "__main__":
    app.run(debug=True)