from youtube_transcript_api import YouTubeTranscriptApi
import json
import re

def fetch_youtube_text(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi'])
        return " ".join([x['text'] for x in transcript])
    except Exception as e:
        print("❌ Lỗi khi lấy phụ đề:", e)
        return ""

def extract_video_id(url):
    # Hỗ trợ các dạng link phổ biến của YouTube
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url  # Nếu chỉ là ID

def make_lesson_entry(full_text, idx, lesson_name):
    return {
        f"bai_{idx+1}": {
            "ten": lesson_name,
            "tomtat": full_text[:150000],
            "vidu": ["Ví dụ minh họa từ nội dung", "Thông tin thêm có thể"]
        }
    }

if __name__ == "__main__":
    # Nhập mỗi dòng: link hoặc ID | tên bài học
    print("Nhập mỗi dòng: link hoặc ID video YouTube | tên bài học (Enter 2 lần để kết thúc):")
    input_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        input_lines.append(line.strip())
    lessons = {}

    for idx, line in enumerate(input_lines):
        if "|" in line:
            link_part, name_part = line.split("|", 1)
            link = link_part.strip()
            lesson_name = name_part.strip()
        else:
            link = line.strip()
            lesson_name = f"Bài học từ video {idx+1}"
        video_id = extract_video_id(link)
        print(f"🔎 Đang lấy phụ đề cho video: {video_id}")
        full_text = fetch_youtube_text(video_id)
        if full_text:
            lessons.update(make_lesson_entry(full_text, idx, lesson_name))
        else:
            print(f"❌ Không lấy được phụ đề cho {video_id}")

    if lessons:
        with open("all_youtube_subtitles.json", "w", encoding="utf-8") as f:
            json.dump(lessons, f, ensure_ascii=False, indent=2)
        print("✅ Đã tạo file all_youtube_subtitles.json chứa toàn bộ phụ đề các video (theo format yêu cầu).")
    else:
        print("❌ Không có phụ đề nào được lưu.")
