# Game Design Document v0.1 — DRAFT

> **Owner decision 2026-11-27 (D-034):** the standalone Flashcard feature (G-005) is **CANCELLED — merged into the Vocabulary Library**. Viewing a word, its Vietnamese meaning, the shared image and the selected-language pronunciation stays in the Vocabulary Library; there is no separate Flashcard screen, card flip or review mode, and no Flashcard entry in the Main Menu. Phase numbers are not renumbered. Flashcard mentions below are historical unless marked otherwise.

**Project:** Multimedia Project 1
**Product direction:** Unity Desktop 2D preferred; Windows x64 proposed
**Status:** Planning draft for owner review, 2026-11-25. Gameplay details and numeric tuning are not approved by this document.

## 1. Vision and scope

An educational, noncommercial vocabulary application with exactly two primary features: **Meteor Defense**, a typing game, and **Flashcard** learning. No other mini-game is selected. Future extensions are TBD. The existing AI Multimedia Pipeline remains a reusable engine independent of the game:

```text
Excel → AI Multimedia Pipeline → Content Pack → Unity application
```

The owner reports accepting the results of the new 15-word multimedia review. That acceptance does not automatically approve every asset in other packs or clear public distribution rights. The pipeline's existing review states and provenance remain authoritative.

## 2. Decision register

| Status | Design direction |
|---|---|
| CONFIRMED | Two primary features: Meteor Defense and Flashcard; typing is the game's primary combat action. English–Vietnamese and Japanese–Vietnamese use shared vocabulary records and semantic images. No Vietnamese audio generation. |
| CONFIRMED | The Python AI Pipeline remains independent. Normal gameplay uses stored Content Pack media and requires no continuous AI inference. Existing background work is protected as a historical reference. |
| PREFERRED | Unity Desktop 2D over Web to reduce deployment and AI hosting complexity. This preference supersedes the earlier Web-first product direction for planning; it is not evidence of lecturer approval. |
| PROPOSED | Windows x64 target, Unity stack, local integration, UI flows, targeting variants, difficulty values, hint variants, distribution configurations, and roadmap. |
| OPEN | Lecturer acceptance of desktop submission; whether a public URL is still required for this direction; exact Unity/Docker interface; Japanese input method; targeting rules; hint semantics; scoring and wave formulas; visual design. |
| OUT_OF_SCOPE | Multiplayer, online leaderboard, accounts, cloud infrastructure, public AI backend, additional mini-games, mobile app, monetization, complex bosses and power-ups. |

The lecturer requires a publicly accessible URL **if the product is implemented as a website**. No evidence confirms lecturer approval of a desktop alternative. The conditional website requirement and any desktop submission requirement need owner confirmation with the lecturer.

## 3. Platform and architecture

The proposed target is a Windows x64 Unity Desktop 2D application. The owner's development machine has a 10th-generation Intel Core i5, 16 GB RAM and an NVIDIA GTX 1650; exact CPU model and VRAM capacity are unverified. No performance benchmark is claimed.

Separate three responsibilities:

1. **Unity application:** menus, Flashcard, Meteor Defense, settings, local progress, Content Pack reading and multimedia playback.
2. **Existing Docker AI Multimedia Pipeline:** optional Excel-to-media processing outside normal gameplay. Its packaging and execution are a separate completed task; G-001 changes no pipeline or Docker files.
3. **Local Content Pack storage:** vocabulary JSON, semantic images, English and Japanese pronunciation audio, with existing status, provenance and eligibility rules intact.

Unity reads compatible Content Packs. Do not rewrite the Python pipeline in C#. Prefer a simple local handoff before an API or database. The exact Unity-to-Docker mechanism, process lifecycle, validation boundary and failure recovery remain open. Newly imported Excel is processed outside normal gameplay. No AI inference runs continuously during play.

### Proposed technology stack

Unity 6 LTS (exact version TBD), C#, Unity 2D, uGUI, TextMeshPro, Unicode-capable EN/JA/VI fonts, 2D sprites, AudioSource, existing Python Docker pipeline, JSON Content Packs and local file storage. G-001 does not install or initialize any of these.

## 4. Shared vocabulary and language modes

