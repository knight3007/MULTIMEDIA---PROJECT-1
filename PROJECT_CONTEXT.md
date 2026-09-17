# Project Context

Ngày khảo sát: 17/09/2026. Tài liệu mô tả working tree hiện tại, gồm cả file chưa commit; không chỉ mô tả phiên bản trong Git. Các con số dữ liệu là ảnh chụp tại thời điểm khảo sát.

Đã đọc các module Python, test, tài liệu, cấu hình, danh sách từ vựng và truy vấn; kiểm kê thư mục dữ liệu và đọc metadata JSON. Không đọc dependency trong `.venv/`, nội bộ `.git/`, bytecode hoặc trọng số model. Không đánh giá trực quan toàn bộ ảnh hay nghe thử audio. Task này chỉ tạo tài liệu, không sửa code hoặc dữ liệu.

## 1. Project Overview

Theo `README.md`, mục tiêu project là “Web-based Multimedia Vocabulary Learning Game”. `projectframework.md` và `progress.md` mô tả hướng xây dựng bộ dữ liệu gồm từ vựng, định nghĩa, ảnh, audio để phục vụ web game.

**Phần thực sự tồn tại hiện nay là pipeline CLI chuẩn bị dữ liệu**, chưa có web game hoạt động:

- Thu thập ảnh JPEG từ Openverse theo từ tiếng Anh và truy vấn riêng.
- Chọn ảnh bằng SigLIP chạy local, hoặc heuristic dựa trên metadata.
- Tổng hợp audio tiếng Nhật bằng Windows SAPI, lưu WAV.
- Lưu metadata, kiểm tra cache, retry và in thống kê kết quả.
- Có danh sách 500 dòng cho mỗi ngôn ngữ Anh, Nhật, Việt.
- Có 6 test offline cho các hành vi chính của collector.

Người thao tác hiện tại là developer/người chuẩn bị dataset qua terminal. Nhóm người học mục tiêu, luật chơi, tiến trình học và yêu cầu business cụ thể: **Chưa xác định rõ từ codebase hiện tại.** JMdict, bộ dựng dataset thống nhất và web game mới xuất hiện trong tài liệu định hướng.

## 2. Current Tech Stack

| Nhóm | Công nghệ có bằng chứng | Vai trò / giới hạn |
| --- | --- | --- |
| Runtime | Python, thư viện chuẩn | CLI, file I/O, HTTP, subprocess, JSON, WAV; chưa có khai báo phiên bản Python bắt buộc |
| CLI | `argparse` | Hai collector độc lập và launcher tương thích |
| HTTP client | `urllib.request`, `urllib.parse`, `urllib.error` | Tìm và tải ảnh |
| AI local | `transformers==5.17.0`, `torch==2.14.0` | `AutoProcessor`, `AutoModel`, inference SigLIP |
| Xử lý ảnh | `Pillow==12.3.0` | Decode và chuyển RGB trước khi chấm điểm |
| Trọng số model | `safetensors==0.8.0` | Dependency khai báo; resolver tìm `model.safetensors`, không import trực tiếp package trong code ứng dụng |
| Audio | Windows PowerShell, COM SAPI | Chọn voice Japanese, tổng hợp ra WAV |
| Lưu trữ | Filesystem, TXT, JSON, JPEG, WAV | Không có database/ORM |
| Test | `unittest`, `unittest.mock`, `tempfile` | Test offline và mock integration |
| Môi trường local | `.venv/`, `requirements.txt` | Các lệnh hiện có dùng Python trong virtual environment |

Phiên bản package trên là phiên bản **khai báo** trong `requirements.txt`, không phải kết quả kiểm toán package đã cài. Không có frontend framework, UI library, TypeScript, bundler, web backend, Docker, queue hoặc CI/CD được triển khai trong repository khảo sát.

## 3. Repository Structure

```text
/
├── README.md
├── PROJECT_CONTEXT.md
├── projectframework.md
├── progress.md
├── requirements.txt
├── comand.txt
├── .gitignore
├── collect data script/
│   ├── collector.py
│   ├── collector_common.py
│   ├── imagecollector.py
│   ├── image_scorer.py
│   ├── audiocollector.py
│   ├── test_collectors.py
│   └── key.txt
├── data/
│   ├── vocabulary/
│   │   ├── en.txt
│   │   ├── jp.txt
│   │   └── vn.txt
│   ├── image/en/
│   │   ├── _metadata/
│   │   └── _candidates/
│   ├── audio/jp/
│   │   └── _metadata/
│   └── description/
├── web/
└── game/
```

`collect data script/` chứa toàn bộ logic thực thi. `data/vocabulary/` là đầu vào văn bản; `data/image/` và `data/audio/` là dữ liệu tạo ra. `data/description/`, `web/`, `game/` chỉ có `.gitkeep`. `_candidates/` là cache trung gian, đang trống lúc khảo sát. `.agents/` hiện trống. Không có cấu trúc monorepo applications/packages hoặc shared library được đóng gói; shared code là một module Python cùng thư mục.

