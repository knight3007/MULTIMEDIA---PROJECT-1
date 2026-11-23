# Current tasks

This is the authoritative current task list. Historical DDG tasks in `tasks/plan.md` and `tasks/todo.md` remain complete and unchanged. Status vocabulary: TODO, IN_PROGRESS, BLOCKED, DONE, NEEDS_REVIEW, PARTIAL. DONE requires verified acceptance; dependencies do not grant execution authority. A-004R's 100-ID experimental routing/execution and review package are DONE with 26 explicit query blockers and owner image decisions pending. A-004 remains the historical default-query baseline. A-001.1 quality-baseline preparation, B-002 importer and B-003.1 offline adapter are complete; parent A-001 still needs human query/image review. B-003.2 live processing is paused. Web Game and Game UX/UI remain undecided (D-014). No automatic inference, implementation or deployment.

## PIPELINE-V2 — Optimise the image pipeline from the owner-approved selection

- Priority/status: P0 / DONE — **FROZEN as is** by owner decision D-021 on 2026-11-23, with known limitations accepted. Owner: Claude Code session, `main`.
- Inputs: the final selection `reports/image_pipeline_experiments/A004R_FINAL_SELECTION/` (finalize.py; 100/100 PASS; strategies: Qwen default 58, descriptive icon 21, `<word> icon` 10, scene 10, curated 1).
- Code:
  - New: `collect data script/visual_query_policy.py`, `image_pipeline_v2.py`, `test_image_pipeline_v2.py` (13 tests).
  - New data: `data/vocabulary/approved_images_v1.json` (100 entries; not read by dataset_builder).
  - Spec: `docs/IMAGE_PIPELINE_V2.md`.
  - `query_generator.py` is unchanged (its hash is pinned by historical benchmarks).
- Validation (`reports/image_pipeline_experiments/PIPELINE_V2_VALIDATION/`): expected routes were frozen before inference. Iteration 3 results: PHOTO 44/44, NON_PHOTO 34/35, CURATE 1/1, valid 99/100 (rain) → NOT PASSED; the 3-iteration budget is used.
- Known issues: example copying (beautiful, password and impossible got "family on beach vacation"; always and sometimes share a query; where and why share a query) and weak or wrong senses for sleep, understand, dangerous and important.
- Tests: collector suite and kaggle_batch suite.
- Freeze: `reports/image_pipeline_experiments/PIPELINE_V2_VALIDATION/freeze_manifest.json` (status FROZEN), guarded by `FreezeTests`. The frozen prompt SHA equals the one validated in iteration 3.
- Next: wiring v2 into Excel imports (B-003.2), production promotion and public release each need separate instruction.

## A-004R-FU — Owner follow-up on A-004R review export

- Priority/status: P0 / DONE. The owner exported `A004R-followup-review-2026-11-23.json` (reviewer HD); it was validated and consolidated into the A004R_FINAL_SELECTION manifest (100/100 PASS images). Codex root wrote the plan and ran the first pass; the Claude Code session reviewed it, fixed it and completed it on 2026-11-23. No active write claim.
- Input: owner export `D:/Download/A004R-review-2026-11-23.json` (reviewer HD), copied to `reports/image_pipeline_experiments/A004R_OWNER_FOLLOWUP_100/owner_review_export.json`.
- Plan: 67 fixed (owner PASS, A001 by owner note including the 066 amendment, A-003 owner decisions, `because` internal-only) and 33 open (owner FAIL, UNREVIEWED, conflicting or "can use icon" notes) with SCENE/ICON queries.
- Results:
  - 41 search attempts (34 + 3 timeout retries + 4 audited query repairs); 229 valid candidates in the current results; every open item RANKED.
  - The gallery also shows the A-001 reference, the earlier owner reference and the valid A-004R candidates.
- Output: `reports/image_pipeline_experiments/A004R_OWNER_FOLLOWUP_100/review_gallery.html` (Export JSON). Verification: [record](history/2026-11-23_A004R_FOLLOWUP_verification.md); follow-up tests 8 OK, collector 184 OK.
- Remaining: the owner reviews the 33 open cards and exports JSON. A separate task consolidates the final selection. No production promotion; rights are unknown.

## A-004R — Isolated conditional-query 100-word experiment

