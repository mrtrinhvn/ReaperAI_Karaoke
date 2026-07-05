78# Tiết Kiệm Token & Quản Lý Mô Hình (Model & VFS Knowledge)

## 1. Cơ Chế Tiết Kiệm Token
Trong môi trường điều khiển từ xa (Telegram), việc tối ưu hóa token là cực kỳ quan trọng để duy trì hiệu suất và chi phí.

### VFS (Virtual File System)
- **Tác dụng**: Giảm 98% lượng token khi khám phá mã nguồn.
- **Cách hoạt động**: Thay vì đọc toàn bộ file, AI sử dụng công cụ `vfs` để chỉ lấy chữ ký (signatures) của hàm và lớp.
- **Quy tắc**: Phải luôn sử dụng `vfs` trước khi dùng `grep` hoặc đọc file đầy đủ. (Xem `GEMINI.md`).

## 2. Chiến Lược Lựa Chọn Mô Hình (Model Strategy)
Hệ thống sử dụng cơ chế "Phân tầng độ khó" để chọn model:

| Độ khó | Tác vụ | Mô hình khuyến nghị | Lý do |
| :--- | :--- | :--- | :--- |
| **Thấp** | Giải thích code, Refactor nhỏ, Chat thông thường | **Ollama (Local)** | Không tốn quota, phản hồi nhanh cho tác vụ đơn giản. |
| **Trung bình** | Fix lỗi, Thêm tính năng mới | **Gemini 3 Flash** | Cân bằng giữa chi phí và độ thông minh. |
| **Cao** | Thiết kế kiến trúc, Debug lỗi phức tạp | **Claude 3.5 Sonnet / Gemini 1.5 Pro** | Độ chính xác cao nhất cho các vấn đề hóc búa. |

## 3. Tích Hợp Local Model (Ollama)
- Bot kết nối trực tiếp với Ollama API tại `http://localhost:11434`.
- Người dùng có thể chọn dùng model local qua lệnh `/model` để "đóng băng" quota Google khi không cần thiết.
