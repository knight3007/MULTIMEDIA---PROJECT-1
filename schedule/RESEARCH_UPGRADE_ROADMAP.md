# Multimedia Project 1 — Research Upgrade Roadmap

> Tài liệu này chỉ bắt đầu **sau khi Product Baseline v1 đã hoàn thành**.
>
> Baseline sản phẩm phải có:
>
> - pipeline modular;
> - backend/API ổn định;
> - web chạy được;
> - game MVP chạy được;
> - data contract ổn định;
> - sample dataset và output có thể reproduce.
>
> Mục tiêu nghiên cứu không phải biến project thành một hệ thống enterprise lớn.
>
> Trọng tâm là:
>
> **Semantic-Aware Observability + Adaptive Retrieval + Quality-Aware Recovery cho AI Image Retrieval Pipeline.**

---

# 1. Vấn đề nghiên cứu

Pipeline baseline:

```text
English word
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
final image
```

Pipeline này biết xử lý khá rõ các lỗi như:

```text
timeout
404
invalid image
corrupt JPEG
```

Nhưng tồn tại một lớp lỗi khó hơn:

```text
pipeline technically succeeds
        ↓
final output exists
        ↓
final output is semantically wrong
```

Ví dụ:

```text
word = ring
target = jewelry

pipeline returns
wrestling ring
```

Hệ thống không crash.

Không có exception.

Nhưng kết quả không đạt mục tiêu.

Đây là:

> **silent semantic failure**

---

# 2. Research goal

Xây một layer có khả năng:

```text
observe
   ↓
estimate output quality / uncertainty
   ↓
detect suspicious result
   ↓
choose limited recovery action
   ↓
retry
   ↓
verify again
```

Mục tiêu:

1. Phát hiện semantic failure tốt hơn.
2. Tự phục hồi khi retrieval kém.
3. Giảm download/computation không cần thiết.
4. Giữ hệ thống dễ kiểm soát và reproduce.

---

# 3. Không nghiên cứu những gì

Để giữ scope hợp lý:

## Không lấy làm contribution chính

- Kubernetes.
- Prometheus dashboard.
- Grafana dashboard.
- OpenTelemetry instrumentation.
- Airflow/Kedro orchestration.
- LLM đọc log để đoán timeout.
- Generic AIOps platform.
- Multi-agent system lớn.
- Agent có unrestricted shell access.

Những công nghệ này có thể hỗ trợ engineering nhưng không phải core research contribution.

---

# 4. Research Questions

Chỉ giữ 3 câu hỏi chính.

## RQ1 — Detection

> Can operational and semantic telemetry reliably identify poor-quality image retrieval outcomes?

Diễn giải:

Có thể dùng các tín hiệu từ pipeline để nhận ra:

```text
output có nguy cơ sai nghĩa
```

trước khi accept không?

---

## RQ2 — Recovery

> Does adaptive recovery improve semantic success compared with fixed retry rules?

So sánh:

```text
fixed rule recovery
vs
adaptive recovery
```

---

## RQ3 — Efficiency

> Can adaptive candidate budgeting reduce download and inference cost while maintaining semantic retrieval quality?

Tức là:

```text
Quality
   vs
Cost
```

---

# 5. Research hypotheses

Các giả thuyết cần được kiểm chứng, không mặc định là đúng.

## H1

Các signal như:

```text
SigLIP top-1
SigLIP top-2
score margin
score distribution
candidate count
download success ratio
```

có khả năng giúp phân biệt output tốt và output kém.

## H2

Adaptive recovery có thể tăng semantic success rate so với chỉ retry/search lại theo fixed rule.

## H3

Không phải mọi vocabulary item đều cần cùng số candidate.

Adaptive candidate budget có thể:

```text
easy word  → fewer candidates
hard word  → more candidates
```

và giảm average cost.

---

# 6. Ground truth — phần bắt buộc

Đây là foundation của toàn bộ research.

Không được dùng SigLIP làm cả:

```text
selector
+
ground truth
```

Nếu làm vậy sẽ circular evaluation.

---

