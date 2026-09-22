# Implementation Plan: Complete DDG image pipeline

## Overview
Finish the existing partial DuckDuckGo integration without changing Qwen or SigLIP. The collector must pass generated Qwen queries unchanged to DDG and SigLIP, rank validated source candidates, normalize only the selected image, and persist accurate metadata.

## Architecture Decisions
- Reuse the existing `search_images`, retry policy, candidate cache, and CLI instead of adding a provider abstraction.
- Store validated candidate source bytes in their decoded format for SigLIP; apply EXIF transpose, RGB conversion, thumbnail sizing, and JPEG encoding only to the winner.
- Keep `query_generator.py` and `image_scorer.py` unchanged.

## Task List

### Phase 1: Regression coverage
- [x] Add focused tests for Qwen-output to DDG wiring, DDG failure handling, candidate continuation, winner-only normalization, and cache behavior.

### Checkpoint: Tests prove the gaps
- [x] New focused tests fail for the missing normalization behavior.
- [x] Existing test suite baseline is recorded.

### Phase 2: Minimal runtime change
- [x] Change candidate validation/storage and final winner normalization in `imagecollector.py` only.
- [x] Keep DDG configuration, page size, metadata, Qwen, and SigLIP behavior intact.

### Checkpoint: Runtime integration
- [x] Full unit suite passes.
- [x] No Openverse runtime code remains.

### Phase 3: Live verification
- [x] Run `test_ddg.py` connectivity smoke test.
- [x] Run a real three-word Qwen to DDG to SigLIP smoke test with isolated output/cache.
- [x] Confirm the saved production command exercises the complete pipeline.

### Checkpoint: Complete
- [x] Final images are RGB JPEG, at most 1024x1024, without crop or upscale.
- [x] Smoke-test metrics and any external failures are reported accurately.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Candidate source formats need filename extensions for Pillow/SigLIP | Medium | Validate with Pillow and save the original response bytes using the decoded format's extension. |
| Network or local model availability blocks live smoke tests | High | Run offline unit tests first, then report the precise external failure without claiming PASS. |
| Existing user data is overwritten | High | Use temporary output/cache paths for smoke testing; never delete the current dataset. |

## Open Questions
- None; the supplied specification resolves provider, query, ranking, normalization, and metadata behavior.
