# G-002 Game Asset Inventory — DRAFT

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Status:** Source assets are present; selection remains **PROPOSED / OWNER_REVIEW_REQUIRED**, 2026-11-26. This checklist points to the detailed [Asset Audit](ASSET_AUDIT.md), [Visual Design System](VISUAL_DESIGN_SYSTEM.md) and [VFX Plan](VFX_PLAN.md). It is not a Unity import manifest.

The owner has downloaded and extracted three Kenney packs and Noto fonts into `game/UXUI/`. Keep all four original ZIPs, extracted assets and license files unchanged. The separate protected [background plan](../../game/background/background_idea.md) is retained as the primary background design reference; no pack texture replaces it automatically. Asset paths below are relative to `game/UXUI/`.

| Need | Candidate source / classification | Remaining work |
|---|---|---|
| Galaxy background | Existing `game/background/background_idea.md`: design source. `kenney_space-shooter-remastered/Backgrounds/blue.png`: **ALTERNATIVE** texture | Owner approves adaptation and readability; no final background asset yet. |
| Starfield, parallax, twinkling | **PROCEDURAL** with sparse stars and 2D layers; `kenney_space-shooter-remastered/PNG/Effects/star1.png` is an optional sprite | Test motion outside learning text; reduced-motion state. |
| Nebula and planets | Nebula **MISSING / NOT_REQUIRED**; `kenney_planets/Planets/planet06.png` **ALTERNATIVE** menu decoration | Planet's shading differs from gameplay; no prominent gameplay use proposed. |
| Player ship and variants | `kenney_space-shooter-remastered/PNG/playerShip2_blue.png` **RECOMMENDED**; `playerShip1_blue.png`, `playerShip3_blue.png` **ALTERNATIVE** | Visual composite and scale review. |
| Engine and shield | `kenney_space-shooter-remastered/PNG/Effects/fire00.png`–`fire19.png`, `kenney_space-shooter-remastered/PNG/Effects/shield1.png` **RECOMMENDED** inputs; animation **PROCEDURAL** | Limit particle count, test HP cue. |
| Primary/additional meteors | `kenney_space-shooter-remastered/PNG/Meteors/meteorGrey_big1.png` **RECOMMENDED**; Grey/Brown size variants **ALTERNATIVE** | Test long-word label independent of sprite rotation. Crystal meteor **MISSING / NOT_REQUIRED**. |
| Debris, trail, impact, explosion | **PROCEDURAL** from meteor/star/fire inputs; no dedicated explosion named in pack | Small burst only; shockwave **NOT_REQUIRED** initially. |
| Laser and target lock | `kenney_space-shooter-remastered/PNG/Lasers/laserBlue01.png`, `kenney_ui-pack-space-expansion/PNG/Blue/Default/crosshair_color_a.png` **RECOMMENDED** | Reticle must remain visible without obscuring text. |
| Menu, settings, selection, results and Flashcard panels | `kenney_ui-pack-space-expansion/PNG/Extra/Default/panel_rectangle.png` **RECOMMENDED for layout trial** | One consistent panel family; verify long EN/VI/JA text. |
| Buttons and basic controls | `kenney_ui-pack-space-expansion/PNG/Blue/Default/button_square_header_large_rectangle.png` **RECOMMENDED for layout trial** | Test contrast and label width; no baked text. |
| HP, score, combo and progress | `kenney_space-shooter-remastered/PNG/UI/playerLife2_blue.png`; `kenney_ui-pack-space-expansion/PNG/Blue/Default/bar_round_large.png`; live TMP text | Pause/back/audio-specific icons **MISSING**; labeled controls can serve until icon selection. |
| Main and vocabulary font | `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Regular.ttf` and `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Medium.ttf` **RECOMMENDED for TMP trial** | Local EN/VI/JA sample glyph check passed; actual TMP render, IME, long strings and atlas memory unverified. |
| Font alternative/logo | `Noto_Sans,Noto_Sans_JP/Noto_Sans/static/NotoSans-Regular.ttf` with Noto Sans JP fallback **ALTERNATIVE**; Kenney Future **REJECTED** for content text, possible short logo only | No final typography approval. |
| SFX | Seven files in `kenney_space-shooter-remastered/Bonus/`: `sfx_laser1.ogg`, `sfx_laser2.ogg`, `sfx_lose.ogg`, `sfx_shieldDown.ogg`, `sfx_shieldUp.ogg`, `sfx_twoTone.ogg`, `sfx_zap.ogg` **ALTERNATIVE pending listening** | Match sounds to events only after listening and volume check. Correct/wrong, explosion, target lock and UI sound are not confirmed. |
| Music | **MISSING / NOT_REQUIRED** for first pass | Optional only; speech priority and mute control if later included. |
| Vocabulary media | Existing validated Content Pack image and EN/JA pronunciation assets | Reuse by item status and rights. Never copy them into the game-art kit or infer approval from files. |

## Candidate import strategy for a later Unity task

Keep `game/UXUI/` as the immutable source library. After owner selection, import only chosen PNGs, font faces and listened-to SFX into a future Unity `Assets/Art/{Backgrounds,Spaceships,Meteors,VFX,UI}`, `Assets/Fonts` and `Assets/Audio`. Unity-generated atlases, prefabs and materials would be separate from originals. Preserve exact source path, pack name, author and included license in a selected-asset manifest. Do not copy all 1,576 extracted files into Unity.

The target machine is a 10th-generation Intel Core i5, 16 GB RAM and GTX 1650. Prefer light 2D sprites and limited effects; no performance benchmark exists. No Unity project, ZIP kit, background replacement, generated asset, import or paid package is part of G-002 documentation execution.