## 4. Application Architecture

```text
Terminal
 ├─ imagecollector.py
 │   ├─ collector_common.py → đọc en.txt, kiểm tra tham số
 │   ├─ key.txt → ghép query theo vị trí dòng
 │   ├─ Openverse → URL ảnh → tải JPEG
 │   ├─ image_scorer.py → SigLIP local (mặc định)
 │   └─ data/image/en/ + JSON metadata
 └─ audiocollector.py
     ├─ collector_common.py → kiểm tra tham số
     ├─ jp.txt → word = reading
     ├─ PowerShell → SAPI voice Japanese
     └─ data/audio/jp/ + JSON metadata

collector.py → chọn một trong hai entry point trên
```

Entry point trực tiếp là `main()` trong mỗi collector, gọi qua `run_cli()` để cấu hình UTF-8 và xử lý lỗi cấp CLI. `collector.py` chuyển sang audio khi có `--audio-only`, còn lại chạy image; import collector đích chỉ khi cần.

Business logic, HTTP/file access và logging nằm trong các hàm của từng collector. `image_scorer.py` tách inference model; `collector_common.py` chia sẻ exception, cấu hình chung, đọc từ tiếng Anh và xử lý đường dẫn. Không có service/repository layer riêng, routing HTTP hoặc client/server boundary. Boundary thực tế là process Python, HTTP ra ngoài và subprocess PowerShell. Không có code nối dataset sang UI.

## 5. Main Application Flows

### Thu thập ảnh

1. `imagecollector.main()` parse và validate tham số; đường dẫn tương đối được tính từ root project.
2. Tạo thư mục đầu ra. `load_vocabulary()` bỏ dòng trống, trim và từ chối từ trùng; `load_query_file()` yêu cầu số query bằng toàn bộ số từ, ngay cả khi `--limit` nhỏ.
3. Lấy N dòng đầu theo `--limit`, ghép từ và query theo thứ tự.
4. `process_word()` kiểm tra tên file. Nếu JPEG qua kiểm tra signature và metadata tồn tại, trả `cached`.
5. Gọi Openverse lấy một trang kết quả, chỉ yêu cầu jpg/jpeg, không mature, có lọc dead link trong query.
6. Mặc định tải các candidate vào `_candidates/<word>/`, rồi `LazySiglipScorer` nạp model khi lần đầu cần chấm điểm. Model dùng lại cho các từ sau trong cùng process.
7. `score_batch()` chấm tất cả candidate của một từ theo query; chọn điểm cao nhất. Điểm là logit từ `logits_per_text`, không phải xác suất hoặc phần trăm.
8. Copy candidate được chọn sang ảnh đích, ghi metadata và dọn candidate của từ đó. Với `--no-siglip`, chọn bằng title/tag/filetype/URL rồi tải trực tiếp.
9. Ghi `ImageResult`, chờ giữa các từ không cache, in tổng kết. Exit 0 nếu không có lỗi trong summary, 1 nếu có.

Không có pagination, ngưỡng chất lượng tối thiểu hay chọn ảnh thủ công trong flow này. Ảnh đã tồn tại nhưng signature không hợp lệ bị báo failed, không tự tái tạo.

### Tạo audio

1. `audiocollector.main()` validate CLI, rồi `collect_audio()` đọc `jp.txt`, trim và bỏ dòng trống; cho phép từ lặp.
2. Xử lý N dòng đầu, đánh số từ 1. Trong flow hiện tại, `reading = word`, không tra cách đọc bằng từ điển.
3. Tên WAV và JSON là nguyên văn từ đã trim, sau kiểm tra ký tự/tên không hợp lệ trên Windows. Ví dụ đầu vào hiện tại `りんご` tạo tên `りんご.wav`.
4. `validate_audio()` kiểm tra file, extension, container RIFF/WAVE, thông số stream và số frame dương. WAV hợp lệ được dùng lại; chỉ tạo metadata nếu chưa có.
5. Nếu cần tạo mới, `synthesize_sapi_wav()` khởi chạy PowerShell, chọn voice có mô tả Japanese hoặc language chứa `411`.
6. SAPI ghi `<word>.tmp.wav`; Python validate rồi replace thành `<word>.wav`, sau đó ghi JSON metadata.
7. Lỗi tổng hợp được retry; in summary gồm success, cache hit, failed và kích thước audio. Exit code tương tự image.

Các từ Nhật giống nhau dùng chung file. Số thứ tự dòng vẫn được ghi trong trường `key` metadata, nhưng không còn là thành phần tên file.

### Chạy lại / tương thích

Chạy lại cùng lệnh tái sử dụng cache theo quy tắc ở trên. `collector.py` vẫn hỗ trợ lệnh cũ cho từng mode; không chạy đồng thời cả ảnh và audio. Không có flow login, gameplay, chấm bài hay lưu tiến độ học.

## 6. Frontend Structure

`web/.gitkeep` và `game/.gitkeep` là toàn bộ nội dung hai thư mục. Chưa có pages/routes, layout, component, hook, form, client state, API client, styling, loading/error UI hoặc reusable component. Không có `package.json` hay lệnh dev/build frontend.