- Priority/status: P0 / DONE for frozen routing and every eligible automated attempt; 26 semantic query blockers and owner review remain explicit. Owner: Codex root on `main`/`936d9fdd27810e50a144fb6399e647b1ba18c371`; no active write claim after checkpoint.
- Scope: repair experimental routing only. A-004 baseline, canonical dataset, A-003 owner decisions and internal override stay unchanged. No production integration, B-003.2, Game UX/UI, commit or push.
- [Integration audit](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/integration_status_report.md), [routing matrix](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/routing_matrix.csv), [routing preview](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/routing_preview.md), [manifest](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/experiment_manifest.json), [retrieval ledger](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/retrieval_results.json), [rankings](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/candidate_rankings.csv), [evaluation matrix](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/evaluation_matrix.csv), [report](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/evaluation_report.md), [gallery](../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/review_gallery.html).
- 100 unique frozen IDs in 10 batches: 62 NORMAL, 10 ICON, 28 SPECIAL_REVIEW. Actual: nine new searches/rankings (six ICON, three NORMAL), 57 A-004 reused results with provenance, six exact owner references, 26 BLOCKED_QUERY, one NO_SUITABLE_IMAGE, one INTERNAL_ONLY_TEMPORARY. New search produced 61 candidate records, 56 valid pairs; all new proposals remain NOT_REVIEWED/NOT_PROMOTED.
- Acceptance evidence: [verification](history/2026-11-23_A004R_verification.md). Frozen source/hash checks, owner references, FIX-001, top ranks and 449 ranking rows verified. Focused 5 tests, collector 174, Kaggle 19 OK; canonical vocabulary 100 rows/zero structural issues and SHA unchanged. Browser gallery 100 cards/9-new filter and no console errors. Preliminary educational quality of nine new tops: five PASS, two NEEDS_REVIEW, two FAIL; no dataset-wide improvement claim.
- Gallery usability follow-up DONE: all valid candidate images are now visible as selectable thumbnails, with the selected image synchronized to the existing JSON export field. The owner-reported text-only candidate list was insufficient for visual choice. [Verification](history/2026-11-23_A004R_gallery_fix.md); no search, scoring or selection manifest changed.
- Next action requires separate instruction: owner reviews gallery/exports JSON; address 26 query blockers by semantic decisions before another retrieval run. Existing five A-003 unreviewed holdouts stay unapproved. B-003.2 and production conditional routing do not start automatically.

## CTX-001 — Persistent context and handoff

- Priority/status: P0 / DONE. Owner: Codex root, completed context-setup session; root `D:/MULTIMEDIA - PROJECT 1`, branch `main`; no active write claim remains.
- Dependencies: existing scope/reports and Git checkpoint.
- Files: `AGENTS.md`, `docs/agent/*.md`, `docs/agent/history/`.
- Acceptance: required seven files exist; confirmed/proposed status is clear; historical work preserved; fresh agent locates next work and gates without whole repo reread.
- Verification: local link/required-field/line-count checks, baseline document hashes, fresh-context read-only dry run; no application tests required for docs-only change.
- Evidence/output: [HANDOFF](HANDOFF.md), [setup baseline](history/2026-11-22_context_setup_baseline.json), [verification and dry run PASS](history/2026-11-22_context_setup_verification.md), 22/11/2026.

## REVIEW-001 — Initial 100-ID evidence triage

- Priority/status: P0 / DONE (initial inventory only, not final model evaluation). Owner: previous Codex session.
- Dependencies: existing query/image audit and full staging inventory.
- Files/output: [initial findings](../../reports/phase0_quality_review/02_initial_quality_findings.md), [100-ID CSV](../../reports/phase0_quality_review/03_existing_evidence_100.csv), input hashes beside them.
- Acceptance verified: 100 unique IDs joined; 2 confirmed/5 inferred concerns marked; 93 unknown; license isolated from quality; source reports retained.
- Verification: prior session parsed CSV, checked counts 100/7/93 and input hashes; see findings and handoff. No new media viewing/listening or inference was performed.

## A-001 — Comprehensive existing-output review of 100 IDs

- Priority/status: P0 / NEEDS_REVIEW. First verifiable evaluation round/package complete; final human-verified query/image quality pending. Owner: Codex root completed initial round, main/936d9fdd27810e50a144fb6399e647b1ba18c371; root D:/MULTIMEDIA - PROJECT 1. No active write claim remains. Audio accepted PASS for all 100 by user; no listening re-review required.
- Dependencies: REVIEW-001; use owner decisions for ambiguous meanings. Final independent certification needs bilingual reviewer, but desk review can progress with explicit uncertainty.
- Relevant files: phase0 rubric/100-ID CSV; `data/vocabulary/semantic_decisions_v1.json`; original query ledger routed by INDEX. Read source only if tracing provenance.
- Acceptance: all 100 IDs have reasoned review per dimension, raw vs human override distinguished; pass/fail/unknown totals use denominator 100; uncertain meanings stay explicit; no license criterion in quality score.
- Verification: count unique IDs, reference/hash consistency, review rationale and independent labels where available. No re-inference to fill missing evidence.
- Output/evidence: [summary](../../reports/phase0_quality_review/a001_20261122/01_evaluation_summary.md), [matrix](../../reports/phase0_quality_review/a001_20261122/evaluation_matrix.csv), [gallery](../../reports/phase0_quality_review/a001_20261122/review_gallery.html), [verification](../../reports/phase0_quality_review/a001_20261122/verification.md). All 100 reconstructed with six query dimensions, actual image observations (99 selected), attribution and missing evidence. Composite query 37/22/41/0 and image learning 27/55/17/1 (PASS/FAIL/NEEDS_REVIEW/UNKNOWN) are preliminary; not model accuracy. Audio technical 100 PASS and owner batch acceptance 100 PASS. Local gallery/browser and artifact checks PASS; no inference/download or pipeline mutation. Final query/image labels remain unapproved; no DONE claim for full independent evaluation.

