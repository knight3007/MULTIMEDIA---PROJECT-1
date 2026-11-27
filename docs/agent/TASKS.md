# Current tasks

## VC-001 — Version control checkpoint (Unity G-008 baseline)

- Status: **COMMITTED LOCALLY, NOT PUSHED**, 2026-11-27 (owner approved; D-053 CONFIRMED). Branch `feature/unity-g008-baseline`: `2429b13` (ignore/attributes), `c4aa296` (project, 303 files), `58e7bc8` (tests, 41 files), then the docs commit. Audit and plan: [version-control audit](VERSION_CONTROL_AUDIT_G008.md).
- **Candidates:** 346 files (Assets with all .meta, ProjectSettings, Packages, fixtures, tools, licenses). No secrets found. No restricted assets. One machine path made overridable.
- **LFS:** not needed.
- **Plan:** branch `feature/unity-g008-baseline`, 4 core commits plus 2 optional.
- **Excluded:** `Kaggle_…V4.ipynb` (token-like content), `reports/**`, `game/UXUI/`, `data/vocabulary/unified_dataset_v1.json` (needs owner review).
- **Next:** push and merge only on separate owner approval. Optional commits 5 (promotion tool) and 6 (background/mockup, `web/` deletions) await the owner. `unified_dataset_v1.json`, README, comand.txt, schedule and integration_notes stay uncommitted.

## G-007-R3 — Vocabulary coverage fix

- Status: **DONE, OWNER_VERIFICATION_REQUIRED**, 2026-11-27 (D-051). The owner saw missing words in play. Reproduced on G007_R2 (4 dev-bot sessions on v47, 15 usable items each): per-word counts 0–3 over 30 spawns, and one session never showed `backpack`. Root cause: `VocabularyDeck` drew 10 of a fresh shuffle per wave. Fixed with deck cycles of all items. The regression tests cover pack sizes 10, 12, 15, 20, 30 and 31, with simulated lane postponements. R3 runtime: every word exactly twice in all 5 sessions, cycles 15+15, waves distinct. New logs `G007_SPAWN` (index, item, cycle, wave) and `G007_DEFER`. EditMode 120/120, PlayMode 60/60. Build `game/New Unity Project/Builds/G007_R3_Win64/WordOrbit.exe` (0 warnings, 0 errors). **On owner instruction it also contains the G-008 code** (see below); G007_R2 is kept. Dev-bot runs no longer write learning history; the 4 bot lines written by the first R3 build were removed.

## G-008 — Scoring, audio, waves and results

- Status: **IMPLEMENTED, OWNER_VERIFICATION_REQUIRED**, 2026-11-27 (finalization).
  - **Build:** `game/New Unity Project/Builds/G008_Win64/WordOrbit.exe`, 0 warnings, 0 errors. EditMode 123/123, PlayMode 62/62.
  - **Added in finalization:**
    - Vocabulary coverage in Results, logs and history (usable / encountered / answered correctly / review).
    - Current and highest combo on the HUD.
    - `LearningHistory.Target`, so dev bots never write player history (tested).
    - A genuine lane-deferral PlayMode scenario: 15 deferrals, every word still exactly twice.
  - **Perf matrix:** Comparable runs, `Logs/g008_perf/`. Workload A (no kills, Normal, seed 60, up to 3 meteors in every build), avg/p95 ms uncapped: 1920 R1 3.61/6.28, R2 2.89/4.26, G008 2.76/4.16; 1366 R1 1.95/2.50, R2 1.99/3.15, G008 2.55/4.74; 1280 R1 1.81/2.51, R2 1.98/3.00, G008 2.05/4.02. With vsync at 1920 all three run at about 7.0 ms (143 FPS). Workload B (bot answers every 2 s, 1 meteor on screen), repeated twice: R2 2.96–3.14, G008 3.01–3.10, equal (a first single G008 run of 3.92 was noise). Spikes over 33 ms (1–11 per 25 s, max 66 ms) come in clusters with no speech or answer event nearby, and also happen in R1 and R2 (max 42–78 ms), so they are not attributed to G-008. Limits: one run per cell, except repeated B (run-to-run noise about ±0.7 ms); R1 bot submits whole words (no per-character typing); R1 and R2 do not log spike counts; the windowed runs shared the desktop with other apps; Expert lane capacity was not part of the comparison.
  - **Owner request:** a breach now flashes the screen red under the HUD for 0.4 s and shakes the camera lightly for 0.25 s. With reduced motion (F2) the flash is softer and there is no shake. PlayMode test added.
  - **Owner checks open:** feel of pacing, combo and score, speech and SFX by ear, native JA IME, Results/Review readability.
  - Earlier status line follows.
