import json

def build_prompt(user_msg, lesson_data):
    return f"""
Bạn là trợ lý dạy Tin học lớp 9. Trả lời câu hỏi dưới đây một cách ngắn gọn, rõ ràng, dễ hiểu.

Câu hỏi: "{user_msg}"

Tài liệu hỗ trợ:
{lesson_data}

Nếu có thể, hãy đưa ví dụ minh họa hoặc gợi ý học tập.
"""

def match_lesson(user_msg, data):
    for key, value in data.items():
        if key in user_msg or value["ten"].lower() in user_msg:
            return key
    return None