## A-001.1 — Human review consolidation and quality baseline

- Priority/status: P0 / DONE for preparation, not final human verification. Owner: Codex root on main/936d9fdd27810e50a144fb6399e647b1ba18c371; no active write claim after checkpoint.
- Dependencies: saved A-001 matrix, statistics, audio owner acceptance and gallery. No human gallery JSON export found in repository; 0/100 IDs human-reviewed for query/image and 100 await review. Do not infer labels from browser localStorage or test screenshots.
- Acceptance verified: all 100 stable IDs in a versioned preliminary/unverified CSV and P1/P2/P3 queue; AI vs human, technical vs semantic/educational and public rights separated; source hashes/basis recorded; failure categories and missing evidence preserved; owner audio PASS 100; UX/UI freeze D-014 persisted. Original evaluation unchanged.
- Output: [human status](../../reports/phase0_quality_review/a001_20261122/human_review_status.md), [priority queue](../../reports/phase0_quality_review/a001_20261122/review_priority_queue.csv), [quality baseline](../../reports/phase0_quality_review/a001_20261122/quality_baseline.md), [preliminary CSV](../../reports/phase0_quality_review/a001_20261122/preliminary_unverified_baseline_v1.csv), [A-002 candidates](../../reports/phase0_quality_review/a001_20261122/a002_improvement_candidates.md), [summary](../../reports/phase0_quality_review/a001_20261122/a001_1_completion_summary.md), [verification](history/2026-11-22_A001_1_verification.md). Queue P1 59/P2 19/P3 22. No A-002/B-002 started.

## A-002 — Diagnose image failures by stage

- Priority/status: P0 / TODO. Owner: unassigned.
- Dependencies: A-001 for affected meanings; known cases can be inspected earlier. Missing candidate/score history blocks only definitive attribution, not all investigation.
- Relevant files: image lineage/quality CSVs in audit directory, relevant staging manifest/metadata/hash, `imagecollector.py`, `image_scorer.py` if required.
- Acceptance: distinguish Qwen, search, download/mapping, ranking and unresolved cases; no blame assignment without supporting candidates/scores; visual quality separate from rights.
- Verification: inspect saved files/contact sheets per ID, map exact query/source/hash; mark unavailable evidence UNKNOWN.
- Output: new diagnosis report in `reports/phase0_quality_review/`; no image mutation or new requests.

## A-002-PILOT — Icon retrieval on 20 difficult items

- Priority/status: P0 / NEEDS_REVIEW. The automated stages are complete and verified; the human A/B decision is pending.
- Ownership: retrieval was run by the Codex root session (12:19–12:32 +07). The Claude Code session took over after that process exited and rendered and verified the review artifacts on `main` at HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. There is no active write claim.
- Authorization: latest owner task permits 20 real `english + " icon"` searches/downloads and existing SigLIP ranking if available. It does not authorize production optimization, broader 100-ID search, Game UX/UI/frontend, promotion or commit/push.
- Acceptance: exactly 20 hard current IDs selected; query isolated; bounded real retrieval with all candidates/source URLs/hashes/errors and original baseline references; separate A/B internal gallery and export; actual counts and unresolved human decision; preserve prior assets. If provider fails, keep valid partial output and report it.
- Output: `reports/image_pipeline_experiments/A002_ICON_PILOT_20/`
  - Files: manifest, selection CSV, `retrieval_results.json`, `comparison.csv`, `review_gallery.html`, `experiment_report.md`, `automated_visual_observations.md`, `run_pilot.py`, `render_pilot.py`, and `images/<vocab_id>/` holding 129 raw and 129 JPEG files.
  - IDs completed: 019, 041, 042, 043, 047, 048, 051, 053, 054, 055, 056, 058, 061, 062, 065, 075, 077, 078, 081, 082 (all 20). Pending or failed IDs: none. Failed candidate: `vocab-000078-07` (HTTP 403).
- Verification: [record](history/2026-11-22_A002_PILOT_verification.md).
  - Hashes: 258/258 match; 0 orphan files.
  - Gallery: 169/169 images load; export works.
  - Tests: collector suite 160 OK; vocabulary validation 0 issues.
  - Production: no files changed.
  - Deviations from production: timeout 12 s vs 20 s; retries 1/0 vs 2/2.
