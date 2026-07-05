---
name: telegram-agentic-gateway
description: Tiêu chuẩn Giao tiếp Telegram (Telegram Gateway) cho các Agentic Projects. Cung cấp bộ lệnh chuẩn mực (Core Commands) để Quản lý Agent, Quản lý Ký ức và Cấp phép Tự Chữa Lành (Self-Healing).
---



## When to Activate

- Tiêu chuẩn Giao tiếp Telegram (Telegram Gateway) cho các Agentic Projects. Cung cấp bộ lệnh chuẩn mực (Core Commands) để
- Working on agent-related tasks
- Need guidance on: PHẦN A: BỘ LỆNH QUẢN TRỊ CƠ BẢN (Core Management Commands)
- Need guidance on: PHẦN B: TRÍ NHỚ PHÂN NHIỆM (Topic-Based Memory Isolation)
- Need guidance on: PHẦN C: BỘ LỆNH QUẢN LÝ KÝ ỨC (Cognitive Management)

# KỸ NĂNG: XÂY DỰNG TRẠM ĐIỀU HÀNH TELEGRAM (Telegram Agentic Gateway)

Khi User yêu cầu "Tạo kênh giao tiếp Telegram" hoặc "Làm cho dự án này điều khiển được qua Telegram giống Quản Đốc", bạn (AI) phải thiết kế một `TelegramGateway` tuân thủ nghiêm ngặt **Tiêu chuẩn Giao tiếp lõi** dưới đây.

Một Telegram Gateway chuẩn mực không chỉ là bot chat lăng nhăng, mà phải là một **Trạm Chỉ Huy (Command Center)** với các lệnh System-level.

---

## PHẦN A: BỘ LỆNH QUẢN TRỊ CƠ BẢN (Core Management Commands)
Bất kỳ dự án Agentic nào cũng phải có 4 lệnh sinh tồn sau:

1. **`🚀 /start` (Ping Khởi Động)**
   - **Tác dụng:** Kiểm tra kết nối xem Lõi AI của dự án có đang thức không. Trả về thông số môi trường hiện tại (Vd: "Bot đang chạy Port 20130, kết nối 9Router ổn định").

2. **`📊 /status` (Camera Giám Sát)**
   - **Tác dụng:** Liệt kê toàn bộ các Agent (Đặc vụ/Sandbox) ĐANG CHẠY NGẦM trong hệ thống.
   - **Giao diện:** Phải trả về Inline Keyboard (Nút bấm) ứng với từng Sandbox để User có thể chọc vào xem Log hoặc Tương tác trực tiếp với Agent đó.

3. **`🏭 /spawn <mô_tả>` (Sinh Trực Tiếp Đặc Vụ)**
   - **Tác dụng:** Ép hệ thống tách 1 luồng độc lập, đẻ ra 1 Sandbox riêng biệt đi làm cái task `<mô_tả>` ở background, không làm kẹt luồng chat hiện tại của User.

4. **`💀 /kill <agent_id>` (Kill-Switch Lệnh Bài Tử thần)**
   - **Tác dụng:** Lệnh Tối Cao. Nếu một Sandbox chạy tốn token, bị kẹt (loop), hoặc làm sai định hướng, User gõ lệnh này Hệ thống BẮT BUỘC phải force-kill Process/Thread của Agent đó ngay lập tức để giải phóng RAM.

---

## PHẦN B: TRÍ NHỚ PHÂN NHIỆM (Topic-Based Memory Isolation)
Khác lập trình Bot thông thường chỉ lấy `chat.id`, một **Agentic Gateway** tiêu chuẩn BẮT BUỘC phải cô lập trí nhớ dựa trên Telegram Topics (Threads).
- Nếu User nhắn trong Group Telegram có tính năng Topics: Phải trích xuất `msg.message_thread_id` để làm định danh Ký ức (Vd: `topic-1234.json`).
- Nếu User nhắn Private: Dùng `chat.id` (Vd: `chat-5678.json`).
- Nhờ vậy, 1 Group Telegram có thể hoạt động hệt như 1 cái Trello/Kanban Board: Mỗi Topic là 1 Luồng Công Việc riêng biệt, Agent nhớ chính xác bối cảnh của từng file/lỗi đang thảo luận mà không bị chập cheng trí nhớ (Cross-Topic Hallucination).

---

