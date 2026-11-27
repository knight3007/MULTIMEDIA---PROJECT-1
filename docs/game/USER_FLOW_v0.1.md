# G-002.1 User Flow v0.1 — DRAFT

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Status:** Proposed for owner review, 2026-11-26. This document refines navigation only. It does not approve open mechanics or authorize Unity implementation.

## Shared rules

- A single selected Content Pack supplies Meteor Defense and Flashcard. Keep its `pack_id`, `pack_version`, language mode and prior valid selections when navigating back.
- Language modes are `ENGLISH_TO_VIETNAMESE` and `JAPANESE_TO_VIETNAMESE`. Source text and pronunciation follow the selected language; the meaning is Vietnamese. No Vietnamese audio is generated.
- Show counts of playable `ready` items. A file existing on disk is not approval. Validate the active pack and media before use; explain unavailable items without changing review state or running AI during play.
- Back returns to the preceding screen. A destructive action such as abandoning an active game needs confirmation. After a failed import, keep the existing library intact.

## Navigation map

```text
S01 Main Menu
├─ Play → S02 Vocabulary Library → S05 Language Selection → S06 Game Configuration
│                                           → S07 Meteor Defense ↔ S08 Pause
│                                               → S09 Game Results
│                                                   ├─ Replay → S06/S07
│                                                   ├─ Review → S10 Flashcard [proposed]
│                                                   └─ S01 Main Menu
├─ (Flashcard entry removed, D-034: S02 Vocabulary Library → language → word/image/pronunciation view)
├─ Vocabulary Library → S02 → S03 Import Excel → S04 AI Processing Progress → S02
├─ Settings → S11 Settings → S01
└─ Exit [confirm only if work would be lost]
```

S02 and S05 retain an entry-purpose flag (`Play` or `Flashcard`) so Continue reaches the correct destination. S03 contains file selection, validation results and a normalized preview; there is no accepted import until the learner confirms a warning-free or warning-acknowledged preview.

## Normal paths and back navigation

| Path | Forward | Back / exit |
|---|---|---|
| Play | S01 → S02 select pack → S05 select EN/JA → S06 choose difficulty, hint, answer and targeting → S07 → S09 | S06 → S05 → S02 → S01. S07 → S08; resume returns to S07. Quit from S08 requires confirmation. |
| ~~Flashcard~~ Vocabulary viewing (D-034) | S01 → S02 Vocabulary Library → language → word view; previous/next and play selected-language audio, no flip | Word view → S02 → S01 via visible Back. |
| Excel | S02 → S03 select `.xlsx` → local validation and preview → confirm → S04 processing → validate completed Content Pack → S02 | S03 → S02 without job. During S04, back must not silently cancel a job; show its actual lifecycle and whether safe exit/resume is supported. |
| Settings | S01 → S11 → S01 | Cancel discards unsaved settings; Save reports failure if persistence fails. |

## Failure and empty routes

- **No pack or no playable items:** S02 stays usable for inspection/import; Play and Flashcard explain why they cannot start. A pack with only `needs_review` is not silently promoted.
- **No items for a language/configuration:** S05 or S06 shows the eligible count and blocks Continue. Offer a return to the previous choice, not an automatic change of hint or answer mode.
- **Invalid Excel:** S03 shows all available structural/row errors with physical row and column. It creates no import, pack or generation job; select a corrected file and retry. Warnings need explicit acknowledgement.
- **Docker unavailable, generation error, interruption or partial result:** S04 separates completed, failed and awaiting-review items; it never labels generated files as approved. Retry/resume behavior depends on the later Unity–Docker handoff design.
- **Missing or corrupt media:** disable the affected item, report a local diagnostic and allow library inspection. Gameplay does not trigger AI, alter the signed-off pack or hide the problem.
- **IME composition active:** proposed rule is to delay game-level Tab/Enter/Esc shortcuts until composition is committed or canceled. Verify in a later Windows prototype.
- **Audio playback failure:** preserve navigation and show a compact error. Do not substitute another language's audio.

## Distribution configurations

The player configuration uses prebuilt or already imported packs and needs no Docker for ordinary play. The full configuration may expose S03–S04 for local Excel processing. These are proposed configurations of one application, not authorization for two apps or a Unity–Docker interface. Desktop acceptance and any public-URL requirement remain open with the lecturer.

## Owner review gates

Confirm: (1) whether import processing lives inside the app or launches a separate local workflow; (2) whether Results can open a missed-word Flashcard subset; (3) how an active job behaves when leaving S04; (4) how Desktop submission satisfies the lecturer.

**References:** [GDD](GDD_v0.1.md), [Excel v1](../contracts/excel_v1.md), [Content Pack v1](../contracts/content_pack_v1.md).
