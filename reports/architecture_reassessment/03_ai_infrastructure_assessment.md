# 03 — AI, hiệu năng và hạ tầng

## Model đang phục vụ bước nào?

**Verified:** Qwen tạo truy vấn trước khi tìm ảnh (`collect data script/query_generator.py:91-296`); DDG/Bing trả ứng viên và SigLIP xếp hạng (`imagecollector.py:201-276,690-838`); gTTS tải MP3 (`audiocollector.py:166-179`). Dataset builder chỉ đọc/kiểm tra và xuất JSON, không suy luận (`dataset_builder.py:42-173`). Chưa có runtime game hoặc đường gọi model trong gameplay (`web/`, `game/`). Vì vậy độ trễ model hiện tại là **offline preprocessing latency**, chưa phải độ trễ khi người học chơi. Với Excel do người học nhập, thời gian chờ phát sinh **trước lần chơi đầu của bộ từ mới**, dù gameplay sau đó offline.

## Số đo có thật và phần chưa biết

| Nút thắt | Bằng chứng và phạm vi đo | Điều chưa biết |
|---|---|---|
| Qwen local 1.7B | Benchmark 25 từ trên thiết bị CUDA `device=0`, float16: Variant A **192,197 s**, B **628,620 s**, toàn run **822,915 s** (`reports/image_pipeline_benchmark/20261106-image-query-v1/experiment_manifest.json:7-31,551-584`). Đây là 25 từ × hai variant, gồm thiết lập run; không ngoại suy thành SLA 100 từ. | P50/P95 theo từ, máy phổ thông/CPU, RAM/VRAM đỉnh, lần tải model và cache cold/warm. |
| Remote Qwen4B | D1 V4 ghi `status=prepared`, các request `not_run`, revision `unverified` (`reports/remote_qwen/d1-five-20261107-qwen4b-v4/experiment_manifest.json:1-10,64-72`); D0 `contract_incompatible` (`reports/remote_qwen/d0-five-20261107/experiment_manifest.json:1-8`). | Latency end-to-end, thời gian cấp GPU, quota/cost thật, availability, concurrency. Không dùng duration chép trong bản chuẩn bị làm số đo live mới. |
| Image search + scoring | 89 ảnh staged hợp lệ kỹ thuật; 236 candidate tải thành công trong các run mới, nhưng 29 ảnh có lỗi quan sát (`reports/full_media_staging_review.md:49-79`). | Latency mạng theo nhà cung cấp, tải asset khi chơi, tỷ lệ thành công trên Excel tùy ý. |
| Audio | 100 MP3 staged hợp lệ kỹ thuật, tổng 808.896 byte theo inventory; production 0 (`reports/full_media_staging_inventory_v1.json:totals`; kiểm tra đường dẫn/kích thước 22/11). | Thời gian gTTS cho bộ Excel bất kỳ, điều khoản phân phối, chất lượng nghe của 90 hash chưa duyệt chính xác. |
| Storage | 99 ảnh được chọn có tổng 12.601.002 byte; 100 MP3 có 808.896 byte, tính từ inventory và đối chiếu kích thước file. | Gói công khai sau duyệt, băng thông, quota browser, raw candidates/model cache. Không dùng tổng staging làm kích thước release. |

Không có benchmark runtime vì chưa có runtime. Không có số đo được lưu cho CPU/GPU/RAM trên máy phổ thông, tải asset qua Internet, PWA cache eviction, chi phí host/job tháng hoặc tính ổn định dài hạn. **Unknown** phải được giải bằng prototype và phép đo nhỏ, không bằng số giả định.

## Ba cách tích hợp AI

| Kiến trúc | Độ trễ và UX | Chi phí/độ tin cậy | Offline, chất lượng và quản lý asset |
|---|---|---|---|
| 1. Inference lúc chơi | Chờ model trên thao tác người dùng; local/remote đều chưa có số đo gameplay. | Cần máy đủ mạnh hoặc dịch vụ luôn sẵn; lỗi mạng/server chặn tính năng. | Offline chỉ khi model local khả thi; output động cần review khó hơn. Không phù hợp gameplay cốt lõi hiện mô tả. |
| 2. Tạo trước khi phát hành | Model chạy theo lô; người chơi mở pack đã duyệt gần như chỉ chịu tải asset. | Hạ tầng chỉ cần khi chuẩn bị/cập nhật nội dung; có thể xử lý bất đồng bộ. | Chơi offline dễ nhất; cần ID, checksum, quyền sử dụng, trạng thái review và version. **Phù hợp bộ nội dung cố định**, nhưng không đủ cho Excel mới của từng người học. |
| 3. Hybrid | Bộ mẫu đã duyệt tải nhanh; Excel mới tạo một job online, báo tiến độ, lưu pack rồi chơi offline. | Cần dịch vụ nhận và xử lý job khi người dùng nhập; không bắt buộc AI server trong từng frame gameplay. Cần retry/idempotency và giới hạn tài nguyên. | Hợp mục tiêu sản phẩm nếu chỉ phát hành item đã qua kiểm tra. Thời gian chờ bộ mới và vận hành service là rủi ro phải đo. |

