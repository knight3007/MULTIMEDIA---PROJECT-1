# 02 — So sánh phương án kiến trúc

## Bài toán thực tế và phương pháp chấm

**Verified:** hiện chưa có Web Game để “tiếp tục” hoặc frontend để đóng gói (`web/`, `game/`, `README.md:1-2`); pipeline tạo nội dung là Python (`collect data script/imagecollector.py:757-838`, `audiocollector.py:166-179`). **Yêu cầu chủ dự án:** người học nhập Excel theo mẫu; khi có mạng hệ thống lấy/lưu ảnh và audio, sau đó chơi offline. Bộ 100 từ hiện tại là benchmark cần đánh giá chất lượng model trước khi mở rộng, không phải số từ tối đa. Nếu chọn web, giảng viên yêu cầu URL công khai truy cập được trước 2/12/2026.

Điểm 1–5 là **ước lượng quyết định**, không phải benchmark đo được. Trọng số theo đề bài: tái sử dụng 20%, trải nghiệm runtime 20%, offline 15%, chi phí triển khai/duy trì 15%, tốc độ/độ đơn giản phát triển 15%, bảo trì 10%, tích hợp AI 5%. Tổng = `Σ(điểm × trọng số)`. Mỗi ô ghi `điểm — lý do [độ tin cậy]`; Cao = bằng chứng trực tiếp/chuẩn nền tảng, Trung = suy luận từ repo và tài liệu chính thức, Thấp = chưa có prototype hoặc phép đo.

| Tiêu chí | A — Web thông thường | B — Web offline/PWA | C — Desktop đóng gói (Tauri/Electron) | D — Game engine (Godot/Unity) | E — Tách pipeline/runtime* |
|---|---|---|---|---|---|
| Tái sử dụng 20% | **2** — chỉ tái sử dụng data contract/Python, chưa có web [Cao] | **2** — như A, thêm cache [Cao] | **2** — chưa có web để bọc; Python dùng riêng [Cao] | **1** — runtime mới, chỉ giữ data [Cao] | **4** — giữ pipeline, registry, manifest [Cao] |
| Runtime/UX 20% | **4** — game nhẹ không cần inference lúc chơi [Trung] | **4** — chơi từ local asset/cache [Trung] | **4** — tài nguyên local, nhưng chưa có prototype [Thấp] | **4** — engine đủ cho game, chưa chứng minh cần [Thấp] | **4** — nội dung đã lưu giúp tách độ trễ chơi [Trung] |
| Offline 15% | **1** — bản web thông thường cần mạng để tải lại [Trung] | **4** — service worker/cache sau tải đầu; còn phải thử quota [Trung] | **5** — có thể đóng gói asset, import/generation vẫn cần mạng [Trung] | **5** — tương tự C cho gameplay [Trung] | **4** — content pack chơi offline trên runtime phù hợp [Trung] |
| Chi phí 15% | **3** — host tĩnh rẻ, nhưng Excel→media online cần dịch vụ [Trung] | **3** — thêm cache, dịch vụ tạo media vẫn cần [Trung] | **2** — thêm đóng gói/updates, online generation vẫn tốn [Thấp] | **2** — toolchain và đóng gói riêng [Thấp] | **3** — tạo theo lô giảm phụ thuộc gameplay, chưa biết giá job [Trung] |
| Phát triển 15% | **3** — UI/public URL đơn giản hơn, Excel→media vẫn khó [Trung] | **2** — thêm offline/version/cache và kiểm thử [Trung] | **1** — đóng gói thêm khi runtime chưa có [Trung] | **1** — viết gameplay bằng engine mới [Trung] | **2** — cần hợp đồng input/output, review và service job [Trung] |
| Bảo trì 10% | **3** — một runtime nhưng phụ thuộc dịch vụ online [Trung] | **3** — thêm cache/version cần quản lý [Trung] | **2** — ứng dụng/installer/OS updates [Trung] | **2** — engine và pipeline khác công nghệ [Trung] | **4** — ranh giới rõ giữa tạo nội dung và chơi [Trung] |
| AI về sau 5% | **3** — thêm API được, chưa có hạ tầng [Trung] | **3** — tương tự A, offline không giải quyết inference [Trung] | **3** — có thể gọi remote/local, không tăng tốc model mặc định [Trung] | **2** — cần adapter riêng [Thấp] | **5** — thay model/provider mà không đổi gameplay contract [Trung] |
| **Tổng /5** | **2,70** | **3,00** | **2,75** | **2,50** | **3,60*** |