# 7. Vocabulary benchmark

## 7.1. Bắt đầu nhỏ

Khuyến nghị giai đoạn đầu:

```text
100 vocabulary items
```

Sau khi pipeline evaluation ổn mới tăng.

---

## 7.2. Mỗi item cần intended sense

Không chỉ:

```text
bank
```

Mà cần:

```yaml
word: bank
target_sense: financial institution
definition: an organization that holds and lends money
```

Ví dụ:

```yaml
word: bat
target_sense: animal
definition: a flying nocturnal mammal
```

Target sense phục vụ **ground truth**.

Không bắt buộc baseline Qwen phải nhìn thấy definition.

---

## 7.3. Chia difficulty

Có thể chia benchmark thành:

```text
easy
ambiguous
abstract / difficult
```

Ví dụ:

### Easy

```text
apple
dog
car
chair
```

### Ambiguous

```text
bank
bat
ring
spring
date
light
```

### Difficult

Những từ:

- khó search bằng ảnh;
- abstraction cao;
- có nhiều visual interpretation.

---

# 8. Human evaluation

Output cuối cùng cần được đánh giá độc lập.

Rubric đơn giản:

```text
2 = correct and visually clear
1 = related but ambiguous / weak
0 = wrong
```

## Nếu có thể

Hai evaluator đánh giá độc lập.

Sau đó:

```text
agreement
disagreement
final adjudication
```

Nếu chỉ có một evaluator thì phải ghi rõ limitation.

---

# 9. Benchmark modes

Cần tách hai mode.

## 9.1. Controlled benchmark

Mục tiêu:

> reproducibility

Lưu:

```text
query
search metadata
candidate URL
candidate image
timestamp
provider
```

Nếu có thể cache candidate images.

Các approach được chạy trên cùng candidate context khi experiment yêu cầu fairness.

---

## 9.2. Live-world evaluation

Chạy với:

```text
real DuckDuckGo
```

Mục tiêu:

> xem system hoạt động thế nào ngoài môi trường controlled.

Không dùng live search duy nhất để kết luận method A tốt hơn method B nếu candidate pool khác nhau quá nhiều.

---

# 10. Baseline A — Current Product Pipeline

Đây là baseline đã freeze trước research.

```text
Qwen
 ↓
DDG
 ↓
N = fixed
 ↓
download
 ↓
validate
 ↓
SigLIP
 ↓
top-1
 ↓
save
```

Ví dụ:

```text
N = 10
```

Không semantic recovery.

---

# 11. Baseline B — Fixed Rule Recovery

Thêm rule đơn giản.

Ví dụ:

```text
timeout
→ retry

404
→ skip

invalid image
→ discard

too few valid images
→ search again

quality below threshold
→ search again
```

Mục tiêu:

> chứng minh proposed system có tốt hơn một giải pháp đơn giản hay không.

Không được so proposed system chỉ với baseline quá yếu.

---

# 12. Proposed System

Kiến trúc mục tiêu:

```text
                        word
                         │
                         ▼
                   Qwen3-1.7B
                         │
                         ▼
                  semantic query
                         │
                         ▼
                    DDG Search
                         │
                         ▼
                Adaptive Candidate
                      Budget
                         │
                         ▼
               Download + Validate
                         │
                         ▼
                      SigLIP
                         │
                         ▼
                Quality Telemetry
                         │
                         ▼
                 Quality Detector
                   /           \
                  /             \
              GOOD             UNCERTAIN
               │                   │
               ▼                   ▼
             ACCEPT         Recovery Controller
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              MORE CANDIDATES  SEARCH AGAIN  REGENERATE QUERY
                    │              │              │
                    └──────────────┴──────────────┘
                                   │
                                   ▼
                                 RETRY
```

---

# 13. Quality telemetry

Không thu thập mọi thứ chỉ vì có thể.

Ưu tiên signal có liên quan trực tiếp.

---

## 13.1. Query signals

Ví dụ:

```text
word length
query length
query generation latency
query regeneration count
```

Nếu có feature semantic/query difficulty sau này thì thêm.

---

