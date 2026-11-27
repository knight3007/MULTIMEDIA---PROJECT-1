# Latest handoff — G-002.9 interactive UI mockup

Updated 2026-11-27 (Asia/Saigon) by Claude Code, `main`/`57b6ccb09d25945eb4301f41af2342eb37ea2bda`. Pre-existing unrelated tracked edits and untracked files remain. The previous handoff (gameplay mechanics spec, SKILL-ZIP-001) is in [history](history/2026-11-27_before_G002_9_HANDOFF.md). No active write claim, commit or push.

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
