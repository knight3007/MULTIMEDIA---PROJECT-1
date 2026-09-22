# DDG image pipeline tasks

## Task 1: Add regression tests

**Description:** Cover the required DDG boundary and image lifecycle before changing runtime code.

**Acceptance criteria:**
- [x] Generated Qwen query is the exact DDG query and metadata search query.
- [x] Failed candidates are skipped while valid candidates continue.
- [x] Only the winner receives final JPEG normalization.

**Verification:**
- [x] Focused unittest run demonstrates the current normalization gap.

**Dependencies:** None

**Files likely touched:**
- `collect data script/test_collectors.py`

**Estimated scope:** Small

## Task 2: Normalize only the selected candidate

**Description:** Preserve validated downloaded candidates for SigLIP and normalize the winner once for final output.

**Acceptance criteria:**
- [x] Candidates are decoded and validated without flashcard normalization.
- [x] Winner is EXIF-transposed, RGB, JPEG quality 90, max 1024x1024, no crop/upscale.
- [x] Existing DDG retries, SigLIP ranking, metadata, and cache behavior remain active.

**Verification:**
- [x] Focused tests pass.
- [x] Full collector unittest suite passes.

**Dependencies:** Task 1

**Files likely touched:**
- `collect data script/imagecollector.py`
- `collect data script/test_collectors.py`

**Estimated scope:** Medium

## Checkpoint: Offline integration
- [x] All unit tests pass.
- [x] `query_generator.py` and `image_scorer.py` have no diff.

## Task 3: Verify dependencies, command, and live pipeline

**Description:** Confirm `ddgs`, the saved CLI command, DDG connectivity, and a three-word real pipeline run.

**Acceptance criteria:**
- [x] `requirements.txt` uses `ddgs`, not `duckduckgo_search`.
- [x] `comand.txt` invokes the current Qwen-DDG-SigLIP collector CLI.
- [x] Live smoke outputs are inspected and reported truthfully.

**Verification:**
- [x] `test_ddg.py` returns image URLs.
- [x] Three-word collector smoke test runs with isolated cache/output.

**Dependencies:** Task 2

**Files likely touched:**
- `requirements.txt`
- `comand.txt`

**Estimated scope:** Small

## Checkpoint: Complete
- [x] Full acceptance criteria and Definition of Done are satisfied.
