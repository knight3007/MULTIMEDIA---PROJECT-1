# G-002 Galaxy Source Asset Audit — DRAFT

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Inspection date:** 2026-11-26 (Asia/Saigon). **Status:** documentation completed; visual selection requires owner review. **Source root:** `game/UXUI/` (actual capitalization). This is a game-art audit, separate from Content Pack vocabulary images and pronunciation audio. No source asset was changed.

## Scope and evidence levels

The owner extracted three Kenney packs and a Noto font download. A recursive metadata pass covered all **1,576 extracted files**, plus four preserved original ZIP archives. All 1,097 PNG files opened successfully for dimension/mode inspection; all 371 SVG files parsed as XML; the sprite-sheet XML lists 294 regions. This does **not** mean every image was visually reviewed. Visual observations below are from the three pack previews and representative ship, meteor, planet, background, UI, reticle and effect PNGs. Seven OGG files were identified by filename but **not evaluated by listening**. No Unity import, TMP render, animation, build or performance test has run.

| Extracted source | Author/license evidence | Files and contents |
|---|---|---|
| `kenney_space-shooter-remastered/` | Kenney; [included CC0 license](../../game/UXUI/kenney_space-shooter-remastered/license.txt) | 314 files: 301 PNG, 7 OGG, 2 TTF, 1 SVG, 1 SWF, 1 sprite-sheet XML and license. 294 gameplay PNGs under `PNG/`; ship, meteor, laser, effects, UI, enemies and parts. |
| `kenney_ui-pack-space-expansion/` | Kenney; [included CC0 license](../../game/UXUI/kenney_ui-pack-space-expansion/License.txt) calls it **UI Pack: Sci-fi (2.0)**, although the extracted folder is named `space-expansion` | 1,117 files: 742 PNG, 370 SVG, 2 TTF and supporting files. Blue/Green/Grey/Red/Yellow/Extra variants, each with Default/Double PNG sizes. Preserve the observed name mismatch in later provenance records. |
| `kenney_planets/` | Kenney; [included CC0 license](../../game/UXUI/kenney_planets/License.txt) | 57 files: 54 PNG, license and two URL shortcuts. Ten 1280×1280 planets, 42 1024×1024 component parts and two preview/sample images. |
| `Noto_Sans,Noto_Sans_JP/` | Noto Project; [Noto Sans OFL](../../game/UXUI/Noto_Sans,Noto_Sans_JP/Noto_Sans/OFL.txt), [Noto Sans JP OFL](../../game/UXUI/Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/OFL.txt) | 88 files: 84 TTF, two license files and two READMEs. Static and variable fonts. |

Total extracted formats: **1,097 PNG, 371 SVG, 88 TTF, 7 OGG, 7 TXT, 4 URL, 1 XML, 1 SWF**. Four ZIPs remain at the source root. Representative PNG sizes: background 256×256 RGB, ship 112×75 RGBA, grey meteor 101×84 RGBA, blue button 192×64 indexed PNG, blue reticle 30×30 indexed PNG. PNG transparency/alpha or indexed transparency: planets 52/54, shooter 295/301, UI 684/742. The opaque files include previews/backgrounds. Indexed PNG transparency must be checked through the palette metadata, not inferred from the `P` mode alone.

SHA-256 comparison found **66 pairs of byte-identical files** (50 PNG pairs, 16 SVG pairs), all inside the UI pack. Most are interchangeable center segments of round/square bars; one Extra button and panel segment are identical. Other color and scale variants are visually redundant candidates but not necessarily byte-identical. **Keep all source copies**; a future selected-asset import should choose one representation per role. SVG may require an additional Unity import path, so PNG is the simplest first candidate. The SWF file is not recommended for a Unity 2D asset selection.

## Visual observations and weighted evaluation

The [Space Shooter preview](../../game/UXUI/kenney_space-shooter-remastered/preview.png) and inspected sprites have a flat arcade silhouette, pale outlines and blue/cyan accents. The [UI preview](../../game/UXUI/kenney_ui-pack-space-expansion/Preview.png) uses beveled panels and more gloss; selecting only Blue/Default and restrained Extra panels limits the mismatch. The [Planet preview](../../game/UXUI/kenney_planets/Preview.png) and inspected `planet06.png` have stronger dimensional shading and texture than the gameplay meteors. Planets are optional menu decoration, not primary gameplay art.

Scores are **provisional expert ratings from representative visual samples and file metadata**, on a 1–5 scale. The fixed rubric is visual consistency 40%, technical/Unity suitability 25%, gameplay readability 15%, checklist coverage 10%, license 10%. They are not a claim of full visual sign-off. Formula: `0.40V + 0.25T + 0.15R + 0.10C + 0.10L`.

| Set | V | T | R | C | L | Calculation | Total |
|---|---:|---:|---:|---:|---:|---|---:|
| **A: Shooter + selected Blue/Default UI + restrained procedural VFX** | 4.2 | 4.4 | 4.4 | 4.1 | 5.0 | 1.68 + 1.10 + 0.66 + 0.41 + 0.50 | **4.35/5** |
| B: Shooter with minimal native UI | 4.5 | 4.6 | 3.8 | 2.8 | 5.0 | 1.80 + 1.15 + 0.57 + 0.28 + 0.50 | **4.30/5** |
| C: A with prominent planet art during gameplay | 2.9 | 3.6 | 3.6 | 4.3 | 5.0 | 1.16 + 0.90 + 0.54 + 0.43 + 0.50 | **3.53/5** |

