# Implementation Plan: Production Defense-in-Depth Pipeline

Kế hoạch này tích hợp 13 TODOs từ Lab 11 vào một hệ thống phòng thủ đa lớp (Defense-in-Depth) hoàn chỉnh theo yêu cầu của bài tập lớn.

## Mục tiêu Hệ thống
Xây dựng pipeline bảo mật cho AI Agent ngành ngân hàng gồm 6 lớp:
1. **Rate Limiter**: Chống tấn công từ chối dịch vụ (DoS).
2. **Input Guardrails**: Chặn Prompt Injection và Topic Filtering (Lọc chủ đề).
3. **NeMo Guardrails**: Kiểm soát luồng hội thoại bằng Colang.
4. **Output Guardrails**: Quét PII (thông tin cá nhân) và Secrets.
5. **LLM-as-Judge**: Đánh giá đa tiêu chí (Safety, Relevance, Accuracy, Tone).
6. **Audit & Monitoring**: Ghi nhật ký hệ thống và cảnh báo bất thường.

---

## Sprint 1: Nền tảng & Tấn công (TODO 1-2)
*Mục tiêu: Tạo bộ dữ liệu kiểm thử (safe queries, attacks, edge cases) theo đúng yêu cầu đề bài.*

- **Task 1.1**: Cập nhật `src/attacks/attacks.py` với 7+ mẫu tấn công từ đề bài (DAN, CISO impersonation, SQL injection...).
- **Task 1.2**: Implement `generate_ai_attacks` dùng Gemini để tạo thêm biến thể tấn công tinh vi.
- **Task 1.3**: Chuẩn bị bộ test Rate Limit (15 requests liên tục).

---

## Sprint 2: Lớp Bảo vệ Đầu vào & Rate Limiting (TODO 3-5 + New)
*Mục tiêu: Chặn đứng các mối đe dọa ngay từ cửa ngõ.*

- **Task 2.1**: **[NEW]** Xây dựng `RateLimitPlugin` trong `src/guardrails/input_guardrails.py` (Cơ chế Sliding Window).
- **Task 2.2**: Hoàn thiện `detect_injection` (Regex nâng cao) và `topic_filter` (Semantic check).
- **Task 2.3**: Tích hợp tất cả vào `InputGuardrailPlugin` (Google ADK callback).

---

## Sprint 3: Lớp Bảo vệ Đầu ra & LLM-as-Judge (TODO 6-8)
*Mục tiêu: Đảm bảo phản hồi của AI an toàn và chuyên nghiệp.*

- **Task 3.1**: Hoàn thiện `content_filter` trong `src/guardrails/output_guardrails.py` để ẩn (redact) email, số thẻ, mật khẩu.
- **Task 3.2**: Triển khai `LLM-as-Judge` với prompt đánh giá 4 tiêu chí: **Safety, Relevance, Accuracy, Tone**.
- **Task 3.3**: Cấu hình `OutputGuardrailPlugin` để trả về VERDICT (PASS/FAIL).

---

## Sprint 4: NeMo Guardrails & Hệ thống Giám sát (TODO 9 + New)
*Mục tiêu: Thêm lớp bảo mật logic và khả năng quan sát hệ thống.*

- **Task 4.1**: Viết file Colang trong `nemo_guardrails.py` để xử lý các tình huống bẻ lái (jailbreak) phức tạp.
- **Task 4.2**: **[NEW]** Triển khai `AuditLogPlugin` để xuất file `audit_log.json` chứa: input, output, layer nào chặn, độ trễ (latency).
- **Task 4.3**: **[NEW]** Xây dựng module `MonitoringAlert` để in cảnh báo khi tỉ lệ bị chặn > 20%.

---

## Sprint 5: Testing, HITL & Report (TODO 10-13)
*Mục tiêu: Kiểm chứng hệ thống và hoàn thiện báo cáo cá nhân.*

- **Task 5.1**: Chạy `SecurityTestPipeline` trong `testing.py` để so sánh kết quả Trước và Sau khi có bảo vệ.
- **Task 5.2**: Hoàn thiện `hitl.py` với logic Confidence Router (Chuyển tiếp cho người duyệt nếu độ tự tin thấp).
- **Task 5.3**: Viết Báo cáo cá nhân (Part B):
    - Bảng phân tích Layer nào chặn tấn công nào.
    - Phân tích False Positive (nhầm lẫn).
    - Phân tích lỗ hổng còn tồn tại (Gap analysis).
    - Đề xuất triển khai thực tế (Production readiness).

---

## Kế hoạch Xác nhận (Verification)
1. **Chạy Full Pipeline**: `python src/main.py`
2. **Kiểm tra đầu ra**: 
    - File `audit_log.json` phải đầy đủ thông tin.
    - Test 3 (Rate Limit) phải chặn 5 requests cuối.
    - Test 2 (Attacks) phải bị chặn bởi ít nhất 1 layer.
