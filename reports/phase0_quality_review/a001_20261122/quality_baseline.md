# A-001.1 quality baseline — preliminary v1

**Run:** `a001_20261122`; **frozen source:** `evaluation_matrix.json` SHA-256 `0e066ed052f07ca7de59a8b75a723aaba9ca89be364c6c2827785b1577b23e5f`; `statistics.json` SHA-256 `8d3dc38378011a8af33fca06a11449d1a2a29db3e775e17e650c75854dd048a8`; `owner_audio_acceptance.json` SHA-256 `c290fe57f3323d72d0306fb79a22675f11de9ee77fdb8d536cdfaa3b69f6acad`. This version is [preliminary_unverified_baseline_v1.csv](preliminary_unverified_baseline_v1.csv). The original A-001 matrix and reports are preserved unchanged.

The CSV records all 100 ordered stable IDs and trilingual terms, explicit target sense or `UNRESOLVED`, original Qwen query, effective image query, model/prompt evidence, exact revision when available, AI query and image judgments, separate human query/image statuses, selected image/audio references and SHA-256, technical validity, owner audio acceptance, failure categories, missing evidence and reviewer fields. An unresolved target sense is **not** silently inferred from the English word. Path references are repository-local evidence, not publication URLs.

| Measure, N=100 | PASS | FAIL | NEEDS_REVIEW | UNKNOWN | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Query correct meaning | 75 | 16 | 9 | 0 | AI preliminary |
| Query all six checks | 37 | 22 | 41 | 0 | AI preliminary; 37/59 PASS among PASS+FAIL only |
| Image relevance | 44 | 27 | 28 | 1 | AI preliminary; 1 missing image |
| Image visual quality | 39 | 47 | 13 | 1 | AI preliminary |
| Image learning suitability | 27 | 55 | 17 | 1 | AI preliminary; 27/82 PASS among PASS+FAIL only |
| Image technical integrity | 99 | 0 | 0 | 1 | File checks, not semantic approval |
| Audio technical integrity | 100 | 0 | 0 | 0 | File checks |
| Audio owner acceptance | 100 | 0 | 0 | 0 | Owner batch decision; no agent listening |

**Human query/image verified:** 0/100 IDs; 100 remain awaiting both decisions. `PASS` for technical validity, AI semantic correctness, educational suitability and human verification are distinct fields. Do not report AI PASS or PASS/(PASS+FAIL) as final model accuracy. A future comparison should retain this run's IDs, intended meanings, original query and exact asset hashes; collect human labels without overwriting AI fields, then report changed/missing assets separately.

**Limits:** 94 accepted raw decoded Qwen outputs, exact historical model revisions, and full candidate URLs/bytes/score order for 98 applicable search-selected assets are missing. ID009 is curated direct; ID038 stopped at an input approval gate. Historical collection mixed prompts, caches and human overrides, so this is a traceable observed-output baseline, not a controlled model benchmark. Public distribution eligibility and image rights are separate from these quality statistics.