- Earlier: **IMPLEMENTED (in working tree and the G007_R3 build), OWNER_VERIFICATION_REQUIRED**, 2026-11-27. The owner approved O1–O6 as recommended and authorised G-008. G-008.1–.7 are done, with the history writer skipping dev-bot runs. G-008.8 is partly done: spike and postponed counters were added, but the comparable R1/R2/G-008 perf matrix has not run. The G-008 spec notes and a dedicated `G008_Win64` build are still open. Earlier planning status: PLANNED, IMPLEMENTATION_PENDING. Plan: [G-008 plan](../game/G008_IMPLEMENTATION_PLAN_v0.1.md). Tasks G-008.1 session model (waves/combo/points/typos/per-item), .2 wave flow, .3 HUD, .4 audio pending slot + clip cache + SFX roles, .5 Results, .6 Review via VocabularyPreview filter, .7 local history (needs owner O5), .8 comparable perf verification, .9 docs/build. Proposed rules D-046–D-050. Owner decisions O1–O6 open. No gameplay code changed; waits for owner authorization. G-007-R2 owner playtest pending.

## G-007-R2 — Character-Based Combat & Responsive Laser Feedback

- Status: **DONE, OWNER_VERIFICATION_REQUIRED**, 2026-11-27 (D-044, D-045). Each correct answer unit fires one laser at the target and deals damage; wrong units give feedback without damage; the last correct unit destroys the meteor without Enter (score and pronunciation once). Damage = expected answer units (Full Word: whole term; Fill: missing units only); separators are not shots. Damage bar, ship aims at the target, pooled beams (max 3 per input), quiet rate-limited laser SFX. No farming via Backspace/unchanged input; paste counted but beams capped; no damage while an IME composes. Long Fill labels are clamped inside the screen (owner report, D-045); the console mode line is one line with autosize. New `Scripts/Game/TypingCombat.cs`, `Tools/headless.ps1`. EditMode 101/101, PlayMode 55/55 (headless on the real project, Editor closed); build `game/New Unity Project/Builds/G007_R2_Win64/WordOrbit.exe` (0 warnings, 0 errors); captures `Screenshots/g007_r2/` (8 PNG). Videos skipped at owner request (owner will test and report). Native IME and audio by ear still need the owner. R1 build kept.

## G-007-R1 — Remove image hints from gameplay

- Status: **DONE, OWNER_VERIFICATION_REQUIRED**, 2026-11-27 (D-043). Hint options now Chỉ nghĩa / Nghĩa + chữ đầu; image code removed from gameplay and the setup preview. EditMode 87/87, PlayMode 46/46 (live Editor); build `game/New Unity Project/Builds/G007_R1_Win64/WordOrbit.exe` (0 warnings, 0 errors); captures in `Screenshots/g007_r1/` (6 PNG, Easy JA Fill victory 30/30). G007_Win64 kept as the earlier build.

## G-007 — Gameplay Configuration, Difficulty & Answer Modes

