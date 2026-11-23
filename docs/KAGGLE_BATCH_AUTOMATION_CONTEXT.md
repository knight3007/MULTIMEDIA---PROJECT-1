# Bối cảnh quyết định D2: tự động chạy Qwen3-4B theo lô trên Kaggle

**Cập nhật:** 2026-11-07. **Trạng thái:** kiến trúc được phê duyệt có điều kiện cho **D2-1 offline**; được tạo code, tests, notebook template, snapshot local và workflow nháp. Chưa được chạy Kaggle, dùng GPU, công bố snapshot, cấu hình credential thật, commit/push, POC 5 từ hoặc batch 100 từ. Đọc file này và [tài liệu kiến trúc](KAGGLE_BATCH_AUTOMATION_ARCHITECTURE.md) trước mọi công việc D2 tiếp theo.

## A. Tổng quan dự án

- Dự án: MULTIMEDIA – PROJECT 1. Repository GitHub Public: knight3007/MULTIMEDIA---PROJECT-1. Thư mục local: D:\MULTIMEDIA - PROJECT 1.
- Mục tiêu chính: tự động tạo kết quả Qwen3-4B cho 100 mục từ vựng EN/JP/VN.
- Thứ tự ưu tiên: chi phí bằng 0 nếu khả thi, ít lãng phí quota GPU, ít thành phần, không chạy lại phần đã xác minh, có thể tái lập và kiểm tra nguồn gốc.
- Phải giữ nguyên vocabulary production, ảnh, MP3, cache Qwen3-1.7B, quyết định ngữ nghĩa, pipeline hiện tại, notebook API V4 và các báo cáo Phase A/B/C0/D0/D1. Không tự động đưa output mới vào production.
- Đích hiện tại là hoàn thiện D2-1 offline để chủ dự án review; chưa có quyền triển khai live.

## B. Kiến trúc hiện có và mức xác minh

| Hạng mục | Bằng chứng và trạng thái |
|---|---|
| Qwen3-1.7B local và dữ liệu 100 từ | Có mã nguồn [query_generator.py](<../collect data script/query_generator.py>), nguồn [vocabulary](../data/vocabulary/) và [data contract](DATA_CONTRACT_V1.md) trong repository. Không chạy lại model local cho so sánh D2. |
| Phase A/B image-query và Phase C0 retrieval | Có mã nguồn [image_query_benchmark.py](<../collect data script/image_query_benchmark.py>) và [image_retrieval_benchmark.py](<../collect data script/image_retrieval_benchmark.py>), cùng báo cáo lịch sử trong [reports](../reports/). Giữ nguyên artifact lịch sử. |
| Phase D0/D1 remote Qwen | Có [client V4](<../collect data script/remote_qwen_client.py>), [probe](<../collect data script/remote_qwen_probe.py>), [tài liệu V1](REMOTE_QWEN_API_V1.md), [tài liệu V2](REMOTE_QWEN_API_V2.md) và manifest D1 năm từ. D1 A+B là thí nghiệm API V4 độc lập. Repository hiện chỉ có manifest/dry-run D1, chưa có bằng chứng kết quả live D1 trong thư mục báo cáo. |
| Notebook API V4 | Đã đọc [file notebook tham khảo](../Kaggle_Qwen3_4B_Cloudflare_Quick_Tunnel_V4.ipynb) ở chế độ chỉ đọc; SHA-256 của file tham khảo khi kiểm tra: c66f4d069a15fe41c4a50067014ba670b0f2a44b39231de9cdd98279099d00d9. File này không chứa output cell đã lưu. Chủ dự án nói đã kiểm tra remote inference Windows ↔ Kaggle; kết quả đó chưa được lưu trong báo cáo D1 local. |
| Cấu hình Qwen3-4B trong V4 | Mã notebook dùng Qwen/Qwen3-4B, FP16, GPU 0, Transformers, tokenizer chat template với enable_thinking=False, do_sample=False, max_new_tokens ≤256, input ≤2048 token theo tokenizer và không truncate. Mã đo thời gian tải tokenizer/model nhưng file tham khảo không có số đo đã chạy. Revision đặt là main; mã chỉ in commit hash nếu thư viện cung cấp, nên revision thực tế chưa được xác minh. |
| GPU và API demo | Chủ dự án xác nhận dùng Tesla T4. Metadata file V4 chỉ ghi accelerator=gpu; quyền cấp T4 và quota hiện tại của tài khoản chưa được kiểm tra qua Kaggle. V4 có Cloudflare Quick Tunnel, Bearer API, giới hạn demo 20 generation/15 phút và tự dừng demo; các giới hạn demo này không được áp dụng máy móc cho batch mới. |
| CLI local | Chưa thấy lệnh Kaggle CLI trong PATH hoặc môi trường .venv của workspace lúc kiểm tra. Chưa đăng nhập Kaggle, chưa push notebook và chưa dùng GPU trong D2. |

