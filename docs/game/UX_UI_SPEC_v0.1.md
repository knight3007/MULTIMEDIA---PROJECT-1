# G-002.1 UX/UI Spec v0.1 — DRAFT

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Status:** Proposed for owner review, 2026-11-26. Screen design and numerical game values are not approved. This is a planning specification, not production Unity UI.

The [GDD](GDD_v0.1.md) owns product requirements. [User Flow](USER_FLOW_v0.1.md) owns routes. This document describes screen behavior and compatibility without restating the Excel or Content Pack schemas.

## Screen inventory

| ID / screen | Purpose and required information | Actions and destinations | Required UI components; dependencies | Empty, loading and error states |
|---|---|---|---|---|
| S01 Main Menu | Enter Play, Flashcard, Library, Settings or Exit; show current pack only if valid | Play/Flashcard → S02; Library → S02; Settings → S11; Exit | Clear navigation buttons, focus indicator; application shell | No pack: direct player toward Library. Pack check pending: avoid promising Play. Error: link to Library diagnostic. |
| S02 Vocabulary Library | Inspect pack name/ID, version, language support, `ready` count and unavailable count | Select pack → S05; Import → S03; Back → S01 | List, pack detail, state badges and action buttons; pack loader/validator | Empty: import/prebuilt-pack guidance. Loading: progress. Broken pack or zero `ready`: visible reason and disabled Continue. |
| S03 Import Excel | Select workbook, see validation errors/warnings and normalized preview | Select/replace file; confirm valid preview → S04; Back → S02 | File picker, row/column error list, preview, warning acknowledgement; Excel v1 validator | Empty: accepted format help. Loading: validation progress. Any error: no job. Warnings alone: confirmation needed. |
| S04 AI Processing Progress | Show actual job stage, per-item completed/failed/needs-review counts and next action | Inspect, retry/resume if supported, return to S02 after result | Progress indicator, status list, safe diagnostic panel; optional local Docker handoff and pack validation | Docker unavailable, interrupted, failed or partial: explicit state; generated media is never shown as owner approved. |
| S05 Language Selection | Choose EN–VI or JA–VI for the selected pack; show eligible count | Select → S06 for Play or S10 for Flashcard; Back → S02 | Two mode controls, sample text and audio labels, eligibility count; validated pack | Zero eligible items for a mode: disable Continue and explain. |
| S06 Game Configuration | Pick difficulty, hint, answer and targeting; preview a representative question and compatible-item count | Start → S07; Back → S05 | Choice controls, preview, count and warnings; question eligibility filter | Zero compatible questions: block Start; never silently alter the user's choices. |
| S07 Meteor Defense | Keep Vietnamese prompt, source puzzle, active target and input legible; show HP, score, combo, wave | Type, target by approved rule, Pause → S08; end → S09 | Text input with IME composition, target reticle, meteor sprites, HUD, audio and effects; game/content runtime | Wave loading: short visible pause. Media invalid mid-run: stop safely with diagnostic. Audio error: nonblocking indicator. |
| S08 Pause | Resume or leave an active run | Resume → S07; restart → S07; quit → S01 after confirmation | Overlay with keyboard focus and explicit buttons | Prevent accidental quit; resolve active IME composition before game shortcuts. |
| S09 Game Results | Show outcome, score, correct/missed items, pack/language/configuration | Replay → S06/S07; Review → S10 [proposed]; Library → S02; Menu → S01 | Summary, item list, buttons; result data | Empty review subset: explain/disable Review. Local save error: show result regardless. |
| S10 Flashcard | Show source term, Vietnamese meaning, suitable image and selected-language audio | Flip, previous/next, replay audio, Back → S05 or S09 | Large text, image area, audio and navigation controls; pack media | Empty set: explanation. Missing image/audio: explicit unavailable state, no fabricated substitution. |
| S11 Settings | Set speech/SFX/music volume, text size and reduced motion [proposed] | Save/Cancel → prior screen | Sliders/toggles, keyboard help, save feedback; local preferences | Persistence failure: report and keep current visible values. |

## Typography: mandatory compatibility gate

**Owner update:** English, Vietnamese and Japanese must all remain readable in the asset/UI direction. This applies to vocabulary, hints, menus, HUD, Flashcard and text near meteors. Decorative science-fiction lettering may be considered only for a short logo; it is not a vocabulary font.