**Khuyến nghị:** Architecture 3 cho sản phẩm Excel tùy chỉnh, với gameplay hoạt động như Architecture 2 sau khi pack đã sẵn sàng. Phần AI không được phép tự nâng một ảnh/MP3 lên `available`: `dataset_builder.py:42-120` hiện cố ý đặt asset hiện hữu thành `needs_review`, URL `null`. Inventory ghi 98 ảnh có quyền `unknown`, toàn bộ audio có quyền phân phối `unresolved` (`reports/full_media_staging_inventory_v1.json`); do đó 100 file kỹ thuật không chứng minh 100 nội dung hợp lệ.

## Kaggle, Tunnel và server

**Verified:** Kaggle batch runner và workflow là bản D2-1 offline, 19 test mock pass; catalog `kaggle_batch/approved_experiments.json` rỗng và adapter còn chặn trước live push (`docs/KAGGLE_BATCH_AUTOMATION_ARCHITECTURE.md:154-162`). Không có kết quả Kaggle batch 100 từ hoặc số đo production. [Kaggle CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) cung cấp lệnh chạy và tải output notebook, nhưng tài khoản/quota/khả dụng thực tế phải kiểm tra riêng. [Cloudflare Quick Tunnel](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) chỉ dành thử nghiệm, URL tạm và không bảo đảm uptime: không dùng làm API cho người học. GitHub Pages là [static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages); nó không thực thi Python pipeline.

**Inferred:** Nếu Excel được người học tải lên website và media được tạo/tải tự động, cần dịch vụ online ngoài static host (hoặc xử lý local trên máy người học với model/provider riêng). Native App chỉ đổi chỗ chạy client; gọi Kaggle/remote vẫn cần Internet và không tự giảm inference latency. **First measurement:** một job 3–5 hàng Excel mẫu, ghi thời gian parse, queue, Qwen, search, SigLIP, gTTS, review, download/cache và lỗi; chỉ làm sau khi cổng đánh giá 100 từ xác định model/asset pipeline đủ chất lượng.

## Docker và Kubernetes có phù hợp không?

**Verified:** repository không có `Dockerfile`, Compose hay manifest Kubernetes; roadmap sản phẩm cũ còn ghi “Không Kubernetes” (`schedule/TODO_PRODUCT_BEFORE_RESEARCH_UPGRADE.md:1126`). [Docker](https://docs.docker.com/get-started/introduction/index.html) có thể đóng gói Python worker/dependencies để chạy nhất quán; nó **không** làm Qwen nhanh hơn, cung cấp GPU, biến máy cá nhân thành server luôn bật hoặc thay thế host URL công khai. Nếu chạy GPU trong container, host vẫn cần driver và cấu hình NVIDIA Container Toolkit ([NVIDIA](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)). Model weights, ảnh, MP3, metadata và job state cần lưu bền vững ngoài lớp ghi tạm của container.

**Đánh giá:** Docker **có thể hợp lý sau Phase 0**, khi đã chọn nơi chạy service Excel→media và cần tái lập môi trường; một image worker hoặc Compose nhỏ chỉ nên thêm nếu phép thử triển khai cho thấy lợi ích cụ thể. Web tĩnh vẫn phát hành riêng qua Pages. [Kubernetes](https://kubernetes.io/docs/concepts/index.html) quản lý workload nhiều container, scale, networking và storage, nhưng đòi cụm, GPU node/driver, quan sát, secret và persistent storage; dữ liệu trong pod ephemeral không bền ([Kubernetes storage](https://kubernetes.io/docs/concepts/storage/ephemeral-storage/)). Hiện chưa có traffic, số job đồng thời, SLA hay đội vận hành để biện minh. **Khuyến nghị No-Go Kubernetes cho MVP trước 2/12**; chỉ xem lại nếu số đo cho thấy nhiều worker/host, tự động scale và độ sẵn sàng mà một dịch vụ đơn không đáp ứng. Docker/Kubernetes là quyết định **triển khai backend**, không phải phương án thay thế Web/PWA/Native và không sửa được chất lượng 100 từ.