- Status: **IMPLEMENTED, OWNER_VERIFICATION_REQUIRED**, 2026-11-27. Owner authorised work while remote; G-006 manual checks remain open.
  - G-007.1 Game Configuration screen (`GameSetup` scene) — done.
  - G-007.2 Difficulty presets Easy/Normal/Hard/Expert from spec §5 (D-038) — done.
  - G-007.3 Hint modes: Chỉ nghĩa, Nghĩa + chữ đầu, Nghĩa + chữ đầu + ảnh, Chỉ ảnh (D-040) — done.
  - G-007.4 Answer modes: Gõ cả từ, Điền chỗ trống (D-039) — done.
  - G-007.5 Targeting: Tự động + Tab (default), Tự động, Thủ công (D-041) — done.
  - G-007.6 Configuration compatibility with reasons (D-040) — done.
  - G-007.7 Safe spawn below the HUD (D-042) — done.
  - G-007.8 Tests, build, evidence — done: EditMode 87/87, PlayMode 46/46, build `game/New Unity Project/Builds/G007_Win64/WordOrbit.exe` (0 warnings, 0 errors), gallery `game/New Unity Project/Screenshots/g007/index.html` (19 screenshots, 4 videos without audio).
  - Final-build performance (uncapped avg / p95, vsync avg): 1920×1080 3.20 / 5.38 ms, 6.97 ms; 1366×768 1.62 / 2.19 ms; 1280×720 1.49 / 1.99 ms; Expert + images, max 3 meteors on screen; allocated ~120 MB.
  - Owner checks still open: IME, pronunciation by ear, balance, visuals. Details: [HANDOFF](HANDOFF.md). G-008 not started.

## G-006 — Meteor Defense Core Implementation

- Status: **IMPLEMENTED, OWNER_VERIFICATION_REQUIRED**, 2026-11-27. First playable Meteor Defense on the reviewed pack v47, EN-VI and JA-VI. Entry: Main Menu "Chơi Meteor Defense" → Vocabulary Library (pack + language) → MeteorDefense scene.
  - G-006.1 session rules (`MeteorDefenseSession`, `GameConfig`, D-037) — done.
  - G-006.2 seeded deck and spawning (`VocabularyDeck`, `LaneChooser`, 5 lanes, label overlap avoidance) — done.
  - G-006.3 targeting (auto nearest line, Tab cycle, per-meteor drafts; `TargetSelector`) — done.
  - G-006.4 Full Word answer check (NFC + trim; EN case-insensitive; JA exact script; `AnswerChecker`) — done.
  - G-006.5 laser, burst, +100 popup, correct-language pronunciation (newest interrupts older) — done.
  - G-006.6 HP, score, Pause (Resume/Restart/Main Menu with confirm), Back pauses, Victory/Game Over panel (Replay/Library/Main Menu) — done.
  - G-006.7 developer fixtures hidden from the default Library and blocked from play (D-036) — done.
  - G-006.8 tests, build, captures, recording, perf — done: EditMode 66/66, PlayMode 34/34, build `game/New Unity Project/Builds/G006_Win64/WordOrbit.exe` (0 warnings, 0 errors), captures and 30 s recording in `Screenshots/g006/`.
  - Owner checks still open: Japanese IME in the build, audio by ear, playfeel and balance, visual approval. Details: [HANDOFF](HANDOFF.md). G-007 not started.

## G-005 — Flashcard

- Status: **CANCELLED — MERGED INTO VOCABULARY LIBRARY** (D-034, owner, 2026-11-27). Main Menu Flashcard entry removed; word/meaning/image/pronunciation viewing stays in the Vocabulary Library. Phase numbers unchanged; next product phase is G-006 (not started).

## G-004-R1 — Real Content Pack readiness

- Status: **DONE**, 2026-11-27. Owner approved v46 media (15/15 images, EN and JA audio); agent checked meanings (owner-delegated). `reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v47_reviewed/`: 15 ready, EN-VI 15, JA-VI 15, validate_pack valid, media byte-identical to v46; v46 unchanged. Verified in the unchanged G-004 build and by a PlayMode test decoding all 45 media. Library hides unusable packs by default (owner chose hide over delete). Details: [HANDOFF](HANDOFF.md).

## G-004 — Content Pack Runtime & Vocabulary Library

