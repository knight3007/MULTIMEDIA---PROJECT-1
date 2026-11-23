# 05 — Roadmap có điều kiện và cổng quyết định

**Mục tiêu nộp môn:** trước **2/12/2026**, nếu chọn web, người khác truy cập được một URL công khai. Đây là hard deadline của người dùng, **không phải ước lượng** rằng mọi phase dưới đây sẽ kịp. Excel import theo mẫu và khả năng tạo/lưu media cho bộ từ mới là chức năng trọng tâm; 100 từ hiện tại dùng đánh giá model, không phải giới hạn sản phẩm. Mọi bước bên dưới là kế hoạch, chưa triển khai.

## Phase 0 — Kiểm chứng model và baseline (effort: vừa, ưu tiên đầu tiên)

- **Objective:** xác định chính xác model/pipeline có đạt mục tiêu **100/100** hay không trước khi tiếp tục runtime.
- **Scope:** đóng băng input 100 ID, model/prompt/cache và dữ liệu output hiện có; tách ba chỉ số: (1) query hợp lệ cú pháp, (2) query đúng nghĩa EN/JP/VN theo người review, (3) media đúng nghĩa/kỹ thuật/quyền sử dụng. Lấy nhãn độc lập từng ID, ghi pass/fail/unknown và lý do, không tự lấp chỗ thiếu bằng model. Đối chiếu 20 nghĩa `needs_decision`, ảnh rice/chicken, 29 ảnh mới có cờ lỗi, 60 ảnh mới chưa được review (`01_current_project_audit.md`; `reports/full_media_staging_review.md:75-92`).
- **Dependencies:** registry/manifest hiện có và người duyệt song ngữ/media; không cần chạy lại Qwen để chấm output đã lưu. Nếu 94 raw accepted output thiếu làm cản truy nguyên, ghi hạn chế trước khi quyết định chạy thêm (`reports/image_pipeline_audit/20261106T102750Z-cd93f8a1/audit_statistics.json`).
- **Deliverables:** bảng 100 ID với bằng chứng theo phiên bản/hash, định nghĩa mẫu số và tiêu chí pass, tỷ lệ từng chỉ số, danh sách lỗi ưu tiên, baseline thời gian/tài nguyên hiện có và phép đo còn thiếu.
- **Acceptance:** không còn mục nào bị tính “đạt” chỉ vì parse/file tồn tại; người duyệt xác nhận rubric; báo cáo nêu rõ **đạt/chưa đạt/chưa đủ bằng chứng** cho 100/100. Chỉ tuyên bố 100/100 khi đủ 100 nhãn pass độc lập cho tiêu chí đã định.
- **Risks:** thiếu raw/nhãn, nghĩa mơ hồ, quyền media chưa rõ. **Go/No-Go:** chỉ qua Phase 1 khi lỗi đã được định lượng và có đường sửa cụ thể; nếu thiếu bằng chứng, dừng tuyên bố chất lượng và lấy bằng chứng trước.

## Phase 1 — Ổn định nội dung và hợp đồng Excel (effort: lớn)

- **Objective:** tạo được một bộ nội dung có thể phát hành từ Excel mẫu mà không làm hỏng pipeline hiện tại.
- **Scope:** chốt workbook `Vocabulary` với ba cột bắt buộc `english`, `japanese`, `vietnamese`, `target_sense` tùy chọn (`04_recommended_architecture.md`); chọn parser; validation và preview theo hàng; map import ID riêng. Sửa các lỗi model/ảnh được Phase 0 chỉ ra, duyệt nghe/nguồn/quyền, chỉ promote đúng hash được phê duyệt; phát hành content pack versioned cho 3–5 hàng MVP trước. Không sửa bộ 100 benchmark để che lỗi.
- **Dependencies:** kết quả Phase 0, quyết định nghĩa và quyền media; thử trên pipeline local cô lập, chưa cần host production.
- **Deliverables:** mẫu Excel, thông báo lỗi đầu vào, pack schema/hashes, danh sách asset được duyệt và phép đo job nhỏ.
- **Acceptance:** Excel hợp lệ 3–5 hàng đi hết import→media→pack trong môi trường thử local; file lỗi báo đúng hàng/ô trước khi dùng model; một item lỗi không làm mất item đã hợp lệ; không có asset `needs_review`/không rõ quyền trong pack. Kiểm tra hash và nguồn khi retry. Người học tự phục vụ qua web thuộc Phase 3.
- **Risks:** chất lượng 100 từ thấp, quyền ảnh/audio, gTTS giới hạn, thời gian inference. **Go/No-Go:** nếu không có ít nhất 3 item media được duyệt và luồng import hoạt động, không gắn nhãn “Excel→media hoàn chỉnh”.

## Phase 2 — Runtime web nhỏ nhất (effort: vừa)

