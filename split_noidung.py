import json
import os

def split_text(text, maxlen=1000):
    parts = []
    start = 0
    while start < len(text):
        end = start + maxlen
        if end >= len(text):
            parts.append(text[start:].strip())
            break
        # Tìm vị trí kết thúc gần nhất là khoảng trắng
        split_pos = text.rfind(' ', start, end)
        if split_pos == -1 or split_pos <= start:
            split_pos = end
        parts.append(text[start:split_pos].strip())
        start = split_pos
    return parts

with open("informatics9.json", encoding="utf-8") as f:
    data = json.load(f)

for bai in data.values():
    if "noidung" in bai:
        parts = split_text(bai["noidung"], 1000)
        for idx, part in enumerate(parts, 1):
            bai[f"noidung_{idx}"] = part
        del bai["noidung"]

with open("informatics9.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