- Status: **IMPLEMENTED, OWNER_VERIFICATION_REQUIRED**, 2026-11-27. G-004.1 contract recovery, G-004.2 reader, G-004.3 validation/eligibility, G-004.4 media runtime, G-004.5 library, G-004.6 pack + mode selection, G-004.7 shared `LearningSession`, G-004.8 tests: EditMode 47/47, PlayMode 18/18, build `Builds/G004_Win64/WordOrbit.exe`, standalone captures in `Screenshots/g004/`. Real packs: 0 eligible (no `ready` items); contract fixture b001: JA-VI 1, EN-VI 0. Details: [HANDOFF](HANDOFF.md). Owner approved G-003-R1 visuals; G-003 manual checks still open.

## G-003-R1 — Owner feedback: Back navigation and denser Galaxy background

- Status: **DONE, OWNER_VISUAL_REVIEW_REQUIRED**, 2026-11-27. Owner tested G-003 and requested visible Back buttons and a richer, larger starfield. Implemented in `game/New Unity Project/`; EditMode 12/12, PlayMode 11/11; build `Builds/G003_R1_Win64/WordOrbit.exe` (old `Builds/G003_Win64/` kept). Before/after and regression captures in `Screenshots/r1/`. Details: [HANDOFF](HANDOFF.md). Both requests are persistent UX requirements (D-031).

## G-003 — Unity Foundation & Technical Prototype

- Status: **IMPLEMENTED, OWNER_VERIFICATION_REQUIRED**, 2026-11-27. G-003.1 to G-003.9 done in `game/New Unity Project/`: EditMode 10/10, PlayMode 7/7, Windows x64 dev build succeeded, real captures at 1920x1080/1366x768/1280x720, standalone media self-test passed, about 7 ms per frame (vsync 144 Hz) with up to 40 meteors. Pending manual: Japanese IME, real-keyboard and laser visuals in the build, audio listening, visual approval. Details: [HANDOFF](HANDOFF.md). G-004 not started.

## UNITY-SETUP-001 — Unity CLI and agent plugin

- Status: **DONE**, 2026-11-27, by owner request. Installed Unity CLI 1.1.0 via `winget install Unity.CLI`, added marketplace `Unity-Technologies/unity-agent-plugin` and installed `unity@unity-agent-plugin` (user scope), ran `unity pipeline install` in `game/New Unity Project/` (adds `com.unity.pipeline` 1.0.1 to `Packages/manifest.json`), opened the project in Editor 6000.6.10f1. Verified: `unity status` → port 7800 `ready`; `unity pipeline editors` → hasPipelinePackage true, serverReachable true. No scenes, scripts or gameplay created; G-003 not started. The Unity project is still untracked in git.

## SKILL-ZIP-001 — Export installed skills

- Status: **DONE**, 2026-11-26. Codex root on `main`/`57b6ccb`; write scope was the ZIP and these three context files. `C:/Users/dotha/Downloads/skills-export-2026-11-26.zip` contains 118 skill directories and a manifest. ZIP CRC and source/destination SHA-256 checks passed. No follow-up required.

## G-002 — Galaxy asset audit and UX/UI documentation