Both features consume the same item records and semantic images from default or compatible imported Content Packs. The player selects English–Vietnamese or Japanese–Vietnamese. Display and answer text use the selected source language; Vietnamese supplies the meaning. Correct answers play the existing English or Japanese pronunciation audio for that mode. Vietnamese pronunciation audio is not generated.

Missing, unsuitable or unreviewed media must remain explicit; file existence does not imply human approval. The runtime should degrade gracefully for missing media without fabricating assets or changing the Excel or Content Pack contracts during G-001.

## 5. Meteor Defense

The detailed [Gameplay Mechanics Specification v0.1](GAMEPLAY_MECHANICS_SPEC_v0.1.md) records the owner's choices for a planning draft and provisional, testable rules. It does not approve the GDD's open balancing, Unity input or visual decisions.

Inspired by Chicken Invaders, vocabulary meteors fall toward a spaceship or defense base from the top of the screen. Each meteor represents a vocabulary item. The player types the correct answer for the selected meteor to destroy it. The conceptual default shows the Vietnamese meaning above the meteor, a vocabulary puzzle on or near it, and a visible target indicator. A correct completed answer destroys the meteor, awards score, plays the selected language's pronunciation, shows an appropriate destruction effect and makes another target available.

### Targeting — proposed

Support Tab-based targeting and/or Auto Aim. Candidate modes are **Auto Aim + Tab** and **Manual Tab targeting**. Auto Aim would prioritize the meteor nearest the defense boundary. The target must not change automatically during an answer in progress. Exact Tab order, switching behavior, partial-input preservation and tie-breaking remain open.

### Difficulty — proposed, subject to balancing

| Parameter | Easy | Normal | Hard | Expert |
|---|---:|---:|---:|---:|
| Falling speed | Slow | Medium | Fast | Very fast |
| Concurrent meteors | 1–2 | 2–3 | 3–5 | 4–6 |
| Hidden character ratio | 25% | 50% | 75% | 90% |
| Starting HP | 5 | 4 | 3 | 2 |
| Score multiplier | x1 | x1.5 | x2 | x3 |

All numbers are provisional. Difficulty, Hint Mode and Answer Mode are independently configurable.

### Hint Mode — required capability, proposed options

Provide play with and without hints. Candidate settings are `TEXT_AND_IMAGE`, `TEXT_ONLY`, `IMAGE_ONLY` and `NO_HINT`. The precise meaning of `NO_HINT` is open. A configuration must never create an impossible question, including a fully hidden answer with insufficient clues. `IMAGE_ONLY` requires an available, suitable image; an item without one needs a safe fallback or exclusion decided in later design.

### Answer Mode — two required modes

- **FILL_IN_THE_BLANK:** type only the missing characters in displayed order. Vietnamese `quả dứa`, puzzle `p _ n e _ p p l e`, input `ia`, completed answer `pineapple`.
- **FULL_WORD:** type the entire vocabulary word. For the same puzzle, input `pineapple`.

Hiding the entire source word is an additional proposal only when meaningful clues remain. Puzzle generation and matching must account for short words, multi-word expressions, spaces and punctuation. The exact normalization and error feedback rules are open.

### Japanese entry — open design decision

Japanese gameplay must permit actual Japanese vocabulary entry, not just a Latin transliteration. Evaluate native Japanese IME, romaji-to-kana conversion and support for both. Test Hiragana, Katakana, Kanji, small Kana, long vowels and active IME composition; imported words must not be assumed Kana-only. Select the final method during a later prototype without altering the existing Excel or Content Pack schema in G-001.

### Other mechanics — proposed

HP and meteor collision damage, score multipliers, combos, waves, increasing difficulty, survival play, wrong-input feedback, pause/restart, local high scores, weak-word replay, image hints and audio playback priority. Exact formulas, victory and failure rules, and wave length remain TBD.

## 6. Flashcard

Flashcard displays source-language vocabulary, Vietnamese meaning and semantic image; plays the selected English or Japanese pronunciation; flips cards; and navigates previous/next. It consumes default and imported Content Packs. Shuffle, known/unknown classification, review of wrong or missed items and local learning progress are proposed extensions. The proposed learning loop is **Learn → Play → Evaluate → Review → Replay**.