- Owner feedback (2026-11-22, qualitative only): icon search is "generally satisfactory" for the other tested words, but "because" is still unsuitable. This is not a per-item JSON review. Do not record it as 19 individual PASS labels.
- Remaining: a formal per-item export is still optional and absent. No permanent query strategy has been adopted. Do not expand to 100 IDs, change the production pipeline, or start A-003 or B-002 without a new instruction. "because" follow-up: A-002-CAUSAL.

## A-002-CAUSAL — Causal-concept visual pilot for "because"

- Priority/status: P0 / DONE for the pilot scope. Owner selected **V3_BEST, candidate V3-01** (same image as V2-01, SHA-256 `8dd3e8a2…d7ab`) by chat on 2026-11-22.
- No gallery export file exists: the agent's earlier export test had disabled downloads in the in-app tab the owner used. The decision is recorded in `owner_review_decision.json` from the chat message.
- Open issues on V3-01: printed CAUSE/EFFECT labels, an Adobe Stock watermark (rights not cleared), and cause→effect order. Not promoted; the production query strategy is unchanged.
- Ownership: the Claude Code session on `main` at HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No active write claim after the checkpoint.
- Authorization: live retrieval for `vocab-000081` (because / なぜなら / bởi vì) only.
  - At most 4 variants (V1 to V3 owner-specified; V4 agent-written and recorded before searching), at most 7 candidates each, with existing SigLIP and an optional fixed-text score.
  - Not authorized: Qwen, AI image generation, other words, changes to production prompts or routing, A-003, B-002, Game UX/UI, commit or push.
- Output: `reports/image_pipeline_experiments/A002_CAUSAL_CONCEPT_PILOT/`
  - Files: manifest, `query_variants.csv`, `retrieval_results.json`, `comparison.csv`, `review_gallery.html`, `experiment_report.md`, `run_causal.py`, `render_causal.py`, and `images/V1..V4/`.
  - Searches: 4/4 SUCCESS.
  - Downloads: 25/27 candidate records (V1-02 HTTP 400, V1-06 HTTP 403). V3-01 reused V2-01's identical URL, so there are 24 unique images (48 files).
  - SigLIP: query scores and fixed-text scores computed for all variants, plus fixed-text scores for the ORIGINAL image and the 7 ICON candidates.
  - SigLIP query-score picks: V1-05, V2-05, V3-01, V4-03.
  - Automated verdict (AI preliminary): `NO_SUITABLE_VISUAL_FOUND`. The closest are V2-01/V3-01 (explicit causality, but text and watermark) and V4-02/V4-03 (text-free, but the cause–result link is only implied).
- Verification: [record](history/2026-11-22_A002_CAUSAL_verification.md). Hashes 48/48; 0 orphans; gallery 38/38 images, 7 choices, export works. The A-001 matrix and icon-pilot results hashes are unchanged; no production file changed.
- Usage (D-015, owner, 2026-11-22): V3-01 may be used **temporarily, internally only**. No public use until its rights are cleared or it is replaced. It has not been copied into `data/` or a pack (that needs a separate step).
- Remaining: a cleaner replacement can be revisited later; other connectors are not piloted. Strategy options (manual curation, multi-panel effect-then-reason, contextual search) are listed only; none is adopted. Similar connectors (therefore, but, if…) are identified only; searching them needs new authorization.

## A-003 — Controlled evaluation of conditional image search

- Priority/status: P0 / NEEDS_REVIEW. Automated stages are complete and verified. Seven owner chat feedback statements were consolidated in A-003.1; only four include explicit A/B preferences, five items remain unreviewed, and there is no completed 12-item gallery export. Owner of original experiment: Claude Code session, `main` at `936d9fdd27810e50a144fb6399e647b1ba18c371`. No active write claim.
- Authorization: at most 12 paired NORMAL vs `<english> icon` comparisons on holdout IDs, existing SigLIP, no Qwen. Not authorized: production integration, B-002, Game UX/UI, commit or push.
- Sample: frozen before retrieval; no substitution.
  - CONCRETE: 001 apple, 011 cat, 016 mountain, 021 house, 028 car, 031 book.
  - ACTION: 057 eat, 059 buy, 063 receive.
  - ABSTRACT: 045 happy, 046 hungry, 083 sometimes.
  - Excluded: the 20 pilot IDs, 081, 086 (baseline query is already "why icon") and 038.
