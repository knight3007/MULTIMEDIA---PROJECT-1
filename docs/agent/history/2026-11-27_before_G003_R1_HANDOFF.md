# Latest handoff — G-002.9 interactive UI mockup

Updated 2026-11-27 (Asia/Saigon) by Claude Code, `main`/`57b6ccb09d25945eb4301f41af2342eb37ea2bda`. Pre-existing unrelated tracked edits and untracked files remain. The previous handoff (gameplay mechanics spec, SKILL-ZIP-001) is in [history](history/2026-11-27_before_G002_9_HANDOFF.md). No active write claim, commit or push.

## G-003 checkpoint (2026-11-27): IMPLEMENTED, OWNER_VERIFICATION_REQUIRED

Owner authorized G-003 on 2026-11-27. Unity project reused in place at `game/New Unity Project/` (existing empty project; `game/unity/` not created; nothing overwritten). Unity 6000.6.10f1, Editor `E:/unity engin/6000.6.10f1/Editor/Unity.exe`, Built-in Render Pipeline, Gamma, Mono, legacy Input Manager (Editor warns it is marked for deprecation; Input System migration is a later decision). Packages added: `com.unity.ugui` 2.6.0 (uGUI + TextMeshPro), `com.unity.test-framework` 1.8.0, plus `com.unity.pipeline` 1.0.1 from UNITY-SETUP-001. Hardware seen by Unity: i5-10300H, 16 GB, GTX 1650 (D3D12).

Implemented (all provisional; Option A visuals not approved):
- G-003.2 structure: Assets/Art, Audio, Fonts, Materials, Prefabs, Scenes, Scripts, Tests, Editor; project `.gitignore`; TMP Essential Resources imported.
- G-003.3 assets: 21 files from `game/UXUI/`; mapping and licenses (Kenney CC0, Noto OFL) in `game/New Unity Project/ASSET_SOURCES.md`.
- G-003.4 `Scripts/Background/GalaxyBackground.cs`: procedural navy/teal gradient, 160 stars in 3 depth bands, constant fall and wrap, spring/damping pointer parallax, twinkle, about 2% Kenney star1 sparkles, Pulse() hook. Reduced motion (F2 or `-reducedMotion`) freezes motion. `blue.png` not used.
- G-003.5 `TypographyInput` scene: 3 font configs (Noto Sans JP Regular, Medium, Noto Sans + JP fallback), all EN/VI/JA samples, a long string, an intentional missing glyph (emoji renders as a box with a TMP warning; U+20BB7 is present in the font), live atlas info; input probe separating committed text from `Input.compositionString` and logging Tab/Enter/Esc/Backspace/Space handling (`ImeGate`).
- G-003.6 `MainMenu` scene: Play, Flashcard, Library and Settings disabled and labelled "chưa có"; Exit works; 3 technical-test entries; visible keyboard focus; 1920x1080 reference CanvasScaler.
- G-003.7 `GameplaySandbox` scene (PROTOTYPE ONLY): ship and flame, rotating meteors with upright clue/answer labels (Layout A), reticle, Tab target cycling, per-meteor drafts, Enter exact-match check, laser sprite, particle burst, score popup, SFX, shield flash on breach (no HP loss), HUD, FPS readout; F1 EN/JA, F3/F4 add/remove 5 meteors.
- G-003.8 `MediaProbe` scene: reads Content Pack v46 (`needs_review`, `test_only`) from disk; no copy, no status change; missing-file and outside-pack cases handled.
- Builder `Assets/Editor/G003Builder.cs` regenerates imports, fonts, materials and all 4 scenes (it overwrites scenes). Dev switches in `Scripts/Dev/DevCommandLine.cs` are for verification only.

Verification actually run:
- Compile OK (`unity command script recompile_status`). Console errors 0; warnings only for the Input Manager deprecation and the intentional missing glyph.
- EditMode 10/10 passed; PlayMode 7/7 passed (scenes load with background, fonts and sprites; unavailable menu entries disabled; labels upright while sprites rotate; a correct answer resolves the target and scores).
- Windows x64 Development build succeeded: `Builds/G003_Win64/WordOrbit.exe`, 177,315,744 bytes, 0 errors, 2 warnings (obsolete `FindObjectsSortMode` in `DevCommandLine`). Ignored by git.
- Real standalone captures via `-g003Capture`: `game/New Unity Project/Screenshots/build/{MainMenu,TypographyInput,GameplaySandbox,MediaProbe}_{1920x1080,1366x768,1280x720}.png` and `MediaProbe_after_selftest.png`. Layout readable at all three sizes.
- Standalone media self-test (`-g003MediaSelfTest`, log `Logs/g003/media_selftest.log`): image 683x1024 loaded; EN mp3 1.10 s and JA mp3 1.34 s loaded with isPlaying=True and advancing samples; missing file handled; outside-pack path rejected. Not checked by ear.
- Performance, standalone 1920x1080 windowed, vsync on (display-capped at about 144 Hz): MainMenu avg 6.94 ms; Sandbox with 3 meteors 7.01 ms (max 20.9 ms); 20 meteors 7.00 ms (max 27.7 ms); 40 meteors 7.08 ms (max 27.8 ms). Reserved memory 285-543 MB. Headroom above vsync not measured.
- `game/UXUI/` fingerprint and background SHA-256 unchanged.