- **Objective:** người học mở pack, học từ và chơi một vòng hoàn chỉnh; không gọi AI trong gameplay.
- **Scope:** trang web desktop, flashcard ảnh/audio, game nhập từ và điểm local theo mô tả `projectframework.md:1-17`; hiển thị rõ item lỗi/chưa có media. Tải và lưu pack cục bộ, version/checksum, thử trạng thái offline sau lần tải đầu. Không xây Android/native song song.
- **Dependencies:** hợp đồng pack và ít nhất 3 item `ready` từ Phase 1.
- **Deliverables:** MVP chạy local, hướng dẫn dùng và kết quả thử nhập/chơi/offline.
- **Acceptance:** người dùng đi từ chọn bộ từ → flashcard → game → lưu điểm; reload sau khi ngắt mạng vẫn dùng pack đã lưu; không có request Qwen/SigLIP/gTTS trong gameplay.
- **Risks:** cache bị xóa/quota, âm thanh browser, bàn phím và khả năng truy cập. **Go/No-Go:** thất bại offline hoặc data integrity thì chưa phát hành công khai.

## Phase 3 — Tích hợp online import và đo hiệu năng (effort: lớn)

- **Objective:** kiểm chứng luồng người học **tự tải Excel lên web → xử lý media khi online → lưu pack → chơi offline**.
- **Scope:** dịch vụ/job xử lý có giới hạn và trạng thái rõ ràng, không dùng Quick Tunnel production; bảo vệ upload, giới hạn tài nguyên, retry không nhân đôi generation. Đo parse, queue, model, search, audio, review, download và lần tải game; thử mạng chậm/mất mạng, hai import liên tiếp và file lỗi. Chỉ thử Docker cho worker nếu nơi chạy service cần đóng gói nhất quán; không dựng Kubernetes cho MVP. Không suy ra tốc độ 100 từ từ benchmark 25 từ.
- **Dependencies:** Phase 0–2, nơi chạy job thật và chính sách quyền dữ liệu/media.
- **Deliverables:** báo cáo latency/tài nguyên/chi phí thật, test end-to-end và quy trình xử lý lỗi.
- **Acceptance:** job nhỏ 3–5 hàng hoàn tất hoặc trả lỗi có thể sửa; kết quả chưa review không phát hành; pack đã tải chơi được khi tắt mạng; lỗi job không làm mất pack cũ.
- **Risks:** không có hạ tầng/chi phí được duyệt trước deadline. **Go/No-Go:** nếu chưa có đường xử lý online ổn định, không tuyên bố Excel tự phục vụ đã hoàn thành; cần báo giảng viên phần demo bị thu hẹp.

## Phase 4 — Đóng gói, đưa lên Internet và xác minh (effort: vừa)

- **Objective:** người khác truy cập bản web qua URL công khai trước hạn nộp, với chức năng đúng như đã chứng minh.
- **Scope:** build/upload **chỉ** web artifact và asset đủ quyền lên GitHub Pages; kiểm tra base path repository, HTTPS, service worker, version cache, trang lỗi và cách rollback bản trước. Dịch vụ online (nếu Phase 3 đạt) có endpoint riêng, không nằm trên Pages. Không publish workspace, staging, workbook người dùng, secret hoặc raw experiment.
- **Dependencies:** Phase 2; Phase 3 nếu công bố chức năng Excel→media tự động.
- **Deliverables:** URL công khai, commit/build/version phát hành, checklist thử từ thiết bị khác và hướng dẫn phục hồi.
- **Acceptance:** máy/điện thoại khác mở URL không đăng nhập, tải app/pack và media hợp lệ, import theo phạm vi đã công bố, chơi được; sau tải lần đầu, tắt mạng và reload vẫn chơi pack đã lưu. Dùng bản cũ nếu bản mới lỗi. [GitHub Pages là static host](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages); [offline cache cần service worker phù hợp](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers).
- **Risks:** Pages build/permission, path sai, cache cũ, media chưa rõ quyền. **Go/No-Go:** không có URL công khai kiểm thử được hoặc asset chưa đủ quyền thì không gọi bản nộp là đạt.

## Risk register và đường chuyển đổi

| Rủi ro | Mức | Hành động trước khi đi tiếp |
|---|---|---|
| Model có output 100/100 nhưng không đúng nghĩa 100/100 | Rất cao | Phase 0 chấm độc lập từng ID; sửa lỗi theo nhóm và chấm lại, giữ dấu phiên bản. |
| Excel tùy ý cần media online; hiện chưa có backend sản phẩm | Rất cao | Prototype job 3–5 hàng sớm sau cổng chất lượng; đo chi phí/latency và báo rõ phần chưa đạt. |
| 98 ảnh chưa rõ quyền; audio chưa rõ quyền phân phối | Rất cao | Chỉ dùng asset được duyệt theo hash/nguồn hoặc thay bằng nguồn có quyền xác minh. |
| Hạn 2/12 ngắn, repo chưa có runtime | Cao | Làm một vertical slice Excel→pack→game→URL; dừng mở rộng nền tảng/tính năng phụ. |
| Docker/Kubernetes bị dùng để thay thế phép đo và quyền media | Trung | Chỉ container hóa worker sau khi biết host/GPU/storage; Kubernetes chỉ xét khi có nhu cầu scale/availability đo được. |
| Offline cache/asset update sai | Trung | Thử online→offline→update→rollback với pack có version/hash. |

Không migration phá vỡ: giữ nguyên Python pipeline, 100-ID registry và báo cáo lịch sử; xây pack adapter riêng, thử trên dữ liệu nhỏ, so sánh hash/status, rồi mới tích hợp runtime. Nếu Phase 0/1 thất bại, **không thay nền tảng để né lỗi nội dung**. Không chạy Kaggle GPU, batch ảnh/audio hay phát hành trong chính đợt đánh giá kiến trúc này.
