from flask import Flask, request, jsonify, render_template
import requests
import json

API_KEY = "AIzaSyDlftg_bjcLMXklRtcoGbVn70BKpxUHyKo"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

app = Flask(__name__)

with open("informatics9.json", encoding="utf-8") as f:
    lessons = json.load(f)

def gemini_generate_content(prompt):
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
    resp = requests.post(GEMINI_API_URL, headers=headers, json=data)
    try:
        result = resp.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()

    # Tìm xem có chủ đề nào liên quan đến ý nghĩa câu hỏi không
    matched_lessons = find_lesson_by_content(user_msg, lessons)
    if matched_lessons:
        # Nếu có liên quan, yêu cầu Gemini trả lời trực tiếp câu hỏi của người dùng dựa trên nội dung chủ đề
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
        return jsonify({"reply": reply})

    # Nếu không liên quan, đối thoại bình thường và hướng người dùng đến nội dung liên quan trong chủ đề
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
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)

"""
Bạn có thể public hệ thống chatbot Flask này trên các nền tảng sau:

1. **Heroku**  
   - Dễ triển khai, miễn phí cho dự án nhỏ, hỗ trợ Python/Flask.
2. **Render.com**  
   - Tương tự Heroku, dễ dùng, có gói miễn phí.
3. **Railway.app**  
   - Đơn giản, hỗ trợ Python, có gói miễn phí.
4. **Google Cloud Run / Google App Engine**  
   - Triển khai Flask app dễ dàng, tích hợp tốt với các dịch vụ Google.
5. **Azure App Service**  
   - Hỗ trợ Python/Flask, dễ tích hợp với các dịch vụ Azure.
6. **Amazon Elastic Beanstalk**  
   - Hỗ trợ Flask, tự động hóa triển khai.
7. **Vercel/Netlify**  
   - Chủ yếu cho frontend, nhưng có thể dùng cho backend nhỏ qua serverless function (không tối ưu cho Flask truyền thống).
8. **VPS riêng (DigitalOcean, Linode, Vultr, ...)**  
   - Toàn quyền kiểm soát, cần tự cấu hình server (Nginx, Gunicorn, ...).
9. **Docker + bất kỳ cloud nào**  
   - Đóng gói app thành container, triển khai lên bất kỳ nền tảng hỗ trợ Docker.

**Lưu ý:**  
- Không public trực tiếp API key Gemini trên client/frontend.
- Nếu dùng các nền tảng miễn phí, chú ý giới hạn tài nguyên và thời gian hoạt động.
- Đảm bảo bảo mật endpoint và dữ liệu người dùng khi public.

Bạn nên chọn Heroku, Render, Railway hoặc Google Cloud Run nếu muốn triển khai nhanh, dễ bảo trì cho Flask app nhỏ.

**Cách đưa hệ thống Flask của bạn lên Render.com:**

1. **Chuẩn bị mã nguồn**
   - Đảm bảo có các file: `app.py`, `requirements.txt`, thư mục `templates/`, file dữ liệu (`informatics9.json`), v.v.
   - Trong `requirements.txt` cần có:  
     ```
     flask
     requests
     ```
     (và các thư viện khác nếu có)

2. **Tạo file Procfile** (nếu chưa có)
   - Nội dung:
     ```
     web: gunicorn app:app
     ```
   - Nếu chưa cài gunicorn, thêm vào `requirements.txt`:
     ```
     gunicorn
     ```

3. **Đẩy mã nguồn lên GitHub**
   - Tạo repo mới trên GitHub.
   - Commit toàn bộ mã nguồn và push lên repo.

4. **Tạo dịch vụ mới trên Render**
   - Đăng nhập vào [https://render.com](https://render.com).
   - Chọn "New +" → "Web Service".
   - Kết nối với repo GitHub vừa tạo.
   - Chọn branch (thường là main/master).
   - Environment: Python 3.x
   - Start command:  
     ```
     gunicorn app:app
     ```
   - (Nếu app.py không ở root, cần sửa lại đường dẫn.)

5. **Thiết lập biến môi trường (nếu cần)**
   - Nếu API_KEY để trong code thì không cần, nhưng nên để vào biến môi trường (Environment Variable) trên Render để bảo mật hơn.

6. **Deploy**
   - Nhấn "Create Web Service".
   - Đợi Render build và deploy xong, bạn sẽ có một đường link public để truy cập chatbot.

**Lưu ý:**
- Nếu dùng file dữ liệu (như `informatics9.json`), file này phải nằm trong repo.
- Nếu cần upload file lớn hoặc dữ liệu động, nên dùng cloud storage.
- Đảm bảo không để lộ API key Gemini trên frontend.
- Nếu gặp lỗi port, Render mặc định dùng biến môi trường `PORT`, Flask nên chạy với `port=os.environ.get("PORT", 10000)` (nhưng với gunicorn thì không cần sửa).

**Tài liệu tham khảo:**  
- https://render.com/docs/deploy-flask
- https://render.com/docs/web-services

**Tóm tắt:**  
- Đẩy code lên GitHub → Kết nối Render → Deploy → Lấy link public.
"""