- Results:
  - Searches: 24/24 SUCCESS. Downloads: NORMAL 74/81, ICON 73/77. SigLIP ranked 24/24.
  - AI-preliminary preference on CONCRETE: BOTH_GOOD 3, ICON_BETTER 2 (house and book, caused by normal-query sense drift), NORMAL_BETTER 1 (car).
  - AI-preliminary preference on DIFFICULT: ICON_BETTER 2 (buy, hungry), NORMAL_BETTER 1 (eat, a name collision), BOTH_GOOD 1 (happy), BOTH_BAD 2 (receive, which was a ranking miss; sometimes).
  - Defect found: transparent images are flattened to black (ICON 29 transparent / 8 black; pilot selected 10/20).
- Recommendation (proposal):
  - Revise before integrating.
  - (a) Fix transparency compositing first.
  - (b) Owner reviews the 12 pairs.
  - (c) Consider a dual pool (normal + icon) with rejection rules and a human pick for flagged non-concrete words.
  - (d) Add a `NO_SUITABLE_IMAGE` outcome and keep the override path.
  - Concrete nouns keep normal queries, with query-sense fixes through semantic decisions.
- Output: `reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/` (manifest, frozen_sample.csv, retrieval_results.json, comparison_matrix.csv, review_gallery.html, evaluation_report.md, images/, run_a003.py, render_a003.py).
- Verification: [record](history/2026-11-22_A003_verification.md). Collector 160 OK, kaggle 19 OK, vocabulary 0 issues.
- Remaining: owner review for five other holdout items. The seven A-003.2 selective proposals are consolidated in A-003.3. B-002 importer was later authorized separately; do not integrate conditional search from this image experiment.

## A-003.1 — Human feedback consolidation and SigLIP ranking diagnosis

- Priority/status: P0 / DONE for diagnostic scope, 2026-11-23. Owner: Codex root on `main`/`936d9fd`; no active write claim after checkpoint. Authorization: existing A-003 candidates and focused offline SigLIP scoring only; no retrieval, production ranking change, dataset edit, promotion, commit or push.
- Output: [feedback](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/owner_feedback.json), [candidate table](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/candidate_diagnosis.csv), [score table](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/scoring_comparison.csv), [diagnosis](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/ranking_diagnosis.md), [recommendations](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/recommended_fixes.md), and reproducibility scripts/contact sheets.
- Acceptance verified: seven chat statements stored separately from AI assessments, four explicit preferences only; vocab-000083 spelling confirmed; 89 candidate records, 82 downloaded assets hashed and scored; seven pools visually inspected; query vs shared-meaning top-1/top-3 reported with source hashes; retrieval/ranking/query/composition/unknown separated. [Verification](history/2026-11-23_A003_1_verification.md): collector 162 OK, Kaggle 19 OK, vocabulary 0 structural issues, diagnostics validated. No original asset or production-data content change.
- Findings: suitable arm-level top-1 by analyst review is 4/14 with original query scoring and 6/14 with shared-meaning scoring. Shared meaning helps receive and book, but can still choose a construction chart for house, an Action shop for buy, and an unusable image for sometimes. No automatic production integration is justified. A-003 owner review remains open.

## A-003.2 — Selective image repair and owner approval

- Priority/status: P0 / DONE for the seven-item owner review, 2026-11-23. Preparation was previously verified; the owner supplied the exported decisions for A-003.3. Owner: Codex root on `main`/`936d9fd`; no active write claim after checkpoint. Authorized scope: seven owner-mentioned items, at most three new queries each for book/sometimes only, isolated report/gallery, no promotion, production edit, commit or push.
- Existing-candidate decisions: hungry ICON-01 and eat NORMAL-06 preserve explicit owner A/B preferences; receive ICON-07, buy ICON-01, house NORMAL-05 and book ICON-03 are review proposals. `sometimes` proposes `NO_SUITABLE_IMAGE`. None is marked approved for promotion.
- Retrieval: book 0 queries because clear ICON-03 exists. Sometimes 2 frozen queries (calendar activity; occasional rain/sunny days), both searches succeeded after initial sandbox timeouts; 14 candidates, 13 valid downloaded images, 1 download failure. The valid results do not clearly depict occasional frequency. No new model/SigLIP run.
- Output: [manifest](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/repair_manifest.json), [retrieval results](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/targeted_retrieval_results.json), [proposals](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/proposed_image_selections.csv), [gallery](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/review_gallery.html), [report](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/repair_report.md), scripts and inspection contact sheet.
- Verification: [record](history/2026-11-23_A003_2_verification.md). All referenced assets/13 new raw+JPEG pairs match hashes; proposal and source records pass focused assertions; collector offline suite exit 0, Kaggle 19 OK, vocabulary 0 structural issues, `git diff --check` clean. Static gallery checks pass; real browser preview was blocked by the browser tool's `file://` URL policy, so export interaction is not runtime-verified.
- Review result: six proposed images accepted for quality, and `sometimes` accepted as `NO_SUITABLE_IMAGE`; [A-003.3 manifest](../../reports/image_pipeline_experiments/A003_OWNER_DECISIONS/final_image_selection_manifest.json). Five other A-003 holdout items remain unreviewed. Game UX/UI remains UNDECIDED.