Pending owner/manual checks (acceptance not claimed): Japanese IME composition and confirmation in the build (steps shown in TypographyInput); real-keyboard typing, Tab, Enter and the laser/particle visuals in the standalone build (code paths covered by PlayMode tests, not watched); listening to pronunciation audio and SFX; owner review of provisional visuals. Lecturer acceptance of a desktop submission remains open.

Next: owner runs the checks above. Do not start G-004 without instruction. No commit/push.

## UNITY-SETUP-001 checkpoint (2026-11-27)

Owner-requested tooling setup is done: Unity CLI 1.1.0 (winget), official Claude plugin `unity@unity-agent-plugin`, `com.unity.pipeline` 1.0.1 in `game/New Unity Project/Packages/manifest.json`. The Editor (6000.6.10f1, pid 7520) is open and connected on port 7800. Owner note: the G-002.9 HTML mockup is preview only, and the Unity build should be more professional. No gameplay or G-003 work started.

## Status and scope

**G-002.9 OWNER_REVIEW_REQUIRED; G-002 overall OWNER_REVIEW_REQUIRED; G-003 not started.** Codex built the prototype on 2026-11-26 but did not sync context. On 2026-11-27 the owner asked to continue and finish it. Changed only `game/prototypes/g0029_ui_mockup/` (`app.js`, `styles.css`, `index.html`, `README.md`, `screenshots/`), these context files, and a local `.claude/launch.json` for the preview server. Fixes: primary-button label placement on the Kenney header asset, review toolbar moved outside the 16:9 frame, SVG twin of the recommended crosshair placed behind meteors, Full Word label showing per-meteor draft or first-character hint, Text + Image thumbnails, laser aimed at selected meteor, input focus preserved across re-render, Tab skips resolved meteors, footer/help overlap, `word-break: keep-all` for JA samples, `answer=` URL parameter and toolbar Answer Mode select.

Follow-up the same day (owner request "use the UX/UI skills"): ui-ux-pro-max guideline searches and emil-design-eng review applied: 220ms screen-change transition (fade only under reduced motion), `scale(.97)` press feedback, 150ms color transitions, toast `@starting-style` entry, red label border on wrong Enter, raised minimum font sizes. `impeccable` was not run (its launcher downloads a binary; needs owner approval). 13 screenshots re-captured.

Impeccable pass (owner approved launcher download): critique scored 24/40 with 1 P0, 2 P1, 2 P2 (report in `.impeccable/critique/`). Owner chose learning-experience first, top 3, single-surface Kenney button. Fixed: flashcard recall (front hides meaning, Space/←/→), JS-driven one-way meteor descent with amber near-line state and impact (HP −1, red edge flash, named toast, combo reset), `buttonBlue.png` primary via border-image with equal heights, wrong-answer toast naming the meteor plus "Sai ·" text cue, placeholder contrast. Detector rerun on S01/S07/S10 leaves only genre styling flags (radial-halo, dark-glow, cyan bar) and nested-cards. Not done: P2 Play-now path and single simulation badge. Impeccable design hook not installed.

## Verification and limitations

- Browser pane at 1366×768: S01, S06, S07 (EN/JA, layout A/B, Full Word/Fill), S09, S10 inspected. Typing, per-meteor drafts, Tab, Enter correct-answer laser/burst/score popup and toast exercised. No broken images, no horizontal scroll, Noto JP 400/500 loaded.
- Headless Edge 1920×1080 captured all 13 screenshots, reviewed as a contact sheet. `node --check app.js` passed. Protected background SHA-256 `B33CC978…298DF4` unchanged; `game/UXUI/` untouched.
- Not verified: audio by ear, a dedicated 1280×720 visual pass, real Windows IME composition, Unity TextMeshPro. Browser rendering is not Unity evidence. Results-screen shield icon renders faintly (cosmetic, left as is).

## Next action

Owner chose label **Layout A** (D-029, 2026-11-27). Remaining owner decisions: primary-button style (Kenney header asset vs alternative), reticle style, and whether G-002 visual Option A is approved. Do not start Unity/G-003, change contracts or commit without a new instruction.