- Overall status: **OWNER_REVIEW_REQUIRED**. Documentation execution is complete for the inspected evidence; this is not visual approval or Unity implementation. Codex root, `main`/`57b6ccb09d25945eb4301f41af2342eb37ea2bda`; no active write claim after checkpoint. Owner downloaded and extracted the source library into `game/UXUI/`. Original ZIPs and extracted assets remain local/untracked and unchanged by this task.
- **G-002.1 — User flow and mechanics planning: OWNER_REVIEW_REQUIRED.** [Gameplay Mechanics Spec v0.1](../game/GAMEPLAY_MECHANICS_SPEC_v0.1.md) records the owner's preferred planning choices, compatibility and eligibility rules, provisional balance, state diagrams and acceptance scenarios. [GDD](../game/GDD_v0.1.md) remains DRAFT; [User Flow](../game/USER_FLOW_v0.1.md) retains S01–S11 and [UX/UI Spec](../game/UX_UI_SPEC_v0.1.md) remains a screen proposal. Acceptance for closure: owner reviews the complete mechanics draft, including numerical tuning and unresolved runtime behavior. Documentation verification only; no Unity test or playtest.
- **G-002.2 — Source asset audit: DONE at reported inspection depth.** Dependency: owner-extracted library. [Audit](../game/ASSET_AUDIT.md) records 1,576 extracted files + four ZIPs, metadata/alpha/licensing, 66 exact duplicate pairs, representative visual inspections and unreviewed assets. Verification: recursive metadata/PNG open/SVG parse/hash checks; seven OGG files not listened to and every sprite not visually inspected.
- **G-002.3 — Asset evaluation and selection: OWNER_REVIEW_REQUIRED.** Dependency: G-002.2. Option A is the **PROPOSED** primary set, score 4.35/5 by the weighted sampled rubric; B 4.30, C 3.53. Deliverables: [audit](../game/ASSET_AUDIT.md) and [inventory](../game/GAME_ASSET_INVENTORY.md). Acceptance: owner reviews the composite at real text sizes and chooses assets; no asset is promoted by documentation alone.
- **G-002.4 — Visual design system: OWNER_REVIEW_REQUIRED.** Dependency: G-002.3 candidate set. [Proposal](../game/VISUAL_DESIGN_SYSTEM.md) documents dark Galaxy/2D Space Arcade, Blue/Default UI, contrast/layout and the separate protected background plan. Verification: contrast calculations recorded; no Unity composite or background rendered.
- **G-002.5 — Multilingual typography: PARTIAL.** Dependency: downloaded Noto fonts. Local cmap checks passed requested EN/VI/JA samples for Noto Sans JP Regular/Medium; [visual proposal](../game/VISUAL_DESIGN_SYSTEM.md) and [UX/UI spec](../game/UX_UI_SPEC_v0.1.md) record the TMP plan. Acceptance: later authorized Windows build confirms glyphs, line wrapping, IME and atlas memory; those runtime checks remain BLOCKED by current documentation-only scope.
- **G-002.6 — Screen asset mapping: OWNER_REVIEW_REQUIRED.** Dependency: G-002.3–4 candidate direction. [UX/UI spec](../game/UX_UI_SPEC_v0.1.md) maps UI-01–09 to S01–S11 and exact source paths, preserving AI Progress and Language Selection. Verification: references and source paths checked; no visual mockup or scene approved.
- **G-002.7 — Procedural VFX planning: OWNER_REVIEW_REQUIRED.** Dependency: G-002.3 candidate set. [VFX plan](../game/VFX_PLAN.md) covers 13 effects, input assets, components, motion reduction and risks. Verification: documentation review only; no effect built or measured.
- **G-002.8 — Documentation and context synchronization: DONE for this checkpoint.** Dependency: G-002.2–7 documentation. Updated current agent context and decision register without changing AI/Docker statuses. Verification: documentation links, protected-background SHA-256, source-library fingerprint, scope diff and whitespace checks recorded in [handoff](HANDOFF.md).
- **G-002.9 — Interactive UI mockup & visual review: OWNER_REVIEW_REQUIRED.** Prototype at [game/prototypes/g0029_ui_mockup/](../../game/prototypes/g0029_ui_mockup/README.md) (HTML/CSS/vanilla JS, Canvas starfield, local Kenney/Noto assets, three needs_review Content Pack v46 items). S01–S11 screens, review toolbar, layout A/B and Full Word/Fill-in-the-Blank toggles. Built by Codex 2026-11-26; 2026-11-27 Claude fixed unreadable primary-button labels, toolbar covering HUD, blurry/opaque reticle, static Full Word placeholder, fixed-point laser, input focus loss, footer/help overlap and mid-word JA wrapping, and replaced the 754×440 screenshots with 13 real 1920×1080 captures. Launch: `python -m http.server 8765 --bind 127.0.0.1` from repo root, open `http://127.0.0.1:8765/game/prototypes/g0029_ui_mockup/`. Verification: browser pane at 1366×768 (navigation, typing, Tab, Enter, laser, JA/EN, layout B, Fill mode), headless Edge 1920×1080 captures, `node --check app.js`, background SHA-256 unchanged. Not verified: audio playback by ear, 1280×720 visual pass, real IME composition. Owner chose label Layout A (D-029). Impeccable critique 24/40 (dual-agent, snapshot in `.impeccable/critique/`); owner chose top 3, fixed: flashcard front hides meaning + Space/arrow keys, one-way meteor descent with near-line and impact (HP/edge flash) states, single-surface Kenney `buttonBlue.png` primary button; plus wrong-answer copy/combo reset and placeholder contrast. Open from critique: Play-now path, single simulation badge, nested flashcard panel. Same day UX polish pass (ui-ux-pro-max + emil-design-eng): screen-change transition, press/hover feedback, toast entry, wrong-answer label flash, minimum text sizes; screenshots re-captured. Still open: primary-button style, reticle style, Option A approval. Acceptance: owner approves or requests revision; no Unity/G-003.
- Next planning action: owner reviews the gameplay mechanics draft alongside Option A, optional planet use, label placement and font direction; separately confirms lecturer acceptance of Desktop. A `ready` Content Pack or separately authorized labeled synthetic prototype set is needed before real gameplay testing. G-003 is not started. No commit/push.

