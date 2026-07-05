---
name: clean-code
description: Trọng số bắt buộc khi viết logic code. Ghi đè mọi thói quen lập trình mặc định.
allowed-tools: Read, Write, Edit
version: 3.2 (Generic-Safe)
priority: CRITICAL
---

# LÕI RÀNG BUỘC (MANDATORY CONSTRAINTS)

CẤM áp dụng tư duy lập trình phổ thông nếu vi phạm 6 bộ luật sinh tử sau:

## 1. Luật Trạng Thái Tiến Trình (Process State Safety)
Background Task / long-running process lưu trạng thái vào DB/file. Khi server restart, flag bị kẹt.
- ❌ **CẤM:** Dùng PID check (`os.kill(pid, 0)`) để verify process còn sống — PID có thể được tái sử dụng bởi OS.
- ✅ **BẮT BUỘC:** Dùng heartbeat timestamp: process tự ghi `last_ping = now()` mỗi N giây. Nếu `now() - last_ping > timeout` → coi là dead.
- ✅ **BẮT BUỘC:** Reset stale flags trong sự kiện `startup/lifespan` khi server boot.

## 2. Luật Nhất Quán Thời Gian (Time Abstraction)
- ❌ **CẤM:** Dùng `Date.now()` / `datetime.now()` trực tiếp rải rác trong business logic — phá khả năng test và mock.
- ✅ **BẮT BUỘC:** Wrap time source vào 1 hàm trung tâm (`getCurrentTime()`, `getNow()`, v.v.). Toàn bộ code dùng wrapper đó.
- **Lý do:** Dễ mock trong test, dễ implement time-travel debugging, dễ thêm timezone logic sau này.

## 3. Luật Mảnh Vỡ (Dependency Atomicity)
- ❌ **CẤM:** Sửa File Cốt Lõi rồi bỏ rơi File gọi nó (đổi chữ ký hàm trong `core.ts` mà quên update `service.ts`).
- ✅ **BẮT BUỘC:** Sửa `A` → Tìm toàn bộ file gọi `A` (`grep_search`) → Sửa đồng bộ tất cả. Broken import = Phạm Tội.
- ✅ **BẮT BUỘC:** Sau mỗi refactor, chạy `tsc --noEmit` (TypeScript) hoặc `python -m py_compile` (Python) để verify không gãy.

## 4. Luật Thay Đổi Cục Bộ (Surgical Strike)
- ❌ **CẤM:** Tự ý "cải thiện", refactor hoặc sửa format các đoạn code/comment lân cận không liên quan trực tiếp đến yêu cầu.
- ❌ **CẤM:** Xóa pre-existing dead code (code thừa có từ trước) trừ khi được chỉ định rõ ràng.
- ✅ **BẮT BUỘC:** Chỉ chạm vào đúng những gì cần thiết để giải quyết vấn đề. Dọn sạch những biến/import/logic thừa do CHÍNH thay đổi của mình tạo ra (Orphan cleanup).

## 5. Luật Đơn Giản Hóa (Simplicity First)
- ❌ **CẤM:** Over-engineering. Không xây dựng các abstraction (class/interface) cho code chỉ dùng 1 lần.
- ❌ **CẤM:** Code "đón đầu" tính năng hoặc tạo độ linh hoạt (configurability) khi Sếp không yêu cầu.
- ✅ **BẮT BUỘC:** Chỉ viết lượng code tối thiểu cần thiết để giải quyết đúng bài toán hiện tại. Nếu 200 dòng có thể rút thành 50 dòng đơn giản hơn, phải viết 50 dòng.

## 6. Luật Minh Bạch Tư Duy (Think Before Coding)
- ❌ **CẤM:** Suy đoán ngầm (silent assumption). Nếu yêu cầu mơ hồ hoặc luồng code hiện tại khó hiểu, KHÔNG được tự ý chọn đại một cách giải quyết.
- ❌ **CẤM:** Che giấu sự nhầm lẫn. Phải báo ngay nếu phát hiện logic bất đồng nhất (inconsistencies) trong code cũ.
- ✅ **BẮT BUỘC:** Phải nói rõ giả định của mình và trình bày các điểm Trade-offs (Được/Mất) để Sếp chọn trước khi lao vào code các logic phức tạp.

---


## When to Activate

- Trọng số bắt buộc khi viết logic code. Ghi đè mọi thói quen lập trình mặc định.
- Need guidance on: 1. Luật Trạng Thái Tiến Trình (Process State Safety)
- Need guidance on: 2. Luật Nhất Quán Thời Gian (Time Abstraction)
- Need guidance on: 3. Luật Mảnh Vỡ (Dependency Atomicity)
- Need guidance on: 4. Luật Thay Đổi Cục Bộ (Surgical Strike)


# GIAO THỨC NGHIỆM THU

Khép task code, KHÔNG báo cáo mõm. Agent phải chạy Audit Script dựa theo phân cấp:
- **Frontend / UI:** `python scripts/ux_audit.py .`
- **Backend / API:** `python scripts/api_validator.py .`
- **Database Modeller:** `python scripts/schema_validator.py .`
- **Nhét General Default:** `python scripts/lint_runner.py .`

**Quy Trình Kiểm Tra:**
1. Rake Log
2. Hiển thị thông báo: `[Đỏ X lỗi] | [Vàng Y cảnh báo] | Pass`.
3. Stop, Đợi Sếp Quyết: "Sếp, cho phép diệt lỗi không?". Không được lấp liếm.
