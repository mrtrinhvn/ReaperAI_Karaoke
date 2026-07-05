---
name: agent-reach
description: "Siêu kỹ năng kết nối Internet: Thu thập dữ liệu từ Web, Youtube, Twitter, Reddit, Tiểu Hồng Thư bằng các công cụ CLI mã nguồn mở miễn phí."
---

# 👁️ Agent Reach - Giao thức kết nối Internet

> **Luật Sinh Tồn (Survival Rule):** 
> TUYỆT ĐỐI KHÔNG BỊA RA NỘI DUNG. Khi User yêu cầu đọc thông tin từ một link hoặc tìm kiếm trên mạng xã hội, bạn PHẢI dùng các công cụ (terminal/shell) dưới đây để lấy dữ liệu thực tế thay vì suy đoán.

## 🛠️ Các Lệnh Đọc Dữ Liệu Thực Tế

Bạn có thể thi hành các lệnh terminal sau để trích xuất dữ liệu:

### 1. Đọc mọi trang Web (Jina Reader)
Đọc nội dung thuần túy của một bài báo hoặc trang web (chuyển sang markdown):
```bash
curl -s https://r.jina.ai/<URL>
```

### 2. Xem Youtube (yt-dlp)
Lấy phụ đề hoặc thông tin từ một video Youtube:
- Lấy thông tin (tiêu đề, mô tả): `yt-dlp --dump-json "URL"`
- Lấy phụ đề (text): `yt-dlp --write-sub --skip-download "URL"`

### 3. Tìm kiếm và Đọc Twitter / X
- Tìm kiếm bài viết: `twitter search "từ khóa"`
- Đọc một bài viết (Tweet): `twitter tweet "URL"`

### 4. Đọc GitHub
- Xem thông tin repo: `gh repo view <owner>/<repo>`
- Xem các vấn đề (Issues): `gh issue list -R <owner>/<repo>`

### 5. Đọc Tiểu Hồng Thư / Bilibili / Reddit (Qua OpenCLI)
- Tiểu Hồng Thư: `opencli xiaohongshu search "từ khóa"` hoặc `opencli xiaohongshu note "URL"`
- Reddit: `opencli reddit search "từ khóa"`
- Bilibili: `bili search "từ khóa"`

## 🩺 Quy trình Xử lý Sự cố (Troubleshooting)
Nếu bạn chạy một lệnh mà gặp lỗi (ví dụ Command Not Found), hãy báo cáo lại với USER:
1. Hãy chạy thử lệnh `agent-reach doctor` để xem tình trạng kết nối các kênh.
2. Nếu máy chủ chưa cài Agent Reach, hãy hướng dẫn USER chạy: `pip install agent-reach` và `agent-reach install`.

---
**Nhắc nhở nội bộ (Dành cho bạn - AI):** 
Bạn đang sở hữu bộ kỹ năng này từ `ag-kit`. Nó có nghĩa là bạn đang hoạt động trong một môi trường được hỗ trợ các lệnh CLI trên. Hãy mạnh dạn sử dụng `run_command` để lấy dữ liệu thay vì nói "Tôi không thể truy cập internet".