Tài liệu nền tảng đã đối chiếu: [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks), [Kaggle CLI kernels](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md), [kernel metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md), [CLI changelog](https://github.com/Kaggle/kaggle-cli/blob/main/CHANGELOG.md), [GitHub workflow_dispatch](https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow), [GitHub Actions limits](https://docs.github.com/en/actions/reference/limits) và [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Tài liệu Kaggle mô tả Save & Run All chạy thành phiên riêng và lưu output của phiên bản; không chứng minh file đang ghi trong một phiên bị hủy đột ngột sẽ còn tải được. Thông báo Kaggle cũ chỉ cho lập lịch CPU; hỗ trợ lập lịch GPU cho tài khoản này chưa được xác minh và không nằm trong phạm vi ban đầu.

## C. Quyết định đã được chủ dự án xác nhận

### Chế độ và kích hoạt

- Batch inference là hướng chính cho 100 từ. Giữ API V4 cho tương tác; chưa tự động khởi động API và không dùng Cloudflare Tunnel trong batch.
- Kaggle phải tiếp tục chạy sau khi Windows tắt hoặc PowerShell đóng. Windows có thể tải output về sau; không cần tự tải khi máy tắt.
- Chọn GitHub Actions làm **ứng viên bộ điều phối duy nhất**, chỉ dùng standard GitHub-hosted runner CPU của repository Public; không dùng larger runner trả phí. Ban đầu chỉ có workflow_dispatch thủ công, chưa lập lịch. Đây là phê duyệt lựa chọn công nghệ, không phải phê duyệt kiến trúc cuối hay triển khai.
- GitHub Actions sẽ khởi chạy và theo dõi từng phiên Kaggle tuần tự, xác minh output rồi mới xét batch tiếp theo. Toàn bộ suy luận Qwen3-4B chạy trên Kaggle GPU. Không chạy chồng phiên nhằm tránh tiêu hao quota.

### Suy luận và POC

- Toàn bộ 100 từ: mặc định chỉ Variant B, tối đa 100 generation. Batch runner dự kiến cho phép chọn A, B hoặc A+B về sau, nhưng mặc định B. Dùng nguyên prompt Variant B gốc; không rút ngắn, viết lại hoặc thay đổi quyết định ngữ nghĩa.
- So sánh Qwen3-4B B với kết quả Qwen3-1.7B B đã có; không chạy lại model local. Variant C Vietnamese-first/semantic-aware nếu có phải là thí nghiệm mới, không ghi đè A/B.
- D1 năm từ A+B qua API V4 được giữ độc lập. POC D2 mới chỉ chạy B cho đúng ID 004, 009, 041, 054, 065; tối đa 5 generation. POC phải kiểm chứng luồng Actions → Kaggle → tải và xác minh output, không chỉ chứng minh model trả text.
- Tách hai giai đoạn: (1) sau khi kiến trúc được phê duyệt, chuẩn bị mã, notebook batch riêng, workflow, kiểm thử và báo cáo offline; (2) chỉ khi có phê duyệt riêng mới chạy POC GPU. Nên kiểm thử logic điều phối với hai batch giả lập offline.

### Thời gian, quota và phục hồi

- Trần POC là 60 phút kể từ lúc thực thi Kaggle bắt đầu, gồm setup, tải model, nạp model, inference và lưu output; đây không phải mục tiêu thời gian. Hoàn tất thì thoát ngay. Sau phút 50 không khởi động inference mới; dùng phần còn lại để ghi manifest, output và logs.
- Ghi riêng thời gian environment setup, model download, model loading, từng inference và output finalization. Quá giới hạn thì ghi timeout hoặc incomplete, không báo thành công và không tự retry POC.
- Phân biệt timeout/hủy GitHub Actions với trạng thái thực của Kaggle. Kiểm tra nội bộ notebook là cơ chế tự dừng có điều kiện, chưa được xác nhận là cưỡng chế dừng GPU chính xác sau 60 phút.
- Checkpoint bền vững là output của **phiên bản Kaggle đã hoàn tất và đã được xác minh**. Không yêu cầu lưu bền vững từng từ trong lúc phiên chạy. Cân nhắc 10–25 từ mỗi batch, chưa chốt kích thước trước khi có số đo POC; nhỏ hơn giảm công chạy lại, lớn hơn giảm số lần tải model.
- Mỗi batch cần ID, danh sách từ, manifest và output riêng. Chỉ đánh dấu hoàn tất sau khi đối chiếu đúng số phiên bản Kaggle, manifest, số bản ghi, checksum và file output. Chỉ chạy lại batch chưa xác minh hoàn tất; kiểm tra toàn bộ output trước khi gộp 100 từ. Không ghi đè output cũ.
- Khi Actions bị hủy: **để batch Kaggle đang chạy hoàn tất hoặc chạm giới hạn nội bộ**; Actions không khởi chạy batch tiếp theo. Có thể còn một phiên Kaggle mồ côi, vẫn tiêu hao GPU. Trước khi tiếp tục phải kiểm tra đúng phiên bản và output; nếu còn chạy thì báo trạng thái, không khởi chạy bản thay thế. Chủ dự án có thể dừng thủ công trong giao diện Kaggle khi bất thường hoặc muốn tiết kiệm quota. Hủy Actions không đồng nghĩa Kaggle đã dừng.
- Không tự động retry generation hay khởi chạy lại POC khi chưa xác minh trạng thái phiên trước. Khi workflow thất bại hoặc bị hủy, phải lưu đủ định danh để lần sau đối chiếu phiên bản Kaggle đã tạo.
- Trước live run, kiểm tra quota GPU nếu Kaggle cung cấp thông tin. Kaggle CLI 2.2.x có lệnh [kaggle quota](https://github.com/Kaggle/kaggle-cli/blob/main/CHANGELOG.md); chưa kiểm thử với tài khoản này.
- Khi raw output và checksum đã đủ nhưng một kết quả B không parse hợp lệ, lưu nguyên raw/hash/lỗi, đánh dấu `needs_review`, dừng trước batch tiếp theo và không tự retry. Trạng thái **collection** (đã thu đủ và xác minh file) tách khỏi **quality** (parse và đánh giá ngữ nghĩa).
- Resume do chủ dự án kích hoạt một lần bằng `workflow_dispatch` với logical experiment ID cũ. Quy trình đối chiếu phiên Kaggle cũ, giữ batch đã xác minh thành công, chỉ chạy lại batch chưa thành công sau khi xác nhận phiên cũ không còn chạy. Nếu không thể xác minh experiment ID, version và checksum thì dừng an toàn; artifact Actions không phải nguồn trạng thái duy nhất. GitHub run ID chỉ là định danh lần dispatch, không phải định danh thí nghiệm bền vững.
- Sau POC mới tính trần GPU cụ thể và mức dự phòng cho 100 từ từ số đo thực, trình chủ dự án duyệt trước khi chạy. Chưa có trần số học được phê duyệt cho 100 từ.

### Kaggle, dữ liệu và bảo mật

- Username Kaggle: knight3007. Notebook batch và output Kaggle phải **Private**, không tự công bố. Tên/slug từng phiên batch là chi tiết thiết kế chờ phê duyệt và kiểm chứng khả dụng; đề xuất slug đơn trước đây không phải quyết định đã chốt.
- Ghim và thử Kaggle CLI 2.2.5 vì [changelog](https://github.com/Kaggle/kaggle-cli/blob/main/CHANGELOG.md) ghi đã sửa lỗi bỏ qua số phiên bản ở status, output, files và logs. Luôn dùng định danh phiên bản cụ thể khi xác minh; không dùng latest. Chưa thử CLI thật hoặc account này.
- Snapshot input GitHub Public chỉ được đồng ý **về nguyên tắc**. Tạo ở thư mục mới, chứa tối thiểu 100 vocabulary ID, EN/JP/VN, ngữ nghĩa đã được duyệt nếu cần và prompt B nguyên văn; không gồm ảnh, MP3, cache lớn, file tạm hoặc báo cáo nội bộ không cần thiết.
- Trước khi công bố, lập báo cáo chính xác file, kích thước, SHA-256, nội dung thay đổi; rà soát secrets, token, đường dẫn riêng tư, dữ liệu cá nhân, bản quyền và nội dung không phù hợp để Public. Chủ dự án phải duyệt nội dung cụ thể trước commit/push. Actions sau đó dùng commit SHA cố định và kiểm tra checksum snapshot trước khi khởi chạy Kaggle.
- Dùng GitHub Secrets cho xác thực Kaggle. Không yêu cầu gửi token trong chat, không ghi thông tin xác thực vào Markdown, source, output hay logs.
- Raw output, parsed output, model, prompt, prompt SHA-256, token count, latency, UTC timestamp, metadata, logs và manifest phải được giữ riêng cho từng batch. Không tự động chuyển kết quả sang production, không tự động commit/push.
- Kaggle giữ raw output. GitHub Actions chỉ giữ metadata/trạng thái xác minh và logs đã lọc trong artifact 30 ngày; kết quả tải thủ công về Windows sau nằm trong thư mục mới `reports/kaggle_batch_runs/<experiment_id>/`, không ghi đè. Sau 30 ngày phải vẫn đối chiếu được định danh phiên và checksum từ Kaggle; không xác minh được thì dừng.
- POC đọc `main` của `Qwen/Qwen3-4B` nhưng phải ghi chính xác commit SHA Hugging Face thực dùng. Các lần chạy 100 từ dùng commit SHA đó làm revision cố định.
- POC chỉ đạt cổng chất lượng khi đủ 5 raw outputs, checksum đúng, cả 5 parse hợp lệ; sau đó chủ dự án đánh giá ngữ nghĩa. Nếu không đạt, giữ output, báo `needs_review`, không tự chạy 100 từ.

### Ranh giới phê duyệt

**Đã phê duyệt có điều kiện:** chỉ triển khai D2-1 offline. **Chưa được phê duyệt:** mọi Kaggle push/live run/GPU, credential thật, commit/push GitHub, công bố snapshot, POC 5 từ và chạy 100 từ. Giới hạn 60 phút và snapshot Public về nguyên tắc vẫn chỉ là quyết định thiết kế.

## D. Phương án bị loại hoặc hoãn

| Phương án | Trạng thái và lý do |
|---|---|
| Cloudflare Tunnel luôn chạy cho batch | REJECTED: tốn GPU khi nhàn rỗi, không cần HTTP API cho công việc hữu hạn; API V4 vẫn giữ cho tương tác. |
| Tự động khởi động API tương tác | DEFERRED: mục tiêu D2 là batch; không cần workflow thứ hai lúc này. |
| Windows làm bộ điều phối sau khi bấm chạy | REJECTED: Windows có thể tắt; không thể đáng tin cậy khởi chạy batch Kaggle kế tiếp. |
| Kho checkpoint ngoài để lưu từng từ | DEFERRED: chủ dự án chấp nhận chạy lại từ phiên bản Kaggle hoàn tất gần nhất; thêm kho sẽ tăng thành phần và quyền truy cập. |
| A+B cho cả 100 từ (200 generation) | REJECTED ở lần mở rộng đầu: mặc định B để tiết kiệm quota; giữ lựa chọn A/B cấu hình cho thí nghiệm sau. |
| Chạy GPU lớn trước POC | REJECTED: phải kiểm chứng offline, rồi POC 5 từ có phê duyệt riêng và đánh giá trước khi xét 100 từ. |
| Retry inference hoặc restart khi phiên cũ chưa rõ trạng thái | REJECTED: có thể tạo kết quả trùng và tiêu hao quota; kiểm tra đúng phiên bản trước. |
| Dựa vào output latest hoặc coi hủy Actions là hủy Kaggle | REJECTED: latest có thể thuộc batch khác; Kaggle tiếp tục chạy độc lập. |

## E. Kiến trúc đề xuất, chưa triển khai

**workflow_dispatch thủ công → GitHub Actions runner CPU chuẩn → Kaggle CLI → notebook/script batch Private trên Kaggle GPU → Qwen3-4B Variant B → output Kaggle theo phiên bản → Actions tải và xác minh → batch kế tiếp.**

- Actions đọc snapshot ở commit SHA đã duyệt, đối chiếu checksum, kiểm tra quota và trạng thái phiên cũ, ngăn workflow trùng. Mỗi lần chỉ push một batch Kaggle. Cấu hình notebook batch tách hẳn notebook API V4; không có server HTTP hay Tunnel.
- Notebook ghi input manifest, output nguyên văn và parsed, lỗi, hash, model/revision thực sự xác minh được, số token, mốc UTC và thời gian từng giai đoạn vào output riêng. Nó tự thoát khi xong hoặc báo incomplete/timeout khi vượt giới hạn. Không tự tạo metadata mà API/model không cung cấp.
- Actions ghi lại owner/slug/version của lần push, theo dõi chính phiên bản đó, tải output đúng phiên bản, so manifest, số record, ID, variant và SHA-256 trước khi đánh dấu collection xong. Parse lỗi đưa quality về `needs_review`; chỉ POC 5/5 parse hợp lệ mới được trình chủ dự án đánh giá ngữ nghĩa. Artifact 30 ngày chỉ là bản sao nhỏ; cơ chế khôi phục phải dựa vào định danh phiên Kaggle và output/checksum của chính phiên đó.
- Khi Actions bị hủy, phiên Kaggle hiện tại có thể trở thành mồ côi. Luồng khôi phục phải tìm đúng phiên bản đã tạo, chờ/kiểm tra output hoặc báo cần thao tác thủ công; không tự push batch thay thế. Không thể khẳng định tự hủy Kaggle qua CLI: [Kaggle CLI hiện không tài liệu hóa lệnh cancel](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md), và [đề xuất bổ sung lệnh cancel còn mở](https://github.com/Kaggle/kaggle-cli/issues/1172). Một API trong SDK được nêu trong issue nhưng chưa được chọn làm hợp đồng tự động hóa.
- Với repository Public, standard GitHub-hosted runner [được GitHub mô tả là miễn phí](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Mỗi job Actions có [trần 6 giờ](https://docs.github.com/en/actions/reference/limits); cách chia job/tiếp tục khi vượt trần còn phải thiết kế và kiểm thử. Kaggle GPU dùng quota của tài khoản; chưa có số đo thời gian hoặc quota thực.

## F. Rủi ro và điều chưa xác minh

1. T4 và quota GPU thực tế của knight3007, quyền Internet Kaggle, khả năng tải model từ Hugging Face và khả năng tạo notebook GPU mới chưa được kiểm thử.
2. Slug batch cuối và hành vi tạo notebook Private trên tài khoản thật chưa được kiểm chứng; yêu cầu Private đã được xác nhận.
3. Thời gian setup, tải/nạp model, tốc độ B inference và mức tiêu thụ quota chưa có số đo lưu trong notebook V4. Kích thước batch 10–25 và timeout của batch 100 từ phải dựa trên POC.
4. File ở /kaggle/working chỉ là checkpoint tạm khi phiên đang chạy; khả năng tải file sau phiên bị hủy đột ngột không được tài liệu xác nhận. Chỉ output phiên bản đã hoàn tất và xác minh mới là recovery point.
5. Cần kiểm chứng CLI 2.2.5 với tài khoản thực: version number từ push; status/output/logs/files gắn version; định dạng lỗi/quota; output retention. CLI chưa được cài trong workspace.
6. Workflow có thể bị hủy sau push nhưng trước khi lưu version vào GitHub artifact/log. Cần cơ chế đối chiếu phiên Kaggle còn chạy mà không tự suy luận lại.
7. Không có lệnh cancel Kaggle phiên đang chạy được tài liệu hóa trong CLI; timeout tự kiểm tra có thể không ngắt ngay một lệnh tải model/generate bị treo. Không khẳng định GPU dừng cứng đúng 60 phút.
8. Cần phân biệt Kaggle session hoàn tất, output đủ và hợp lệ về cấu trúc, output được human review, và kết quả được duyệt dùng cho production. Không tự đồng nhất các trạng thái này.
9. Tổng thời gian 100 từ có thể vượt giới hạn 6 giờ của một job Actions hoặc quota Kaggle; cần cách điều phối có điểm dừng an toàn và resume.
10. Kaggle native scheduler có mô tả lịch thời gian/dataset nhưng hỗ trợ GPU cho tài khoản chưa xác minh; không giả định scheduler tự nối batch.
11. Snapshot Public cần rà soát và duyệt nội dung cụ thể; commit SHA chỉ tồn tại sau bước công bố có phép. Không đưa secret vào repository Public.
12. Khả năng GitHub Actions hiển thị nút Run workflow phụ thuộc workflow đã có trên default branch; bước commit/push cần phê duyệt sau khi người dùng xem bản triển khai.

## G. Nhật ký quyết định

Chỉ dùng các trạng thái CONFIRMED, PROPOSED, PENDING_OWNER_APPROVAL, REJECTED, SUPERSEDED. Ngày dưới đây là ngày ghi nhận D2; nếu quyết định đổi, thêm dòng mới và đánh dấu dòng cũ SUPERSEDED cùng lý do, không xóa lịch sử.

| Ngày | Quyết định | Lý do | Trạng thái |
|---|---|---|---|
| 2026-11-07 | Batch inference là hướng chính; giữ V4 API tương tác độc lập. | 100 từ cần job hữu hạn; API vẫn hữu ích cho thí nghiệm. | CONFIRMED |
| 2026-11-07 | Không tự động khởi động API, không dùng Cloudflare Tunnel cho batch. | Giảm thành phần và thời gian GPU nhàn rỗi. | CONFIRMED |
| 2026-11-07 | Kaggle tiếp tục sau khi Windows tắt; tải kết quả về Windows sau. | Một lần kích hoạt không phụ thuộc PC. | CONFIRMED |
| 2026-11-07 | GitHub Actions là ứng viên điều phối CPU duy nhất, workflow_dispatch thủ công, standard runner. | Chạy độc lập với PC và ưu tiên chi phí 0. | CONFIRMED |
| 2026-11-07 | Chưa dùng schedule. | Cần kiểm chứng luồng thủ công trước; GPU scheduling chưa xác minh. | CONFIRMED |
| 2026-11-07 | 100 từ mặc định Variant B, tối đa 100 generation; tham số A/B/A+B để mở rộng. | Giảm quota nhưng giữ đường mở rộng nghiên cứu. | CONFIRMED |
| 2026-11-07 | Giữ nguyên prompt B và không thay quyết định ngữ nghĩa. | Tái lập và bảo toàn đầu vào. | CONFIRMED |
| 2026-11-07 | D1 năm từ A+B qua API V4 là thí nghiệm độc lập. | Không gộp benchmark API với batch mới. | CONFIRMED |
| 2026-11-07 | POC batch mới gồm ID 004,009,041,054,065; B; tối đa 5 generation. | Kiểm tra kiến trúc với chi phí nhỏ trước 100 từ. | CONFIRMED |
| 2026-11-07 | POC phải xác minh phiên bản, manifest, 5 record và checksum. | Text từ model một mình chưa chứng minh luồng hoàn chỉnh. | CONFIRMED |
| 2026-11-07 | POC trần 60 phút; sau phút 50 không bắt đầu inference; xong thì thoát. | Giữ quota và dành thời gian lưu output. | CONFIRMED |
| 2026-11-07 | Đo riêng setup, download, load, inference, finalization. | Chọn kích thước batch theo dữ liệu thực. | CONFIRMED |
| 2026-11-07 | Output phiên Kaggle hoàn tất và xác minh là checkpoint bền vững; không cần store từng từ. | Giảm thành phần, chấp nhận chạy lại phần đang dở. | CONFIRMED |
| 2026-11-07 | Chỉ batch chưa xác minh hoàn tất mới được chạy lại; không chồng phiên. | Tránh mất kết quả đã hoàn tất và trùng inference. | CONFIRMED |
| 2026-11-07 | Hủy Actions: để phiên Kaggle hiện tại kết thúc hoặc chạm trần; không khởi chạy batch mới. | Actions hủy không dừng GPU; bảo toàn khả năng thu hồi output. | CONFIRMED |
| 2026-11-07 | Trước retry/resume, kiểm tra chính xác version Kaggle; nếu còn chạy thì chỉ báo trạng thái. | Tránh suy luận trùng khi có phiên mồ côi. | CONFIRMED |
| 2026-11-07 | Chủ dự án có thể dừng phiên bất thường thủ công trong Kaggle UI. | CLI cancel chưa có hợp đồng được tài liệu hóa. | CONFIRMED |
| 2026-11-07 | Username Kaggle là knight3007; notebook batch phải độc lập V4. | Định danh notebook và bảo vệ API cũ. | CONFIRMED |
| 2026-11-07 | Snapshot GitHub Public được đồng ý về nguyên tắc, cần rà soát và duyệt file cụ thể trước công bố. | Tái lập mà không lộ dữ liệu không cần thiết. | CONFIRMED |
| 2026-11-07 | Snapshot tối thiểu, commit SHA cố định và checksum trước khi push Kaggle. | Ngăn đầu vào trôi phiên bản và phát hiện sửa đổi. | CONFIRMED |
| 2026-11-07 | GitHub Secrets chứa xác thực Kaggle; không lộ trong chat, source, log. | Bảo vệ tài khoản. | CONFIRMED |
| 2026-11-07 | Không tự động promotion production, commit hay push. | Giữ bước duyệt của chủ dự án. | CONFIRMED |
| 2026-11-07 | Notebook slug đơn knight3007/qwen3-4b-vocab-batch và Private visibility. | Đề xuất ban đầu; Private đã được chốt, còn slug sẽ thiết kế theo run/batch/attempt để hỗ trợ khôi phục. | SUPERSEDED |
| 2026-11-07 | Ghim Kaggle CLI 2.2.5 và dùng version cụ thể. | Bản này sửa lỗi bỏ qua version trong status/output. | PROPOSED |
| 2026-11-07 | Cân nhắc batch 10–25 từ. | Cân bằng checkpoint và chi phí tải model; chờ số đo POC. | PROPOSED |
| 2026-11-07 | Kiến trúc D2 cuối và file snapshot cụ thể. | Chưa trình chủ dự án duyệt bản hoàn chỉnh. | PENDING_OWNER_APPROVAL |
| 2026-11-07 | Triển khai code/workflow, commit/push, live POC/GPU. | Mỗi hành động cần phê duyệt tương ứng; hiện chưa có. | PENDING_OWNER_APPROVAL |
| 2026-11-07 | Windows điều phối sau khi tắt hoặc dùng Tunnel luôn bật cho batch. | Không đáp ứng PC-off hoặc lãng phí GPU. | REJECTED |
| 2026-11-07 | A+B cho cả 100 từ và auto retry khi phiên trước chưa rõ trạng thái. | Tốn quota và có thể tạo kết quả trùng. | REJECTED |
| 2026-11-07 | Phỏng vấn D2 mỗi lần một câu. | Quy trình phỏng vấn ban đầu; chủ dự án đã yêu cầu gom toàn bộ câu hỏi. | SUPERSEDED |
| 2026-11-07 | Gom toàn bộ câu hỏi D2 còn cần chủ dự án quyết định thành một danh sách có lựa chọn và đề xuất; nhận câu trả lời trong một tin nhắn. | Giảm lượt trao đổi, không hỏi lại thông tin đã cung cấp; các kiểm chứng kỹ thuật do trợ lý tự thực hiện. | CONFIRMED |
| 2026-11-07 | Dừng phỏng vấn D2 sau khi chủ dự án trả lời đủ bảy quyết định. | Đã đủ thông tin để trình kiến trúc; không hỏi thêm nếu kiểm chứng kỹ thuật tự giải quyết được. | CONFIRMED |
| 2026-11-07 | 1A: raw/hash đủ nhưng parse lỗi thì `needs_review`, giữ raw/hash/lỗi, dừng chuỗi batch, không tự retry; collection và quality tách biệt. | Giữ bằng chứng mà không tiêu hao GPU khi chưa hiểu lỗi. | CONFIRMED |
| 2026-11-07 | 2A: notebook batch và output Kaggle Private. | Không tự công bố dữ liệu hoặc kết quả. | CONFIRMED |
| 2026-11-07 | 3A: Kaggle giữ raw; Actions artifact chỉ metadata và logs đã lọc 30 ngày; tải Windows vào thư mục mới, không ghi đè. | Giảm lưu trữ và phát tán; artifact hết hạn không được làm mất khả năng khôi phục. | CONFIRMED |
| 2026-11-07 | 4B: POC ghi commit SHA thực tế của Qwen/Qwen3-4B từ `main`; 100 từ dùng revision cố định đó. | Giữ lần POC tương thích cách chọn revision ban đầu và tái lập lần mở rộng. | CONFIRMED |
| 2026-11-07 | 5A: resume một lần với ID thí nghiệm cũ, đối chiếu phiên trước, giữ batch thành công, chỉ chạy lại batch chưa thành công. | Tránh trùng inference và không phụ thuộc artifact 30 ngày. | CONFIRMED |
| 2026-11-07 | 6A: POC đủ 5 raw, checksum đúng, 5/5 parse hợp lệ rồi chủ dự án đánh giá ngữ nghĩa; không đạt thì `needs_review`. | Kiểm tra toàn bộ luồng và chất lượng trước quyết định chạy 100 từ. | CONFIRMED |
| 2026-11-07 | 7A: đặt trần GPU số học cho 100 từ sau POC và trình duyệt riêng. | Chưa có số đo setup, download, load, inference để đặt trần đáng tin cậy. | CONFIRMED |
| 2026-11-07 | Phê duyệt kiến trúc có điều kiện cho D2-1 offline; không cấp quyền Kaggle push/live/GPU, công bố snapshot, credential thật hoặc Git commit/push. | Chủ dự án yêu cầu chứng minh offline và review riêng trước các bước live. | CONFIRMED |
| 2026-11-07 | Pending dispatch dùng `queue: max`, `cancel-in-progress: false`; không dựa vào thứ tự dispatch. | GitHub mặc định có thể thay pending cũ; mọi run phải reconcile lại. | PROPOSED |
| 2026-11-07 | ID thí nghiệm được duyệt và fingerprint thay GitHub run ID làm khóa dedup/resume; catalog rỗng trong D2-1. | Chặn hai dispatch khác GH run ID nhưng cùng đầu vào. | PROPOSED |
| 2026-11-07 | Preflight các phiên nhìn thấy qua CLI và xác nhận dành riêng GPU của chủ dự án cho phiên V4/direct không quan sát được. | Concurrency của GitHub không bao trùm phiên Kaggle bên ngoài. | PROPOSED |
| 2026-11-07 | D2-1 chỉ tạo mã và bằng chứng offline; catalog live rỗng, adapter quota và negative lookup chặn push cho tới khi D2-2 xác minh. | 19 phép thử local đạt; không tiêu quota hoặc công bố snapshot. | CONFIRMED |

## H. Câu hỏi còn mở

**Đã giải quyết bằng quyết định của chủ dự án; không hỏi lại:** 1A parse lỗi → `needs_review`; 2A Kaggle Private; 3A artifact metadata/logs đã lọc 30 ngày, Kaggle giữ raw, thư mục tải về mới; 4B POC ghi SHA từ `main`, lần 100 từ ghim SHA; 5A resume cùng ID thí nghiệm và chỉ chạy lại batch chưa thành công sau xác minh; 6A POC đủ 5 raw/hash/parse rồi đánh giá ngữ nghĩa; 7A trần quota 100 từ đặt sau số đo POC. Cách xử lý khi Actions bị hủy đã chốt trước đó. **Quy trình phỏng vấn D2 đã kết thúc.**

**Các việc kỹ thuật còn phải kiểm chứng, không phải câu hỏi yêu cầu chủ dự án trả lời lúc này:**

1. Slug theo run/batch/attempt có hợp lệ và khả dụng; tài khoản knight3007 có quyền Private, T4, Internet và quota thực tế; Hugging Face tải được model.
2. Kaggle CLI 2.2.5 có trả đúng version khi push, status/pull/output/files/logs của version cụ thể và phân biệt chính xác phiên đang chạy, thành công, lỗi; xác minh bằng tài khoản thực trước live POC.
3. Khôi phục sau khi artifact 30 ngày hết hạn bằng slug/phiên bản/manifest/checksum trên Kaggle; nếu thông tin thiếu hoặc mâu thuẫn thì dừng. Thử offline cả trường hợp Actions bị hủy ngay sau push, trước khi lưu artifact.
4. Đảm bảo một workflow đang chạy tại một thời điểm và batch GPU tuần tự; thiết kế job dưới 6 giờ, tiếp tục qua các job trong cùng một workflow khi cần; thử với hai batch giả lập offline.
5. Xác minh commit SHA thực của model trong POC, package versions và dữ liệu thời gian; sau POC mới chọn số từ/batch, timeout và trần GPU 100 từ để duyệt.
6. Rà soát snapshot input Public, báo cáo file/size/SHA-256/diff và lấy phê duyệt riêng trước mọi commit/push; workflow phải tồn tại trên default branch mới có nút chạy.
7. Xác minh thực tế output sau fail/cancel và giới hạn timeout; CLI chưa có lệnh cancel được tài liệu hóa nên không cam kết dừng GPU cứng ở phút 60.

## I. Bước tiếp theo

1. **D2-1 offline đã thực hiện tại local:** tạo snapshot tối thiểu 100 từ và prompt B, notebook template/runtime độc lập, driver CPU, catalog phê duyệt rỗng, workflow `workflow_dispatch` nháp và 19 test offline đạt. Hai batch giả lập đi tuần tự; batch 2 đối chiếu source/output của version batch 1 trước khi push. Không gọi tài khoản Kaggle, không dùng GPU, không commit/push.
2. Snapshot cần duyệt công bố riêng: `batch_inputs/d2_v1/vocabulary_100.json` — 41.522 byte, SHA-256 `7bcdd41280111663e34a983ee9d11d60ee94fc673f81cdddcf7294323b4e4282`; `batch_inputs/d2_v1/variant_b_prompt.json` — 1.784 byte, SHA-256 `c6833a80929badfeeb9f613417bc824d5b624ca3fd1ba7206ba0c1a546dffc33`. Có 100 ID liên tục, 3 quyết định nghĩa đã approved, prompt system B 1.560 ký tự. Quét offline không thấy token dạng Kaggle/HF, đường dẫn riêng tư, email hay URL trong hai file; chủ dự án vẫn phải đọc nội dung và duyệt trước khi đưa lên GitHub Public.
3. **Cổng D2-2 còn đóng:** chủ dự án duyệt chính xác file/snapshot, commit/push và cấu hình GitHub Secrets ngoài chat. Sau khi công bố, xác minh workflow trên default branch, commit đầu vào cố định, định dạng CLI 2.2.5 (list/status/pull/output/quota), slug/version 1, quyền Private/T4/Internet, quota và khả năng quan sát phiên GPU khác. Kiểm chứng thông báo `push` cần một bài thử `--no-run` trên tài khoản thật và **quyền Kaggle live push riêng** dù không dùng GPU. Catalog hiện rỗng; adapter quota và kiểm tra slug vắng mặt cố ý dừng trước push cho đến khi kiểm chứng, nên workflow nháp không thể chạy GPU.
4. **Cổng D2-3 còn đóng:** cần phê duyệt riêng cho Kaggle GPU POC 5 từ. Giới hạn 60 phút chưa được chứng minh là giới hạn cứng từ lúc Kaggle cấp phiên; notebook đếm từ khi bắt đầu code và ngừng bắt đầu inference từ phút 50, `kaggle kernels push -t 3600` còn cần kiểm chứng thực tế. Không tự chạy POC hoặc batch 100 từ.
5. Sau POC, chủ dự án đánh giá ngữ nghĩa; dùng số đo thực để trình kích thước batch, timeout và trần GPU 100 từ để duyệt riêng. Không tự đưa kết quả vào production.
