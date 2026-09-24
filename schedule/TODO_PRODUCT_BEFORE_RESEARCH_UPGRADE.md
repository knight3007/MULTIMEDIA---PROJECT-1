# Multimedia Project 1 — Master TODO trước giai đoạn Research Upgrade

> Mục tiêu của tài liệu này: đưa project từ trạng thái pipeline thu thập dữ liệu hiện tại thành một **sản phẩm hoàn chỉnh có thể chạy end-to-end**, gồm:
>
> 1. Data pipeline ổn định.
> 2. Backend/API rõ ràng.
> 3. Web hoàn chỉnh.
> 4. Game hoàn chỉnh ở mức MVP có thể demo.
> 5. Dữ liệu, logging, test, tài liệu và deployment đủ để người khác chạy được.
>
> **Không triển khai research upgrade trong tài liệu này.**
>
> Các phần như semantic failure detection, adaptive candidate budget, quality-aware recovery, OpenTelemetry research telemetry, AIOps/RCA... được chuyển sang tài liệu `RESEARCH_UPGRADE_ROADMAP.md`.

---

# 0. Quy tắc làm project từ thời điểm này

## 0.1. Thứ tự ưu tiên

Không làm song song tất cả.

Thứ tự cố định:

```text
Refactor pipeline
      ↓
Stabilize pipeline
      ↓
Freeze data contract
      ↓
Backend/API
      ↓
Web
      ↓
Game
      ↓
Integration
      ↓
Testing
      ↓
Deployment
      ↓
Documentation
      ↓
PRODUCT BASELINE FREEZE
      ↓
Research Upgrade
```

## 0.2. Điều kiện chuyển phase

Chỉ chuyển sang phase tiếp theo khi:

- chức năng chính của phase hiện tại chạy được;
- không còn bug blocker;
- input/output đã rõ;
- có test tối thiểu;
- đã cập nhật tài liệu cần thiết.

Không yêu cầu mọi thứ hoàn hảo mới được đi tiếp.

Mục tiêu là:

> **ổn định đủ để tiếp tục phát triển**, không phải tối ưu vô hạn.

---

# 1. Phase A — Freeze pipeline hiện tại

## Mục tiêu

Tạo một phiên bản baseline trước khi refactor để sau này biết chính xác mình đã thay đổi những gì.

## TODO

- [ ] Tạo một branch/tag hoặc commit mốc cho pipeline hiện tại.
- [ ] Xác nhận luồng hiện tại:

```text
data/vocabulary/en.txt
        ↓
query_generator.py
        ↓
Qwen3-1.7B
        ↓
semantic query
        ↓
DuckDuckGo Images
        ↓
N candidates
        ↓
download
        ↓
validate
        ↓
SigLIP
        ↓
best candidate
        ↓
normalize
        ↓
final image + metadata
```

- [ ] Ghi lại command hiện tại dùng để collect image.
- [ ] Ghi lại dependency hiện tại.
- [ ] Chạy một smoke test nhỏ, ví dụ 10–20 từ.
- [ ] Lưu lại:
  - output image;
  - metadata;
  - lỗi phát sinh;
  - thời gian chạy tương đối;
  - số ảnh thất bại nếu có.
- [ ] Không sửa semantic logic ở bước này.

## Definition of Done

- Có một commit/tag baseline.
- Có command chạy được.
- Có bộ output nhỏ dùng để so sánh sau refactor.

---

# 2. Phase B — Refactor image retrieval pipeline

## Mục tiêu

Tách pipeline thành các component độc lập nhưng **không thay đổi mục tiêu đầu ra**.

## Kiến trúc mục tiêu

```text
Vocabulary
    ↓
QueryGenerator
    ↓
ImageSearchProvider
    ↓
DownloadManager
    ↓
ImageValidator
    ↓
SigLIPRanker
    ↓
ImageNormalizer
    ↓
Storage / Metadata
```

---

## 2.1. Query Generator

- [ ] Giữ `Qwen3-1.7B`.
- [ ] Giữ semantic query hiện đang cho output ổn định.
- [ ] Chuẩn hóa interface.

Ví dụ:

```python
generate_query(word: str) -> str
```

