import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Tạo hình vẽ
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 11)
ax.axis('off')

# Vẽ tác nhân: Học sinh
ax.text(1, 10, 'Học sinh', ha='center', fontsize=12)
ax.plot([1], [9], marker='o', markersize=20, color='black')
ax.plot([1, 1], [8.5, 9], color='black')
ax.plot([0.8, 1.2], [8.7, 8.7], color='black')
ax.plot([1, 0.9], [8.5, 8.2], color='black')
ax.plot([1, 1.1], [8.5, 8.2], color='black')

# Vẽ tác nhân: ChatBot
ax.text(1, 6.5, 'ChatBot', ha='center', fontsize=12)
ax.plot([1], [5.5], marker='o', markersize=20, color='black')
ax.plot([1, 1], [5, 5.5], color='black')
ax.plot([0.8, 1.2], [5.2, 5.2], color='black')
ax.plot([1, 0.9], [5, 4.7], color='black')
ax.plot([1, 1.1], [5, 4.7], color='black')

# Vẽ tác nhân: Hệ thống
ax.text(1, 3.3, 'Hệ thống', ha='center', fontsize=12)
ax.plot([1], [2.3], marker='o', markersize=20, color='black')
ax.plot([1, 1], [1.8, 2.3], color='black')
ax.plot([0.8, 1.2], [2.0, 2.0], color='black')
ax.plot([1, 0.9], [1.8, 1.5], color='black')
ax.plot([1, 1.1], [1.8, 1.5], color='black')

# Vẽ hệ thống chính
system_box = patches.FancyBboxPatch((4, 1), 9, 9, boxstyle="round,pad=0.1", edgecolor="black", facecolor="#f0f0f0")
ax.add_patch(system_box)
ax.text(8.5, 9.6, 'Hệ thống Chatbot hỗ trợ Tin học 9', ha='center', fontsize=13, weight='bold')

# Các use case
use_cases = [
    ("Nhập câu hỏi", (8.5, 8.6)),
    ("Phân tích câu hỏi", (8.5, 7.6)),
    ("Lấy transcript từ video YouTube", (8.5, 6.6)),
    ("Tìm nội dung phù hợp trong transcript", (8.5, 5.6)),
    ("Gửi nội dung và câu hỏi đến Gemini API", (8.5, 4.6)),
    ("Sinh câu trả lời phù hợp", (8.5, 3.6)),
    ("Hiển thị kết quả cho học sinh", (8.5, 2.6))
]

for text, (x, y) in use_cases:
    ellipse = patches.Ellipse((x, y), width=5.3, height=0.9, edgecolor='black', facecolor='white')
    ax.add_patch(ellipse)
    ax.text(x, y, text, ha='center', va='center', fontsize=10)

# Kết nối từ các tác nhân đến các use case
ax.plot([1.3, 6], [8.7, 8.6], linestyle='--', color='blue')  # Học sinh -> Nhập câu hỏi
ax.plot([1.3, 6], [8.7, 2.6], linestyle='--', color='blue')  # Học sinh <- Kết quả

ax.plot([1.3, 6], [5.5, 7.6], linestyle='--', color='green')  # ChatBot -> Phân tích
ax.plot([1.3, 6], [5.5, 3.6], linestyle='--', color='green')  # ChatBot -> Sinh câu trả lời

ax.plot([1.3, 6], [2.3, 6.6], linestyle='--', color='purple')  # Hệ thống -> Lấy transcript
ax.plot([1.3, 6], [2.3, 5.6], linestyle='--', color='purple')  # Hệ thống -> Tìm nội dung
ax.plot([1.3, 6], [2.3, 4.6], linestyle='--', color='purple')  # Hệ thống -> Gửi đến Gemini

plt.title("Use Case Diagram – Chatbot + Gemini API + YouTube + 3 tác nhân", fontsize=14)
plt.tight_layout()
plt.show()
