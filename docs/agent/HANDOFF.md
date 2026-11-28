# Latest handoff — G-007 Gameplay Configuration, Difficulty & Answer Modes

Updated 2026-11-27 (Asia/Saigon) by Claude Code, `main`/`57b6ccb`. Nothing committed or pushed. Pre-existing unrelated tracked edits and untracked files remain. The previous handoff (G-006) is in [history](history/2026-11-27_before_G007_HANDOFF.md). No active write claim.

## Update VC-001 push (2026-11-28)

**VC-001 PUSHED (2026-11-28):** `origin/feature/unity-g008-baseline` = local HEAD `8cefee7` (verified with `git ls-remote`), plus this docs-sync commit. Not merged into `main` (still `57b6ccb`); no force-push, no history rewrite. Commits: `2429b13` ignore/attributes, `c4aa296` Unity project (303), `58e7bc8` tests (41), `0c12d8b` docs, `738c402` promotion tool, `8cefee7` background move + mockup. `origin` is the **public** repository `knight3007/MULTIMEDIA---PROJECT-1`. Not committed: the downloaded background `.jfif` (licence unknown), the Kaggle notebook, `.claude/`, `reports/**`, `game/UXUI/`, `unified_dataset_v1.json`, README, comand.txt, `schedule/`, `docs/contracts/integration_notes.md`. Pre-push audit of `origin/main..HEAD` (390 files): no credentials or tokens, no Content Pack media, reports, `game/UXUI/`, builds, Library or player history; largest blob 6.9 MB (`NotoSans-Regular SDF.asset`), no LFS (0 LFS files); 346 Unity files tracked, every Assets file has a `.meta`, 8 scenes, Packages and ProjectSettings present; `git fsck` clean. `C:/Users/dotha/...` paths appear in docs, but the same username was already public in 4 files on `origin/main`. Only `test_promote_reviewed_pack.py` was run (10/10 OK); Unity suites were not rerun (unchanged).

## Update VC-001 version-control checkpoint (2026-11-27)

**Committed locally after owner approval, not pushed.** Branch `feature/unity-g008-baseline`: `2429b13` (ignore/attributes), `c4aa296` (project, 303 files), `58e7bc8` (tests, 41 files), then the docs commit. Staged by explicit paths only; the Unity project has no untracked files left. Optional commits 5–6 and excluded files remain in the working tree.
- **Report:** [version-control audit](VERSION_CONTROL_AUDIT_G008.md).
- **Added:** `game/New Unity Project/.gitattributes` (LF for Unity YAML, `unityyamlmerge`, SDF atlases `-diff`, fonts/png/ogg `binary`; verified with `git check-attr`). `Tools/headless.ps1` reads `UNITY_EDITOR_EXE` first.
- **Findings:**
  - 346 candidate files, 0 missing or orphan `.meta`.
  - Registry-only packages.
  - Unity Services off. No secrets.
  - Licenses: CC0 and OFL included.
  - The v47/v46 Content Packs stay outside Git. PlayMode tests skip without them.
- **Open:**
  - The owner approves the commit plan.
  - The owner reviews the modified `data/vocabulary/unified_dataset_v1.json` and the Kaggle notebook before any broad commit.
  - The owner keeps a private archive of the v46/v47 packs.

## Update G-008 finalization (same day)

**Status:** IMPLEMENTED, OWNER_VERIFICATION_REQUIRED. Build `Builds/G008_Win64/WordOrbit.exe` (0 warnings, 0 errors); EditMode 123/123, PlayMode 62/62 (headless, `Tools/headless.ps1`).

**Checked against plan and spec:**
- Waves 3 × 10: gate, 3 s pause, ×1.1 fall speed, ×0.95 spawn interval, long-word allowance first.
- Score `round(100 × mult × (1 + min(0.1 × combo, 0.5)))`, once per destroyed meteor. Combo is reset by a wrong Enter or a breach.
- Results separate word accuracy, typing accuracy and coverage.
- Review uses the VocabularyPreview filter with the same pack and language.
- History is local JSONL.