## 7. Backend Structure

Không có HTTP backend, API handler, controller, middleware, repository, scheduler hay worker service. Hai collector là batch CLI chạy foreground.

| Phần xử lý tương ứng | Vị trí | Trách nhiệm |
| --- | --- | --- |
| Validation chung | `collector_common.py` | Limit/timeout dương, retries/delay hợp lệ, vocabulary tiếng Anh không trùng |
| Image orchestration | `imagecollector.py` | HTTP retry, chọn ảnh, cache, file/metadata và summary |
| Model inference | `image_scorer.py` | Resolve model local, device/dtype và batch scoring |
| Audio orchestration | `audiocollector.py` | Gọi SAPI, validate WAV, retry, cache và metadata |
| Lỗi cấp CLI | `collector_common.py` | Bắt `CollectionError`/`OSError`, in lỗi và exit 1 |

Logging dùng `print()`, chưa có structured logging, log rotation hoặc telemetry. HTTP retry dừng sớm với 400/401/403/404; các lần retry khác chờ tăng tuyến tính. Lỗi audio trong vòng tổng hợp được bắt theo `CollectionError`, `OSError`, `subprocess.SubprocessError`.

## 8. API Overview

Project **không cung cấp API nội bộ**. Các request thực tế là outbound:

| Method / cơ chế | Endpoint / đích | Mục đích | Auth trong code | Implementation |
| --- | --- | --- | --- | --- |
| GET | `https://api.openverse.org/v1/images/` | Tìm candidate theo q/page_size/mature/filter_dead/extension | Không gửi token; có User-Agent | `imagecollector.py`: `build_openverse_search_url`, `search_image` |
| GET | URL lấy từ trường `url` của kết quả Openverse | Tải JPEG | Không cấu hình credential | `imagecollector.py`: `download_jpeg`, `request_with_retry` |
| Local COM, không phải HTTP | `SAPI.SpVoice`, `SAPI.SpFileStream` | Tổng hợp giọng Nhật | Dùng môi trường Windows hiện tại | `audiocollector.py`: `synthesize_sapi_wav` |

Hugging Face loader được gọi với `local_files_only=True`; code này không tự tải model từ mạng.

## 9. Database & Data Model

Không có database, ORM, migration, index database hoặc entity persist qua SQL. Data model là các danh sách theo dòng và file metadata.

### Đầu vào và quan hệ

| File | Dòng không rỗng | Giá trị riêng biệt | Vai trò |
| --- | ---: | ---: | --- |
| `data/vocabulary/en.txt` | 500 | 500 | Tên ảnh tiếng Anh |
| `data/vocabulary/jp.txt` | 500 | 486 | Văn bản đọc và tên audio |
| `data/vocabulary/vn.txt` | 500 | 497 | Danh sách nghĩa Việt; chưa được code đọc |
| `collect data script/key.txt` | 500 | 500 | Query tìm ảnh; đây không phải API key |

Ghép `en.txt` và `key.txt` theo vị trí là quan hệ được code thực thi. Các dòng Anh/Nhật/Việt có biểu hiện được sắp tương ứng, nhưng chưa có code validate hoặc xuất quan hệ ba ngôn ngữ. Không có ID dataset chung, manifest tổng hay JSON record tập hợp cả ảnh và audio.

### Metadata ảnh

`metadata_from_result()` ghi `word`, `search_query`, `source`, `source_url`, `image_url`, `title`, `creator`, `creator_url`, `license`, `license_url`, `foreign_landing_url`. Các giá trị nguồn có thể null. Khi dùng SigLIP, thêm `image_selection` với `method`, `model`, `score`.

Tên metadata là `<English word>.json`; ảnh cùng stem, đuôi `.jpg`. Dataclass trong RAM: `ImageResult` lưu trạng thái/từ/query/ảnh chọn/score/candidate count/reason; `Summary` lưu tổng, số thành công, lỗi và kết quả chi tiết.

### Metadata audio

`write_audio_metadata()` ghi `key` (số dòng dưới dạng chuỗi), `word`, `reading`, `audio` (đường dẫn tương đối root), `source`, `format`, `size`, `duration_seconds`, `status`. Metadata mới dùng cùng stem từ Nhật với WAV.

Dataclass trong RAM gồm `AudioValidation`, `AudioResult`, `AudioSummary`. Summary có `cache_hit`; cache hit vẫn được tính vào success. Metadata không lưu toàn bộ history của các lần chạy.

### Dữ liệu thực tế lúc khảo sát

- Có 10 JPEG và 10 JSON metadata ảnh, tương ứng nhóm 10 từ đầu; cả 10 metadata có `image_selection`.
- Có 10 JSON metadata audio dạng tên số/hash cũ, nhưng **không có WAV** trong thư mục audio được kiểm kê. Cả 10 trường `audio` đều trỏ tới đường dẫn không tồn tại.
- Metadata audio cũ còn từ `リンゴ`, trong khi dòng đầu `jp.txt` hiện là `りんご`; không tự đồng bộ.
- `data/description/` chỉ có `.gitkeep`; chưa có definition dataset.