- [ ] Không để module này biết DuckDuckGo là gì.
- [ ] Không download image trong module này.
- [ ] Không chấm SigLIP trong module này.

### Done khi

```text
word → semantic query
```

là trách nhiệm duy nhất của module.

---

## 2.2. Image Search Provider abstraction

Tạo interface chung:

```python
class ImageSearchProvider:
    def search(self, query: str, limit: int):
        ...
```

- [ ] Tạo `ImageSearchProvider`.
- [ ] Tạo implementation:

```text
DuckDuckGoProvider
```

- [ ] Pipeline phía sau không import trực tiếp logic DuckDuckGo.
- [ ] Search result trả về structured object.

Gợi ý structure:

```python
{
    "image_url": "...",
    "source_page": "...",
    "title": "...",
    "provider": "duckduckgo",
    "rank": 1
}
```

### Chưa cần

- Google CSE.
- SerpAPI.
- Unsplash.
- Multi-provider fusion.

Các provider khác chỉ là future extension.

---

## 2.3. Download Manager

### Yêu cầu

- [ ] Tách download khỏi search.
- [ ] Có timeout.
- [ ] Có retry giới hạn.
- [ ] Một URL lỗi không làm chết cả word.
- [ ] Có concurrency cho candidate download.

Luồng mong muốn:

```text
candidate URLs
      ↓
concurrent downloader
      ↓
candidate 1 PASS
candidate 2 timeout
candidate 3 404
candidate 4 PASS
...
      ↓
continue with valid images
```

### Không được

```text
candidate 2 fail
      ↓
abort whole word
```

---

## 2.4. Image Validator

- [ ] Kiểm tra response thực sự là image.
- [ ] Pillow mở được image.
- [ ] Loại corrupted image.
- [ ] Kiểm tra kích thước tối thiểu nếu pipeline đang yêu cầu.
- [ ] Loại file không phù hợp.
- [ ] Không crop ở đây.
- [ ] Không normalize final output ở đây.

Validator chỉ trả lời:

```text
candidate usable?
YES / NO
```

---

## 2.5. SigLIP Ranker

- [ ] Giữ SigLIP.
- [ ] SigLIP phải dùng đúng **Qwen semantic query** đã dùng cho search.
- [ ] Rank tất cả candidate hợp lệ.
- [ ] Trả về ít nhất:

```text
candidate
score
rank
```

- [ ] Lưu full score list trong metadata nếu chi phí chấp nhận được.

---

## 2.6. Normalizer

Chỉ chạy với winner cuối cùng.

Giữ rule hiện tại:

- [ ] EXIF transpose.
- [ ] RGB.
- [ ] JPEG.
- [ ] max `1024 × 1024`.
- [ ] preserve aspect ratio.
- [ ] NO crop.
- [ ] NO upscale.
- [ ] JPEG quality theo config hiện tại.

---

## 2.7. Metadata schema

Trước khi làm web, schema phải ổn định.

Ví dụ:

```json
{
  "word": "apple",
  "query": "apple fruit",
  "provider": "duckduckgo",
  "source_url": "...",
  "source_page": "...",
  "title": "...",
  "siglip_score": 0.81,
  "image_path": "data/image/en/apple.jpg"
}
```

### TODO

- [ ] Chốt schema.
- [ ] Có version nếu cần.
- [ ] Không để web phụ thuộc vào internal variable rời rạc.
- [ ] Có fallback khi metadata field bị thiếu.

---

# 3. Phase C — Test và stabilize pipeline

## 3.1. Unit tests

Ít nhất test:

- [ ] QueryGenerator nhận English word.
- [ ] Search provider nhận **generated query**, không nhận raw word nếu pipeline không thiết kế như vậy.
- [ ] Search provider trả đúng structure.
- [ ] Downloader xử lý timeout.
- [ ] Downloader xử lý HTTP error.
- [ ] Validator loại invalid image.
- [ ] SigLIP nhận đúng query.
- [ ] Normalizer giữ aspect ratio.
- [ ] Final image đúng JPEG/RGB.
- [ ] Metadata save đúng.

---

## 3.2. Integration test

Test:

```text
word
 ↓
Qwen
 ↓
DDG
 ↓
download
 ↓
validate
 ↓
SigLIP
 ↓
normalize
 ↓
save
```