## 13.2. Search signals

```text
number of search results
duplicate ratio nếu có
search latency
provider error
```

---

## 13.3. Download signals

```text
requested candidates
successful downloads
failed downloads
download success ratio
bytes downloaded
download latency
```

---

## 13.4. SigLIP signals

Đây là nhóm quan trọng.

```text
top-1 score
top-2 score
top-1 - top-2 margin
mean score
median score
score variance
full score distribution nếu cần
```

Ví dụ:

```text
case A

0.82
0.51
0.45

margin = 0.31
```

so với:

```text
case B

0.48
0.47
0.46

margin = 0.01
```

Case B có thể là retrieval uncertainty cao hơn.

Đây là hypothesis cần test, không mặc định là chân lý.

---

# 14. Quality Detector v0 — Rule based

Không bắt đầu bằng LLM.

Ví dụ conceptual:

```python
if top1 >= T1 and margin >= T2:
    ACCEPT
else:
    UNCERTAIN
```

Threshold phải học/tune từ development split.

Không tune trên test set.

---

# 15. Quality Detector v1 — Lightweight model

Sau khi rule baseline có kết quả, có thể thử:

```text
logistic regression
small tree model
small MLP
```

Input:

```text
top1
top2
margin
variance
download success ratio
candidate count
...
```

Output:

```text
probability of semantic success
```

Mục tiêu:

> xem ML đơn giản có tốt hơn rule hay không.

---

# 16. LLM-based detector — chỉ thử nếu có lý do

Không mặc định Qwen/LLM là detector tốt nhất.

Chỉ thử nếu:

- rule/model nhỏ không đủ;
- có evidence text hữu ích;
- chi phí inference chấp nhận được.

Nếu không:

```text
do not add LLM
```

---

# 17. Adaptive Candidate Budget

Đây là một hướng nghiên cứu chính.

## Fixed baseline

```text
every word
→ N = 10
```

## Adaptive version

```text
word
 ↓
query
 ↓
N = 3
 ↓
download
 ↓
SigLIP
 ↓
confident?
 /       \
yes       no
 │         │
accept    +K candidates
             │
             ▼
          re-score
             │
          confident?
          /       \
        yes        no
         │          │
       accept   recovery
```

---

# 18. Candidate budget policy

Version đơn giản:

```text
initial N = 3
increment K = 3
max N = 10
```

Đây chỉ là ví dụ.

Các giá trị phải được test.

---

# 19. Recovery Controller

Controller phải restricted.

Allowed actions:

```text
ACCEPT
RETRY_DOWNLOAD
GET_MORE_CANDIDATES
SEARCH_AGAIN
REGENERATE_QUERY
SKIP
```

Không cho controller:

```text
edit source code
run arbitrary shell
restart arbitrary service
delete files
change system config
```

---

# 20. Recovery policy v0 — Rules

Ví dụ:

```text
download ratio too low
→ retry / search again

SigLIP uncertain
and N < max
→ get more candidates

SigLIP uncertain
and N == max
→ regenerate query

regeneration limit reached
→ skip / accept best with low-confidence flag
```

---

# 21. Recovery policy v1 — Learned policy

Chỉ thử sau khi rule policy có baseline.

Có thể dùng classifier:

```text
state
→ recommended action
```

Nhưng cần dataset/action labels đủ tốt.

Nếu không có dataset phù hợp thì không ép dùng ML.

---

# 22. Query regeneration

Nếu quality thấp:

```text
original word
      ↓
Qwen
      ↓
query v1
      ↓
poor retrieval
      ↓
regenerate
      ↓
query v2
```

Quan trọng:

- [ ] Không để regeneration echo bad query vô hạn.
- [ ] Có max attempts.
- [ ] Log từng query version.
- [ ] Final metadata phải biết winner đến từ query nào.

---

# 23. Semantic failure taxonomy

Tạo taxonomy rõ.

## Class A — Query drift

```text
word sense
↓
wrong semantic query
```

## Class B — Search failure

```text
query correct
↓
candidate pool poor
```

## Class C — Ranking failure