## 7. Content Packs and local AI

The application should load the existing Content Pack format and support a built-in vocabulary pack, import of compatible packs and pack selection. A proposed full configuration accepts Excel, validates it, processes images and both language audio through the optional local Docker engine, displays progress, validates the resulting pack and adds it to the local library. Technical validity is distinct from human content review and distribution eligibility. Missing media and failed items remain visible.

## 8. Proposed user flows and distribution

**Main menu:** Play · Vocabulary Library · Settings · Exit. (Flashcard removed by D-034; word/image/pronunciation viewing lives in the Vocabulary Library.)

**Game:** Select Pack → Select Language → Configure Difficulty → Configure Hint Mode → Configure Answer Mode → Configure Targeting → Gameplay → Results → Replay or Review.

**Vocabulary Library (replaces Flashcard, D-034):** Select Pack → Select Language → view words, images and pronunciation.

**Excel:** Select Excel → Validate → Process through Docker → Validate Content Pack → Add to Library. The exact local integration and user recovery flow remain open.

**Player configuration:** Unity application, both features and prebuilt or imported Content Packs; Docker is not required for ordinary gameplay. **Full configuration:** the same application plus optional local Docker processing for Excel. These are distribution configurations, not two separately maintained apps unless later justified.

## 9. Capability map and provisional roadmap

Each capability should become independently testable in its later task: `content-pack-runtime`, `application-shell`, `game-configuration`, `vocabulary-input`, `flashcard`, `meteor-defense`, `multimedia-playback`, `learning-results`, `local-ai-integration`, `desktop-distribution`.

| Milestone | Proposed result |
|---|---|
| G-001 | This GDD and protected legacy-directory migration |
| G-002 | User flow and UX/UI design |
| G-003 | Unity technical foundation |
| G-004 | Content Pack integration |
| G-005 | ~~Flashcard~~ **CANCELLED — MERGED INTO VOCABULARY LIBRARY** (D-034, 2026-11-27) |
| G-006 | Meteor Defense core |
| G-007 | Difficulty, Hint and Answer configuration |
| G-008 | Scoring, audio, waves and results |
| G-009 | Docker and Excel integration |
| G-010 | System tests and measured performance |
| G-011 | Windows packaging |

This sequence is provisional and authorizes no milestone beyond G-001. Future prototypes should measure CPU, RAM, GPU and frame rate on the owner's hardware; no measurements are available yet.

## 10. Legacy Design References & Preserved Assets

The project previously planned a Web Game; Unity Desktop is now the owner's preferred primary direction. Product material therefore moves from `web/` to the existing neutral `game/` directory. The protected [star-background concept](../../game/background/background_idea.md) originated at `web/background_idea.md` and currently resides at `game/background/background_idea.md` with its original filename and bytes. Its SHA-256 is `B33CC9780FC82664608A621BFEE7EC30DCBB6B1D450F2AB11BCAF9F637298DF4` before and after migration.

The document contains a navy/teal falling-star field, depth and parallax, pointer response, twinkling and historical React/Canvas examples. Those platform-specific passages remain intact as historical context. It mentions a reference image, but no linked file or related visual asset has been located; its identity and location are **UNKNOWN**. The background is an owner-protected historical reference, **not** a final approved Unity visual. Changing platform does not automatically invalidate the concept. Any Meteor Defense adaptation belongs to a separately authorized Game UX/UI design task.

## 11. Open review questions

The [mechanics draft](GAMEPLAY_MECHANICS_SPEC_v0.1.md) records preferred planning answers for questions 3–6; final runtime behavior and numerical balance still require owner review and playtesting.

1. Will the lecturer accept Windows Desktop, and what submission or public-access evidence is required?
2. Which local Unity-to-Docker handoff is simplest and reliable on the target machine?
3. How should Tab/Auto Aim switch targets while text or an IME composition is active?
4. What exactly does `NO_HINT` show, and how are unsolvable item/configuration pairs prevented?
5. Which Japanese input method and answer normalization are acceptable to learners?
6. What score, damage, wave, outcome and audio-priority rules feel fair after playtesting?
7. Which historical background elements, if any, should be adapted during G-002?