- [ ] Chạy 10 từ dễ.
- [ ] Chạy 10 từ khó/ambiguous.
- [ ] Không crash toàn batch nếu một từ fail.
- [ ] Error phải được ghi rõ.

---

## 3.3. Smoke test lớn hơn

Sau khi ổn:

- [ ] Chạy 50–100 vocabulary item.
- [ ] Kiểm tra thủ công sample output.
- [ ] Ghi lại lỗi.
- [ ] Fix lỗi blocker.
- [ ] Không bắt đầu research semantic detector ở đây.

---

# 4. Phase D — Freeze Data Contract cho product

Đây là bước rất quan trọng trước khi web/game cùng đọc dữ liệu.

## 4.1. Chốt vocabulary format

Cần xác định mỗi vocabulary item có gì.

Tối thiểu:

```text
word
language
image
```

Nếu project đã có thêm dữ liệu:

```text
meaning
example
audio
phonetic
category
difficulty
...
```

thì cần đưa vào schema rõ ràng.

---

## 4.2. Chốt asset directory

Ví dụ:

```text
data/
├── vocabulary/
├── image/
│   └── en/
├── audio/
├── metadata/
└── cache/
```

- [ ] Không để web/game đoán path.
- [ ] Path được sinh theo rule nhất quán.
- [ ] Missing asset có fallback.

---

## 4.3. Chốt ID

Không nên dùng display text làm primary key nếu sau này data phức tạp.

Ví dụ:

```text
vocab_id
word
language
```

- [ ] Mỗi item có ID ổn định.
- [ ] ID không đổi khi sửa UI text.

---

# 5. Phase E — Backend / API layer

## Mục tiêu

Web và game không đọc trực tiếp file hệ thống một cách tùy tiện.

Tạo một backend/API rõ ràng.

---

## 5.1. Chốt backend stack

- [ ] Chọn framework.
- [ ] Chốt project structure.
- [ ] Chốt config/environment.
- [ ] Chốt cách chạy development server.

Nếu backend đã dùng Python thì ưu tiên stack đơn giản, tránh thêm công nghệ không cần thiết.

---

## 5.2. API tối thiểu

Tùy sản phẩm thực tế, nhưng nên có các nhóm endpoint:

### Vocabulary

```text
GET /vocabulary
GET /vocabulary/{id}
```

### Assets

```text
GET image
GET audio
```

hoặc trả asset URL trong vocabulary response.

### Game/session

Nếu cần:

```text
POST /game/session
GET  /game/question
POST /game/answer
```

### Progress

Nếu sản phẩm lưu tiến độ:

```text
GET  /progress
POST /progress
```

---

## 5.3. API contract

- [ ] Viết request schema.
- [ ] Viết response schema.
- [ ] Error response thống nhất.
- [ ] Có HTTP status rõ ràng.
- [ ] Web và game cùng dùng chung contract.

---

## 5.4. Backend tests

- [ ] API trả đúng schema.
- [ ] Missing vocabulary → error hợp lý.
- [ ] Missing asset → fallback/error hợp lý.
- [ ] Invalid request không crash server.
- [ ] Game request không làm corrupt state.

---

# 6. Phase F — Web Product

## Mục tiêu

Có một web interface hoàn chỉnh đủ để người dùng ngoài project có thể hiểu và sử dụng.

---

## 6.1. Chốt scope web trước khi code

Viết rõ web MVP có những màn hình nào.

Tối thiểu nên xác định:

```text
Home
Vocabulary / Learning
Game
Progress hoặc Result
About / Project info
```

Nếu project thực tế không cần một trang nào đó thì bỏ.

---

## 6.2. Design system tối thiểu

- [ ] Font.
- [ ] Spacing.
- [ ] Button.
- [ ] Card.
- [ ] Input.
- [ ] Modal nếu có.
- [ ] Responsive breakpoint.
- [ ] Loading state.
- [ ] Error state.
- [ ] Empty state.

Không cần làm design system enterprise.

Mục tiêu:

> UI nhất quán.

---

## 6.3. Background / visual concept

Nếu tiếp tục ý tưởng background star:

