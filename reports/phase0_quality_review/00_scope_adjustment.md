# Điều chỉnh phạm vi Phase 0 — học thuật, phi thương mại

**Ngày:** 22/11/2026. **Nguồn quyết định:** cập nhật trực tiếp của chủ dự án trong chat. Tài liệu này điều chỉnh ưu tiên trong `reports/architecture_reassessment/`; các báo cáo đó được giữ nguyên như ảnh chụp lịch sử. Roadmap hiện hành được bổ sung tại [01_revised_roadmap.md](01_revised_roadmap.md).

## Academic/non-commercial scope

Dự án phục vụ học tập, nghiên cứu và trình diễn, phi thương mại. Phạm vi này không được dùng để tự gán quyền sử dụng cho ảnh/audio. Không thực hiện full copyright audit 100 ảnh trong Phase 0; không cần xác minh license từng ảnh trước khi đánh giá model hoặc phát triển vertical slice. Không tải lại ảnh chỉ để bổ sung license metadata. Giữ source URL, metadata, license/status, registry, staging và asset hashes hiện có; không chỉnh lịch sử đánh giá.

## Hai thước đo độc lập

| AI Content Quality | Public Release Eligibility |
|---|---|
| Query đúng nghĩa bộ EN/JP/VN và ý định đã xác nhận | Sẵn sàng kỹ thuật cho bản phát hành |
| Ảnh đúng nội dung, phù hợp để dạy từ | Nội dung đã duyệt cho tập phát hành |
| Chất lượng hiển thị ảnh | Quyền phân phối phù hợp cho asset thực sự public |
| Phát âm audio đúng | Có nguồn/bằng chứng quyền hoặc điều kiện sử dụng tương ứng |
| File, metadata và mapping nguyên vẹn | Không chứa asset bị hạn chế rõ ràng khi chưa được phép |

`license_status=unknown` không phải lỗi query, semantic correctness, image relevance hay technical integrity. Watermark/chữ che ảnh có thể là lỗi hiển thị được quan sát riêng; không suy ra quyền sử dụng chỉ từ watermark hoặc tên host. File hợp lệ chưa chứng minh đúng nghĩa; nội dung tốt chưa tự động đủ điều kiện public. **Không dùng `game_ready=false` hoặc `promotion_eligible_now=0` làm tỷ lệ chất lượng model.** Các trường đó trong inventory lịch sử gộp nhiều cổng, gồm quyền phát hành.

Mỗi chiều chất lượng dùng `pass / fail / unknown`, kèm bằng chứng, người/cách review và mức chắc chắn. Báo cáo `pass/100`, `fail/100`, `unknown/100` riêng; không bỏ unknown khỏi mẫu số để tuyên bố 100/100. License được giữ ở cột riêng và không tham gia phép tính chất lượng. Kết quả đọc query trong lần này là desk review của trợ lý, không phải nhãn độc lập của người duyệt song ngữ.

## Thứ tự ưu tiên

- **P0:** đánh giá query/semantic correctness đủ 100 ID; phân tích ảnh sai và mức đóng góp của Qwen, search, SigLIP; chuẩn bị hợp đồng Excel và content pack.
- **P1:** xây vertical slice Web Game offline-first sau quyết định triển khai; kiểm tra quyền của tập asset được chọn trước khi đưa lên URL công khai.
- **P2:** hoàn thiện license/metadata inventory cho phần dữ liệu còn lại. Công việc này không chặn P0 hoặc P1.

## Yêu cầu phát hành công khai

Chỉ rà soát quyền của asset thực tế đi vào release; giữ attribution/nguồn và bằng chứng theo hash. Không đánh dấu `licensed` nếu thiếu bằng chứng; không public ảnh bị hạn chế rõ ràng khi chưa có phép. Asset còn unknown có thể tiếp tục được đánh giá chất lượng, nhưng chưa được mặc nhiên coi là đủ quyền phát hành. Quyết định release nằm ở tập phát hành, không yêu cầu dọn sạch toàn bộ 100 ảnh trước khi xây MVP.

## Critical path của MVP

Chốt rubric → kiểm tra query và lỗi ảnh hiện có → chốt Excel/content pack → quyết định sửa pipeline hoặc thử nghiệm tiếp theo → vertical slice với tập nhỏ → kiểm tra kỹ thuật/nội dung/quyền của tập phát hành → publish và thử offline trên URL thật. Bộ 100 từ là benchmark, không phải giới hạn số từ sản phẩm. Đợt này chỉ đọc bằng chứng và tạo báo cáo mới; inference, tải media và implementation cần yêu cầu tiếp theo.
