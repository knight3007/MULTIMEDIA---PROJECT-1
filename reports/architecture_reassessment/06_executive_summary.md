# 06 — Executive summary

- **Verdict:** **PARTIALLY ADOPT** — tách pipeline AI khỏi gameplay; chưa có bằng chứng biện minh chuyển sang Native App.
- **Recommended Product Platform:** Web Game cho trình duyệt desktop, URL công khai, lưu content pack để chơi offline sau lần tải đầu; đây là **kiến trúc đề xuất**, chưa được xây.
- **Recommended AI Architecture:** Hybrid theo giai đoạn: đánh giá/sửa model trên benchmark 100 từ trước; tạo và duyệt media trước khi chơi; Excel mới của người học cần xử lý online bất đồng bộ, sau đó lưu pack offline.
- **Top 3 Reasons:** (1) Chưa có web/game runtime để “migration” (`web/`, `game/`); (2) Qwen/SigLIP/gTTS hiện thuộc bước tạo nội dung, không có gameplay inference (`collect data script/imagecollector.py:757-838`, `audiocollector.py:166-179`); (3) Native không tự giải quyết chất lượng model, quyền media hay dịch vụ Excel→media (`reports/full_media_staging_inventory_v1.json:totals`).
- **Biggest Risk:** 100 query parse và 100 MP3 staged hợp lệ kỹ thuật nhưng **0/100 item game-ready**; 29 ảnh mới đã thấy lỗi, 60 ảnh chưa được review, quyền phát hành media phần lớn chưa rõ (`reports/full_media_staging_review.md:22-28,75-92`). Không thể chứng nhận model đạt 100/100.
- **First Action Before Implementation:** lập rubric và chấm độc lập từng ID của benchmark 100 từ về đúng nghĩa query, chất lượng ảnh/audio và quyền sử dụng; ghi pass/fail/unknown với bằng chứng/hash, rồi quyết định sửa model/pipeline ở đâu (`05_migration_roadmap.md`, Phase 0).

## Quyết định có thể hành động

**Đừng bỏ hướng web lúc này.** Với yêu cầu giảng viên, web phải được publish cho người khác mở trước 2/12/2026; GitHub repo public nhưng chưa có web deploy (`.github/workflows/`). [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) là ứng viên host static, chỉ xuất artifact và asset được phép công khai. PWA/cache cần thử trên URL thật. Excel import là ưu tiên sản phẩm số một, không phải tính năng nâng cao như `projectframework.md:17` từng ghi; chưa có parser/mẫu Excel. `04_recommended_architecture.md` đề xuất hợp đồng `.xlsx` tối thiểu, do chủ dự án cho phép tự định nghĩa.

**Không đánh đồng publish web với hoàn thành sản phẩm:** static host không xử lý Python model cho Excel mới. Phải có job online riêng, hoặc công bố rõ demo chỉ dùng bộ đã chuẩn bị; phương án thứ hai **không đáp ứng** luồng tự phục vụ Excel→media đã yêu cầu. Chi phí, độ trễ và chất lượng của job chưa đo. Nếu không vượt cổng Phase 0/1/3 trong thời gian còn lại, báo trung thực phạm vi đã đạt trước khi nộp.

## Phần giữ lại và phần phải làm

Giữ collectors, stable ID, semantic ledger, staging, validation và builder (`01_current_project_audit.md`). Xây mới hợp đồng/preview Excel, ranh giới content pack được duyệt, web runtime, xử lý online cho import và phát hành URL công khai. Desktop wrapper hoặc game engine chỉ xét sau khi MVP chứng minh một nhu cầu mà web không đáp ứng (`02_architecture_comparison.md`). Chi tiết điều kiện Go/No-Go và rủi ro nằm ở `05_migration_roadmap.md`.

**Docker/Kubernetes:** có thể cân nhắc Docker để đóng gói worker Excel→media sau khi xác định host/GPU và đo job thật; **không dùng Kubernetes cho MVP** vì chưa có nhu cầu scale/availability đã chứng minh. Cả hai không tăng chất lượng model hay giúp máy cá nhân chạy server liên tục (`03_ai_infrastructure_assessment.md`).

**Dựa trên hiện trạng codebase và các bằng chứng thu thập được, dự án KHÔNG NÊN chuyển sang Native App lúc này vì chưa có runtime để tái sử dụng, inference hiện nằm ở bước tạo nội dung, còn các nút thắt cấp bách là chất lượng model 100 từ, quyền media và luồng Excel→media.**