```text
good candidate exists
↓
SigLIP selects wrong candidate
```

## Class D — Ambiguous target

```text
ground truth itself unclear
```

Class D không nên bị tính giống system error bình thường.

---

# 24. Operational failure taxonomy

Song song:

```text
timeout
HTTP error
invalid image
corrupt file
model error
resource error
filesystem error
```

Operational failure xử lý bằng deterministic code trước.

Không cần dùng AI cho vấn đề đã rõ.

---

# 25. Metrics

## 25.1. Primary quality metric

Human semantic score.

Có thể tính:

```text
semantic accuracy
```

Ví dụ:

```text
success = score 2
```

hoặc report cả distribution:

```text
% score 2
% score 1
% score 0
```

---

## 25.2. Detection metrics

Nếu detector dự đoán:

```text
GOOD / BAD
```

đo:

```text
precision
recall
F1
false accept rate
false recovery rate
```

Đặc biệt quan trọng:

### False Accept

```text
bad image
→ detector says GOOD
```

Đây là failure nguy hiểm.

---

## 25.3. Efficiency metrics

```text
images downloaded / word
bytes downloaded / word
SigLIP inference count
Qwen calls / word
wall-clock time
search calls / word
recovery actions / word
```

---

## 25.4. Reliability metrics

```text
successful final outputs
skipped items
hard failure rate
recovery success rate
```

---

# 26. Main experiment

So sánh ít nhất:

```text
A = Fixed N, no semantic recovery

B = Fixed N + fixed-rule recovery

C = Adaptive candidate budget + quality-aware recovery
```

Cùng benchmark.

Report:

```text
semantic quality
cost
latency
recovery
```

Không chỉ report accuracy.

---

# 27. Example experiment table

| Method | Semantic success | Downloads/word | Qwen calls | Latency | Recovery success |
|---|---:|---:|---:|---:|---:|
| A | ... | ... | ... | ... | N/A |
| B | ... | ... | ... | ... | ... |
| C | ... | ... | ... | ... | ... |

Không điền số trước khi chạy thật.

---

# 28. Ablation experiments

Sau main experiment, nếu còn thời gian.

## A1 — Remove score margin

Detector dùng:

```text
top1
```

thay vì:

```text
top1 + margin
```

Xem margin có thực sự hữu ích không.

---

## A2 — Fixed candidate vs adaptive candidate

```text
N=10
vs
N=3→6→10
```

---

## A3 — No query regeneration

Xem contribution của regeneration.

---

## A4 — No recovery

Xem recovery đóng góp bao nhiêu.

---

# 29. Threshold tuning protocol

Không được:

```text
test set
→ tune threshold
→ report same test set
```

Nên chia:

```text
train/dev/test
```

Hoặc nếu dataset nhỏ:

```text
development
test
```

Rule threshold tune trên development.

Final report trên test.

---

# 30. Controlled fault injection

Chỉ dùng fault injection cho operational side nếu muốn đo reliability.

Ví dụ:

```text
forced timeout
dead URL
invalid bytes
slow response
```

Không giả vờ những fault này là semantic failure.

Semantic failure cần benchmark riêng.

---

# 31. Reproducibility

Mỗi experiment lưu:

```text
experiment_id
timestamp
git commit
config
candidate budget
thresholds
model versions
queries
search snapshot
result
human label
```

Nếu có randomness:

```text
seed
```

---

# 32. Experiment artifact structure

Gợi ý:

```text
research/
├── benchmark/
│   ├── vocabulary.json
│   ├── labels/
│   └── snapshots/
│
├── configs/
│   ├── baseline_a.yaml
│   ├── baseline_b.yaml
│   └── proposed.yaml
│
├── runs/
│   └── <experiment_id>/
│       ├── config.json
│       ├── results.json
│       ├── telemetry.jsonl
│       └── outputs/
│
├── analysis/
│   ├── metrics.py
│   └── plots.py
│
└── README.md
```

---

# 33. Metadata research schema

Final output metadata nên mở rộng.

Ví dụ:

```json
{
  "word": "ring",
  "target_sense": "jewelry",
  "query_history": [
    "ring jewelry object",
    "ring finger jewelry"
  ],
  "search_calls": 2,
  "candidate_budget": 6,
  "download_success": 5,
  "siglip_top1": 0.72,
  "siglip_top2": 0.52,
  "siglip_margin": 0.20,
  "recovery_actions": [
    "GET_MORE_CANDIDATES"
  ],
  "final_action": "ACCEPT",
  "human_label": 2
}
```

Ground-truth fields và runtime fields cần phân biệt rõ.

---

# 34. OpenTelemetry — optional instrumentation

Chỉ thêm sau khi research pipeline đã rõ.

Trace conceptual:

```text
collect_image(word)
│
├── qwen.generate
│
├── ddg.search
│
├── download.batch
│
├── validate
│
├── siglip.rank
│
├── quality.detect
│
├── recovery.decide
│
└── normalize
```

OpenTelemetry giúp:

```text
observe execution
```

nhưng không tự tạo contribution.

---

# 35. Dashboard — optional

Nếu cần demo:

```text
success rate
recovery rate
average downloads
average latency
semantic quality
```

Có thể dùng Grafana hoặc custom dashboard.

Không bắt buộc cho core experiment.

---

# 36. Web/Game integration với research

Research layer không nên phá product layer.

Luồng nên là:

```text
Research pipeline
      ↓
produces better dataset
      ↓
same backend contract
      ↓
same web/game
```

Web/game không cần biết:

```text
candidate budget
SigLIP margin
recovery policy
```

trừ khi bạn cố tình làm admin/research dashboard.

---

# 37. Feature flag

Nên có mode:

```text
BASELINE
FIXED_RECOVERY
ADAPTIVE
```

Ví dụ config:

```yaml
retrieval_mode: adaptive
```

Mục tiêu:

- dễ benchmark;
- dễ rollback;
- web/game không đổi.

---

# 38. Research implementation phases

## R0 — Freeze Product v1

- [ ] tag product baseline.
- [ ] freeze API.
- [ ] freeze data schema cơ bản.
- [ ] lưu sample output.

---

## R1 — Build benchmark

- [ ] 100 words.
- [ ] target sense.
- [ ] difficulty group.
- [ ] evaluation rubric.
- [ ] snapshot protocol.

---

## R2 — Evaluate Baseline A

- [ ] run controlled benchmark.
- [ ] human label.
- [ ] measure semantic quality.
- [ ] measure cost.

---

## R3 — Implement telemetry schema

- [ ] top1.
- [ ] top2.
- [ ] margin.
- [ ] score distribution.
- [ ] download ratio.
- [ ] latency.
- [ ] candidate count.
- [ ] query count.

---

## R4 — Build Baseline B

- [ ] fixed rule recovery.
- [ ] rerun benchmark.
- [ ] human label.
- [ ] compare A vs B.

---

## R5 — Quality Detector v0

- [ ] rule detector.
- [ ] tune on development set.
- [ ] test detector.
- [ ] report false accept.

---

## R6 — Adaptive Candidate Budget

- [ ] initial N small.
- [ ] incremental candidates.
- [ ] max budget.
- [ ] track download savings.

---

## R7 — Recovery Controller

- [ ] restricted action set.
- [ ] query regeneration.
- [ ] search again.
- [ ] max attempts.
- [ ] skip policy.

---

## R8 — Proposed System evaluation

- [ ] run method C.
- [ ] human evaluate.
- [ ] compare A/B/C.
- [ ] quality-cost trade-off.

---

## R9 — Ablation

- [ ] margin off.
- [ ] adaptive budget off.
- [ ] regeneration off.
- [ ] recovery off.

Chỉ làm nếu main experiment đã hoàn chỉnh.

---

## R10 — Live-world evaluation

- [ ] run limited live DDG evaluation.
- [ ] record date/time/provider.
- [ ] compare behavior, không dùng thay controlled benchmark.

---

# 39. Decision gates

Sau mỗi phase cần tự hỏi:

## Gate 1

