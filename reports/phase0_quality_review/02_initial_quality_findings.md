# Phase 0 — Đối chiếu ban đầu từ bằng chứng hiện có

**Ngày:** 22/11/2026. Đây là bước review tiếp nối, không phải benchmark inference mới hoặc chấm điểm cuối cùng. Không tải ảnh, không chạy model, không nghe lại audio hoặc xem lại toàn bộ ảnh trong bước này. [03_existing_evidence_100.csv](03_existing_evidence_100.csv) kiểm kê đủ 100 ID và nối query, human override, ghi chú ảnh, hash và bằng chứng audio; [04_review_input_hashes.json](04_review_input_hashes.json) ghi hash nguồn và sáu báo cáo kiến trúc để đối chiếu về sau.

## Rubric chất lượng áp dụng

| Chiều | Pass khi | Fail khi | Unknown khi |
|---|---|---|---|
| Query semantic correctness | Query giữ đúng nghĩa EN/JP/VN hoặc ý định đã xác nhận | Đổi nghĩa, đổi thực thể, đổi loại khái niệm | Nghĩa chưa rõ hoặc chưa đủ review |
| Image relevance | Ảnh thể hiện được nghĩa cần học | Sai đối tượng/hành động/ngữ cảnh | Chưa xem ảnh hoặc nghĩa chưa quyết định |
| Image visual quality | Đủ rõ để học trên kích thước hiển thị mục tiêu | Chữ/watermark/độ nhỏ gây cản nội dung, hoặc minh họa khó dùng | Chưa quan sát ở kích thước mục tiêu |
| Audio pronunciation | Nghe đúng reading, rõ, không cắt/lỗi phát âm | Người nghe xác nhận lỗi reading/phát âm | Chưa nghe đúng file/hash |
| Technical integrity | File decode/play được, ID/metadata/hash khớp | File hỏng hoặc mapping/hash sai | Chỉ có ghi nhận lịch sử, chưa kiểm lại |

Mỗi chiều tính pass/fail/unknown trên mẫu số 100, riêng raw model query và effective query sau override. Không cộng license vào điểm. Các lỗi chữ/watermark là quan sát hiển thị, không phải phán quyết quyền sử dụng. Kết luận về Qwen dùng parsed query gốc; không lấy query do người sửa để tăng điểm model. Chưa có review độc lập đầy đủ để chứng nhận tỷ lệ đạt cuối cùng.

## Kết quả đọc query ban đầu

**Verified:** ledger lịch sử có 100 query parsed; 35 cờ `needs_semantic_review`, 65 `not_independently_validated`. Đó là nhãn triage cũ, không phải 35 fail/65 pass. Trong CSV mới, desk review ưu tiên **7 query có dấu hiệu lỗi rõ**, gồm 2 lệch nghĩa đã có owner decision và 5 nhận định **Inferred** cần người duyệt xác nhận. 93 hàng còn lại giữ `unknown`, không coi là pass chỉ vì chưa có lỗi được xác nhận.

| ID | Query model gốc | Đối chiếu nghĩa | Mức bằng chứng |
|---|---|---|---|
| 004 rice | `rice grain` | Ledger xác nhận cooked rice; effective query đã sửa thành `cooked rice` | Verified — lệch approved sense |
| 009 chicken | `chicken animal` | Ledger xác nhận chicken meat; effective query đã sửa thành `chicken meat` | Verified — lệch approved sense |
| 019 rain | `rain illumination` | Ánh sáng không giữ rõ hiện tượng mưa | Inferred — Qwen nghi vấn |
| 041 today | `today timepiece` | Chuyển hôm nay thành loại đồ vật đồng hồ | Inferred — Qwen nghi vấn |
| 042 tomorrow | `tomorrow timepiece` | Chuyển ngày mai thành loại đồ vật đồng hồ | Inferred — Qwen nghi vấn |
| 043 yesterday | `yesterday place` | Chuyển thời gian sang địa điểm | Inferred — Qwen nghi vấn |
| 066 software | `software device` | Chuyển phần mềm sang thiết bị vật lý | Inferred — Qwen nghi vấn |