## 10. Authentication & Authorization

Không có account hệ thống, login/logout, session, token, cookie, refresh token, role hoặc permission model trong code. CLI chạy với quyền filesystem của người dùng hiện tại. Không có route nhạy cảm để đánh giá bảo vệ vì chưa có web server. Từ “password”, “account”, “user” trong vocabulary là nội dung học, không phải module authentication.

## 11. State Management & Data Flow

State local của một lần chạy là danh sách từ/query, dataclass kết quả, summary và instance model nạp lười. Không có global UI state, server state hay dữ liệu gửi tới browser.

Persistence/cache:

- Image cache cuối: JPEG đúng signature và metadata tồn tại. Không đọc lại JSON để so query, model hoặc score.
- Candidate cache: `_candidates/<word>/<index>.jpg`. Được tái sử dụng theo index rồi dọn khi chọn và ghi thành công.
- Audio cache: WAV hợp lệ theo tên từ; metadata tồn tại không bị cập nhật trong cache hit.
- Model: Hugging Face cache local hoặc đường dẫn truyền qua CLI. Không có distributed cache.

Không có lệnh force refresh, cơ chế invalidation theo phiên bản hay refetch tự động khi query/model/voice đổi. Không có cơ chế đồng bộ giữa metadata và media ngoài logic từng collector.

## 12. External Services & Integrations

| Integration | Mục đích | Code/config |
| --- | --- | --- |
| Openverse | Tìm ảnh và provenance | `imagecollector.py`; endpoint/User-Agent là hằng số, query file và page size qua CLI |
| Các host ảnh trong kết quả | Cung cấp JPEG | `imagecollector.py`; URL từ response, hiện metadata mẫu có nguồn Flickr |
| SigLIP qua Transformers/PyTorch | Xếp hạng ảnh theo text | `image_scorer.py`; model mặc định `google/siglip2-so400m-patch16-384`, CLI model/device/dtype |
| Hugging Face cache local | Tìm snapshot model đã có | `image_scorer.py`; thư mục dưới `Path.home()`, loader chỉ dùng local |
| Windows SAPI / PowerShell | Tạo audio tiếng Nhật | `audiocollector.py`; tự chọn voice đầu tiên phù hợp, không có cờ chọn voice |

Không có integration JMdict dù sơ đồ định hướng đề cập. Không có OpenAI API, image generation AI, payment, email, OAuth, analytics hoặc cloud storage trong code hiện tại.

## 13. Environment Variables

Không tìm thấy biến môi trường ứng dụng được đọc trực tiếp bằng `os.environ`, `getenv`, dotenv hoặc cơ chế tương đương trong source hiện tại. Không có `.env.example` trong cây khảo sát; `.gitignore` có quy tắc bỏ qua `.env` và `.env.*`.

Config ứng dụng đến từ hằng số, CLI và filesystem. `Path.home()` được dùng để tìm cache model; executable `powershell` được tìm theo môi trường process. Dependency có thể có hành vi môi trường riêng nhưng repository không khai báo hợp đồng biến nào cho chúng. Không chép giá trị secret/credential vào tài liệu này.

## 14. Configuration

| Cấu hình | Mặc định / hành vi | Nguồn |
| --- | --- | --- |
| Project root | Parent của thư mục script | `collector_common.py` |
| Limit | 10 từ đầu | `collector_common.py` |
| Timeout | 20 giây mỗi HTTP operation hoặc subprocess audio | `collector_common.py`, hai collector |
| Retry | 2 lần retry, tối đa 3 attempts | `collector_common.py`, hai collector |
| Retry delay | 2 giây × số attempt trước lần thử tiếp | Hai collector |
| Delay giữa từ | 1 giây; bỏ qua sau cache hit | Hai collector |
| Candidate page size | 7, chỉ kiểm tra >= 1 | `imagecollector.py` |
| Image selection | SigLIP mặc định; tắt bằng `--no-siglip` | `imagecollector.py` |
| Device | auto/cpu/cuda; auto chọn CUDA nếu có | `image_scorer.py` |
| Dtype | auto/float16/bfloat16/float32; auto dùng float16 trên CUDA, float32 trên CPU | `image_scorer.py` |
| Output | Cố định trong data/image/en và data/audio/jp | Hai collector; chưa có CLI output directory |

Không có cấu hình TypeScript, bundler, lint, formatter, build, container hoặc deployment. `requirements.txt` pin dependency trực tiếp; chưa có lock đầy đủ dependency bắc cầu.

`.gitignore` loại virtualenv, bytecode, env files, model weights và một số output. Quy tắc multimedia hiện bỏ qua JPEG/metadata ảnh English, MP3 audio English và description English; không phủ WAV/metadata audio Japanese hoặc JPEG trong candidate subdirectory.

## 15. Scripts & Commands

Các lệnh dưới đây lấy từ `comand.txt`, `README.md` và entry point có thật, chạy tại root bằng PowerShell.