**Deviations from the spec:** all are owner-approved (D-052): one-slot speech instead of interrupt, typos ignored for combo, typo words included in review.

**Speech policy as implemented and observed:**
- The current word is never interrupted. While it plays, the newest request replaces any waiting one (counted as `speechReplaced`).
- When the current word ends, the waiting word plays if it was requested at most 1.5 s ago in scaled time; otherwise it is dropped (`speechDropped`). Pause does not age it. The final word may finish under Results.
- PlayMode: 3 kills in one frame give 1 playing, 1 replaced, then the newest plays.
- Dev runs at time scale ×5 show `speechDropped` 1–10, because 1.5 scaled seconds is only 0.3 s real at ×5. Normal play is ×1.

**Coverage:**
- Results, logs and history now record usable items, unique encountered, unique answered correctly, and review count.
- Coverage = encountered / usable. With 40 usable items and 30 spawns the maximum is 75% (EditMode test), and Results notes that the pack is larger than the session.

**Deferral:** PlayMode `DeferredSpawnsKeepEveryWordAndBalance` uses slow meteors with 5 lanes. It produced 15 genuine `Requeue`s and still showed all 15 words exactly twice, with no duplicate on screen.

**History isolation:**
- `LearningHistory.Target(override, devBot)`: dev-bot runs write nothing.
- The PlayMode `SetUpFixture` redirects history to a temp folder.
- After the R3/G008 bot runs, no history folder exists under the player's LocalLow path.

**Perf:** Comparable runs, `Logs/g008_perf/`. Workload A (no kills, Normal, seed 60, up to 3 meteors in every build), avg/p95 ms uncapped: 1920 R1 3.61/6.28, R2 2.89/4.26, G008 2.76/4.16; 1366 R1 1.95/2.50, R2 1.99/3.15, G008 2.55/4.74; 1280 R1 1.81/2.51, R2 1.98/3.00, G008 2.05/4.02. With vsync at 1920 all three run at about 7.0 ms (143 FPS). Workload B (bot answers every 2 s, 1 meteor on screen), repeated twice: R2 2.96–3.14, G008 3.01–3.10, equal (a first single G008 run of 3.92 was noise). Spikes over 33 ms (1–11 per 25 s, max 66 ms) come in clusters with no speech or answer event nearby, and also happen in R1 and R2 (max 42–78 ms), so they are not attributed to G-008. Limits: one run per cell, except repeated B (run-to-run noise about ±0.7 ms); R1 bot submits whole words (no per-character typing); R1 and R2 do not log spike counts; the windowed runs shared the desktop with other apps; Expert lane capacity was not part of the comparison.

**Breach feedback (owner request):** `MeteorDefenseController.DamageFeedback`: a red overlay (first canvas child, so it sits below the HUD, peak alpha 0.26 fading over 0.4 s) plus a 0.25 s camera shake (amplitude 0.12, decaying). Reduced motion: alpha 0.14, no shake. The camera is restored afterwards. Test `BreachFlashesRedAndShakesBrieflyThenRestores`.

**Git tracking:**
- Only `game/.gitkeep` is tracked. `game/New Unity Project/` (345 versionable files: Assets 311 including .meta, ProjectSettings 24, Packages 2, Tools 1, ContentPackFixtures 5, ASSET_SOURCES.md, .gitignore) and `game/UXUI/` (234 MB of owner source packs; root rules ignore its 1,104 PNG/OGG) are untracked.
- The project `.gitignore` already excludes Library/Temp/Logs/UserSettings/Builds/Screenshots/AgentScripts and IDE files. Settings: Force Text serialization and Visible Meta Files. git-lfs 3.7.1 is installed.
- **Proposal (owner decision, nothing staged):**
  1. Commit `game/New Unity Project/` as it would be staged now, with .meta files.
  2. Add `.gitattributes` with Git LFS for `*.ttf *.otf *.png *.ogg *.mp3` (about 11 MB of fonts) and `*.unity *.prefab *.asset merge=unityyamlmerge`.
  3. Keep `Builds/` out of git and archive the owner-review exes elsewhere.
  4. Keep `game/UXUI/` out of git (or track only its original ZIPs via LFS), since the used assets are copied into `Assets/` with `ASSET_SOURCES.md`.
  5. Commit in slices (docs/agent, Unity project, tests) on a feature branch.

