# 🤖 Informatics ChatBot - Trợ lý học tập môn Tin học

Hệ thống ChatBot thông minh hỗ trợ học tập môn Tin học, tích hợp trí tuệ nhân tạo (Generative AI) và cơ sở dữ liệu nội dung chương trình học phổ thông.

---

## ✨ Tính năng chính

### 👤 Dành cho Học sinh
- **Đăng ký/Đăng nhập**: Quản lý tài khoản cá nhân, lưu trữ lịch sử trò chuyện.
- **Hỏi đáp thông minh**: Chat với AI được huấn luyện dựa trên nội dung sách giáo khoa (Tin học 6, Tin học 9,...).
- **Quản lý phiên chat**: Tạo nhiều chủ đề trò chuyện, đổi tên hoặc xóa các phiên chat cũ.
- **Phản hồi nhanh**: Tự động gợi ý các chủ đề liên quan nếu câu hỏi chưa có trong dữ liệu gốc.
- **Quên mật khẩu**: Hỗ trợ đặt lại mật khẩu nhanh chóng.

### 🛠️ Dành cho Quản trị viên (Admin)
- **Bảng điều khiển (Dashboard)**: Quản lý toàn diện hệ thống.
- **Quản lý nội dung học tập**: Thêm, sửa, xóa các chủ đề và yêu cầu cần đạt (lessons) thông qua giao diện trực quan.
- **Quản lý người dùng**: Xem danh sách học sinh, cấp quyền Admin hoặc xóa tài khoản.
- **Cấu hình hệ thống**: Thay đổi API Key (Gemini/OpenRouter), điều chỉnh Max Tokens, chọn khối lớp (Grade) và tệp dữ liệu hoạt động.
- **Thống kê & Báo cáo**: Theo dõi số lượng câu hỏi, các chủ đề được quan tâm nhiều nhất thông qua biểu đồ và bảng số liệu.
- **Nhật ký lỗi (Logs)**: Theo dõi hoạt động hệ thống để kịp thời xử lý sự cố.

---

## 🚀 Công nghệ sử dụng

- **Backend**: Python, Flask
- **AI Engine**: Google Gemini API (hỗ trợ fallback qua OpenRouter)
- **Database**: SQLite3 (Quản lý người dùng, phiên chat, thống kê)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS/Mobile responsive)
- **Data storage**: JSON (Lưu trữ nội dung yêu cầu cần đạt theo từng khối lớp)

---

## 🛠️ Hướng dẫn cài đặt

### 1. Yêu cầu hệ thống
- Python 3.8 trở lên.
- API Key từ [Google AI Studio](https://aistudio.google.com/) hoặc [OpenRouter](https://openrouter.ai/).

### 2. Cài đặt môi trường
Mở terminal tại thư mục gốc và chạy các lệnh sau:

```bash
# Tạo môi trường ảo (khuyến nghị)
python -m venv .venv
source .venv/bin/activate  # Trên Windows dùng: .venv\Scripts\activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường
Tạo file `.env` tại thư mục gốc với các nội dung sau:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
SECRET_KEY=yoursecretkey
```

### 4. Khởi chạy ứng dụng
```bash
python app.py
```
Ứng dụng sẽ chạy tại địa chỉ: `http://127.0.0.1:5000`

---

## 🔑 Tài khoản mặc định

- **Admin**: `admin` / `admin123`
- Bạn có thể thay đổi mật khẩu hoặc tạo thêm admin mới trong giao diện quản trị.

---

## 📂 Cấu trúc thư mục

- `app.py`: Tệp tin chính xử lý logic server và API.
- `templates/`: Giao diện người dùng (HTML).
- `static/`: Chứa các tệp CSS, JS, hình ảnh.
- `*.json`: Dữ liệu nội dung học tập (ví dụ: `informatics9.json`).
- `users.db`: Cơ sở dữ liệu SQLite (Tự động tạo khi chạy lần đầu).
- `config.json`: Lưu trữ cấu hình hệ thống động từ Admin Dashboard.

---

## 📩 Liên hệ
Nếu có bất kỳ thắc mắc hoặc góp ý nào, vui lòng liên hệ đội ngũ phát triển.
