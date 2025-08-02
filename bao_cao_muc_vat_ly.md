# BÁO CÁO MỨC VẬT LÝ HỆ THỐNG CHATBOT TIN HỌC 9

## 1. TỔNG QUAN HỆ THỐNG

### 1.1. Mô tả hệ thống
Hệ thống ChatBot Tin học 9 là một ứng dụng web được xây dựng bằng Python Flask, tích hợp với Google Gemini AI để cung cấp trợ lý học tập cho môn Tin học lớp 9. Hệ thống hỗ trợ đa người dùng với phân quyền admin và user thường.

### 1.2. Kiến trúc tổng thể
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python Flask
- **Database**: SQLite
- **AI Service**: Google Gemini API
- **Deployment**: Local development server

## 2. CẤU TRÚC VẬT LÝ

### 2.1. Cấu trúc thư mục
```
chatBot/
├── app.py                    # File chính của ứng dụng Flask
├── config.json              # Cấu hình hệ thống
├── informatics9.json        # Dữ liệu nội dung Tin học 9
├── users.db                 # Database SQLite
├── requirements.txt         # Dependencies Python
├── static/
│   └── css/
│       └── style.css       # Stylesheet chính
├── templates/               # HTML templates
│   ├── index.html          # Trang chính chat
│   ├── login.html          # Trang đăng nhập
│   ├── register.html       # Trang đăng ký
│   ├── admin_dashboard.html # Dashboard admin
│   ├── admin_add.html      # Thêm nội dung
│   ├── admin_edit.html     # Sửa nội dung
│   ├── admin_config.html   # Cấu hình hệ thống
│   ├── admin_logs.html     # Xem logs
│   ├── admin_stats.html    # Thống kê
│   └── forgot_password.html # Quên mật khẩu
└── Lib/                    # Virtual environment
```

### 2.2. Các file cấu hình vật lý

#### 2.2.1. app.py (21KB, 582 dòng)
- **Chức năng**: File chính chứa toàn bộ logic ứng dụng
- **Các thành phần chính**:
  - Khởi tạo Flask app
  - Định nghĩa routes và endpoints
  - Xử lý authentication và authorization
  - Tích hợp Gemini API
  - Quản lý database operations

#### 2.2.2. config.json (82B, 4 dòng)
```json
{
  "API_KEY": "AIzaSyDlftg_bjcLMXklRtcoGbVn70BKpxUHyKo",
  "MAX_TOKEN": 2048
}
```
- **Chức năng**: Lưu trữ cấu hình hệ thống
- **Thông tin**: API key cho Gemini và giới hạn token

#### 2.2.3. informatics9.json (5.9KB, 72 dòng)
- **Chức năng**: Cơ sở dữ liệu nội dung Tin học 9
- **Cấu trúc**: 6 chủ đề chính với nội dung chi tiết
- **Dung lượng**: 5.9KB với 72 dòng JSON

#### 2.2.4. users.db (56KB, 176 dòng)
- **Chức năng**: Database SQLite chính
- **Cấu trúc bảng**:
  - `users`: Thông tin người dùng
  - `chat_sessions`: Phiên chat
  - `chat_messages`: Tin nhắn chat
  - `chat_stats`: Thống kê chat

## 3. CÁC CHỨC NĂNG VÀ MỨC VẬT LÝ

### 3.1. Chức năng Authentication

#### 3.1.1. Đăng ký tài khoản
- **Route**: `/register` (GET, POST)
- **Template**: `templates/register.html` (1.0KB, 27 dòng)
- **CSS**: Responsive design trong `style.css`
- **Database**: INSERT vào bảng `users`
- **Validation**: Kiểm tra username tồn tại

#### 3.1.2. Đăng nhập
- **Route**: `/login` (GET, POST)
- **Template**: `templates/login.html` (1.1KB, 28 dòng)
- **Session**: Lưu thông tin user trong Flask session
- **Database**: SELECT từ bảng `users`

#### 3.1.3. Quên mật khẩu
- **Route**: `/forgot_password` (GET, POST)
- **Template**: `templates/forgot_password.html` (1.0KB, 27 dòng)
- **Database**: UPDATE password trong bảng `users`

### 3.2. Chức năng Chat

#### 3.2.1. Giao diện chat chính
- **Route**: `/` (GET)
- **Template**: `templates/index.html` (11KB, 252 dòng)
- **JavaScript**: Xử lý real-time chat
- **CSS**: Responsive design với media queries
- **Features**:
  - Markdown rendering cho bot messages
  - Session management
  - Real-time message display

#### 3.2.2. API Chat
- **Route**: `/chat` (POST)
- **Input**: JSON với message và session_id
- **Processing**:
  - Tìm kiếm nội dung liên quan trong `informatics9.json`
  - Gọi Gemini API với prompt được tạo
  - Lưu thống kê vào database
- **Output**: JSON response với reply

#### 3.2.3. Session Management
- **Routes**:
  - `/session/create` (POST): Tạo session mới
  - `/session/rename` (POST): Đổi tên session
  - `/session/delete` (POST): Xóa session
  - `/session/list` (GET): Danh sách sessions
  - `/session/messages` (POST): Lấy tin nhắn session

### 3.3. Chức năng Admin

#### 3.3.1. Dashboard Admin
- **Route**: `/admin` (GET)
- **Template**: `templates/admin_dashboard.html` (4.0KB, 96 dòng)
- **Features**: Hiển thị danh sách nội dung và users