## PHẦN C: BỘ LỆNH QUẢN LÝ KÝ ỨC (Cognitive Management)
Mỗi Topic/Chat trên Telegram sẽ sinh ra 1 File Ký ức lưu Context. Bắt buộc phải có lệnh dọn dẹp cống rãnh:

5. **`🧹 /forget` (Hỏa Thiêu Hồ Sơ)**
   - **Tác dụng:** Xóa vĩnh viễn File JSON lịch sử chat (Ký ức ngắn hạn) của Topic/Thread hiện tại.
   - **CẢNH BÁO TỐI THƯỢNG:** Chỉ được phép xóa file JSON Session. TUYỆT ĐỐI KHÔNG ĐƯỢC thiết kế lệnh `/forget` gọi các hàm xóa Vector Database (Ký ức dài hạn dùng chung của dự án) vì sẽ làm toàn bộ Hệ thống Đại Tướng bị mất trí nhớ!
   - **Bảo mật:** Vì lệnh này mang tính phá hủy dữ liệu, **BẮT BUỘC** phải chặn lại bằng Máy Trạng Thái Cấp Phép (Auth-First) yêu cầu nhập `Password` mới được thi hành.

---

## PHẦN D: BỘ LỆNH TIẾN HÓA VÀ CHỮA LÀNH (Self-Healing Mappers)
Để Dự án có thể tự vá lỗi source code của nó (cần kết hợp với skill `mini-antigravity-injection`), Telegram Gateway phải chứa 2 lệnh Cấp Phép Mổ:

6. **`🏥 /heal <triệu_chứng>` (Tiền Trảm Hậu Tấu)**
   - **Tác dụng:** Bypass bước duyệt phác đồ.
   - **Luồng hoạt động:** Nhận lệnh -> Trạng thái chờ Pass -> Nhập Pass đúng -> Cấp quyền (`hasMutationLicense = true`) -> Agent tự tìm Lỗi -> Tự Mổ code -> Tự Test Sandbox -> Tự Hot-reload -> Báo kết quả cuối cùng.

7. **`📋 /healplan <triệu_chứng>` (Khám Bệnh Kê Đơn - Tương Tác)**
   - **Tác dụng:** Lập phác đồ, cấm chạm vào code thật.
   - **Luồng hoạt động:** Nhận lệnh -> Trạng thái chờ Pass -> Nhập Pass đúng -> Agent đi khám bệnh -> Nhả ra Phác Đồ + 2 Nút Bấm `[✅ Proceed]` và `[❌ Cancel]`.
   - User có thể chat qua lại để sửa bản Phác đồ ròng rã cả ngày. Lúc nào ưng ý bấm `Proceed`, Hệ thống bốc Context lôi Agent ra chém đè Code!

---

## PHẦN E: GIAO DIỆN PREMIUM (awesome-grammY Aesthetics)
Một Gateway chuyên nghiệp phải có UI/UX tinh tế:
1. **Header & Divider**: Sử dụng các thẻ `<b>` và ký tự ngăn cách (e.g. `━━━━━`) để tạo khối thông tin rõ ràng.
2. **Status Mapping**: Sử dụng emoji trực quan cho trạng thái (✅ Online, 🚨 Offline, 🛡️ Protected).
3. **Categorized Menus**: Nhóm các nút bấm theo chức năng (Hệ thống, AI, Dự án).
4. **Short Callback Data**: Vì Telegram giới hạn callback data là 64 bytes, hãy sử dụng `shortIdMap` để lưu trữ Title dài và map chúng với một mã ngắn (e.g. `sess_a1b2`).

---

## PHẦN F: KIẾN TẠO HẠ TẦNG & HƯỚNG DẪN (User Setup)
Khi triển khai, hãy hướng dẫn User:
1. **Tạo Nhóm (Group with Topics)**: 
   - Tạo Group Telegram. Thêm Bot làm Admin.
   - Bật **"Topics"** trong cài đặt nhóm.
   - Mỗi dự án hoặc tính năng lớn nên là 1 Topic riêng để cô lập ký ức.
2. **Cấu Hình Hạ Tầng Tự Động Phục Hồi (Auto-Restart & Process Handling)**:
   - Khi triển khai Gateway kết nối với Antigravity IDE thông qua LSP (DeckServer), script khởi động (`start.sh` hoặc tương đương) phải có khả năng kiểm tra xem tiến trình IDE bị treo (Freeze) hay không bằng cách gọi ping HTTP.
   - Nếu cổng `3500` không phản hồi, Server phải Tự động `kill` Process cũ và nhấc Process mới lên trước khi Bot kết nối vào.