**Option A is the working proposal, not approved selection.** Option B is a viable simpler alternative. Set C's planet treatment is rejected for the main gameplay field because its dimensional style and visual weight compete with the meteor labels. Planet use in a menu remains an alternative.

## Exact candidate paths and current classification

Paths below are relative to `game/UXUI/`. `RECOMMENDED` means recommended **for owner review**, not imported or approved.

| Use | Relative source path | Classification / evidence |
|---|---|---|
| Background texture candidate only | `kenney_space-shooter-remastered/Backgrounds/blue.png` | ALTERNATIVE; visually inspected. The separate [background plan](../../game/background/background_idea.md) is the design source; this texture must not replace it automatically. |
| Ship | `kenney_space-shooter-remastered/PNG/playerShip2_blue.png` | RECOMMENDED; visually inspected, 112×75 RGBA. `playerShip1_blue.png` and `playerShip3_blue.png` are ALTERNATIVE. |
| Meteor | `kenney_space-shooter-remastered/PNG/Meteors/meteorGrey_big1.png` | RECOMMENDED; visually inspected, 101×84 RGBA. `meteorBrown_big1.png` is ALTERNATIVE. Long words need a separate, non-rotating label. |
| Laser / flame / shield | `kenney_space-shooter-remastered/PNG/Lasers/laserBlue01.png`; `kenney_space-shooter-remastered/PNG/Effects/fire00.png`; `kenney_space-shooter-remastered/PNG/Effects/shield1.png` | RECOMMENDED as source frames; visually inspected flame, others metadata-verified. |
| HP | `kenney_space-shooter-remastered/PNG/UI/playerLife2_blue.png` | RECOMMENDED; metadata-verified. |
| Panel / button / bar / reticle | `kenney_ui-pack-space-expansion/PNG/Extra/Default/panel_rectangle.png`; `kenney_ui-pack-space-expansion/PNG/Blue/Default/button_square_header_large_rectangle.png`; `kenney_ui-pack-space-expansion/PNG/Blue/Default/bar_round_large.png`; `kenney_ui-pack-space-expansion/PNG/Blue/Default/crosshair_color_a.png` | RECOMMENDED for layout trial; visually inspected. Keep one main UI variant. Text contrast/long labels remain to be tested. |
| Planet decoration | `kenney_planets/Planets/planet06.png` | ALTERNATIVE for menu only; visually inspected, 1280×1280 indexed PNG with transparency. |
| Font | `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Regular.ttf`; `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Medium.ttf` | RECOMMENDED for TMP trial; local cmap check passed requested EN/VI/JA samples. |
| Font alternative | `Noto_Sans,Noto_Sans_JP/Noto_Sans/static/NotoSans-Regular.ttf` + Noto Sans JP fallback | ALTERNATIVE; Noto Sans passes EN/VI samples and lacks JA glyphs. |
| Decorative font | `kenney_ui-pack-space-expansion/Font/Kenney Future.ttf`; `kenney_space-shooter-remastered/Bonus/kenvector_future.ttf` | REJECTED for vocabulary/HUD/menu text: local cmap lacks many Vietnamese diacritics and Japanese glyphs. ALTERNATIVE for a short logo only. |

The local cmap test checked `pineapple`, `traffic light`, `frequently`, Vietnamese strings/diacritics, `りんご`, `パイナップル`, `信号機`, `日本語`, `食べる`, and mixed Score/Điểm/スコア. Both Noto Sans JP Regular and Medium contain all tested code points. This is **font-file coverage only**; TMP glyph atlas, IME, line layout, long imported terms and Windows build behavior remain unverified. Noto Sans JP static Regular is about 5.7 MB; actual build/atlas memory has not been measured.

## Coverage and gaps

| Area | Available / candidate | Gap or procedural plan |
|---|---|---|
| Environment | Dark star texture; optional planets | Separate nebula not found and not required. Parallax/twinkle: PROCEDURAL under existing background plan. |
| Player and meteors | Ships, meteor sizes/colors, shield frame | Crystal/special meteor: MISSING/NOT_REQUIRED. Idle, fall, rotation and debris: PROCEDURAL. |
| Combat VFX | Lasers, flame, stars, shield, reticle | No named explosion/impact/trail/shockwave sprite; use restrained PROCEDURAL effects. Shockwave: NOT_REQUIRED. |
| UI | Panels, buttons, bars, crosshair, HP icon | No dedicated pause/back/audio icons identified; MISSING. Use labeled controls until their need is confirmed. |
| Audio | Seven OGG by filename: `sfx_laser1/2`, `sfx_lose`, `sfx_shieldDown/Up`, `sfx_twoTone`, `sfx_zap` | Sound content/level NOT LISTENED. No background music or dedicated correct/incorrect/target-lock/explosion sound verified. Music NOT_REQUIRED for first pass. |

Do not duplicate Content Pack vocabulary images or EN/JA pronunciation audio. Content Pack review state and public eligibility remain authoritative.

## Next verification before selection

Review the proposed set at actual Meteor Defense and Flashcard text sizes, hear the seven OGG files, test font rendering and fallback in a Windows Unity prototype only when implementation is authorized, verify sprite slicing/scale and texture memory, and record each selected file's source and license. Keep original ZIPs, extracted files, fonts, audio and license files unchanged. No additional asset download is required for the current documentation phase.