Ảnh — lệnh hiện lưu trong `comand.txt`, xử lý 1 từ với tối đa một trang 10 candidate:

```powershell
.\.venv\Scripts\python.exe "collect data script\imagecollector.py" --limit 1 --page-size 10 --siglip-device cpu --siglip-dtype float32
```

Audio — xử lý 10 dòng đầu:

```powershell
.\.venv\Scripts\python.exe "collect data script\audiocollector.py" --limit 10
```

Test offline — lệnh có trong README:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s "collect data script" -p "test_*.py"
```

Cả hai CLI hỗ trợ `--help`, `--limit`, `--timeout`, `--retries`, `--retry-delay`, `--rate-limit-delay`, `--vocabulary`. Image còn có `--query-file`, `--page-size`, các cờ SigLIP. Audio nhận alias `--audio-vocabulary`. Launcher `collector.py` dùng `--audio-only` để chuyển mode; chỉ các tham số collector đích hiểu mới được chấp nhận.

Không có script npm/dev/build/lint/deploy. Repository chưa cung cấp script cài voice Nhật hoặc tải model. Không thực thi collector trong đợt khảo sát tài liệu này.

## 16. Testing

`collect data script/test_collectors.py` chứa 6 test `unittest`:

1. Import audio không nạp image collector/Pillow/Torch/Transformers.
2. Launcher cũ chuyển đúng mode và chuyển tiếp return code.
3. Từ chối một số tham số không hợp lệ và vocabulary tiếng Anh trùng.
4. Cache ảnh bỏ qua search/model scoring.
5. `ImageScoringError` được chuyển thành `CollectionError`.
6. Tổng hợp WAV giả trong thư mục tạm, kiểm tra tên từ Nhật, metadata, duration và cache hit.

Đây là test offline dùng mock; không kiểm chứng HTTP thật, inference model thật hoặc SAPI thật. Test SigLIP exception import `image_scorer`, nên chạy toàn suite vẫn cần Pillow. Không có e2e UI hoặc coverage report/config; không suy ra tỷ lệ coverage.

Những phần chưa được test trong file này: retry HTTP/SAPI nhiều lần, cache candidate thay đổi URL, đồng bộ ba ngôn ngữ, metadata mồ côi, audio trùng từ với nhiều key, toàn bộ tập filename không hợp lệ, corruption/truncation media và chạy song song. Trong task chỉ đọc/tạo tài liệu, không chạy lại test; kết quả test từ các task trước không được coi là kiểm chứng mới cho snapshot này.

## 17. Deployment

**Chưa xác định rõ từ codebase hiện tại.** Không có cloud config, CI/CD, Dockerfile, production config hay build artifact. Cách chạy được tài liệu hóa là local CLI với `.venv` trên Windows; audio phụ thuộc PowerShell, SAPI và voice Japanese đã cài. Image cần Internet cho ảnh mới và model local nếu dùng SigLIP. Chưa có quy trình phát hành hoặc đưa dataset lên web.

## 18. Important Files

| File | Trách nhiệm |
| --- | --- |
| `README.md` | Mục đích tổng quát và cách chạy hiện tại |
| `projectframework.md` | Sơ đồ định hướng; không đại diện toàn bộ phần đã triển khai |
| `progress.md` | Ghi chú tiến độ, hiện trùng nội dung sơ đồ |
| `requirements.txt` | Dependency ML/ảnh được pin |
| `comand.txt` | Hai lệnh chạy tiện dụng |
| `.gitignore` | Quy tắc quản lý file local/generated |
| `collect data script/collector.py` | Launcher tương thích |
| `collect data script/collector_common.py` | CLI, paths, validation và exception chung |
| `collect data script/imagecollector.py` | Toàn bộ pipeline ảnh |
| `collect data script/image_scorer.py` | Load và inference SigLIP |
| `collect data script/audiocollector.py` | Pipeline WAV từ văn bản Nhật |
| `collect data script/test_collectors.py` | Regression tests offline |
| `collect data script/key.txt` | Danh sách truy vấn ảnh |
| `data/vocabulary/en.txt` | Danh sách từ English / tên ảnh |
| `data/vocabulary/jp.txt` | Văn bản tiếng Nhật / tên audio |
| `data/vocabulary/vn.txt` | Nghĩa tiếng Việt, chưa có consumer trong code |
| `data/image/en/_metadata/apple.json` | Ví dụ provenance và SigLIP score thực tế |
| `data/audio/jp/_metadata/0001-effafd165ca1.json` | Ví dụ metadata audio cũ, media đích hiện thiếu |

## 19. Dependency / Module Map

```text
collector.py
 ├─ collector_common
 └─ imagecollector HOẶC audiocollector (lazy import)

imagecollector
 ├─ collector_common
 ├─ urllib + JSON + filesystem
 └─ image_scorer (khi cần SigLIP)
     ├─ Pillow
     └─ torch + transformers (khi khởi tạo model)

audiocollector
 ├─ collector_common
 ├─ wave + JSON + filesystem
 └─ subprocess → PowerShell → Windows SAPI