#### 3.3.2. Quản lý nội dung
- **Thêm nội dung**:
  - Route: `/admin/add` (GET, POST)
  - Template: `templates/admin_add.html` (1.7KB, 39 dòng)
  - Database: Cập nhật `informatics9.json`

- **Sửa nội dung**:
  - Route: `/admin/edit/<key>` (GET, POST)
  - Template: `templates/admin_edit.html` (1.4KB, 31 dòng)

- **Xóa nội dung**:
  - Route: `/admin/delete/<key>` (POST)

#### 3.3.3. Quản lý người dùng
- **Set Admin**: `/admin/set_admin/<user_id>` (POST)
- **Delete User**: `/admin/delete_user/<user_id>` (POST)

#### 3.3.4. Cấu hình hệ thống
- **Route**: `/admin/config` (GET, POST)
- **Template**: `templates/admin_config.html` (1.1KB, 27 dòng)
- **File**: Cập nhật `config.json`

#### 3.3.5. Xem logs
- **Route**: `/admin/logs` (GET)
- **Template**: `templates/admin_logs.html` (750B, 24 dòng)
- **File**: Đọc từ `error.log`

#### 3.3.6. Thống kê
- **Route**: `/admin/stats` (GET)
- **Template**: `templates/admin_stats.html` (1.4KB, 43 dòng)
- **Features**: Thống kê theo user và topic

### 3.4. Tích hợp AI (Gemini)

#### 3.4.1. API Integration
- **URL**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
- **Method**: POST
- **Headers**: Content-Type: application/json
- **Authentication**: API Key trong config

#### 3.4.2. Prompt Engineering
- **Content Matching**: Tìm kiếm nội dung liên quan trong `informatics9.json`
- **Prompt Template**: Tạo prompt dựa trên nội dung tìm được
- **Response Processing**: Xử lý và format response từ Gemini

## 4. DATABASE SCHEMA

### 4.1. Bảng users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);
```

### 4.2. Bảng chat_sessions
```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### 4.3. Bảng chat_messages
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    sender TEXT,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
);
```

### 4.4. Bảng chat_stats
```sql
CREATE TABLE chat_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    question TEXT,
    matched_keys TEXT
);
```

## 5. FRONTEND ARCHITECTURE

### 5.1. CSS Structure (style.css - 815 dòng)
- **Responsive Design**: Media queries cho mobile, tablet, desktop
- **Component Styles**: Chat container, messages, forms, admin panels
- **Interactive Elements**: Buttons, inputs, hover effects
- **Markdown Rendering**: Code blocks, syntax highlighting

### 5.2. JavaScript Features
- **Real-time Chat**: AJAX calls to backend
- **Session Management**: Create, rename, delete sessions
- **Markdown Parser**: Custom rendering for bot messages
- **Form Validation**: Client-side validation
- **Dynamic UI**: Show/hide elements based on user state

## 6. DEPENDENCIES VÀ REQUIREMENTS

### 6.1. Python Dependencies (requirements.txt)
```
flask          # Web framework
requests       # HTTP client for API calls
gunicorn       # WSGI server for production
```

### 6.2. External Services
- **Google Gemini API**: AI service cho chat responses
- **SQLite**: Local database
- **Flask Session**: Session management

## 7. SECURITY VÀ AUTHENTICATION

### 7.1. Authentication Flow
- **Session-based**: Flask session với secret key
- **Password Storage**: Plain text (cần cải thiện)
- **Admin Authorization**: Decorator `@admin_required`

### 7.2. Security Measures
- **Input Validation**: Sanitize user inputs
- **SQL Injection Prevention**: Parameterized queries
- **CSRF Protection**: Flask built-in protection

## 8. PERFORMANCE VÀ SCALABILITY

### 8.1. Current Limitations
- **Single-threaded**: Flask development server
- **Local Database**: SQLite không phù hợp cho production
- **No Caching**: Mỗi request đều query database

### 8.2. Optimization Opportunities
- **Database Indexing**: Index trên username, session_id
- **Connection Pooling**: Cho database connections
- **Caching**: Redis cho session và content
- **Load Balancing**: Multiple instances

## 9. DEPLOYMENT VÀ MAINTENANCE

### 9.1. Development Environment
- **Python Virtual Environment**: Isolated dependencies
- **Local Development Server**: Flask debug mode
- **File-based Configuration**: JSON config files

### 9.2. Production Considerations
- **WSGI Server**: Gunicorn cho production
- **Environment Variables**: Cho sensitive data
- **Logging**: File-based logging system
- **Backup Strategy**: Database và content files

## 10. MONITORING VÀ LOGGING

### 10.1. Error Logging
- **File**: `error.log`
- **Content**: API errors, exceptions, system issues
- **Admin Interface**: View logs through web interface

### 10.2. Statistics Tracking
- **User Activity**: Chat sessions, messages
- **Content Usage**: Most asked topics
- **System Performance**: Response times, errors

## 11. KẾT LUẬN

Hệ thống ChatBot Tin học 9 được thiết kế với kiến trúc đơn giản nhưng hiệu quả, sử dụng Flask framework và tích hợp Google Gemini AI. Hệ thống hỗ trợ đầy đủ các chức năng từ authentication, chat, đến admin management. Tuy nhiên, cần cải thiện về security (password hashing) và scalability cho production deployment. 