**Owner verification open:** play G008_Win64, judging wave pacing, combo and score feel, speech and SFX by ear, native JA IME, Results/Review readability, and that the history file appears under `%USERPROFILE%/AppData/LocalLow/MultimediaProject1/Word Orbit G-003 Prototype/LearningHistory/`.

## Update G-007-R3 + G-008 implementation (same day)

**G-008 implemented after owner approval.**
- `GameConfig`: wave and score parameters, `PointsFor`, `FallSeconds(term, wave)`, `SpawnInterval`.
- `MeteorDefenseSession`: waves gate `CanSpawn`, adds combo, max combo, typos, hits, per-item `ItemRecord`, `ActiveSeconds`.
- Controller: wave banner and HUD, one-slot `SpeechSlot` with a per-session clip cache, new SFX, full results, the Review button, and `LearningHistory` JSONL.
- `VocabularyPreviewController.ReviewItemIds`, `SceneNav.SetBack`.
- New tests: `G008SessionTests`, `G008AudioHistoryTests`, `G008FlowTests`. The PlayMode `SetUpFixture` redirects history to a temp folder.

**G-007-R3.** The owner reported missing words.
- Reproduced on G007_R2 and fixed in `VocabularyDeck` (D-051, deck cycles).
- Runtime evidence:
  - R2: `Logs/g007_r3/r2/`, counts 0–3, and JA Easy missed `backpack`.
  - R3: `Logs/g007_r3/r3/`, 15/15 words ×2 in each of the 5 sessions.
  - No deferral happened at runtime. Deferral coverage is proven by the EditMode simulation.