- [ ] Canvas/background nằm riêng khỏi UI content.
- [ ] Star/object rơi theo trục Y.
- [ ] Horizontal movement có thể phản ứng với mouse.
- [ ] Animation không block interaction.
- [ ] Có giới hạn số particle.
- [ ] Có degradation trên mobile/low-power device.
- [ ] `prefers-reduced-motion` nếu triển khai được.
- [ ] Không để animation làm FPS web giảm đáng kể.

---

## 6.4. Home page

- [ ] Project title.
- [ ] Một câu giải thích project làm gì.
- [ ] CTA rõ ràng.
- [ ] Link vào learning/game.
- [ ] UI không quá ngộp.

---

## 6.5. Vocabulary / Learning page

Tối thiểu:

- [ ] Hiển thị word.
- [ ] Hiển thị image.
- [ ] Hiển thị các dữ liệu học tập đang có.
- [ ] Next/Previous.
- [ ] Loading state.
- [ ] Missing image fallback.
- [ ] API error fallback.

Nếu có audio:

- [ ] Play audio.
- [ ] Disable/fallback nếu audio missing.

---

## 6.6. Responsive

Test ít nhất:

- [ ] Desktop.
- [ ] Tablet.
- [ ] Mobile.

Không cần pixel-perfect mọi device.

---

## 6.7. Web accessibility cơ bản

- [ ] Button là button.
- [ ] Image có alt hợp lý.
- [ ] Keyboard navigation cơ bản.
- [ ] Contrast không quá thấp.
- [ ] Không dùng animation làm cách duy nhất truyền thông tin.

---

# 7. Phase G — Game MVP

> Phần game cần được đóng scope chặt.
>
> Không mở rộng gameplay liên tục trong lúc code.

## 7.1. Viết Game Specification trước

Tạo file riêng nếu cần:

```text
GAME_SPEC.md
```

Phải trả lời:

### Core loop

```text
Start
 ↓
Question
 ↓
Player action
 ↓
Evaluate
 ↓
Feedback
 ↓
Score / Progress
 ↓
Next question
 ↓
End
```

### Phải xác định

- [ ] Người chơi phải làm gì?
- [ ] Một round kéo dài bao lâu?
- [ ] Điều kiện đúng/sai?
- [ ] Score tính thế nào?
- [ ] Game kết thúc khi nào?
- [ ] Restart thế nào?
- [ ] Vocabulary được chọn ra sao?
- [ ] Image/audio được dùng thế nào?
- [ ] Có difficulty hay chưa?

---

## 7.2. Scope game MVP

MVP chỉ cần:

- [ ] Start game.
- [ ] Load question.
- [ ] Player input/action.
- [ ] Correct/incorrect.
- [ ] Feedback.
- [ ] Score.
- [ ] Next question.
- [ ] End screen.
- [ ] Replay.

### Chưa cần nếu không bắt buộc

- multiplayer;
- leaderboard online;
- complex inventory;
- matchmaking;
- account system phức tạp;
- procedural world;
- 3D nếu game gốc không yêu cầu;
- achievement system lớn.

---

## 7.3. Game data integration

Game không hard-code vocabulary.

Luồng:

```text
Backend/Data
    ↓
Game Question Generator
    ↓
Game State
    ↓
UI
```

- [ ] Game lấy data từ common source.
- [ ] Không duplicate vocabulary database.
- [ ] Image path đúng.
- [ ] Missing image không crash game.
- [ ] Question không tạo từ record invalid.

---

## 7.4. Game state

Tối thiểu:

```text
status
current_question
current_index
score
answers
remaining_questions
```

- [ ] State transition rõ.
- [ ] Restart reset sạch state.
- [ ] Không để UI component tự giữ business logic rải rác.

---

## 7.5. Game UX

- [ ] Start rõ.
- [ ] Feedback đúng/sai dễ hiểu.
- [ ] Không delay vô lý.
- [ ] Không chuyển question trước khi người chơi đọc feedback.
- [ ] End screen có kết quả.
- [ ] Có replay.

---

## 7.6. Game testing

Test:

- [ ] Correct answer.
- [ ] Wrong answer.
- [ ] Last question.
- [ ] Restart.
- [ ] Missing image.
- [ ] API failure.
- [ ] Empty dataset.
- [ ] Duplicate question nếu không mong muốn.
- [ ] Refresh page giữa session nếu relevant.