## PUSH-001 — Push finalized code without media

- Priority/status: P0 / DONE. Owner authorized pushing to `main` only finalized work and cleaning unused scratch; Codex root, `main`/`57b6ccb09d25945eb4301f41af2342eb37ea2bda`. No active write claim.
- Pushed: three scoped commits for private bilingual Excel pipeline, final gallery and Docker packaging. Included regression tests, usage/contract docs, Docker verification report and the 15-word XLSX fixture. No image/audio additions; `.gitignore` now excludes generated media extensions. Remote `origin/main` was verified at the final SHA.
- Verification: collector 209 OK, Kaggle 19 OK, B-001 fixtures PASS, Compose config exit 0 with local config warnings, committed diff check PASS and 20 changed paths checked for media. Removed five superseded local backup reports and unused `lenh.txt` only.
- Remaining local: G-001 GDD and migration are DRAFT/unpushed; other pre-existing working-tree edits and generated media stay local. No automatic follow-on push.

## G-001 — Draft GDD and preserve legacy background

- Priority/status: P0 / DONE for the authorized documentation and migration; **GDD v0.1 DRAFT pending detailed owner review**. Codex root, `main`/`9f6c54e4b708b7cfb9c477f801875b1f460cc511`; no active write claim after checkpoint.
- Scope: move the protected `web/background_idea.md` unchanged to `game/background_idea.md`; remove only the redundant `web/.gitkeep`; retain `game/.gitkeep`; write [GDD v0.1](../game/GDD_v0.1.md), update active repository context and add D-024 preference. No Unity initialization or G-002.
- Acceptance/verification: protected SHA-256 before and after `B33CC9780FC82664608A621BFEE7EC30DCBB6B1D450F2AB11BCAF9F637298DF4`; `web/` retired; GDD, links, decision history and scoped diff checked. No application tests required for documentation-only work. See [handoff](HANDOFF.md) for exact results.
- Remaining: owner reviews GDD details; lecturer acceptance of Desktop and any public-URL requirement, Japanese input, targeting, hint semantics, balance and local Docker handoff are open. G-002 and later milestones require separate authorization.

## DOCKER-MOVE-001 — Move Docker Desktop data disk to D

- Priority/status: P0 / DONE. Codex root, `main`/`9f6c54e4b708b7cfb9c477f801875b1f460cc511`; no active write claim. Owner operated Docker Desktop disk-location UI; Docker Desktop updated to 4.100.1. Active WSL VHDX is `D:/DockerDataFinal/DockerDesktopWSL/disk/docker_data.vhdx`; old C disk and redundant D copies are absent. C free 34.7 GB (about 11.8 GB before successful move), D free 29.0 GB. Docker Engine running, same three image IDs and PostgreSQL volume, PostgreSQL healthy/accepting connections, project image container smoke and Compose config PASS. Repo changes: agent checkpoint docs and correction to DOCKER-001 report only. No commit/push. See [handoff](HANDOFF.md).