Nguồn: `reports/image_pipeline_audit/20261106T102750Z-cd93f8a1/02_qwen_queries_100.csv`, các hàng theo ID; `data/vocabulary/semantic_decisions_v1.json`, approvals 004/009. Các query chung chung như `easy object`, `study object`, `remember object`, `always object` cần xem tiếp; chưa tự gán fail từ một regex hoặc hậu tố `object`. Chưa tuyên bố 7% là tỷ lệ lỗi model cuối cùng.

## Tách nguyên nhân Qwen, search và SigLIP

| Trường hợp | Điều biết được | Điều chưa chứng minh |
|---|---|---|
| Rice/chicken production cũ | Model query sai nghĩa đã duyệt; người sửa query không chữa được bytes ảnh cũ | Không đánh đồng candidate replacement hiện tại với ảnh production cũ |
| Today/tomorrow | Query hướng vào timepiece; ghi chú ảnh cũ là watch/watch-video graphic | Đóng góp của search/ranker vẫn có thể tồn tại; chưa đủ candidate để định lượng |
| Swim: `person swimming` nhưng ảnh chân dung | Ghi chú ảnh cho thấy output không thể hiện hành động dù query mô tả đúng hành động | Search không có candidate phù hợp hay SigLIP bỏ qua candidate tốt? Unknown |
| Go: `person going` nhưng ảnh chân dung | Mismatch ở downstream hoặc ngữ cảnh ảnh không đủ rõ | Không kết luận chỉ Qwen/SigLIP gây lỗi |
| Shirt: `shirt clothing` nhưng ghi chú ảnh là sơ đồ mũi | Query và ảnh được ghi nhận lệch nhau nghiêm trọng | Cần kiểm tra lineage, download, mapping trước khi quy cho search/ranker |
| Friend 038 | Có nghĩa được duyệt nhưng thiếu approved image intent; pipeline chặn | Đây là thiếu quyết định đầu vào, không phải bằng chứng model inference mới thất bại |

Nguồn quan sát ảnh: `reports/image_pipeline_audit/20261106T102750Z-cd93f8a1/04_image_quality_review.csv`, cột `observed_notes`; đây là **quan sát lịch sử**, chưa phải lượt xem ảnh mới. `audit_statistics.json` cùng thư mục ghi không lưu đầy đủ candidate URL list hoặc score list; vì vậy attribution SigLIP/search phải giữ `unresolved` khi thiếu bằng chứng. `first_observable_failure_stage` là nơi đầu tiên thấy vấn đề, không tự chứng minh nguyên nhân duy nhất.

Để chốt nguyên nhân mà chưa inference: trước tiên đối chiếu query gốc/effective query, ID, selected source URL, metadata và hash; dùng ghi chú/contact sheet hoặc xem file hiện có. Muốn kết luận ranking sai cần chứng minh cùng run có candidate tốt hơn và score/order tương ứng; nếu không lưu thì ghi Unknown và đề xuất phép thử riêng, không tái chạy tự động.

## Audio và technical integrity

Inventory lịch sử ghi 100 MP3 staged hợp lệ kỹ thuật; 10 được nghe duyệt theo hash, 10 có phản hồi chung chưa duyệt theo hash, 80 còn pending (`reports/full_media_staging_inventory_v1.json`, mỗi record `audio`). CSV giữ nguồn này, không nâng thành kết quả nghe mới. Tình trạng quyền audio không làm thay đổi thống kê pronunciation. Metadata/hash được giữ để người duyệt mở đúng file; không sửa hoặc promote asset trong lần này.

## Kết luận Phase 0 hiện tại

Mục tiêu 100/100 semantic correctness **chưa được chứng minh**, đã có ít nhất hai query gốc lệch nghĩa được xác nhận; cần review 5 nghi vấn và 93 hàng còn lại. Tình trạng license không tham gia kết luận đó. Công việc P0 tiếp theo là review nghĩa theo ID, xem lại ảnh sai để xác nhận lineage/nguyên nhân và hoàn thiện Excel/content pack contract. Full license inventory là P2; chỉ tập asset thực sự đưa lên website mới cần qua cổng quyền public trong P1.