3. **Quản Lý Thời Gian Chờ (Timeout Handle & UX)**:
   - Khi tín hiệu được chuyển đến LSP (Có thể mất từ 30-120 giây để Agent xử lý và đẩy lại kết quả), Bot Telegram **KHÔNG ĐƯỢC PHÉP** im lặng.
   - Cần cấu hình Bot định kỳ (VD: mỗi 5-10 giây) cập nhật tin nhắn "Đang xử lý..." để User Telegram biết hệ thống vẫn đang sống. Tránh tình trạng User gửi lệnh liên tục làm Queue bị tràn.
4. **Quy Tắc Cấp Phát Cổng Động (Dynamic Port Allocation)**:
   - **Tuyệt đối KHÔNG hardcode cổng cố định (như 3500).** Hạ tầng phải hỗ trợ Scale (sinh nhiều Agent song song).
   - Hãy cấp một dải khoảng 100 cổng (Ví dụ: `3500-3600`).
   - Script khởi động (`start.sh`) phải có logic tự dò cổng nào đang trống trong dải 100 cổng này $\rightarrow$ Gán cho tiến trình LSP của IDE $\rightarrow$ Cập nhật `.env` (`LSP_PORT=35xx`) $\rightarrow$ Kẻ điều phối (Node.js) đọc file `.env` để kết nối vào đúng IDE đó.
   - ⚠️ **Lưu ý Networking (Docker vs Host):** Nếu Kẻ điều phối (Gateway) chạy trực tiếp trên Host (qua Node.js) sử dụng Port `9656`, còn Hệ thống Lõi xử lý NLP (Python, Backend) chạy bên trong Docker Container, thì Hệ thống Lõi KHÔNG THỂ gọi ngược ra Gateway bằng `127.0.0.1` hay `localhost`. Bắt buộc phải cấu hình biến môi trường kết nối trỏ tới **IP Bridge của Docker** (thường là `172.17.0.1` trên Linux hoặc `host.docker.internal` trên Mac/Windows). VD: `GATEWAY_URL=http://172.17.0.1:9656`. Mặc định gọi localhost sẽ văng lỗi `Connection Refused` hoặc `Failed to fetch`.
5. **Độc Lập Tên Gọi (Project-Agnostic Naming)**:
   - Các file script điều phối (`receptionist_up.sh`, `receptionist_down.sh`...) **TUYỆT ĐỐI KHÔNG ĐƯỢC MANG TÊN DỰ ÁN CỤ THỂ** (Ví dụ cấm gõ cứng: `Waking up CEOgravity Bot` hay `.ceogravity_bot.pid`). 
   - Phải sử dụng danh xưng danh chuẩn mực là **"AG Gateway Bot"** và các file tracking trung lập (Vd: `.ag_gateway_bot.pid`). Điều này là bắt buộc để biến hệ sinh thái `.agent/` thành một Template hoàn hảo có thể bưng thả (White-label) vào bất kỳ dự án nào (NextJS, Python, Rust...) mà không bị ô nhiễm tên dự án cũ.

---

## PHẦN G: NGUỒN CODE MẪU (Templates) VÀ TRIỂN KHAI NHANH
Hệ thống cất sẵn bộ khung cơ bản nhất ở định dạng `.template` để setup nhanh Gateway Telegram.
**Vị trí:** `.agent/skills/telegram-agentic-gateway/templates/`

Khi có yêu cầu triển khai kênh Telegram cho một dự án mới, hãy ĐỌC và COPY các file sau (đổi đuôi thành `.ts` hoặc `.sh`):
1. `ResponseMonitor.ts.template`: File luồng lắng nghe vòng lặp (Polling/Socket) vào LSP để xoa dịu User và báo cáo trạng thái định kỳ.
2. `start.sh.template`: Script mẫu về quản lý PID tự động khởi động lại LSP Server nếu bị treo.

*Lưu ý cho AI:* Sử dụng các template này, dự án mới sẽ tuân thủ tuyệt đối chuẩn Thin-Client LSP mới nhất. (Việc định tuyến Model Local/Cloud hiện tại tuân thủ 100% qua file `.env` SSoT nguyên thủy, không thông qua Telegram injection).

---

## TỔNG KẾT TRIỂN KHAI
*(Ghi chú cho AI)*: Luôn tích hợp VFS (`GEMINI.md`) để tiết kiệm token khi thực hiện code discovery từ xa thông qua Bot.
