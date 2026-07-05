---
name: python-patterns
description: Python Ecosystem Hard Rules cho nền tảng Backend.
version: 3.0 (Metamorphosis Distilled)
priority: CRITICAL
---



## When to Activate

- Python Ecosystem Hard Rules cho nền tảng Backend.
- Working on backend-related tasks
- Need guidance on: 1. Án Tử: Lỗ hổng Dòng Thời Gian Hệ Thống (Time Freeze)
- Need guidance on: 2. Án Tử: Ghost Session trên Background Tasks (Docker)
- Need guidance on: 3. Kiến Trúc Default (KHÔNG TRÌNH BÀY DÀI DÒNG)

# LÕI RÀNG BUỘC BACKEND / PYTHON (MANDATORY CONSTRAINTS)

CẤM áp dụng code tutorial mạng/LLM nếu vi phạm các thiết chế sinh tử sau:

## 1. Án Tử: Lỗ hổng Dòng Thời Gian Hệ Thống (Time Freeze)
- ❌ **CẤM:** Sinh Code dùng `datetime.now()` trực tiếp. Sẽ gây thảm họa phá vỡ Data lúc Backtesting / Quản lý Phân Tích rủi ro.
- ✅ **BẮT BUỘC:** Mọi block check thời gian, tick thời gian phải import hệ sinh thái `get_time_machine()` hoặc check điều kiện `is_trading_hours()`.

## 2. Án Tử: Ghost Session trên Background Tasks (Docker)
- ❌ **CẤM:** Check process bằng `os.kill(pid, 0)`. Khi bật trong Docker, PID hay bị loop/reset -> Gay nghẽn Session ảo.
- ✅ **BẮT BUỘC:** Xóa sạch cờ/trạng thái task đang `running` thông qua hook **`lifespan` / `startup`** của FastAPI lúc khởi động. Triệt tiêu dứt điểm.

## 3. Kiến Trúc Default (KHÔNG TRÌNH BÀY DÀI DÒNG)
- **Framework API:** `FastAPI` (Async I/O First). FastAPI background tasks ok, Celery/Arq nếu nặng cực.
- **ORM Config:** Sử dụng `SQLAlchemy 2.0 Async`. CẤM pha trộn gọi hàm Sync (blocking) vào DB bên trong file Async I/O (gây tắc nghẽn thread pool nghiêm trọng).
- **Validation/Schema:** Luôn phải dùng Type Hint 100% Request / Response với `Pydantic V2`.

## 4. Giao thức Thử Nghiệm / Test
- Code API / Service ngầm -> Bắt buộc Test / Hướng dẫn cách Test qua kịch bản `pytest.mark.asyncio`.