**Preferred candidate for evaluation, not a final font selection:** Noto Sans JP. Google Fonts metadata lists Japanese, Latin, Latin Extended and Vietnamese subsets, OFL licensing and a weight axis from 100 to 900. This is evidence for *candidate coverage*, not proof that a particular Unity TextMeshPro atlas contains every glyph or renders every line well. Noto Sans plus Noto Sans JP, and IBM Plex Sans plus IBM Plex Sans JP, remain alternatives. IBM documents Vietnamese in its extended Latin set and a Sans JP variant. [Noto Sans JP metadata](https://github.com/google/fonts/blob/main/ofl/notosansjp/METADATA.pb), [Noto Sans metadata](https://github.com/google/fonts/blob/main/ofl/notosans/METADATA.pb), [IBM Plex typeface](https://www.ibm.com/design/language/typography/typeface/).

| Gate | Proposed check before any font/asset approval |
|---|---|
| Glyph coverage | English words; Vietnamese `ă â ê ô ơ ư đ` with all tone marks; Hiragana, Katakana and required Kanji, including imported words. Mixed UI text such as `Score · Điểm · スコア`. No missing-glyph boxes. |
| Weights and hierarchy | Test Regular plus Medium/SemiBold and Bold. Candidate use: Medium/SemiBold for meteor word, meaning, Flashcard, buttons and HUD; Bold for short headings. Actual mapping follows visual tests. |
| Legibility | Read small HUD labels and large meteor/Flashcard words quickly. Keep Vietnamese marks clear; avoid overly condensed Flashcard text. Do not place texture or glow behind letterforms. |
| Layout | Test short and long EN/VI/JA strings; allow enough width, wrapping or an explicit overflow rule. Do not scale text below a readable floor to make an ornamented panel fit. |
| Unity verification | In a later prototype, inspect TextMeshPro font assets/fallbacks in the Windows build, font weight appearance, IME text and missing glyphs. Dynamic atlases carry a runtime cost; choose atlas strategy only after testing. [Unity dynamic font assets](https://docs.unity3d.com/jp/current/ScriptReference/TextCore.Text.AtlasPopulationMode.Dynamic.html). |
| License | Record official source and exact license for every font file selected later. Font binaries remain separate from an image-only asset ZIP. |

**Minimum layout strings:** `pineapple — quả dứa`, `traffic light — đèn giao thông`, `repair — sửa chữa`, `りんご`, `リンゴ`, `修理する`, and `Score / Điểm / スコア`. These samples include Kanji even though the current canonical `japanese.display` values are Kana-only; imported Excel may contain Kanji. Also test the longest real pack strings before sign-off. This check belongs in the UI/asset review rubric beside image quality.

## Gameplay readability and visual direction

The protected [background concept](../../game/background/background_idea.md) is retained as the separate primary background plan. A navy/teal gradient, sparse falling stars, layered parallax and subtle twinkling are candidate Unity 2D adaptations only after owner review. The downloaded `kenney_space-shooter-remastered/Backgrounds/blue.png` is an optional texture candidate, not a replacement. Pointer response should be limited to menu or a very small effect during play. No text-critical region should have bright stars, a strong glow or dense motion behind it. Distinguish the selected meteor by a reticle plus shape/label, not color alone. Galaxy/neon character should mainly come from panels, borders, target indicator and restrained VFX. No final background or asset design is approved by this draft.

## G-002 source-asset mapping — proposed

The screen inventory above remains authoritative for purpose, information, actions, navigation and failure states. The requested UI-01–UI-09 labels are **presentation groups**, mapped below to S01–S11. S04 AI Processing Progress and S05 Language Selection remain separate screens. All paths are exact and relative to the preserved `game/UXUI/` library. Asset keys identify proposals, not imported Unity assets.

| Key | Exact relative source path / role |
|---|---|
| `SHIP` | `kenney_space-shooter-remastered/PNG/playerShip2_blue.png` — player |
| `METEOR` | `kenney_space-shooter-remastered/PNG/Meteors/meteorGrey_big1.png` — base meteor |
| `LASER` | `kenney_space-shooter-remastered/PNG/Lasers/laserBlue01.png` — projectile input |
| `HP` | `kenney_space-shooter-remastered/PNG/UI/playerLife2_blue.png` — HP icon |
| `PANEL` | `kenney_ui-pack-space-expansion/PNG/Extra/Default/panel_rectangle.png` — restrained panel candidate |
| `BUTTON` | `kenney_ui-pack-space-expansion/PNG/Blue/Default/button_square_header_large_rectangle.png` — button candidate |
| `BAR` | `kenney_ui-pack-space-expansion/PNG/Blue/Default/bar_round_large.png` — progress/HP bar candidate |
| `RETICLE` | `kenney_ui-pack-space-expansion/PNG/Blue/Default/crosshair_color_a.png` — target indicator |
| `PLANET` | `kenney_planets/Planets/planet06.png` — optional menu decoration only |
| `FONT` | `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Regular.ttf` and `Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Medium.ttf` — text candidates |

The historical [background plan](../../game/background/background_idea.md) supplies background direction. `kenney_space-shooter-remastered/Backgrounds/blue.png` is an **alternative texture**, not the default selection. [Asset Audit](ASSET_AUDIT.md), [Visual Design System](VISUAL_DESIGN_SYSTEM.md) and [VFX Plan](VFX_PLAN.md) provide evidence, typography rules and effect limits.

| Presentation group / actual screen | Hierarchy, interaction and navigation | Source keys, planned motion and multilingual check |
|---|---|---|
| UI-01 / S01 Main Menu | Title → Play/Flashcard → Library/Settings/Exit; no-pack state guides to Library | `BUTTON`, `PANEL`, optional `PLANET`; subtle background motion only. Menu labels use `FONT`, not decorative-only Kenney font. |
| UI-02 / S02 Vocabulary Library | Pack name and `ready` count → Play/Flashcard/Import; loading, empty and broken-pack states | `PANEL`, `BUTTON`, `BAR`; restrained selection transition. Long pack names and EN/JA samples wrap. |
| UI-03 / S03 Import Excel | File → row/column validation → preview → confirm; invalid file never starts job | `PANEL`, `BUTTON`, `BAR`; no decorative animation around error text. Vietnamese error strings and workbook names need room. |
| UI-03 / S04 AI Processing Progress | Actual stage and completed/failed/needs-review counts → Library/retry if supported; interrupted/Docker-error state | `PANEL`, `BAR`, `BUTTON`; progress movement only. Never label generated media approved; long safe diagnostics wrap. |
| UI-04 / S05 Language Selection | Pack → EN–VI/JA–VI → eligible count; zero-item mode disables Continue | `PANEL`, `BUTTON`, `FONT`; short selection cue. Show English, Vietnamese and Japanese sample glyphs. |
| UI-04 / S06 Game Configuration | Difficulty/hint/answer/targeting → compatible-item count → Start; zero questions blocks Start | `PANEL`, `BUTTON`, `BAR`; static preview preferred. Source word and Vietnamese meaning must fit without clipping. |
| UI-05 / S07 Meteor Defense | Vietnamese clue and source puzzle/input → target → HP/score/combo/wave → Pause; safe media-error state | `METEOR`, `SHIP`, `LASER`, `RETICLE`, `HP`, `FONT`; VFX stay behind text. Proposed meaning above/adjacent to meteor, puzzle in a separate upright label, meteor rotation independent of text. Test long EN/JA and IME composition. |
| UI-06 / S08 Pause | Resume → Restart/Quit confirmation; keep focus visible | `PANEL`, `BUTTON`, `FONT`; short fade or instant reduced-motion state. Do not intercept active Japanese IME composition. |
| UI-07 / S09 Game Results | Outcome → score/correct/missed words → Replay/Review/Library/Menu; empty review and save-error states | `PANEL`, `BUTTON`, `FONT`; small optional score popup. Long item lists and VI meanings wrap. |
| UI-08 / S10 Flashcard | Source term → Vietnamese meaning → Content Pack image/audio → flip/previous/next; missing-media state explicit | `PANEL`, `BUTTON`, `FONT`; gentle flip without mirrored text. Large Kana/Kanji and VI diacritics stay readable. |
| UI-09 / S11 Settings | Speech/SFX/music, text size, reduced motion and keyboard help → Save/Cancel; save-error state | `PANEL`, `BAR`, `BUTTON`, `FONT`; no VFX needed. Provide multilingual preview text, not three translated menu sets by default. |

Conceptual S07 layout (placement remains owner-review material):

```text
[HP] [Wave]                         [Score] [Combo] [Pause]
             Vietnamese meaning / valid hint
                 [reticle] [meteor sprite]
             upright source puzzle label
                  input / IME composition
                         [ship]
```

Use actual text, never text baked into sprites. Meteor sprite size is only 101×84 px; the separate label is the working proposal for long words. Final label placement, panel scaling, contrast and focus behavior need a visual prototype and owner review.

## Mechanics decision register

| Topic | Status from GDD | Proposed rule to test / decision required |
|---|---|---|
| Difficulty | Multiple difficulty choices proposed; all GDD numbers provisional | Tune speed, spawn interval and simultaneous count together using reading/typing time. Easy/Normal/Hard/Expert and HP/multipliers remain unapproved. |
| Spawning and falling | Meteor Defense confirmed concept | Spawn only eligible, nonduplicate active items; cap simultaneous meteors and keep a minimum readable separation. Test Japanese input time before setting any cap/speed. |
| Auto Aim and Tab | Candidate targeting methods | Auto Aim may choose nearest defense line; lock during answer entry. Tab order, tie-break, use while IME composes and target switching remain open. |
| Partial input | Open | Decide whether switching target saves per-meteor text, clears it or requires confirmation. Never move text to a different target silently. |
| Fill-in-the-Blank | Required Answer Mode | Enter missing visible-language units in order. Hide only valid text units; short or mixed-script words need an eligibility rule. Exact unit and normalization rule remain open. |
| Full Word | Required Answer Mode | Enter entire source text. Difficulty's hidden-character ratio does not apply directly. |
| Hint / No-Hint | With and without hints required; variants proposed | Define `TEXT_AND_IMAGE`, `TEXT_ONLY`, `IMAGE_ONLY` and `NO_HINT` before implementation. Do not launch a configuration with no solvable clues. |
| Input feedback | Correct answer destroys meteor, scores and plays pronunciation | Use a compact success cue. Wrong input should indicate the location/error without masking the next question; penalty and correction window are open. |
| HP, score, combo | Proposed | Collision may reduce HP; correct answers may add score and combo. Exact formulas and whether wrong keystrokes break combo require playtest. |
| Waves, game over, victory | Proposed | Define finite-wave victory separately from survival play. Candidate loss: HP reaches zero. Wave length and escalation remain open. |
| Audio | Correct answer plays selected-language pronunciation | Speech takes priority over SFX/music. Decide queue, interrupt or drop behavior for rapid answers; missing audio cannot be replaced with the other language. |

## Question compatibility matrix

Every row also requires a validated `ready` item with playable selected-language text and media. A generated file or `needs_review` item is not enough.

| Hint Mode | Fill-in-the-Blank | Full Word | Eligibility / action |
|---|---|---|---|
| `TEXT_AND_IMAGE` | Candidate ✓ | Candidate ✓ | Vietnamese meaning plus reviewed image; do not reveal the whole answer as a hint. |
| `TEXT_ONLY` | Candidate ✓ | Candidate ✓ | Vietnamese meaning must be sufficiently distinguishing. |
| `IMAGE_ONLY` | Conditional | Conditional | Require a suitable reviewed image that can identify the intended word; otherwise exclude item. |
| `NO_HINT` | Conditional | Invalid if the whole word is hidden | Owner must define the minimum clue. Partial visible letters alone may still be ambiguous; no automatic approval. |
| Any | Invalid when nothing is missing | Invalid when source answer cannot be entered | Exclude the item/configuration and show the resulting count in S06. |

## Japanese input comparison

The current canonical 100-record dataset has 87 Hiragana and 13 Katakana `japanese.display` values, no displayed Kanji, and five non-null `written_form` fields. Imported Excel is not limited to that distribution; the contract permits Kanji text and does not promise automatic reading conversion.

| Option | Benefit | Risk and prototype check |
|---|---|---|
| Native OS Japanese IME | Handles Kana and Kanji using familiar Windows input | Composition is not a committed answer. Tab/Space/Enter can select IME candidates; verify focus, candidate-window placement and switching on a Windows build. |
| Romaji-to-Kana | Could lower setup friction for the current Kana-only display set | Does not solve imported Kanji; small Kana, doubled consonants, long vowels, Katakana and alternate spellings need rules. |
| Hybrid | Offers both entry styles | Two matching paths and user-facing mode explanation increase complexity; may score equivalent answers inconsistently. |

**Prototype recommendation only:** evaluate native IME first, with no score or targeting change while composition is active. Compare committed text against the intended source text under a reviewed normalization policy. Do not equate Hiragana with Katakana or Kanji with reading automatically. Unity documents IME composition and keyboard events, but the exact interaction with the chosen input field needs a later build test. [Unity Input System](https://docs.unity3d.com/ja/Packages/com.unity.inputsystem%401.4/api/UnityEngine.InputSystem.Keyboard.html), [Unity composition](https://docs.unity3d.com/cn/6000.0/ScriptReference/Input-compositionString.html).

## Open owner decisions and GDD updates

1. Define `NO_HINT` and the minimum solvable clue; approve or reject each hint variant.
2. Select Japanese input approach after prototype, including normalization and Kanji handling.
3. Set Tab order, Auto Aim switch timing and partial-input preservation.
4. Playtest difficulty, HP, score, combo, wave and pronunciation priority before approving numbers.
5. Approve a font only after EN/VI/JA coverage, layout, build rendering and license checks. Noto Sans JP is the first candidate, not a finalized choice.
6. Clarify in GDD that invalid/unreviewed media makes an item unavailable, and that the hidden-character ratio does not govern Full Word.

No GDD text is overwritten by this proposal.
