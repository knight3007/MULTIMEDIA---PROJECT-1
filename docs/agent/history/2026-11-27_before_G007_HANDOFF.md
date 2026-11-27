# Latest handoff — G-006 Meteor Defense Core Implementation

Updated 2026-11-27 (Asia/Saigon) by Claude Code, `main`/`57b6ccb`. Nothing committed or pushed. Pre-existing unrelated tracked edits and untracked files remain. The previous handoff (G-002.9 to G-004-R1) is in [history](history/2026-11-27_before_G006_HANDOFF.md). No active write claim.

## Status

**G-006 IMPLEMENTED, OWNER_VERIFICATION_REQUIRED.** G-007 not started. No AI pipeline, Docker, contract, source asset, background or Content Pack change.

## What a player gets

1. Main Menu "Chơi Meteor Defense" opens the Vocabulary Library in play mode.
2. The player picks a pack and presses "Chơi English → Tiếng Việt" or "Chơi 日本語 → Tiếng Việt". The buttons are enabled only for a non-fixture pack with at least 10 eligible items in that mode.
3. MeteorDefense scene: meteors fall with the Vietnamese meaning above and the answer label below (Layout A). The nearest meteor to the defense line is targeted automatically; Tab cycles targets; each meteor keeps its own draft. Enter checks the Full Word answer (NFC + trim; English case-insensitive; Japanese exact stored script, no romaji). Correct: laser, burst, +100, pronunciation in the source language (a newer clip interrupts an older one). Wrong: red flash and a toast, no HP loss. Breach: -1 HP once.
4. Esc, the Pause button or Back pauses: Resume, Restart, Main Menu (two-step confirm). Session ends in Victory (30 spawn events resolved, HP > 0) or Game Over (HP 0). End panel: Replay, Library, Main Menu, with missed words listed.

Provisional Normal values (D-037) live in `Assets/Scripts/Game/GameConfig.cs`. Developer fixtures (D-036) are hidden from the default Library and cannot start a game.

## Files (all under `game/New Unity Project/`)

- New: `Assets/Scripts/Game/{GameConfig,VocabularyDeck,AnswerChecker,TargetSelector,LaneChooser,MeteorDefenseSession,MeteorView,MeteorDefenseController,GameEntry}.cs`, `Assets/Scripts/Content/PackAudience.cs`, `Assets/Scripts/Dev/MeteorDefenseDevBot.cs`, `Assets/Tests/EditMode/GameLogicTests.cs`, `Assets/Tests/PlayMode/MeteorDefenseFlowTests.cs`, scene `Assets/Scenes/MeteorDefense.unity` (generated).
- Changed: `Assets/Editor/G003Builder.cs` (MeteorDefense scene, Main Menu Play, Library play buttons), `Assets/Scripts/UI/MainMenuController.cs`, `Assets/Scripts/Library/VocabularyLibraryController.cs`, `Assets/Scripts/Dev/DevCommandLine.cs` (frame recording, perf count), `Assets/Tests/PlayMode/SceneSmokeTests.cs`.

## Verification actually run

- EditMode 66/66, PlayMode 34/34 (real v47 pack: both modes, correct/wrong/empty, Tab drafts, breach, pause, Back, Game Over, Victory + Replay, start gate with no selection and with fixture b001, Main Menu → Library gating). Console errors 0.
- Build `Builds/G006_Win64/WordOrbit.exe`: Windows x64 Development, 0 warnings, 0 errors.
- Standalone runs with the verification bot (`-g006Bot`): Victory 30 correct, score 3000, HP 4/4; Game Over 4 missed, HP 0. EN/JA clip load 7–27 ms.
- Performance (1920×1080, MeteorDefense, before the lane fix; the fix changes only lane choice): vsync on avg 6.95 ms (143.9 FPS), vsync off avg 2.98 ms (335.6 FPS), p95 5.08 ms.
- Captures in `Screenshots/g006/`: library entry; EN and JA gameplay at 1920×1080, 1366×768, 1280×720 (several meteors, target lock, laser/burst); wrong feedback; pause; victory; game over; recording `g006_gameplay_EN_1280x720.mp4` (30 s, bot play).
- Protected data: v47 `content_pack.json` SHA-256 prefix a1b713c4, v46 b64819fd, background b33cc978 — unchanged. `game/UXUI/` last write 2026-11-26.

## Bug found and fixed during verification

All meteors spawned in the leftmost lane: free lanes had infinite clearance, so the random tie-break never mattered. `LaneChooser` now caps clearance and has a regression test.

## Open owner checks

- Japanese IME typing in the build (only simulated input was tested).
- Pronunciation by ear in game.
- Playfeel and balance of D-037 values; visual approval of the scene.
- A meteor's clue label sits behind the top HUD for about one second after spawning; acceptable for entry, but say so if it bothers you.
- G-003 manual checks remain open.

## Dev command-line switches (verification only)

`-g004Pack <dir> -g006Play EN|JA -g006Seed N -g006Bot win|lose -g006BotDelay s -g006WrongFirst -g006PauseAt s -g006TimeScale x -g006Record <dir> -g006RecordSeconds s -g006RecordStart s`, plus the G-003 switches `-g003Scene -g003Capture -g003Delay -g003Perf -g003NoVsync`.

## Next

Owner plays the G-006 build and reports. G-007 (difficulty, combo, waves, hint matrix, history) starts only on owner instruction.