## A-003.3 — Consolidate owner decisions and close image experiments

- Priority/status: P0 / DONE for seven-item consolidation, 2026-11-23. Owner: Codex root on `main`/`936d9fd`; no active write claim after checkpoint. The owner supplied `D:/Download/A003-selective-repair-review.json`; its earlier absence is preserved in [historical search evidence](history/2026-11-23_A003_3_missing_export.md).
- Output: [final manifest](../../reports/image_pipeline_experiments/A003_OWNER_DECISIONS/final_image_selection_manifest.json), [candidate dispositions](../../reports/image_pipeline_experiments/A003_OWNER_DECISIONS/candidate_disposition.csv), [report](../../reports/image_pipeline_experiments/A003_OWNER_DECISIONS/consolidation_report.md), exact export copy and validation script. Six quality selections approved, one `NO_SUITABLE_IMAGE`, zero unresolved among seven. Four earlier explicitly rejected candidates remain distinct from 85 not individually reviewed and eight failed downloads.
- Verification: [record](history/2026-11-23_A003_3_verification.md). Export/proposal IDs, paths, URLs and raw/JPEG SHA-256 hashes validated. Canonical dataset content unchanged; D-015/D-016 `because` internal-only restriction checked. No retrieval, model change, production promotion, conditional-search integration, commit or push.
- Closure: the seven-item selective image experiment is closed. Parent A-003 still needs review of apple, cat, mountain, car and happy. B-002 importer was later authorized separately; Game UX/UI remains undecided by D-014. Do not treat image-quality selections as media approval for B-003 or public release.

## FIX-001 — Composite transparent images onto white

- Priority/status: P0 / DONE. Owner approved 2026-11-22 (D-017). Done by the Claude Code session on `main` at `936d9fdd27810e50a144fb6399e647b1ba18c371`; uncommitted.
- Files changed: `collect data script/image_scorer.py` (`flatten_to_rgb`, used in `score_batch`), `collect data script/imagecollector.py` (`normalize_image_to_jpeg`), and `collect data script/test_collectors.py` (+2 tests).
- Verification:
  - The new tests fail on the old code (black corners) and pass with the fix.
  - Collector suite 162 OK; kaggle_batch 19 OK; vocabulary validation 0 issues; `git diff --check` clean.
  - Offline re-check (`reports/image_pipeline_experiments/ALPHA_FIX_RECHECK/`): black squares A-003 8→0 and pilot 4→0. SigLIP selection changed in 4 A-003 icon arms and 2 pilot items; the new picks are not uniformly better.
- Not done: no data regeneration; existing experiment galleries are left as historical pre-fix evidence. Baked-in checkerboard images are not handled.

## B-001 — Specify Excel import and content pack

- Priority/status: P0 / DONE (contract/fixture design, not application implementation). Owner: Codex root, completed B-001 session on main at 936d9fdd27810e50a144fb6399e647b1ba18c371; root D:/MULTIMEDIA - PROJECT 1. No active write claim remains.
- Dependencies: D-002/D-003; proposed contract D-007. Does not require full 100-image rights audit or 100/100 model success.
- Relevant files: revised roadmap/Excel proposal, `docs/DATA_CONTRACT_V1.md`, `dataset_builder.py`, registry conventions.
- Acceptance: finalized proposed workbook/pack specification with examples, validation, import identity, separate quality/public eligibility, and test scenarios; clearly state approvals still needed. Documentation only; no parser/runtime.
- Verification: trace example Excel rows into pack records; check no benchmark-ID collisions or production-schema mutation.
- Output: [Excel v1](../contracts/excel_v1.md), [pack v1](../contracts/content_pack_v1.md), [integration](../contracts/integration_notes.md); [fixtures/checker](../../tests/fixtures/b001/README.md). Workbook rules/row errors/Unicode/duplicate/identity policy and state transitions specified. Fixture checks PASS: five workbooks, five item states, seven negative mutations, checksums, safe paths and 101-item shape. Historical source/data/report hashes unchanged; see [verification](history/2026-11-22_B001_verification.md). The Excel portion is implemented in B-002; runtime and independent AI quality review remain unimplemented.

## B-002 — Implement Excel Vocabulary Importer

