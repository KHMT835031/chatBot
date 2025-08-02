from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import requests
import json
import sqlite3
import os
from functools import wraps

API_KEY = "AIzaSyDlftg_bjcLMXklRtcoGbVn70BKpxUHyKo"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_PATH = "users.db"
DATA_PATH = "informatics9.json"
CONFIG_PATH = "config.json"
LOG_PATH = "error.log"
STATS_PATH = "chat_stats.json"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )''')
    # Tạo tài khoản admin mẫu nếu chưa có
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ("admin", "admin123", 1))
    # Bảng chat_sessions: mỗi session tương ứng 1 đoạn chat có thể đặt tên
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Bảng chat_messages: lưu từng câu hỏi-trả lời
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            sender TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
    ''')
    # Bảng chat_stats: lưu thống kê chat
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            question TEXT,
            matched_keys TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password, is_admin FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, password, is_admin=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, is_admin))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin FROM users")
    users = [{"id": row[0], "username": row[1], "is_admin": bool(row[2])} for row in c.fetchall()]
    conn.close()
    return users

def set_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
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
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_lessons(lessons):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # Tạo file config mặc định nếu chưa có
        config = {"API_KEY": API_KEY, "MAX_TOKEN": 2048}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return config
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def log_error(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    try:
        resp = requests.post(url, headers=headers, json=data)
        result = resp.json()
        # Nếu Gemini trả về lỗi
        if "error" in result:
            log_error(f"Gemini API error: {result['error']}")
            return "❌ Lỗi khi gọi Gemini API."
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        log_error(f"Exception: {str(e)}")
        return "❌ Lỗi khi gọi Gemini API."

def find_lesson_by_content(user_msg, lessons):
    user_msg_lower = user_msg.lower()
    matched_lessons = []
    for bai in lessons.values():
        for k in bai:
            if k.startswith("noidung"):
                if user_msg_lower in bai[k].lower():
                    matched_lessons.append((bai, bai[k]))
    return matched_lessons

def log_chat_stat(username, question, matched_keys):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_stats (username, question, matched_keys) VALUES (?, ?, ?)",
        (username or "guest", question, json.dumps(matched_keys, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_PATH)
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
    return render_template("index.html", user=session.get("user"), is_admin=session.get("is_admin"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Vui lòng nhập đầy đủ thông tin.")
            return redirect(url_for("register"))
        if add_user(username, password):
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
        if user and user[2] == password:
            session["user"] = user[1]
            session["is_admin"] = bool(user[3])
            flash("Đăng nhập thành công.")
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)", (session_id, sender, message))
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

    if matched_lessons:
        related_content = "\n".join(content for _, content in matched_lessons)
        prompt = (
            "Bạn là trợ lý học tập Tin học 9. Dưới đây là các nội dung yêu cầu cần đạt của chương trình Tin học 9:\n"
            f"{related_content}\n\n"
            f"Câu hỏi của người dùng: \"{user_msg}\"\n"
            "Yêu cầu:\n"
            "- Trả lời trực tiếp câu hỏi của người dùng dựa trên các nội dung liên quan ở trên, ngắn gọn, đúng trọng tâm, dễ hiểu, phù hợp với học sinh cấp 2.\n"
            "- Nếu có công thức hoặc đoạn mã, hãy đặt trong khối code markdown phù hợp (ví dụ: ```excel ... ```).\n"
            "- Không sử dụng màu nền, biểu tượng, hoặc các ký hiệu đặc biệt ngoài markdown cơ bản."
        )
        reply = gemini_generate_content(prompt)
    else:
        suggest_prompt = (
            "Bạn là trợ lý học tập Tin học 9. Dưới đây là các nội dung yêu cầu cần đạt của chương trình Tin học 9:\n"
            + "\n".join(
                bai[k] for bai in lessons.values() for k in bai if k.startswith("noidung")
            ) +
            f"\n\nCâu hỏi của người dùng: \"{user_msg}\"\n"
            "Yêu cầu:\n"
            "- Nếu không có nội dung nào liên quan để trả lời, hãy đối thoại thân thiện với người dùng và gợi ý một hoặc một vài nội dung/chủ đề trong chương trình Tin học 9 mà bạn nghĩ người dùng có thể quan tâm hoặc nên hỏi tiếp."
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
        vidu = request.form.get("vidu", "").splitlines()
        noidungs = {k: v for k, v in request.form.items() if k.startswith("noidung_") and v.strip()}
        if not key or not ten:
            flash("Vui lòng nhập đầy đủ thông tin.")
            return redirect(url_for("admin_add"))
        if key in lessons:
            flash("Chủ đề đã tồn tại.")
            return redirect(url_for("admin_add"))
        lessons[key] = {"ten": ten, "vidu": vidu}
        lessons[key].update(noidungs)
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
        vidu = request.form.get("vidu", "").splitlines()
        noidungs = {k: v for k, v in request.form.items() if k.startswith("noidung_") and v.strip()}
        lessons[key] = {"ten": ten, "vidu": vidu}
        lessons[key].update(noidungs)
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

def update_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
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
    if request.method == "POST":
        api_key = request.form.get("API_KEY", "").strip()
        max_token = request.form.get("MAX_TOKEN", "").strip()
        if not api_key or not max_token.isdigit():
            flash("Vui lòng nhập đầy đủ và hợp lệ.")
            return redirect(url_for("admin_config"))
        config["API_KEY"] = api_key
        config["MAX_TOKEN"] = int(max_token)
        save_config(config)
        flash("Đã cập nhật cấu hình hệ thống.")
        return redirect(url_for("admin_config"))
    return render_template("admin_config.html", config=config)

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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    def gemini_classify_topic(question):
        prompt = (
            "Bạn là trợ lý Tin học 9. Dưới đây là các chủ đề chương trình Tin học 9:\n"
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
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=8)
            result = resp.json()
            if "candidates" in result:
                text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                key = text.split()[0]
                if key in lesson_keys:
                    return key
            return "unknown"
        except Exception as e:
            log_error(f"Gemini classify error: {str(e)}")
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_sessions (user_id, name) VALUES (?, ?)", (user[0], name))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({"session_id": new_id})

@app.route("/session/rename", methods=["POST"])
@login_required
def rename_session():
    session_id = request.json.get("session_id")
    new_name = request.json.get("name")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE chat_sessions SET name=? WHERE id=? AND user_id=(SELECT id FROM users WHERE username=?)",
              (new_name, session_id, session["user"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/session/delete", methods=["POST"])
@login_required
def delete_session():
    session_id = request.json.get("session_id")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages WHERE session_id=?", (session_id,))
    c.execute("DELETE FROM chat_sessions WHERE id=? AND user_id=(SELECT id FROM users WHERE username=?)",
              (session_id, session["user"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/session/list", methods=["GET"])
@login_required
def list_sessions():
    user = get_user(session["user"])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, created_at FROM chat_sessions WHERE user_id=? ORDER BY created_at DESC", (user[0],))
    sessions = [
        {"id": row[0], "name": row[1], "created_at": row[2]} for row in c.fetchall()
    ]
    conn.close()
    return jsonify({"sessions": sessions})

@app.route("/session/messages", methods=["POST"])
@login_required
def get_session_messages():
    session_id = request.json.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT sender, message, timestamp FROM chat_messages WHERE session_id=? ORDER BY timestamp ASC", (session_id,))
    messages = [
        {"sender": row[0], "message": row[1], "timestamp": row[2]} for row in c.fetchall()
    ]
    conn.close()
    return jsonify({"messages": messages})

if __name__ == "__main__":
    app.run(debug=True)