---

# 8. Phase H — Web + Game + Pipeline Integration

Đây là lúc ghép toàn bộ sản phẩm.

## End-to-end flow mong muốn

```text
Vocabulary source
       ↓
Collection pipeline
       ↓
Generated image + metadata
       ↓
Backend/API
       ↓
Web
       ↓
Learning UI
       +
Game
```

---

## Integration TODO

- [ ] Pipeline output được backend đọc đúng.
- [ ] Backend trả đúng asset.
- [ ] Web render đúng.
- [ ] Game sử dụng cùng data.
- [ ] Không cần copy image thủ công.
- [ ] Không cần sửa source code mỗi lần thêm vocabulary.
- [ ] Có command rõ ràng để refresh/rebuild data nếu cần.

---

# 9. Phase I — Product error handling

Phân loại:

## 9.1. Data error

Ví dụ:

```text
missing image
missing metadata
invalid vocabulary
```

- [ ] fallback;
- [ ] log;
- [ ] không crash app.

## 9.2. Network/API error

- [ ] loading;
- [ ] retry button nếu phù hợp;
- [ ] error message dễ hiểu.

## 9.3. Game error

- [ ] session không hợp lệ;
- [ ] empty question list;
- [ ] asset missing.

## 9.4. Pipeline error

- [ ] error từng word không giết toàn batch;
- [ ] failed item được ghi lại để chạy lại.

---

# 10. Phase J — Logging trước research

Chỉ cần logging engineering cơ bản.

Không cần OpenTelemetry research layer ngay.

Log tối thiểu:

```text
timestamp
stage
word
status
error
duration nếu thuận tiện
```

Ví dụ:

```text
[QUERY] apple OK
[SEARCH] apple 10 results
[DOWNLOAD] apple 8/10 valid
[RANK] apple winner score=...
[SAVE] apple OK
```

Web/backend:

```text
request
status
error
```

Game:

```text
session start
session end
unexpected failure
```

Không cần log mọi click của user nếu không có mục đích.

---

# 11. Phase K — Configuration và environment

- [ ] Không hard-code path quan trọng.
- [ ] Có config file hoặc environment variable.
- [ ] Model path/config rõ.
- [ ] Data path rõ.
- [ ] Cache path rõ.
- [ ] Backend URL cho frontend rõ.
- [ ] `.env.example` nếu dùng env.
- [ ] Không commit secret.

---

# 12. Phase L — Reproducibility

Một người khác clone repo phải biết làm gì.

## Cần có

- [ ] Python version.
- [ ] Node/runtime version nếu web dùng.
- [ ] Dependency file.
- [ ] Setup command.
- [ ] Model download/setup.
- [ ] Data preparation.
- [ ] Collect images command.
- [ ] Backend run command.
- [ ] Frontend run command.
- [ ] Build command.
- [ ] Test command.

---

# 13. Phase M — Documentation

## README chính

README nên giải thích theo thứ tự:

```text
Project là gì?
        ↓
Demo / Screenshot
        ↓
Architecture
        ↓
Features
        ↓
Tech stack
        ↓
Setup
        ↓
Run
        ↓
Data pipeline
        ↓
Web
        ↓
Game
        ↓
Limitations
        ↓
Future research
```

---

## Tài liệu nên có

- [ ] `README.md`
- [ ] `ARCHITECTURE.md`
- [ ] `GAME_SPEC.md`
- [ ] `DATA_SCHEMA.md` nếu cần
- [ ] command/run guide
- [ ] `TODO_PRODUCT_BEFORE_RESEARCH_UPGRADE.md`
- [ ] `RESEARCH_UPGRADE_ROADMAP.md`

---

# 14. Phase N — Demo preparation

## Demo flow

Demo phải ngắn và rõ.

Ví dụ:

```text
1. Show vocabulary source
2. Show generated image/data
3. Open web
4. Show learning page
5. Start game
6. Complete several questions
7. Show result
```

Không demo bằng cách mở 20 terminal window nếu không cần.

---

## Chuẩn bị

- [ ] Seed/sample data ổn định.
- [ ] Không phụ thuộc live image collection trong lúc demo nếu không cần.
- [ ] Có fallback nếu internet chậm.
- [ ] Có screenshots/video backup nếu phù hợp.
- [ ] Test full demo một lần từ đầu đến cuối.

