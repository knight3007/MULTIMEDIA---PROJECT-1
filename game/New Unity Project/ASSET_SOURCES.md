# G-003 imported asset sources

Status: **PROVISIONAL sandbox candidates** (G-002 visual Option A is not owner-approved). Copied 2026-11-27 from the read-only library `game/UXUI/`; originals, ZIPs and licenses there are unchanged (tree fingerprint before = after `1e24458e…d590c1d1`, 1,580 files). No file was edited or upscaled.

| Imported path (`Assets/…`) | Source (`game/UXUI/…`) | Pack / license |
|---|---|---|
| `Art/Sprites/Ship/playerShip2_blue.png` | `kenney_space-shooter-remastered/PNG/playerShip2_blue.png` | Kenney Space Shooter Remastered, CC0 (`Art/Licenses/kenney_space-shooter-remastered_license.txt`) |
| `Art/Sprites/Meteors/meteorGrey_big1.png`, `meteorGrey_big2.png`, `meteorBrown_big1.png` | `kenney_space-shooter-remastered/PNG/Meteors/…` | same |
| `Art/Sprites/VFX/laserBlue01.png` | `kenney_space-shooter-remastered/PNG/Lasers/laserBlue01.png` | same |
| `Art/Sprites/VFX/shield1.png`, `fire00.png`, `star1.png` | `kenney_space-shooter-remastered/PNG/Effects/…` | same |
| `Art/Sprites/UI/buttonBlue.png`, `playerLife2_blue.png` | `kenney_space-shooter-remastered/PNG/UI/…` | same |
| `Audio/SFX/sfx_laser1.ogg`, `sfx_zap.ogg`, `sfx_twoTone.ogg`, `sfx_shieldDown.ogg`, `sfx_lose.ogg` (last three G-008) | `kenney_space-shooter-remastered/Bonus/…` | same; **not listened to yet** |
| `Art/Sprites/UI/crosshair_color_a_double.png` | `kenney_ui-pack-space-expansion/PNG/Blue/Double/crosshair_color_a.png` (2× of the recommended Default file) | Kenney UI Pack Space Expansion, CC0 (`Art/Licenses/kenney_ui-pack-space-expansion_License.txt`) |
| `Art/Sprites/UI/panel_rectangle.png` | `kenney_ui-pack-space-expansion/PNG/Extra/Default/panel_rectangle.png` | same |
| `Fonts/NotoSansJP-Regular.ttf`, `NotoSansJP-Medium.ttf` | `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/…` | SIL OFL 1.1 (`Fonts/Licenses/NotoSansJP_OFL.txt`) |
| `Fonts/NotoSans-Regular.ttf` | `Noto_Sans,Noto_Sans_JP/Noto_Sans/static/NotoSans-Regular.ttf` | SIL OFL 1.1 (`Fonts/Licenses/NotoSans_OFL.txt`) |

## Import settings (set by `Assets/Editor/G003Builder.cs`)

Sprites: Texture Type Sprite (Single), 100 pixels per unit (camera orthographic size 5.4 = 1080 px tall), Bilinear filter, no mipmaps, Uncompressed, Alpha Is Transparency, Clamp, centre pivot, Full Rect mesh. 9-slice borders: `buttonBlue.png` 10 px, `panel_rectangle.png` 16 px.

Fonts: three TextMeshPro **Dynamic** SDF font assets (`Fonts/* SDF.asset`, 72 pt sampling, padding 7, SDFAA, 1024×1024, multi-atlas on, dynamic data cleared on build). Glyphs are added on demand, so imported vocabulary needs no pre-baked CJK atlas. `NotoSans-Regular SDF` falls back to `NotoSansJP-Regular SDF`.

Not copied into Assets: Content Pack media. `MediaProbe` reads the private test pack `reports/EXCEL_15_SMOKE/run-bc2d5460-…/content_pack_v46/` from disk (items stay `needs_review`, `test_only`).

Procedural (no asset): background gradient and star dots (`GalaxyBackground`). `Backgrounds/blue.png` was **not** used, so it does not replace the protected background concept.
