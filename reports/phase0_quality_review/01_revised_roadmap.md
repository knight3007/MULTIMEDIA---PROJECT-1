# Roadmap revised — chất lượng trước, quyền tại cổng public

**Ngày:** 22/11/2026. Bổ sung cho roadmap Architecture Reassessment cũ, theo [00_scope_adjustment.md](00_scope_adjustment.md). Không thay đổi nội dung hoặc trạng thái lịch sử của các báo cáo cũ.

## Phase 0 / P0 — Review và hợp đồng dữ liệu

**Objective:** xác định lỗi chất lượng trên benchmark 100 từ và chuẩn bị đường nhập Excel. **Scope:** chấm query theo EN/JP/VN, so raw parsed query với effective query có human override; kiểm tra ảnh sai và bằng chứng candidate/ranking hiện có. Chấm riêng pronunciation và technical integrity khi có bằng chứng. Không kiểm kê license toàn bộ 100 ảnh.

**Dependencies:** cache/ledger, semantic decisions, asset/manifests và nhãn người duyệt. **Deliverables:** ledger 100 ID, nhóm lỗi theo bước, pass/fail/unknown từng chiều, hợp đồng Excel/content pack. **Acceptance:** mọi ID được kiểm kê; không dùng license hoặc `game_ready` làm nhãn model; không quy lỗi SigLIP khi thiếu candidate/score; ghi rõ phần chưa nghe/xem và nghĩa chưa được xác nhận.

**Risks:** raw output và candidate scores thiếu, nghĩa đa nghĩa, chưa đủ nhãn độc lập. **Go/No-Go:** được chuẩn bị contract và kế hoạch thử MVP khi đã biết lỗi/giới hạn; chưa được tuyên bố model đạt 100/100 khi còn fail/unknown. Không cần license inventory đầy đủ để qua bước này. Mọi sửa code/inference là bước riêng sau yêu cầu tiếp theo.

## Phase 1 / P1 — Vertical slice local

**Objective:** kiểm chứng Excel → content pack → học/chơi offline trên tập nhỏ 3–5 hàng. **Scope:** parse/preview, trạng thái lỗi theo item, lưu pack và game nhỏ; dùng media local hiện có có đánh dấu trạng thái, không tự biến thử nghiệm local thành phê duyệt public.

**Dependencies:** contract và lựa chọn tập thử có nội dung phù hợp; quyết định triển khai của chủ dự án. **Deliverables:** vertical slice, kết quả import và offline. **Acceptance:** không mất dữ liệu khi lỗi; không gọi AI trong gameplay; reload offline dùng pack đã lưu. **Risk:** pipeline chưa đáp ứng input tùy ý. **Go/No-Go:** có thể tiếp tục dù license của các asset ngoài tập phát hành chưa rõ; public cần cổng riêng bên dưới.

## Phase 2–3 / P1 — Import online và kiểm chứng

**Objective:** người học nhập file mẫu, xử lý nội dung khi online, lưu rồi chơi offline. **Scope:** job riêng cho Excel→media, đo độ trễ/tài nguyên, thử lỗi input/network/retry; giữ quyền và chất lượng ở hai chiều độc lập. **Dependencies:** vertical slice và nơi xử lý job. **Deliverables:** phép đo nhỏ, pack và kết quả end-to-end. **Acceptance:** trạng thái xử lý/review rõ ràng; lỗi không làm mất pack cũ; chất lượng chưa xác minh không được báo là đạt.

**Risk:** thiếu hạ tầng hoặc chất lượng model. **Go/No-Go:** chỉ công bố chức năng tự phục vụ khi đã thử thật; không dùng Kaggle Quick Tunnel làm API luôn sẵn. Docker là tùy chọn đóng gói worker sau khi biết host; Kubernetes chưa nằm trên critical path.

## Phase 4 / P1 — Release subset và publish

**Objective:** URL công khai cho môn học trước 2/12/2026, theo phạm vi thực sự đạt. **Scope:** chỉ kiểm tra kỹ thuật, nội dung và quyền cho những asset được đưa vào release; không tải lại các ảnh ngoài tập này để bổ sung giấy phép. **Dependencies:** runtime và release manifest có hash/nguồn/quyết định quyền. **Deliverables:** tập phát hành được duyệt, URL và kết quả thử từ máy khác/ngoại tuyến.

**Acceptance:** không có asset bị hạn chế rõ ràng chưa được phép; không tự đánh dấu unknown là licensed; attribution/điều kiện sử dụng được thực hiện; app tải đúng và chơi được sau ngắt mạng. **Risk:** tập release chưa đủ quyền hoặc offline lỗi. **Go/No-Go:** chỉ cổng public của tập đã chọn bị chặn, không chặn đánh giá chất lượng hoặc làm MVP local bằng việc chưa kiểm kê toàn bộ dữ liệu.

## P2 — Hoàn thiện inventory còn lại

Bổ sung quyền/metadata cho asset ngoài release khi có thời gian; giữ nguồn/hash và lịch sử. Không là dependency của P0/P1. Không xóa trường unknown hoặc sửa báo cáo cũ để làm số liệu đẹp hơn.

## Hợp đồng tối thiểu tiếp tục từ P0

Đề xuất workbook `.xlsx`, sheet `Vocabulary`, header bắt buộc `english`, `japanese`, `vietnamese`; `target_sense` tùy chọn. Mỗi hàng là một bộ ba text không rỗng; preview ô lỗi/trùng trước khi gửi xử lý. Đây là thiết kế mới đã được chủ dự án cho phép tự định nghĩa, chưa có parser hoặc workbook mẫu. Benchmark 100 từ giữ nguyên, dữ liệu nhập dùng identity riêng.

Content pack đề xuất giữ ID, bộ ba gốc, ý định nghĩa, media path/hash/source và **hai trạng thái riêng**: chất lượng từng chiều và eligibility public. Runtime chỉ cần content pack hợp lệ kỹ thuật cho thử nghiệm; exporter public thêm cổng nội dung/quyền cho tập release. Không sửa schema production hiện tại trong đợt review.