test_collectors
 ├─ collector + collector_common + hai collector
 └─ image_scorer (trong test lỗi scoring)
```

Audio không phụ thuộc module ảnh hoặc dependency ML. `vn.txt`, `web/`, `game/` và `data/description/` chưa tham gia dependency thực thi. `key.txt` được image collector đọc như dữ liệu, không phải module hay credential.

## 20. Current Design Decisions

- Hai pipeline độc lập, chia sẻ một module tiện ích; launcher mỏng giữ lệnh CLI cũ.
- File TXT/JSON làm nguồn dữ liệu và persistence; chưa có database hoặc dataset service.
- Ảnh đặt theo từ English, audio theo từ Japanese; tên file chính là khóa cache.
- Query tìm ảnh tách khỏi canonical English word, liên kết theo thứ tự dòng.
- Tải ảnh JPEG từ nguồn ngoài và lưu provenance; SigLIP chỉ xếp hạng, không tạo ảnh.
- Model chạy local, nạp lười và tái sử dụng trong process; batch theo các candidate của một từ.
- Thu thập tuần tự với retry/delay, không có parallel downloader.
- Audio dùng SAPI local, không gọi cloud TTS; `word` đồng thời là `reading`.
- Dùng file tạm rồi replace cho HTTP JPEG download và WAV synthesis. Copy ảnh từ candidate và ghi metadata không dùng cùng cơ chế atomic đó.
- Đường dẫn đầu vào tương đối root thay vì phụ thuộc working directory của người chạy.

Đây là các hành vi quan sát được, không khẳng định chúng là lựa chọn kiến trúc cuối cùng.

## 21. Known Problems / Technical Debt

### Architecture

- **Chưa có dataset contract chung** — `data/vocabulary/`, hai collector: ảnh và audio dùng khóa khác ngôn ngữ, không có manifest liên kết. Ảnh hưởng đáng kể khi triển khai consumer/web game; chưa phải lỗi của UI vì UI chưa tồn tại.
- **Liên kết theo vị trí dòng dễ lệch** — `imagecollector.py`, các TXT: chỉ kiểm tra số dòng en/query, chưa kiểm tra ba ngôn ngữ hoặc nội dung tương ứng. Có thể ghép sai nghĩa mà collector vẫn chạy.

### Code organization

- `imagecollector.py` và `audiocollector.py` mỗi file gom CLI, I/O, orchestration, validation, formatting output. Khi mở rộng có thể khó test/cấu hình từng phần; mức ảnh hưởng hiện tại vừa phải.
- Các output directory là hằng số module; test phải patch chúng. Chưa có config object/output-dir option cho nhiều dataset.

### Duplication

- `progress.md` và `projectframework.md` có nội dung giống nhau lúc khảo sát; dễ cập nhật lệch về sau.
- Default SigLIP model lặp ở `imagecollector.py` và `image_scorer.py`; thay một nơi có thể làm resolver/cache lookup lệch.
- Đọc vocabulary, summary và retry có phần tương tự giữa hai collector nhưng policy khác nhau; không nên mặc định coi tất cả là có thể gộp.

### Type safety

- `imagecollector.py` dùng `Any` và dict cho payload ngoài; `http_get_json()` gán kiểu dict nhưng không validate JSON root là object. Response không đúng dạng có thể gây exception ngoài `CollectionError`.
- Kết quả scorer được `zip()` với candidate mà không kiểm tra độ dài. Sai hợp đồng có thể làm mất candidate hoặc lỗi khi lấy phần tử đầu. Chưa có static type-check config.

### Error handling

- `audiocollector.py`: tạo path, validate cache và ghi metadata cho cache hit nằm ngoài vòng try/retry tổng hợp. Lỗi ở đây có thể dừng cả batch qua `run_cli`, khác lỗi tổng hợp được ghi vào summary rồi tiếp tục.
- `image_scorer.py`/`LazySiglipScorer`: lỗi inference hoặc import dependency không phải lúc nào cũng chuyển thành `ImageScoringError`; lỗi runtime có thể dừng CLI mà không có summary hoàn chỉnh.
- JPEG chỉ kiểm tra 3 byte đầu; WAV kiểm tra header/thông số nhưng không đọc đối chiếu toàn bộ frame payload. File cắt cụt có khả năng được coi là cache hợp lệ. Test cache ảnh hiện còn dùng payload signature giả.
- Ghi JSON trực tiếp và copy candidate sang ảnh đích không atomic; gián đoạn có thể để lại dữ liệu chưa hoàn chỉnh.

### Security

- `imagecollector.py` tải URL bên ngoài bằng `urlopen`, đọc hết body vào RAM; chưa có allowlist host, giới hạn kích thước tải hoặc kiểm tra redirect riêng. Hiện là CLI local; cần đánh giá lại nếu sau này cho người dùng không tin cậy điều khiển input.
- `sanitize_filename()` của image chặn separator/ký tự ngoài whitelist nhưng không kiểm tra đầy đủ tên thiết bị Windows như phía audio; có thể gặp lỗi filesystem với vocabulary tùy chỉnh.
- Metadata ảnh có `license`/`license_url` nhưng code không lọc license theo mục đích sử dụng. Đây là điểm cần review yêu cầu dataset trước khi phát hành, không phải kết luận pháp lý.

### Performance

- Download candidate và xử lý từ đều tuần tự; SAPI khởi động một PowerShell process cho mỗi lần thử từng từ. Có thể chậm với toàn bộ 500 dòng.
- Tất cả candidate của một từ được decode/chấm trong một batch, không có batch-size hoặc giới hạn kích thước ảnh; có thể gây áp lực RAM/VRAM.
- Nếu khởi tạo model thất bại và được chuyển thành lỗi từng từ, `LazySiglipScorer.scorer` vẫn rỗng; các từ tiếp có thể lại tải candidate và thử khởi tạo.
- HTTP 429 không có xử lý `Retry-After` riêng; chỉ dùng delay tuyến tính chung.

### Database / dữ liệu file

- **Metadata audio mồ côi** — `data/audio/jp/_metadata/`: 10 file đều trỏ WAV không tồn tại ở snapshot hiện tại. Không thể coi các trường status success cũ là bằng chứng dataset audio sẵn sàng.
- **Khóa audio không còn một-một với dòng** — `jp.txt`, `stable_audio_stem()`, `write_audio_metadata()`: 500 dòng/486 chuỗi riêng biệt. Nhiều dòng cùng từ dùng một WAV/JSON; `key` trong JSON thường giữ dòng đã ghi đầu tiên, không đại diện mọi dòng.
- **Candidate cache không gắn URL** — `candidate_cache_path()`: dùng số thứ tự. Sau một lần lỗi, kết quả search thay đổi có thể khiến JPEG cũ được ghép với URL/metadata mới; rủi ro sai provenance và lựa chọn ảnh.
- **Cache không xét config mới** — hai collector: sửa query/model/voice không tự làm mới file. Image không parse metadata lúc cache hit, audio không cập nhật metadata đã có.
- **Dữ liệu ngôn ngữ cần kiểm tra** — dòng 485: `en.txt` là `ocean`, `jp.txt` là `たいよう`, `vn.txt` là `đại dương`; dòng 69 `sun` cũng dùng `たいよう`. Ghi nhận để review, không sửa hoặc tự quyết định bản dịch trong task này.

### UX

- Chưa có trải nghiệm web/game để đánh giá. CLI audio gọi summary là “AUDIO TEST” kể cả đang thu thập dữ liệu thật (`print_audio_summary()`), có thể gây nhầm.
- Chưa có resume theo offset, chọn danh sách từ riêng, force refresh hoặc giao diện duyệt chất lượng ảnh. `--limit` luôn lấy từ đầu.

### Testing

- Các đường đi thật qua Openverse, model và SAPI chưa được cover trong suite hiện có; mock success không chứng minh hệ thống local đã đủ model/voice.
- Chưa có kiểm tra toàn dataset về số dòng, liên kết media, provenance hoặc độ phù hợp ngữ nghĩa. Chưa có coverage đo được.

### Configuration / deployment

- `.gitignore` chưa phủ output audio Nhật/candidate; generated data có thể xuất hiện trong Git status.
- Không có bootstrap model/voice, khai báo Python version hay lock bắc cầu; khả năng tái lập môi trường mới chưa được kiểm chứng.
- Các tài liệu sơ đồ còn ghi mốc 13/9 đang cài model, chưa phản ánh đầy đủ collector mới; cần phân biệt lịch sử với trạng thái hiện tại.

## 22. Inconsistencies

| Điểm không thống nhất | Bằng chứng |
| --- | --- |
| Image từ chối từ trùng, audio cho phép | `collector_common.load_vocabulary()` và `audiocollector.load_audio_vocabulary()` |
| Cache status khác tên | Image dùng `cached`, audio dùng `cache_hit` |
| Image hỏng báo failed, audio hỏng xóa rồi tổng hợp lại | `process_word()` và `process_audio_entry()` |
| Tên metadata hiện tại và dữ liệu audio cũ khác quy ước | `stable_audio_stem()` trả word; JSON sẵn có vẫn tên số/hash |
| Audio word/reading cũ khác một số từ hiện tại | Metadata đầu tiên `リンゴ`, `jp.txt` hiện `りんご` |
| Filename validation khác policy | English dùng regex ASCII; Japanese giữ Unicode và kiểm tra reserved Windows names |
| Cache ảnh yêu cầu metadata tồn tại; cache audio có thể bổ sung metadata thiếu | Hai hàm process |
| Định hướng có JMdict/definition/web game nhưng code chưa có | Hai tài liệu sơ đồ so với source và thư mục placeholder |
| `.gitignore` nói audio English MP3 nhưng collector tạo Japanese WAV | `.gitignore` và `audiocollector.py` |

## 23. Unclear / Needs Confirmation

- Người học mục tiêu, chiều học Anh–Nhật–Việt và dạng game cụ thể là gì?
- Thứ tự dòng của ba ngôn ngữ có phải contract chính thức? Có cho phép chỉnh/sắp lại độc lập không?
- Dùng chung audio cho từ Nhật trùng là mong muốn; nhưng một metadata key cho nhiều dòng có đáp ứng consumer tương lai không?
- `jp.txt` là dạng hiển thị, cách đọc hay cả hai? Có cần giữ kanji và reading ở hai field riêng?
- Những từ lệch nghĩa như dòng ocean và các query nhiều nghĩa có cần quy trình kiểm duyệt nào?
- 10 WAV cũ được xóa có chủ ý hay chưa được đồng bộ vào workspace? Không thể suy ra chỉ từ metadata.
- Có cần migrate/dọn metadata audio cũ, hay sẽ tạo lại dataset từ đầu?
- Có yêu cầu threshold/độ phân giải/license/style ảnh không? SigLIP score hiện không có tiêu chuẩn đạt/rớt.
- JMdict và definition có còn trong phạm vi triển khai tiếp theo? Chưa có implementation để xác nhận.
- Frontend/backend stack, persistence tiến trình người học và môi trường deployment chưa được quyết định trong code.
- Model local, môi trường CUDA và voice Nhật trên máy đích có sẵn không? Khảo sát repository không xác nhận khả năng runtime này.

## 24. Potentially Dead / Legacy Code

- `collector.py` là **compatibility code có chủ đích**, được test, không phải bằng chứng code chết.
- `SiglipImageScorer.score()` chưa có caller trong repository; flow hiện dùng `score_batch()`. Có thể là API tiện ích, cần xác nhận trước khi loại bỏ.
- `stable_audio_stem(index, word, reading)` giữ tham số index/reading nhưng không sử dụng chúng khi tạo tên. Đây là dấu vết của quy tắc đặt tên trước, không phải hash generator hiện tại.
- Nhánh fallback `queries = ... if query_path else words` trong image main khó đạt qua CLI hiện tại vì `--query-file` luôn là Path được resolve. Có dấu hiệu nhánh dự phòng cũ, chưa xóa.
- 10 metadata audio số/hash là artifact legacy, không được collector mới tự migrate hoặc dùng như index cache.
- `choose_image_result()` vẫn được dùng cho `--no-siglip` và log so sánh, không phải code chết. `vn.txt` chưa có consumer nhưng là input dự kiến; không nên coi là file thừa.

## 25. TODO / FIXME / Temporary Code

Không tìm thấy marker TODO/FIXME/HACK/TEMP có ý nghĩa trong source và tài liệu hiện có khi khảo sát. Không có khối implementation lớn bị comment-out.

Các phần chưa hoàn thiện thể hiện bằng placeholder `web/.gitkeep`, `game/.gitkeep`, `data/description/.gitkeep` và ghi chú tiến độ trong `progress.md`, `projectframework.md`. Các biến/file có chữ `temporary` trong collector là cơ chế ghi file tạm, không tự động được coi là workaround hay TODO.

## 26. Recommended Reading Order

1. `README.md` — mục đích và cách chạy thực tế.
2. `projectframework.md`, `progress.md` — định hướng, đọc với lưu ý các phần chưa triển khai.
3. `data/vocabulary/en.txt`, `data/vocabulary/jp.txt`, `data/vocabulary/vn.txt`, `collect data script/key.txt` — hợp đồng đầu vào theo dòng.
4. `collect data script/collector_common.py` — root path, defaults, validation và exit behavior.
5. `collect data script/collector.py` — điều phối lệnh cũ.
6. `collect data script/imagecollector.py` — đọc main/process_word trước, rồi các hàm HTTP/cache/metadata.
7. `collect data script/image_scorer.py` — model local và score semantics.
8. `collect data script/audiocollector.py` — tên file, WAV validation, SAPI và metadata.
9. Hai thư mục metadata dưới `data/image/en/` và `data/audio/jp/` — so artifact thực tế với schema.
10. `collect data script/test_collectors.py` — hành vi đã được mô tả bằng test và phạm vi mock.
11. `requirements.txt`, `comand.txt`, `.gitignore` — môi trường, lệnh và quản lý output.

## 27. Project Mental Model

Project hiện là một công cụ chuẩn bị tài nguyên chạy từ terminal. Nhánh ảnh đọc từ English và query cùng vị trí, tìm/tải ảnh Openverse rồi chọn bằng model local để lưu JPEG cùng provenance. Nhánh audio đọc trực tiếp từ Japanese, dùng từ đó làm tên file và nội dung đọc, gọi SAPI để lưu WAV cùng metadata. Hai nhánh chỉ gặp nhau ở thư mục dữ liệu và tiện ích Python chung; chưa có record thống nhất hoặc ứng dụng web sử dụng đầu ra. Khi làm task tiếp theo, cần phân biệt dữ liệu thực sự hiện diện với metadata cũ, và phân biệt sơ đồ web game dự kiến với pipeline CLI đã triển khai.