---

# 15. Phase O — Product QA checklist

## Pipeline

- [ ] Query generation ổn.
- [ ] Search ổn.
- [ ] Download lỗi không crash.
- [ ] Validation ổn.
- [ ] SigLIP ranking ổn.
- [ ] Normalize ổn.
- [ ] Metadata ổn.

## Backend

- [ ] API chạy.
- [ ] Error response ổn.
- [ ] Asset load ổn.

## Web

- [ ] Desktop ổn.
- [ ] Mobile chấp nhận được.
- [ ] Loading/error state.
- [ ] Navigation không lỗi.

## Game

- [ ] Start.
- [ ] Answer.
- [ ] Score.
- [ ] End.
- [ ] Replay.
- [ ] Edge case cơ bản.

## Repository

- [ ] README.
- [ ] Setup.
- [ ] Commands.
- [ ] `.gitignore`.
- [ ] Không có secret.
- [ ] Không có file build/cache không cần thiết.

---

# 16. PRODUCT BASELINE FREEZE

Đây là checkpoint quan trọng nhất.

Khi toàn bộ phần trên đã ổn định:

```text
PRODUCT BASELINE v1
```

- [ ] Tạo Git tag/release.
- [ ] Freeze architecture.
- [ ] Freeze main API contract.
- [ ] Freeze data schema.
- [ ] Freeze game MVP behavior.
- [ ] Lưu test result.
- [ ] Lưu sample dataset.
- [ ] Lưu screenshots/demo.

---

# 17. Điều kiện để được bắt đầu Research Upgrade

Chỉ chuyển sang `RESEARCH_UPGRADE_ROADMAP.md` khi:

- [ ] Pipeline modular.
- [ ] Product chạy end-to-end.
- [ ] Web sử dụng được.
- [ ] Game MVP sử dụng được.
- [ ] Dataset contract ổn định.
- [ ] Có baseline output.
- [ ] Có repository/documentation đủ để reproduce.
- [ ] Không còn blocker kiến trúc lớn.

---

# 18. Những việc CỐ TÌNH chưa làm trước Product v1

Để tránh scope creep:

- [ ] Không Kubernetes.
- [ ] Không distributed microservices nếu không thật sự cần.
- [ ] Không Airflow/Kedro chỉ để orchestration pipeline nhỏ.
- [ ] Không Prometheus/Grafana trước khi research cần metric.
- [ ] Không LLM RCA agent.
- [ ] Không unrestricted self-healing agent.
- [ ] Không multi-provider search nếu DDG vẫn đủ cho baseline.
- [ ] Không semantic quality detector.
- [ ] Không adaptive candidate budget.
- [ ] Không quality-aware recovery.
- [ ] Không research benchmark lớn.

Những phần này **không bị bỏ**.

Chúng chỉ được chuyển sang đúng thời điểm.

---

# 19. Master Checklist rút gọn

```text
[ ] A. Freeze current pipeline
[ ] B. Refactor pipeline
[ ] C. Pipeline tests + stabilization
[ ] D. Freeze data contract
[ ] E. Backend/API
[ ] F. Web MVP
[ ] G. Game specification
[ ] H. Game MVP
[ ] I. Full integration
[ ] J. Error handling
[ ] K. Basic logging
[ ] L. Configuration
[ ] M. Reproducibility
[ ] N. Documentation
[ ] O. Demo preparation
[ ] P. Product QA
[ ] Q. Product Baseline v1 freeze
[ ] R. Begin Research Upgrade
```

---

# 20. Mental model cuối cùng

Trong giai đoạn này chỉ cần nghĩ:

```text
             BUILD THE PRODUCT
                    │
        ┌───────────┼────────────┐
        │           │            │
     Pipeline      Web          Game
        │           │            │
        └───────────┴────────────┘
                    │
                    ▼
             Stable Product v1
                    │
                    ▼
            Freeze the baseline
                    │
                    ▼
              Start Research
```

Mục tiêu hiện tại không phải làm project "thông minh nhất".

Mục tiêu là tạo ra một **baseline sản phẩm sạch, chạy được, đo được và có thể nâng cấp**.