## DOCKER-001 — Package finalized Excel-to-multimedia pipeline

- Priority/status: P0 / DONE. Codex root, `main`/`9f6c54e4b708b7cfb9c477f801875b1f460cc511`; no active write claim. Added root Dockerfile/Compose/ignore, private Docker entry point and tests, [usage](../DOCKER_PIPELINE.md), [verification report](../../reports/DOCKER_001/verification_report.md). 15-word run `docker-output/run-cb0ffd4f-b21b-4baa-8522-d35cbd961acc`: 15 reviewed private image choices reused with identical SHA to native and same PHOTO6/ICON8/SCENE1 routing, 15 EN + 15 JA audio generated, valid pack/gallery, 45/45 HTTP media hashes and Edge mode/search/filter checks. 100-word reconstructed workbook full run `docker-output/run-be401d25-b38d-4cc4-bfcd-fe25cd5e001a`: 99 approved image reuse, one explicit `sometimes` no-image, 100 EN generated, 100 JA reused, valid pack/gallery, 299/299 media hashes and Edge missing-image/internal-only checks. Collector 209 OK; Kaggle 19 OK; B-001 fixture verifier PASS; Compose config PASS. Canonical dataset SHA unchanged `644c2dc9…`. Diagnostic failed runs preserved; live uncached DDG/SigLIP ranking not reverified end-to-end. No model/provider/scoring redesign, commit/push, public deployment or Game work. Next owner action: build image, run the documented Excel command, inspect gallery.

## E2E-015 — New 15-word Excel-to-multimedia run

- Priority/status: P0 / DONE. Codex root on `main`/`9f6c54e4b708b7cfb9c477f801875b1f460cc511`; no active write claim after this checkpoint. Exact owner workbook copied to `tests/fixtures/b001/test_vocabulary_15_B001.xlsx`, SHA-256 `00f0056564167dd681bc48bde482b6c91a61068e76b0f119747b1b390f0b3800`.
- [Isolated run](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/): import `imp-6a2afe8b-ccf6-4ff9-94d0-6b05790182bf`, 15 unique items/rows 2–16, 20 actual image searches, PHOTO 6/ICON 8/SCENE 1, 15 selected images/0 NO_SUITABLE_IMAGE, EN 15 generated/0 reused/0 failed, JA 15 generated/0 reused/0 failed, 30/30 audio valid. [Content Pack](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v46/content_pack.json) valid; all 15 needs_review/pending, none READY. [Final gallery](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/final_review_gallery.html), [quality report](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/e2e_15_quality_report.md), [browser/asset validation](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/final_gallery_validation_report.json). Browser verified 15 cards, both modes/audio controls, search/filters/navigation/enlargement and no console errors; HTTP 45/45 media hashes. Collector 206 OK, Kaggle 19 OK, fixture verifier PASS. Canonical 100-word data hash unchanged. Exact opening command and limitations in [handoff](HANDOFF.md). No commit/push, no Game UX/UI.

This is the authoritative current task list. Historical DDG tasks in `tasks/plan.md` and `tasks/todo.md` remain complete and unchanged. Status vocabulary: TODO, IN_PROGRESS, BLOCKED, DONE, NEEDS_REVIEW, PARTIAL. DONE requires verified acceptance; dependencies do not grant execution authority. B-003.2's earlier integration remains PARTIAL pending owner content review. The owner now prefers Unity Desktop, while Game UX/UI remains undecided (D-014). No public deployment.

## R-001 — Final multimedia HTML review gallery