\*E là **lựa chọn ranh giới hệ thống**, kết hợp với A/B/C/D; tổng E chỉ mô tả giá trị của sự tách lớp, không được xếp hạng trực tiếp để chọn nền tảng. Chênh lệch A/B/C nhỏ và phụ thuộc giả định chưa đo; không xem 3,00 là chứng minh B chắc chắn khả thi trước hạn. Nếu bỏ yêu cầu offline, A có thể giảm công việc ban đầu; nếu bắt buộc cài đặt không cần lần tải đầu, C có lợi. Yêu cầu hiện tại giữ offline sau khi lưu và URL công khai cho web, nên B+E là ứng viên chính.

## Kiểm chứng giả thuyết chuyển Native

| Câu hỏi | Kết luận và bằng chứng |
|---|---|
| Web Game có cần backend liên tục để **chơi**? | **Inferred: không**, nếu chỉ đọc content pack đã lưu; runtime chưa tồn tại nên chưa đo. `dataset_builder.py:125-153` đã xuất record tĩnh, nhưng chưa có public asset URL. |
| Người học tự nhập Excel rồi tự động lấy media có cần online service? | **Inferred: có** nếu dùng Qwen/SigLIP/gTTS hiện tại mà không bắt người học cài Python/model. Static host chỉ phục vụ file; browser đọc file người dùng chọn nhưng không chạy Python pipeline. [File API](https://developer.mozilla.org/en-US/docs/Web/API/File_API/Using_files_from_web_applications), [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages). |
| Native làm Qwen nhanh hơn? | **Không có bằng chứng.** Nó thay runtime/packaging; tốc độ phụ thuộc model, thiết bị và hạ tầng inference. Benchmark Qwen local nằm ở `reports/image_pipeline_benchmark/20261106-image-query-v1/experiment_manifest.json:552-584`. |
| Gọi Kaggle/remote GPU từ Native có offline không? | **Không** trong lúc tạo nội dung; chỉ gameplay từ asset đã lưu mới offline. D1 V4 mới `prepared`, không có SLA/latency production (`reports/remote_qwen/d1-five-20261107-qwen4b-v4/experiment_manifest.json:1-10`). |
| Có thể tách pipeline khỏi runtime? | **Có về thiết kế**, bằng content pack/version và trạng thái review; chưa được triển khai. Python builder và manifest là nền tảng (`dataset_builder.py:125-153`). |
| Native giải quyết gì và còn gì? | Giúp đóng gói local/offline ngay sau cài; **không** giải quyết chất lượng ảnh, quyền media, tốc độ model hay dịch vụ Excel→media online. Inventory ghi `game_ready_now=0`. |
| Có thể đơn giản hóa Web? | **Có điều kiện:** UI tĩnh + cache nội dung đã xử lý; xử lý Excel/media là job tách biệt. Fetch tùy ý từ nguồn thứ ba trong browser còn vướng CORS và quyền dùng media ([MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)). |

## Nền tảng và quyết định sớm

**Trình duyệt desktop:** hợp demo qua URL công khai, nhập file và kiểm thử offline sau tải đầu; cần HTTPS/service worker và online processing riêng ([MDN service worker](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers)). **Windows desktop:** phù hợp bản đóng gói về sau nếu khảo sát người dùng cho thấy cache/browser không đủ; thêm installer và cập nhật. **Android:** chưa có yêu cầu MVP, cần UI cảm ứng, nhập file và kiểm thử lưu trữ riêng. **Loại D cho MVP trước 2/12** vì chưa có game engine/runtime, không có yêu cầu gameplay 3D hoặc kỹ thuật chỉ engine đáp ứng. **Tạm loại C cho MVP** vì đóng gói một web runtime chưa tồn tại không giải quyết cổng chất lượng 100 từ hay Excel→media. A không đạt offline như yêu cầu; B+E chỉ đi tiếp sau cổng model, quyền media và thử nghiệm Excel→job→offline.

Docker có thể đóng gói **dịch vụ** xử lý Excel→media, còn Kubernetes điều phối dịch vụ đó; cả hai nằm dưới các phương án A–E, không thay thế nền tảng người học. Không cộng điểm chỉ vì dùng container. `03_ai_infrastructure_assessment.md` kết luận Docker là tùy chọn sau khi đo/triển khai job, Kubernetes chưa có cơ sở cho MVP.
