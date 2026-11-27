# G-002 Visual Design System — PROPOSED

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Status:** Working proposal for owner review, 2026-11-26. No palette, font, asset or background is approved for production. This document defines the visual rules to test against [UX/UI Spec](UX_UI_SPEC_v0.1.md), not new GDD gameplay requirements.

## Direction and sources

The preferred candidate is **Option A: dark Galaxy / 2D Space Arcade**. Use Kenney Space Shooter Remastered for the ship, meteors and combat sprites; use only restrained Blue/Default elements from the extracted Kenney UI pack as the main interface candidate. Planets are optional menu decoration. [Asset Audit](ASSET_AUDIT.md) records the evidence and provisional weighted scores: A 4.35/5, B 4.30/5, C 3.53/5. These numbers are not owner approval or a full visual test.

The protected [background plan](../../game/background/background_idea.md) remains the primary source for background direction. Keep its bytes and concepts intact. The pack's `kenney_space-shooter-remastered/Backgrounds/blue.png` is **only an optional texture candidate**, never an automatic replacement. Navy/teal and subtle stars come from the historical concept; the downloaded sprites lean more blue/cyan/grey. Favor whichever combination stays coherent while leaving the learning text clear.

## Trial tokens, not final color values

| Role | Trial color | Use and constraint |
|---|---|---|
| Background | `#202030` | Approximate dominant dark tone observed in the candidate blue texture; quiet area behind vocabulary. |
| Primary accent | `#59D8FF` | Target focus, key border and selected control; use sparingly. |
| Secondary accent | `#1090D0` | Close to the UI pack's blue region; use for a control surface, not a small white-text field. |
| Main text | `#F3F7FF` | English, Japanese and Vietnamese on dark panels. |
| Muted text | `#B8C9D5` | Secondary labels only; validate contrast at final sizes. |
| Success | `#71DB9B` | Correct response plus shape/text cue, not color alone. |
| Error | `#FF8A8A` | Incorrect response/validation plus text cue, not color alone. |

Calculated contrast for these trial solid colors: main text on background ≈14.9:1; cyan accent on background ≈9.7:1; success ≈9.4:1; error ≈7.1:1. Main text on the UI-blue `#1090D0` is only ≈3.3:1, below the intended 4.5:1 normal-text check. The actual UI button includes more than one color, so place labels on a stable high-contrast region or use a separate text backing; measure final composites again. These are calculations, not a Unity screenshot result.

## Shape, hierarchy and layout

- Keep one main UI treatment: simple Blue/Default buttons and restrained Extra/Default panels. Avoid mixing every color and gloss variant. Use accent green/red for semantic feedback only.
- Reserve the clearest, quietest area for Vietnamese meaning, source-language puzzle and IME text. Keep the selected meteor distinct through a reticle and label, not color alone.
- Treat spacing as a readable layout rule rather than fixed pixel claims: leave room around each meteor label; separate HUD from question area; give settings/error text enough width; test the longest real imported terms before sign-off.
- A 101×84 meteor sprite is too small to guarantee long source words on the sprite. The proposed separate label sits above or adjacent to it. Meteor sprite rotation must not rotate text. The exact label position awaits layout review.
- Use actual text for score, combo, wave, buttons and vocabulary. Do not bake any EN/VI/JA text into image assets. Provide visible keyboard focus and labels for ambiguous icons.

## Typography hierarchy and TMP plan

The owner requires English, Vietnamese including complete diacritics, and Japanese Hiragana/Katakana/Kanji in both gameplay and Flashcard. The local font cmap check in [Asset Audit](ASSET_AUDIT.md) passed all requested sample strings for the downloaded **Noto Sans JP Regular and Medium**. These are the primary candidates, not production selection. Noto Sans for EN/VI plus Noto Sans JP fallback is an alternative. Kenney Future lacks much of the required VI/JA sample coverage and is restricted to a possible short logo.

| Content | Candidate weight and behavior |
|---|---|
| Meteor source word/puzzle and Vietnamese clue | Noto Sans JP Medium; largest, high-contrast text on a calm label. Wrap or widen the label before reducing font size. |
| Flashcard term and meaning | Noto Sans JP Regular/Medium; generous width and line height, no condensed font. |
| Buttons, Library and settings | Regular or Medium; keep button text on one consistent-contrast surface. |
| HUD score/HP/combo/wave | Medium; number and short label readable at smaller size. |
| Short heading/logo | Medium or Bold candidate; decorative Kenney font only if the text is very short and its glyphs verified. |

Test in a later Unity 6 Windows build: TMP font assets and fallback order, Regular/Medium appearance, complete Vietnamese marks, Kana and imported Kanji, IME composition, long strings and line wrapping. A static atlas for fixed UI text and a dynamic path for unpredictable imported vocabulary is a **prototype option**, not a final configuration. Dynamic font atlases and the large Japanese source font may affect build/atlas memory; no measurement exists. [Unity font atlas modes](https://docs.unity3d.com/cn/6000.0/ScriptReference/TextCore.Text.AtlasPopulationMode.html). Do not assume every app menu needs three translated versions; the requirement is script coverage and content support.

## Motion and effects

Use soft stars, mild parallax, short target-lock motion and compact laser/destruction feedback. Keep glow outside glyph edges and limit full-screen light changes. Settings should offer reduced motion; when enabled, retain static target and success/error cues. [VFX Plan](VFX_PLAN.md) specifies inputs and component candidates. No animation or shader is approved by this document.

## Consistency and selection gate

Before selection, compare the ship, meteor, panel, target indicator and Flashcard frame in **one actual layout** with `traffic light / đèn giao thông`, `パイナップル`, `信号機` and longer real pack strings. Review silhouette/outline, color, gloss, scale, contrast and content visibility together. Assets that look good alone can fail the full set. Record chosen source paths and licenses; leave all originals under `game/UXUI/`. The separate background plan controls its own later approval.