- Priority/status: P1 / DONE, 2026-11-23. Owner: Codex root on `main`/`936d9fd`; no active write claim after checkpoint. The owner explicitly narrowed the prior vertical-slice plan to a backend/data-only importer (D-019). Game UX/UI is excluded.
- Dependencies: B-001 Excel v1 contract and synthetic fixtures. Standalone ZIP/XML parser uses Python standard library; no media or AI integration.
- Acceptance verified: five B-001 workbooks handled as expected; valid preview/accept/resume, clear row/field diagnostics, NFC/whitespace normalization, duplicate detection, physical row provenance, payload fingerprint and separate UUID identities. A synthetic 102-row workbook passed; no 100-item limit. Canonical dataset unchanged.
- Output: [importer](../../collect%20data%20script/excel_vocabulary_importer.py), [focused tests](../../collect%20data%20script/test_excel_vocabulary_importer.py), [how to run](../B002_EXCEL_IMPORTER.md), [real fixture import](../../reports/b002_import_demo/fixture_private_import.json), [verification](history/2026-11-23_B002_verification.md). No content pack, runtime, UI or media was created.

## B-003.1 — Excel-to-AI pipeline integration adapter

- Priority/status: P1 / DONE for offline adapter and dry run, 2026-11-23. Owner: Codex root on `main`/`936d9fd`; no active write claim after checkpoint. Authorized scope: accepted B-002 import mapping, private processing manifest, focused offline tests; no live AI/network/media or final pack.
- Output: [adapter](../../collect%20data%20script/import_pipeline_adapter.py), [tests](../../collect%20data%20script/test_import_pipeline_adapter.py), [three-item manifest](../../baseline/imports/imp-3e130d77-9848-4f67-b52a-aab79c2512c7/processing_manifest.json), [integration instructions](../B003_1_IMPORT_PIPELINE_ADAPTER.md), [verification](history/2026-11-23_B003_1_verification.md).
- Acceptance verified: three actual imported rows retain IDs, physical row, English/Japanese/Vietnamese and target sense; planned paths stay per-import; status pending and all review/quality/rights unknown. Existing query/result/image validators reused in offline tests, no 100-word registry dependency. Local evidence recording keeps candidate provenance/hash and score separate from approval; missing image and other failures are representable. Six focused tests, collector 174, Kaggle 19, fixture checker PASS. Canonical data unchanged.

## A-004 — Full 100-word pipeline rerun and quality evaluation

- Priority/status: P0 / **DONE for eligible automated attempts and review package**, 2026-11-23; owner labels still NEEDS_REVIEW. Owner: Codex root on `main`/`936d9fd`; no active write claim after checkpoint. Owner explicitly authorized resuming from the ten-ID partial ledger; prior credit rejection is preserved in [partial evidence](history/2026-11-23_A004_partial_verification.md), and the resource gate succeeded on this run.
- Frozen scope/output: [manifest](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/experiment_manifest.json), [query ledger](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/query_results.json), [retrieval ledger](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/retrieval_results.json), [candidate table](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/candidate_rankings.csv), [100-ID matrix](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/evaluation_matrix.csv), [final report](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/evaluation_report.md), [gallery](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/review_gallery.html), [instructions](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/review_instructions.md), [verification](history/2026-11-23_A004_resume_verification.md).
- Actual results: original Qwen attempts 100/100, 94 normalized valid and 93 effective intents. Image search attempted for all 93 eligible IDs; 93 search calls succeeded, 620 candidate records, 548 valid raw/JPEG pairs, 72 failed downloads, 92 ranked IDs, seven `SKIPPED_QUERY`, vocab-000008 `NO_VALID_CANDIDATES`. The 92 top images were visually assessed AI_PRELIMINARY: educational suitability 30 PASS / 13 NEEDS_REVIEW / 49 FAIL. No human labels or new owner selections were inferred. Existing audio 100/100 hash-match; canonical dataset unchanged. Collector 174 and Kaggle 19 tests passed; gallery runtime filter and JSON export checked.
- Next action: owner reviews all 100 gallery cards and exports JSON; a separate task may validate and consolidate decisions. No production promotion, public-rights clearance, B-003.2 or Game UX/UI change.

## B-003.2 — Live per-import media processing

- Priority/status: P1 / TODO, paused and not authorized. Owner: unassigned.
- Dependencies: B-003.1 manifest, bounded provider/model/job scope and import-local runner; future execution needs explicit owner instruction. Reuse Qwen, retrieval, candidate validation/JPEG, SigLIP, human review and gTTS lower-level functions without canonical IDs/global output paths. Persist transitions and hashes; do not auto-approve ranked images or reuse the `because` internal-only override by text.
- Exact execution prerequisites and boundaries: [B-003.1 integration instructions](../B003_1_IMPORT_PIPELINE_ADAPTER.md). No generation, final content pack, UI or deployment was started in B-003.1.

## UX-001 — Explore and approve final Game UX/UI

