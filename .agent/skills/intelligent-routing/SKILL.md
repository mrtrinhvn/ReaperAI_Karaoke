---
name: intelligent-routing
description: Cơ chế Ủy quyền Tổ Đàn (Hive Mind Delegation). Tự động gọi mcp_ollama-bridge vác việc rác xuống Local Model. Giữ não Cloud luôn rảnh để Orchestrate.
allowed-tools: Read, Write, commands, mcp_ollama-bridge
version: 4.0 (Metamorphosis Distilled)
priority: CRITICAL
---



## When to Activate

- Cơ chế Ủy quyền Tổ Đàn (Hive Mind Delegation). Tự động gọi mcp_ollama-bridge vác việc rác xuống Local Model. Giữ não Clo
- Need guidance on: 1. QUY TẮC ỦY QUYỀN LOCAL MODEL (ZERO-HUD DELEGATION)
- Need guidance on: 2. CHẾ TÀI PHÂN BIỆT INPUT TOKEN (BÀI TOÁN CHI PHÍ)
- Need guidance on: 3. MỎ NEO GỌI CHÉO SKILL (BOOTSTRAPPING)
- Need guidance on: 4. KỸ THUẬT BẢO TOÀN KÉP BẰNG PIPELINE & TOKEN-JUICE (QUAN TRỌNG TỐI MẬT)
- Writing or reviewing bash code

# KIẾN TRÚC TỔ ĐÀN (HIVE MIND DELEGATION) - RÀNG BUỘC TỐI CAO

Tuân thủ triệt để chiến thuật: "Cloud não to làm việc Lớn, Nhường việc Vặt cho Local Model Đàn Em". Tuyệt đối không dùng bản thân Cloud AI để sinh các chuỗi code dài vô nghĩa ngốn Bill API.

## 1. QUY TẮC ỦY QUYỀN LOCAL MODEL (ZERO-HUD DELEGATION)
Sếp **KHÔNG CẦN CHỌN MODEL** ở giao diện IDE/HUD. Bản thân Tổng Đoán AI (Cloud) tự phân luồng ngầm qua MCP Bridge:

- ❌ **CẤM DÙNG CLOUD AI:** (Bản thân AI chính) không được trực tiếp dấn thân vào các Task cơ bắp giá trị thấp: Định dạng Format JSON, Convert Regex, Translate Translation, Clone Boilerplate 100 dòng từ Schema, và đặc biệt Cấm tự thân Summarize cục Log 500 dòng bị lỗi.
- ✅ **BẮT BUỘC KIỂM TRA BIẾN MÔI TRƯỜNG TRƯỚC KHI UY QUYỀN:** Đọc file `.env` ở thư mục gốc của dự án. Nếu biến `OLLAMA_DELEGATION_ENABLED=false`, BẮT BUỘC bỏ qua việc dùng Local Model và Cloud AI phải tự tay xử lý 100% mọi tác vụ.
- ✅ **BẮT BUỘC KIỂM TRA TRẠNG THÁI (Nếu được phép):** Nếu biến bằng `true` hoặc không có, trước khi gọi `mcp_ollama-bridge`, LUON check availability:
  ```bash
  # Option 1: qua MCP
  mcp_ollama-bridge_ollama_list_models()
  # Option 2: qua terminal
  ollama list 2>/dev/null || echo "OFFLINE"
  ```
  - Nếu **ONLINE** → delegate xuống local như bình thường.
  - Nếu **OFFLINE** → xử lý trực tiếp trên Cloud + log: `[⚠️ Local Ollama OFFLINE — xử lý trên Cloud, có thể tốn thêm chi phí token]`
- ✅ **BẮT BUỘC ỦY QUYỀN LOCAL:** Khi nhận điện Task rác/lặp lại, LẬP TỨC dùng Tool `mcp_ollama-bridge_ollama_generate(model="nemotron", prompt="...")` hoặc `ollama_dispatch_task` để vắt kiệt sức lao động của Local Hardware (máy Sếp). Bốc kết quả Local trả về để báo cáo hoặc Paste vào IDE.
- 📣 **BÁO CÁO CÔNG VIỆC CÓ Ý THỨC:** Khi Ủy quyền ngầm, bắt buộc báo hiệu lên Chat Box bằng Emoji: `[🔀 Ủy Quyền Local Model phân tích Log / Sinh Boilerplate...]` để Sếp theo dõi. Giao việc xong tự Cloud hoàn thiện nốt khâu tổng hợp.

