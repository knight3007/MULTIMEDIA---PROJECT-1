# G-002 Procedural VFX Plan — DRAFT

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Status:** Planning only, 2026-11-26. No Unity scene, component, prefab, material, shader or script has been created. Paths are relative to the preserved `game/UXUI/` source library. Proposed use of Unity components requires later prototype verification.

Static sprites are sufficient inputs for many effects. Favor Sprite Renderer, Transform animation and small Animator clips; use Particle System, Trail Renderer or Line Renderer only where a continuous effect benefits. The protected [background concept](../../game/background/background_idea.md) remains the background design source. [Asset Audit](ASSET_AUDIT.md) records actual files and visual-review limits.

| Effect | Source input / planned component | Intended behavior | Complexity and performance risk | Reduced-motion behavior |
|---|---|---|---|---|
| Star twinkling | `kenney_space-shooter-remastered/PNG/Effects/star1.png` or background-plan stars; Sprite Renderer opacity / small Particle System | Sparse stars fade gently behind content | Low; too many animated stars distract from words | Static dim stars |
| Background parallax | Existing background plan; optional `kenney_space-shooter-remastered/Backgrounds/blue.png` as texture only; layered Sprite Renderer/Transform | Far layer moves less than near layer | Low–medium; extra layers and movement can disturb focus | Static layers |
| Engine flames | `kenney_space-shooter-remastered/PNG/Effects/fire00.png`–`fire19.png`; Animator or few particles | Small looping glow under ship | Low–medium; avoid particle overdraw | Single static flame or off |
| Ship idle | `kenney_space-shooter-remastered/PNG/playerShip2_blue.png`; Transform animation | Very slight bob near defense line | Low; never move answer UI with ship | Fixed ship |
| Meteor fall/rotation | `kenney_space-shooter-remastered/PNG/Meteors/meteorGrey_big1.png`; Transform + Sprite Renderer | Fall at game speed, sprite rotates mildly | Low; many simultaneous transforms need a later measured cap | Fall stays necessary; remove decorative rotation |
| Meteor trail | `PNG/Effects/star1.png`; short Trail Renderer or small Particle System | Thin trail behind falling sprite | Medium; trails can cross Vietnamese clues | Trail off |
| Laser firing | `kenney_space-shooter-remastered/PNG/Lasers/laserBlue01.png`; Sprite Renderer or Line Renderer | Brief beam from ship to selected meteor | Low–medium; cap simultaneous beams and avoid text | Brief static line/cue |
| Meteor destruction | Meteor sprite plus `PNG/Effects/star1.png` or `fire00.png`; small Particle System / sprite opacity | Compact burst at the destroyed target | Medium; no dedicated explosion sprite found; avoid screen flash and many particles | Short fade and clear target state |
| Target lock | `kenney_ui-pack-space-expansion/PNG/Blue/Default/crosshair_color_a.png`; Sprite Renderer/Transform | Persistent reticle with subtle pulse | Low; reticle must not obscure word or IME | Static reticle |
| Shield impact | `kenney_space-shooter-remastered/PNG/Effects/shield1.png`; Sprite Renderer/Animator | Short shield cue when HP changes | Low; avoid large translucent overlay | Static icon plus HP change |
| Score popup | TMP text; Transform/opacity | Small score value rises and fades | Low; many popups can clutter meteor labels | Update HUD without popup |
| UI transitions | Selected Blue/Default button and Extra/Default panel sprites; Animator/opacity | Short enter/exit while focus stays predictable | Low; long transition slows navigation | Immediate state change |
| Flashcard flip | `kenney_ui-pack-space-expansion/PNG/Extra/Default/panel_rectangle.png` plus TMP text; Transform/Animator | Narrow card at midpoint, swap content, widen | Low–medium; never mirror text or hide controls for long | Instant front/back swap |

## Readability and implementation gates

1. Meteor sprites may rotate; the Vietnamese meaning, puzzle, target label and text input are separate upright UI elements. Confirm spacing with long English and Japanese terms.
2. VFX must not cover clues, IME candidate windows, focus indicators or essential result text. Success/error feedback must remain understandable when motion is reduced.
3. Use only selected source assets in a later Unity project; keep the original ZIPs and extracted folders untouched. A later Sprite Atlas may group chosen sprites, not the entire library.
4. No frame-rate, CPU, GPU or memory benchmark exists for the i5 10th-generation / 16 GB / GTX 1650 machine. Particle counts, texture sizes and atlas strategy remain to be measured after implementation is separately authorized.

**Open:** final visual intensity, text-label placement, target-lock timing and whether optional trails/shield decoration improve learning clarity. No effect is approved merely because an input sprite exists.