- Priority/status: undecided / BLOCKED, AWAITING_OWNER_DIRECTION. Owner: project owner; no agent implementation claim.
- Dependency: separate owner-authorized exploration and decisions on gameplay, layouts, navigation and visual style. D-014 reserves these choices; A-001 gallery is internal tooling, not a reference design.
- Output: none under A-001.1. Do not create mockups, wireframes, design system, frontend framework commitment or game UI tasks until directed.

## RELEASE-001 — Review release subset and publish

- Priority/status: P1 / BLOCKED. Owner: unassigned.
- Dependencies/blocker: future runtime task, chosen release subset, content/technical/rights clearance for that subset and deployment instruction. Processing-service readiness also required to advertise self-service media generation.
- Relevant files: release artifact manifest, hosting workflow to be chosen, revised roadmap.
- Acceptance: public URL accessible externally before 02/12/2026 under agreed delivery scope; subset suitable for public distribution; offline after initial download verified.
- Verification: external-device/browser smoke test, media paths/cache/update/rollback, rights evidence by released hash.
- Output: release manifest, URL and verification report; no publish in setup task.

## META-001 — Complete remaining license inventory

- Priority/status: P2 / TODO (deferred). Owner: unassigned.
- Dependencies: source evidence as available; never blocks A-001/A-002/B-001 or local B-002.
- Relevant files: metadata/license fields/source URLs and new inventory addenda; preserve old reports.
- Acceptance: record substantiated rights/unknowns without inventing licensed status or changing quality scores; no re-download solely for metadata.
- Verification: source/reference audit only for chosen scope.
- Output: future inventory addendum with provenance.

## DISK-001 — Inspect and clean Windows C: drive

- Priority/status: maintenance / DONE. Owner: Codex root, main/936d9fd, 2026-11-22. Write scope: NVIDIA DXCache files older than 30 days and `C:/Users/dotha/AppData/Local/Temp/7zA3548848`; context notes only in repository.
- Verification: C: free space 0.80 → 6.87 GiB; 155 old cache files removed with zero failures, installer extraction absent, remaining DXCache 0.75 GiB/27 files.
- Remaining issues: larger application data, model caches and pending updates were inventoried but left intact because they may be needed. No application tests apply.

## DISK-002 — Audit D: before cleanup

- Priority/status: maintenance / DONE. Owner: Codex root, main/936d9fd, 2026-11-22. Read-only scope: D: files and disk-0 partition metadata; write scope: audit report and context notes only.
- Output: [D: audit](../../reports/disk_maintenance/2026-11-22_d_drive_audit.md). Confirmed D: 59.06 GiB free, NT532 dated backup 6.58 GiB, installers 4.84 GiB, build outputs 3.51 GiB, and one 0.73 GiB SHA-256 verified duplicate video.
- Verification: recursive directory sizes and targeted file hashes; no deletions or partition changes. Next action: owner chooses candidates, then separately plan 20 GiB C: expansion around intervening 50 GiB Linux-type partition.

## DISK-003 — Remove selected duplicate and inspect EousX backup

- Priority/status: maintenance / DONE. Owner: Codex root, main/936d9fd, 2026-11-22. Write scope: exact `D:/OBS output/editthis.mp4` plus audit/context notes.
- Verification: both video copies had identical 780,310,106-byte length and SHA-256; outside copy removed, project copy retained, D: free 59.78 GiB. EousX Git backup is 25.4 MiB with four commits absent from current EousX history; preserve.
- Remaining: owner review of other D: candidates; 20 GiB C: expansion is a separate partition stage. No application tests apply.

## DISK-004 — Expand C: by 20 GiB while preserving Linux

- Priority/status: maintenance / BLOCKED before partition mutation. Owner: Codex root, main/936d9fd, 2026-11-22. User authorized capacity expansion; Linux dual boot must remain. Write scope so far: readiness/context notes only.
- Evidence: [readiness report](../../reports/disk_maintenance/2026-11-22_c_expansion_readiness.md). On disk 0, C: is followed by a used 50 GiB Linux-type partition and then D:. D: has 59.78 GiB free, but there is no adjacent unallocated space for C:. E: has 209.27 GiB free on disk 1, insufficient to guarantee a full raw image of disk 0.
- Blocker/next action: establish and verify an independent restorable backup plus administrator inspection of boot/recovery/encryption and Linux partition before any offline move/resize. No partition change was run. Do not mark DONE until C: capacity rises 20 GiB and both Windows/Linux boot and data are verified.

## Ownership protocol

Claim an authorized task with agent/session, root/worktree/branch/HEAD and exact write scope before starting. One coordinator edits shared STATE/TASKS/HANDOFF; other agents return evidence. Disjoint task docs may proceed in parallel; shared media/registry/context writes require coordination. On overlap, stop conflicting writes and report; do not merge/overwrite another agent's work. Release claims in handoff, keeping incomplete acceptance visible.