- Priority/status: P0 / DONE. Codex root, `main`/`9f6c54e4b708b7cfb9c477f801875b1f460cc511`; no active write claim after checkpoint. Source Content Pack SHA-256 `08baaf667609a104846804209c53059ccf04f5f8a6ba533cb5006442db903d06`. Created gallery generator, HTML template and focused tests in `collect data script/`, plus [final gallery](../../reports/EXCEL_FULL_PIPELINE_FINAL/run-88c4196d-dc59-497e-a389-76a564615483/final_review_gallery.html) and [validation report](../../reports/EXCEL_FULL_PIPELINE_FINAL/run-88c4196d-dc59-497e-a389-76a564615483/final_gallery_validation_report.json). Existing pack/media, prior gallery, pipeline and canonical data stayed untouched. No commit/push.
- Acceptance: load and validate actual `content_pack_v301`, show 100 items in EN–VI and JA–VI with 99 images and 200 audio, explicit `sometimes` missing-image state, computed summary, search/filters/navigation, accessible responsive review UI, local HTTP and browser verification when available. Preserve review status and restrictions.
- Verified: pack/manifests and hashes valid; 100 IDs, 99 images, 100 EN audio, 100 JA audio, 99 `needs_review`, one failed, `because` INTERNAL_ONLY. Browser over localhost HTTP tested both modes, selected image, search/filters/navigation/enlargement, `sometimes`, and both audio controls loading and starting playback. Initial image-return bug fixed; clean reload had no new console error. Collector 204 OK; Kaggle 19 OK. Mobile viewport not directly emulated; human content review remains B-003.2's next action. See [handoff](HANDOFF.md).

## B-003.2 — Full Excel-to-multimedia dual-mode integration

- Priority/status: P0 / **PARTIAL pending direct gallery review**, current owner instruction, Codex root on `main`/`9f6c54e4b708b7cfb9c477f801875b1f460cc511`; no active write claim after this checkpoint. Scope: importer, adapter, private per-run runner, frozen image v2 integration, EN/JA gTTS, Content Pack extension, internal gallery, tests and reports. No commit/push, canonical data mutation, frozen image file change or game UX.
- Code/docs: [runner](../../collect%20data%20script/excel_multimedia_runner.py), [verification](../../collect%20data%20script/verify_multimedia_run.py), [reconstructed fixture tool](../../collect%20data%20script/reconstruct_benchmark_workbook.py), [usage](../EXCEL_FULL_PIPELINE.md), [dual audio contract](../contracts/content_pack_v1.md). `audiocollector.py` gained explicit `en` locale, and `content_pack_builder.py` validates both assets and mode mappings. Focused tests in `test_excel_multimedia_runner.py`.
- Final run: [execution report](../../reports/EXCEL_FULL_PIPELINE_FINAL/run-88c4196d-dc59-497e-a389-76a564615483/execution_report.md), [gallery](../../reports/EXCEL_FULL_PIPELINE_FINAL/run-88c4196d-dc59-497e-a389-76a564615483/review_gallery.html). Reconstructed workbook, not owner's original, SHA-256 `8e920528835edffaef422e0eaf9362227ad27ea4c6b4fb50b4cfba30efa90bfe`; 100 rows. Images 99 approved reuse/1 historical NO_SUITABLE_IMAGE (`sometimes`), `because` restricted. Audio EN 100 generated/0 reused/0 failed after sandbox network access was granted; JA 0 generated/100 reused/0 failed. 200/200 audio assets valid. Active `content_pack_v301/` valid; 99 needs_review, one failed for missing image, 0 ready. All 100 gallery item/media references checked; no browser interaction check because file URL blocked. Automatic repairs 0.
- Verification: collector suite 202 OK, Kaggle 19 OK; focused runner/pack 14 OK; `node --check` gallery script and structural gallery verifier pass. No subjective pronunciation or translation certification. Current working tree already contained unrelated changes (`comand.txt`, `schedule/20-9 list`, `unified_dataset_v1.json`) and numerous untracked media before this task; they were not altered by this implementation.
- Next action: owner opens the single final gallery, listens to both modes and inspects overall content. Browser automation was blocked by the local file URL policy, so direct playback verification remains unobserved. Do not mark DONE until review/acceptance is verified. Historical B-003.2 TODO note below is superseded by this entry.

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