**Build and housekeeping.**
- `Builds/G007_R3_Win64` contains R2 + deck fix + G-008 (owner choice; the Unity project is untracked, so it can't be split). R2 is kept.
- Dev-bot runs skip history. The 4 bot lines were deleted from `%USERPROFILE%/AppData/LocalLow/MultimediaProject1/Word Orbit G-003 Prototype/LearningHistory/`.

**Open:** G-008 perf matrix (plan §10), G-008 spec notes, owner playtest of R3.

## Update G-008 planning (same day)

Plan only, no code/scene/build change: [G-008 plan](../game/G008_IMPLEMENTATION_PLAN_v0.1.md). Findings: `MeteorDefenseSession` already guards score-once and aborted meteors but gives flat 100 points (no multiplier/combo/waves); `VocabularyDeck` already refills 10 distinct items per wave; `PlaySpeech` interrupts older speech and reloads the clip on every answer (candidate cause of 35–63 ms spikes, unverified); only `sfx_laser1`/`sfx_zap` are imported, Kenney Bonus also has `sfx_twoTone`, `sfx_shieldDown`, `sfx_lose`, no music. R1 vs R2 perf numbers are not comparable (maxMeteorViews 3 vs 1); plan §10 defines fixed workloads. Next: owner answers O1–O6 and authorizes G-008.

## Update G-007-R2 (same day)

Character-based combat (D-044): `TypingCombat` (pure logic, NFC units, high-water-mark hits, separators free, error only on new wrong input) wired in `MeteorDefenseController.Evaluate`; one `Resolve` path for auto-complete and Enter; IME gate via `Input.compositionString` + pending evaluation; ship aims (540°/s, ±75°); pooled beams cancelled if the target leaves; damage bar and shake in `MeteorView`. Dev bot types unit by unit (`-g007TypeGap`, `-g007TabDemo`). Owner report fixed: long Fill labels near the edge are clamped by `SpawnLayout.ClampX` (D-045); console mode line made one line with autosize. Editor was closed, so `game/New Unity Project/Tools/headless.ps1 -Step Scenes|EditMode|PlayMode|Build` ran on the real project: EditMode 101/101, PlayMode 55/55, build `Builds/G007_R2_Win64` 0/0. Perf uncapped (Expert Fill, rapid bot): 1920 3.41 ms avg / p95 5.89, 1366 2.00, 1280 1.78, ~120 MB (R1: 3.16–3.20 / 1.62 / 1.49). Videos skipped at owner request. Next: owner tests R2 and reports; G-008 not started.

## Update G-007-R1 (same day)

Owner decided image hints are not needed in gameplay (D-043, CONFIRMED). Removed `HintMode.TextAndImage` / `ImageOnly`, picture preloading and sprites from `MeteorDefenseController`/`MeteorView`, the image preview from `GameSetupController` and the builder, the image branches of `GameCompatibility`, and the `nearRow` parameter of `LaneChooser`. Tests replaced: image-hint PlayMode test → text-hint test (meaning always, first unit only in Nghĩa + chữ đầu, no Picture objects); compatibility test → missing image does not affect gameplay. Verified in the live Editor (no longer blocked): EditMode 87/87, PlayMode 46/46; build `Builds/G007_R1_Win64/WordOrbit.exe` 0 warnings / 0 errors; captures `Screenshots/g007_r1/` (setup EN/JA, Normal JA Fill, Expert EN No Hint, safe spawn 1280×720, Easy JA Fill victory 30/30 HP 5/5). The G-007 gallery is marked partly superseded. The "Environment note" below is resolved: scene rebuilds now end by opening a saved scene so no modal appears.

## Status

**G-007 IMPLEMENTED, OWNER_VERIFICATION_REQUIRED.** The owner authorised G-007 while working remotely; this is not acceptance of G-006, whose manual checks stay open. G-008 not started. No AI pipeline, Docker, Excel importer, contract, Content Pack, source asset or background change.

## Player flow

Main Menu → Vocabulary Library (pack + language) → **GameSetup** (new) → MeteorDefense. Back from GameSetup returns to the Library; Back after a finished game returns to GameSetup; Replay keeps the configuration (`GameConfig.Selected`, in memory only).

GameSetup shows the pack, language, usable-word count with exclusions and reasons, four option rows (Difficulty, Hint, Answer, Targeting), a one-line explanation per option, a live preview of a real question (image, clue, pattern, expected input) and Start. Start is disabled with a reason when the choice cannot produce at least 10 answerable questions, when no pack is selected, or for developer fixtures.

## What was built (all under `game/New Unity Project/Assets/`)

- `Scripts/Game/GameConfig.cs`: single configuration source. Enums `Difficulty`, `HintMode`, `AnswerMode`, `TargetingMode`; `WithDifficulty` applies the spec §5 table (D-038). Score multiplier stored for G-008, not applied.
- `Scripts/Game/BlankPuzzle.cs`: Fill-in-the-Blank per spec §3 (D-039).
- `Scripts/Game/GameCompatibility.cs`: configuration-specific eligibility on top of pack readiness (D-040).
- `Scripts/Game/TargetSelector.cs`: `Resolve(..., TargetingMode, typing)` and `TabAllowed` (D-041).
- `Scripts/Game/SpawnLayout.cs`: safe spawn below the HUD (D-042).
- `Scripts/Game/GameSetupController.cs` (new screen), `GameEntry.cs` (`SetupScene`, compatibility in the start gate, `GameLabels`).
- `Scripts/Game/MeteorView.cs`: optional picture (aspect kept, fixed height), clue with first-unit hint, puzzle display, `StackTop`.
- `Scripts/Game/MeteorDefenseController.cs`: uses `GameConfig.Selected`; preloads pictures before play for image modes (failed images exclude the item, logged `G007_MEDIA`); per-meteor puzzle seeded from session seed + spawn number; spawn below HUD with a 0.25 s fade-in; targeting modes; two-line header with the configuration; mode-specific help text; Image Only toasts never reveal the meaning; releases picture textures on exit.
- `Scripts/Game/LaneChooser.cs`: optional `nearRow` so tall image stacks keep labels apart.
- `Scripts/Library/VocabularyLibraryController.cs`: Play goes to GameSetup.
- `Scripts/Dev/MeteorDefenseDevBot.cs`: answers puzzles, presses Tab in Manual. `Scripts/Dev/DevCommandLine.cs`: perf log adds `maxMeteorViews`.
- `Editor/G003Builder.cs`: GameSetup scene, two-line MeteorDefense header, help label wired; `Editor/BatchBuild.cs`: headless `RebuildScenes` and `Windows` build entry points.
- Tests: `Tests/EditMode/G007LogicTests.cs` (presets, puzzles, compatibility, targeting, safe spawn); `Tests/PlayMode/GameConfigFlowTests.cs` (setup flow, fixture block, Fill mode + Tab stability, image association and aspect, Manual/Auto, Expert limits + safe spawn, rapid answers audio, full v47 matrix); `MeteorDefenseFlowTests` and `SceneSmokeTests` updated for the new step.

## Verification actually run

- EditMode **87/87**, PlayMode **46/46** (Unity 6000.6.10f1 batchmode on a temporary copy of the project, see below). PlayMode tests force a 16:9 camera aspect because headless runs default to 4:3.
- v47 matrix (both languages × 4 hints × 2 answer modes × 4 difficulties × 3 targeting): every configuration has 15/15 usable words; every usable word's puzzle is solvable. No shared images, no shared clues in v47.
- Build `game/New Unity Project/Builds/G007_Win64/WordOrbit.exe`: Windows x64 Development, 0 warnings, 0 errors. G006_Win64 and older builds kept.
- Standalone bot runs: Easy victory 30/30 correct, 1 deliberate wrong, HP 5/5, score 3000; Expert Game Over (2 missed, HP 0); four 28 s videos with 4–6 correct answers each and matching speech loads; Manual run with Tab acquisition.
- Performance, final build (GTX 1650, i5-10300H): see table in STATE/TASKS; Expert with images peaks at 3 meteors on screen.
- Evidence: `game/New Unity Project/Screenshots/g007/` (19 PNG, 4 MP4, `index.html` gallery). Logs and test XML in `game/New Unity Project/Logs/g007/`.
- Protected data unchanged: v47 `content_pack.json` a1b713c4, v46 b64819fd, background b33cc978, `game/UXUI/` last write 2026-11-26.

## Environment note (important for the next session)

The interactive Unity Editor (pid 10036) was left blocked on a modal "Scene(s) Have Been Modified" dialog after the first scene rebuild; the agent could not click it (computer-use was not approved) and closing the Editor was refused by the safety classifier. All later work ran headless on a temporary copy (`game/.batch_copy/`, deleted afterwards). The final generated scenes were copied back into `Assets/Scenes/`. **When the owner returns: choose "Don't Save" in that dialog** (saving would write the Editor's older in-memory scene over the new one); if in doubt, run `MP1.EditorTools.G003Builder.BuildAll()` again.

## Findings for G-008 / owner

- Expert's cap of 5 is rarely reached: label-overlap avoidance with tall image stacks keeps 2–3 meteors on screen at 16:9.
- Single frame spikes of 35–63 ms in stress runs (p95 stays ≤ 5.4 ms uncapped); likely clip or glyph loading. Not optimised.
- Image Only cannot judge whether an image fits an abstract word; v47 images all passed owner image_relevance review, so none were excluded. Owner content review decides.
- Newest pronunciation interrupts the older one (G-006 behaviour); rapid-answer test confirms the newest word is the one playing. Final audio queue policy is G-008.
- Videos have no audio (frame capture only).

## Open owner checks

Japanese IME in the build; pronunciation by ear; responsiveness and difficulty balance; visual approval of GameSetup and gameplay; outstanding G-003/G-004/G-006 manual checks; lecturer acceptance of a desktop submission.

## Next

Owner reviews the gallery and plays G007_Win64. G-008 (waves, combo/score multiplier, results/learning history, audio policy) starts only on owner instruction.
