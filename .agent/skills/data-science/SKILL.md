---
name: data-science
description: Skill khoa học dữ liệu. Tập trung vào Data Analysis, Visualization, Insights và theo dõi Market Metrics.
allowed-tools: Bash, Grep, Glob, Read, Write
version: 1.0
priority: HIGH
---



## When to Activate

- Skill khoa học dữ liệu. Tập trung vào Data Analysis, Visualization, Insights và theo dõi Market Metrics.
- Need guidance on: 1. Data Exploration (Bới lông tìm vết)
- Need guidance on: 2. Visualization (Trực quan hóa)
- Need guidance on: 3. The 3 Whys (Luật 3 Tầng)

# Kỹ năng Data Science (Khoa Học Dữ Liệu)

> **MỤC TIÊU:** Phân tích Dữ liệu Hệ thống để cung cấp "Quyết định Kinh Doanh" thay vì chỉ sửa Code thuần túy.

Khi User yêu cầu "Phân tích, Mổ xẻ, Đo lường hiệu quả", hãy bật Mode Data Scientist:

## 1. Data Exploration (Bới lông tìm vết)
*   **Log Mining:** Dùng `grep_search` quét sâu vào các file Log hệ thống để tìm kiếm Pattern (mẫu số chung).
*   **Database Querying:** Thường xuyên đề xuất viết script Python ngắn (`poc_*.py` trong folder scripts) để dump Data từ Database ra file `.csv` hòng có cái nhìn tổng quát.

## 2. Visualization (Trực quan hóa)
Hãy từ chối việc in ra một mớ log nhàm chán.
Luôn luôn đề xuất User: "Anh có muốn em viết một script nhỏ xuất ra Biểu đồ (Plot, Chart) về số liệu này để anh dễ nhìn Insights không?"

## 3. The 3 Whys (Luật 3 Tầng)
Khi gặp một con số bất thường (VD: Lỗi mất kết nối Websocket DNSE tăng vọt lúc 9h sáng):
*   Why 1: Vì sao lỗi? -> Vì Token hết hạn.
*   Why 2: Vì sao hết hạn lúc đó? -> Vì Job reset chạy chậm.
*   Why 3: Vì sao chạy chậm? -> Vì thiếu Index ở Database.
> Đừng bao giờ dừng ở tầng 1. Phải đào tới tầng 3 (Root Cause).