Quality detector có thực sự correlate với human label?

Nếu:

```text
NO
```

không xây controller dựa trên detector đó.

---

## Gate 2

Adaptive budget có giảm download?

Nếu:

```text
NO
```

kiểm tra threshold/budget policy.

---

## Gate 3

Recovery có tăng semantic success?

Nếu:

```text
NO
```

không được tuyên bố self-healing có lợi.

---

## Gate 4

Quality tăng nhưng cost quá lớn?

Report trade-off trung thực.

Không chỉ report metric tốt nhất.

---

# 40. Risk register

## Risk A — DuckDuckGo changes

Mitigation:

```text
controlled snapshot
+
live evaluation separate
```

---

## Risk B — Ground truth ambiguous

Mitigation:

```text
target sense
+
definition
+
remove unclear items
```

---

## Risk C — SigLIP score poorly calibrated

Mitigation:

```text
human label
+
margin/distribution
+
detector evaluation
```

---

## Risk D — Too few benchmark items

Mitigation:

Bắt đầu 100 để debug methodology.

Sau khi ổn mới mở rộng.

---

## Risk E — Overengineering

Dấu hiệu:

```text
spending more time on infra
than experiment
```

Mitigation:

Quay về 3 RQ.

---

## Risk F — Research leakage into product

Mitigation:

```text
feature flag
+
stable API
+
separate research config
```

---

# 41. Expected contribution

Nếu experiment support hypotheses, contribution có thể mô tả theo hướng:

```text
1. Semantic failure taxonomy
2. Quality telemetry for retrieval pipeline
3. Adaptive candidate budgeting
4. Restricted quality-aware recovery
5. Controlled benchmark methodology
6. Quality / reliability / cost evaluation
```

Không tuyên bố novelty lớn hơn evidence.

---

# 42. Expected final architecture

```text
                     Vocabulary
                         │
                         ▼
                   Qwen3-1.7B
                         │
                         ▼
                  Semantic Query
                         │
                         ▼
                 Search Provider
                         │
                         ▼
              Adaptive Candidate Budget
                         │
                         ▼
               Download + Validation
                         │
                         ▼
                      SigLIP
                         │
                         ▼
                  Quality Signals
                         │
                         ▼
                 Quality Detector
                   │           │
                 GOOD      UNCERTAIN
                   │           │
                   ▼           ▼
                ACCEPT   Recovery Controller
                             │
                 ┌───────────┼────────────┐
                 ▼           ▼            ▼
               MORE        SEARCH       QUERY
            CANDIDATES      AGAIN       REWRITE
                 │           │            │
                 └───────────┴────────────┘
                             │
                             ▼
                           RETRY
```

---

# 43. Final research checklist

```text
[ ] Product v1 frozen
[ ] Benchmark defined
[ ] Target sense available
[ ] Human evaluation rubric defined
[ ] Controlled snapshot created
[ ] Baseline A evaluated
[ ] Baseline B evaluated
[ ] Quality telemetry collected
[ ] Quality detector evaluated
[ ] Adaptive budget implemented
[ ] Recovery controller implemented
[ ] Proposed system evaluated
[ ] A/B/C compared
[ ] Cost measured
[ ] Semantic quality measured
[ ] Reliability measured
[ ] Ablation completed if time allows
[ ] Live evaluation completed
[ ] Limitations documented
[ ] Research report written
```

---

# 44. Mental model cuối cùng

Không phải:

```text
add AI everywhere
```

Mà là:

```text
         OUTPUT EXISTS
              │
              ▼
      Is it actually good?
          /          \
        yes           no
         │             │
       accept     Why uncertain?
                       │
                       ▼
              Cheapest useful action
                       │
                       ▼
                    retry
                       │
                       ▼
                   verify again
```

Câu hỏi cốt lõi của research:

> **Làm thế nào để pipeline nhận biết “sống nhưng sai”, phục hồi có kiểm soát, và chỉ tiêu thêm tài nguyên khi thật sự cần?**

Đó là trục chính cần giữ xuyên suốt toàn bộ giai đoạn nâng cấp.