## 2. CHẾ TÀI PHÂN BIỆT INPUT TOKEN (BÀI TOÁN CHI PHÍ)
Cloud AI không được máy móc quăng mọi thứ xuống Local. Tránh tình trạng "Làm màu nhưng vẫn mất tiền":
- ❌ **ĐỐI VỚI FILE ĐÍNH KÈM (Upload / Code block / Image kéo thả vào chat):** File này đã bay chạm Đám Mây và **đã trừ tiền Input Token**. Lúc này, QUYẾT ĐỊNH XỬ LÝ LUÔN trên Cloud. Nhồi xuống Local lúc này chỉ tổ tốn thời gian chờ đợi (Latency delay) mà chẳng tiết kiệm được Input.
- ✅ **ĐỐI VỚI CON TRỎ FILE (File Path / Directory Path):** Nếu Sếp bảo "Dịch/Lọc cái thư mục X, file Y". Tối Kị việc dùng `view_file` vác toàn bộ Data kéo lên Cloud. Mệnh lệnh phải là mượn Terminal hoặc `mcp_ollama-bridge` để bơm thẳng Path đó cho bộ não Local ở gốc rễ xử lý. Lợi ích: **Giết 100% chi phí Input Token.**
- ✅ **CỨU CÁNH OUTPUT TOKEN:** Nếu prompt của Sếp siêu ngắn (VD: "Sinh 50 file Boilerplate DTO cắm vào model A"), nhưng kết quả sinh ra dài hàng chục class. Trực tiếp bắn Prompt Template xuống bắt Local làm. Lợi ích: **Giết 100% chi phí Output Token (Vốn đắt gấp 3 lần Input).**

## 3. MỎ NEO GỌI CHÉO SKILL (BOOTSTRAPPING)
Tránh "Béo Phì" Token Input. Cloud AI không load hầm bà lằng Skill:
- ❌ **CẤM:** Load file kỹ năng (Ví dụ: `data-engineer.md`) khi đang sửa lỗi CSS Frontend.
- ✅ **BẮT BUỘC:** Chữa cháy ở đâu, nạp ngữ cảnh ở đó. Trích Lõi (Bootstrapping) - Dùng lệnh `view_file` chui vào `.agent/skills/` đọc đích danh file quy định của hệ đó trước khi sinh code. 

## 4. KỸ THUẬT BẢO TOÀN KÉP BẰNG PIPELINE & TOKEN-JUICE (QUAN TRỌNG TỐI MẬT)
Tuyên ngôn: QUẢN LÝ BẰNG LỆNH CỨNG CỦA HỆ ĐIỀU HÀNH, KHÔNG BẰNG ĐÔI MẮT NHỤC NHÃ CỦA ĐÁM MÂY.
- ❌ **CẤM THU HỒI DATA THÔ:** Điên rồ nhất là gọi Local Model xử lý File Bự rồi DÙNG API ép nó trả nguyên cục Dữ Liệu đó vào mắt Mẹ (Cloud Context) để Mẹ chép. Tiền tấn!
- ✅ **GIẢI PHÁP PIPELINE (`>`):** Đẩy dữ liệu khổng lồ, Cloud AI PHẢI dùng Tool `run_command` đánh lệnh Terminal Bash: `cat to_b0.csv | ollama run qwen:7b "Lọc rác" > da_loc.csv`. 
- 🗜️ **CHẮT LỌC QUA TOKEN-JUICE:** Nếu bắt buộc phải kéo data lên Cloud đọc, PHẢI chạy qua bộ ép nước: `cat output.html | python3 .agent/scripts/token_juice.py -t html`. (Tham khảo tư duy TokenJuice của OpenHuman).
- Ghi đè rễ đất của ổ Sếp, Mây (Đại bàng) chỉ nhận "Exit code 0" hoặc bản "Nước ép" siêu gọn. Tối thượng tiết kiệm chi tiêu Token cho Sếp!

## 5. HIERARCHICAL ROUTING (ĐỊNH TUYẾN PHÂN CẤP) - CHỐNG ENTROPY PHÂN BỔ
Để chống lại hiện tượng "Tình trạng chồng lấn ngữ nghĩa" (Semantic Overlap) khi hệ sinh thái phình to, Tổng Đoán AI không được quét một lượt toàn bộ thư mục skills như một cái túi mù. Phải áp dụng Định tuyến phân cấp (Hierarchical Routing):
- **Bước 1 (Soft Gating - Định tuyển Mềm):** Nhận yêu cầu từ Sếp, phân loại task thuộc những Domain nào. Cho phép chọn TỐI ĐA 2 Domains nếu task nằm ở ranh giới giao thoa (Ví dụ: Tối ưu Dashboard biểu đồ thời gian thực chạy tính toán nặng sẽ cần cả `[Frontend_UI]` lẫn `[Backend_Service]`).
- **Bước 2 (Thu hẹp Target):** Chỉ đối chiếu và chọn lựa các Agents/Skills thuộc 1 hoặc 2 Domain đã chọn để đọc lệnh.
- **Giá trị cốt lõi:** Ngăn chặn tuyệt đối việc LLM bị ảo giác phân bổ (Task Allocation Hallucination) khi phải chọn 1 ứng viên giữa 64 skills. Tắt tịt hiện tượng "Ám ảnh trọng số ngầm" (Implicit Root Bias) khiến chuyên gia Quant nhảy ra code chức năng Login. Đảm bảo Context Thực thi luôn sạch nhất có thể!
