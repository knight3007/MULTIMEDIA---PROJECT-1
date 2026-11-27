# G-008 Implementation Plan v0.1: Waves, Combo/Score, Audio, Results, Review, History

**Status:** IMPLEMENTED, OWNER_VERIFICATION_REQUIRED (2026-11-27). Final build `Builds/G008_Win64/WordOrbit.exe`. Finalization added coverage statistics, the HUD highest combo, the dev-bot history guard, a genuine deferral test and the §10 perf matrix (results in agent HANDOFF). Previous status: IMPLEMENTED in the working tree and the G007_R3 build. The owner approved O1–O6 as recommended. Still open: §10 perf matrix and spec notes. The original planning status was PLANNED, IMPLEMENTATION_PENDING. This is a plan only: no gameplay code, scene or build changed. The owner is playtesting G-007-R2. That acceptance is still pending, and the D-044 combat rules are still PROPOSED. Rules here marked PROPOSED are not owner-approved.

**Baseline (`main`/`57b6ccb`, uncommitted G-007-R2 work):**
- EditMode 101/101, PlayMode 55/55.
- Build `Builds/G007_R2_Win64/WordOrbit.exe`, 0 errors, 0 warnings.
- Reviewed v47 pack.
- Character-based combat with auto-destroy (D-044), per-meteor damage and drafts, 3 targeting modes, 4 difficulty presets, Full Word and Fill.
- No gameplay images (D-043). Edge clamp (D-045).

## 1. Scope

G-008 delivers the GDD milestone "Scoring, audio, waves and results" from GAMEPLAY spec §5–§6:

1. 3 × 10 wave structure inside the existing 30-spawn session.
2. Combo and difficulty-multiplied score.
3. Bounded pronunciation policy and SFX roles.
4. Results summary.
5. Review of weak words through the existing Vocabulary Preview.
6. Optional local learning history.

**Out of scope:**
- Endless mode, settings screen (S11) and background music (no approved music asset exists; the Kenney bonus set has SFX only).
- Flashcard and gameplay image hints.
- Balance retuning beyond the spec §5 table.
- Content Pack, pipeline, importer and Docker changes.

## 2. Ordered tasks and dependencies

| ID | Task | Depends on | Needs R2 playtest? |
|---|---|---|---|
| G-008.1 | Session model: waves, combo, points, typo count, per-item records, duration (pure logic in `MeteorDefenseSession`, plus new constants in `GameConfig`) | — | No (owner answer O1 needed for typo/combo) |
| G-008.2 | Wave flow in the controller: gate spawns per wave, 3 s transition, per-wave fall/spawn scaling, wave banner | .1 | Pacing only |
| G-008.3 | HUD: wave `ĐỢT n/3`, combo `COMBO ×n`, real points in toast/popup (builder adds 2 labels) | .1 | No |
| G-008.4 | Audio: one-slot pending speech queue, clip cache, SFX roles, pause/exit handling | — | Yes (feel/volume) |
| G-008.5 | Results panel: full summary and deduplicated word list | .1 | No |
| G-008.6 | Review: Results "Ôn từ cần ôn" opens VocabularyPreview filtered to weak items, same pack/language | .5 | No |
| G-008.7 | Local learning history (JSON, append-only) | .1, .5, owner O5 | No |
| G-008.8 | Perf verification (comparable R1/R2/G-008 workloads, spike counter in `G003_PERF`) | — | No |
| G-008.9 | Spec/agent docs, decisions, build `Builds/G008_Win64/WordOrbit.exe` | all | — |

**Can start immediately after authorization:** .1, .3, .5, .6 and .8 (logic, tests, data). The .2 numbers, the .4 volumes and the O1 typo rule wait for the R2 playtest report or need a cheap retune afterwards.

## 3. Confirmed vs provisional

**CONFIRMED or PREFERRED (spec/owner):**
- Finite 3 waves × 10 spawns (PREFERRED, spec §0).
- Victory when all 30 resolve with HP > 0. Game Over at HP 0, and remaining meteors are aborted.
- Score never decreases, there is no score for a breach, and score is awarded once per meteor.
- Selected-language audio only. No Vietnamese audio, no TTS.
- No Flashcard (D-034). No gameplay images (D-043).
- No backend, account or cloud.
- A wrong answer costs no HP (PREFERRED).

**PROPOSED (spec numbers, still provisional):** score/combo formula, wave scaling, accuracy definition, audio overlap policy. **OPEN:** persistent history (spec §8).

## 4. Proposed rules and numbers

### Waves (spec §5, D-046 PROPOSED)

- `wave = Spawned / ItemsPerWave` (0-based). Wave *w* spawns only after all 10 meteors of wave *w−1* resolve, then waits `WavePauseSeconds = 3`.
- The wait uses scaled time, so Pause freezes it.
- The banner shows `ĐỢT 2 / 3` during the wait. The first wave starts after the existing `FirstSpawnDelay`.
- Fall time: `FallSeconds(term) / 1.1^w`. The length allowance (+0.6 s per unit above 8, cap +8 s) is applied first, so long-word timing is preserved.
- Spawn interval: `MinSpawnInterval × 0.95^w`. `MaxConcurrent` is unchanged. Lane postponement and requeue are unchanged.
- `VocabularyDeck` already refills 10 distinct items per wave. No change.
- 30 spawns stay as they are: `SessionSpawns = WaveCount × ItemsPerWave`. Victory/Game Over logic is unchanged.
- Expert wave 3: base fall 10 s / 1.21 = 8.3 s. Spawn interval 4 × 0.9025 = 3.6 s.

### Vocabulary scheduling (verified in G-007-R3, D-051)

- **Deck cycles.** Each cycle is a seeded shuffle of all N usable items without replacement, refilled when empty. With k×N spawns every item appears exactly k times (15 items, 30 spawns: exactly twice each). A partial last cycle differs by at most one, and every item appears whenever spawns ≥ N.
- **Waves.** Waves group spawns, not deck draws. Items already used in the current wave go to the end of the next cycle, so a wave stays distinct when N ≥ items per wave.
- **Unchanged.**
  - There is never a duplicate on screen (spawn is postponed instead), and no immediate repeat when another item is available.
  - A lane postponement requeues the item to the front of its cycle and does not count as a spawn.
  - An early Game Over legitimately ends coverage.
- **Evidence.** Runtime logs `G007_SPAWN n item cycle wave active` and `G007_DEFER`. EditMode simulations cover N = 10, 12, 15, 20, 30 and 31.

### Combo and score (spec §5, D-047 PROPOSED)

- **Points per destroyed meteor:** `round(100 × difficultyMult × (1 + min(0.1 × combo_before, 0.5)))`.
  - Use integer math, `100 × mult × (10 + min(combo,5)) / 10`, rounded half away from zero.
  - Normal: 150 → 225 maximum. Expert: 300 → 450.
- **Combo:**
  - +1 only in `ResolveCorrect`, the single destroy path. A character hit never changes score or combo.
  - Reset to 0 on wrong Enter or breach.
  - Not reset by Tab, wave change, Pause or aborted meteors.
  - Track `MaxCombo`.
- **Typos (character-level wrong input, `TypingCombat.Step.Error`):** counted as `TypoCount` per item and per session.
  - **Recommended default:** no combo reset and no score effect. This follows the spec's "count a wrong answer only on Enter" intent and avoids IME accidents.
  - Alternative: a meteor with ≥1 typo still scores but does not raise combo. Owner answer **O1**.
- **Score is awarded once:** the existing `ResolveCorrect` state guard. The Submit and auto-complete paths both go through `Resolve`, so there is still one path.

### Audio (D-048 PROPOSED, changes the spec §6 "interrupt" proposal)

The current behaviour: the newest pronunciation interrupts the older one, and late loads are dropped. During rapid auto-destroys this cuts words off.

The proposal is a **single pending slot**:
- Play immediately when idle.
- When busy, store only the newest request. It replaces any older pending one.
- When the current clip ends, play the pending clip only if it was requested less than `SpeechStaleSeconds = 1.5` s ago (scaled time). Otherwise drop it.
- Worst-case backlog is 1. Nothing plays after gameplay has moved on by more than 1.5 s.

Other rules:
- **Clip cache:** a per-session `Dictionary<itemId, AudioClip>`, preloaded at session start (≤ pack size, ~15 short MP3s). This removes per-answer decode. It is also a likely cause of the 35–63 ms spikes, to be verified in .8. Destroy the clips on scene exit.
- **Language:** the language comes from `LearningItem.Audio`, which `LearningSession.Select` already filters by mode. A test asserts that EN never gets the JA asset and the reverse.
- **SFX roles:**
  - Laser `sfx_laser1`: 0.18, or 0.06 while speech plays. Keep the 0.06 s rate limit.
  - Typo/wrong `sfx_zap`: 0.15/0.25.
  - Destroy: `sfx_twoTone` 0.3.
  - Breach: `sfx_shieldDown` 0.4.
  - Game Over: `sfx_lose` 0.5.
  - New files are copied from the read-only `game/UXUI/kenney_space-shooter-remastered/Bonus` into `Assets/Audio/SFX`. The source is not modified.
  - Speech volume is 1.0, SFX source 0.35. Speech always wins: SFX are ducked while speech plays.
- **Lifecycle:**
  - Pause: `AudioListener.pause` (existing). The pending timer is frozen by scaled time.
  - Resume continues.
  - The final word's pronunciation is allowed to finish under Results. Leaving the scene stops everything.
  - Replay reloads the scene and clears the queue and cache.
- **Music:** none in G-008, because there is no licensed asset. Owner answer **O4** if wanted.

### Results (D-049 PROPOSED)

Show:
- Outcome (Victory / Game Over).
- Score and max combo.
- Word accuracy, typing accuracy and the three counts (correct words, wrong Enter, typos).
- Missed meteors.
- Waves reached `n/3` and progress `resolved/30`.
- HP left / start.
- Duration `mm:ss`.
- Difficulty, hint, answer mode, targeting, language, pack.

**Definitions:**
- **Word accuracy** = `correct / (correct + missed)`. Aborted meteors are excluded, and the value shows "—" when the denominator is 0 (spec §6).
- **Typing accuracy** = `hitUnits / (hitUnits + typoEvents)`. A typo event is one `Step.Error` as defined by D-044 (only new wrong input). It is shown separately and never mixed with word accuracy.
- **Duration:** unscaled time accumulated only while `State == Playing`, so it excludes Pause and dev time scale.

**Word list:** keyed by `item_id`. An item drawn in several waves appears once, with aggregated counts (`đúng ×2 · lỡ ×1 · gõ sai 3`).

**Weak item:** missed ≥ 1 or wrong Enter ≥ 1 (spec), plus typo ≥ 1 if owner **O3** agrees. The list shows at most 8 items, then "+n".

Buttons: Replay (existing), Ôn từ cần ôn (new), Back to GameSetup (existing), Menu.

### Review (G-008.6)

- Results sets `VocabularyPreviewController.ReviewItemIds` (a static `HashSet<string>`, like the existing `ShowReviewItems` flag) and loads VocabularyPreview.
- The preview keeps only those IDs from `LearningSession.EligibleItems`. The pack and mode are already static in `LearningSession`, so they are preserved.
- Image, meaning and pronunciation reuse the existing preview. The title reads `Ôn tập · n từ`.
- The button is disabled with "Không có từ cần ôn" when the set is empty.
- Back returns to GameSetup, and the filter is cleared on leave. No Flashcard screen.

### Learning history (G-008.7, D-050 PROPOSED, spec item OPEN)

- **Storage:** append one JSON line per finished or abandoned session to `Application.persistentDataPath/LearningHistory/sessions_v1.jsonl`, with `JsonUtility` (no new dependency).
- **Record:** `schema=1`, UTC start/end, duration, outcome, `pack_id`, `pack_version`, mode, config (difficulty, hint, answer, targeting), seed, score, max combo, correct, missed, wrong Enter, typos, HP left, waves reached, and `items[{item_id, correct, missed, wrong_enter, typos}]`.
- No source text or meanings are stored. They are looked up from the pack.
- **Cap:** keep the newest 500 lines (rewrite via temp file and rename when over the cap).
- **Errors:** a write failure shows a toast and never blocks Results. A corrupt line is skipped on read.
- **G-008 reads nothing back** except one optional "lần trước: điểm X" line. Aggregated per-word statistics are a later task.
- If owner **O5** prefers session-only, skip .7 entirely.

## 5. Reuse

- `MeteorDefenseSession`: state guards, aborted handling, `WrongAttemptsByItem`, `MissedItems`.
- `VocabularyDeck`: per-wave distinct refill, requeue.
- `GameConfig`: `ScoreMultiplier` is already stored, and `FallSeconds` already holds the length allowance.
- `TypingCombat.Step`: Error and NewHits feed the typo and hit counters.
- `Resolve`: the single destroy path.
- `PlaySpeech`: the request-id drop logic.
- `PackMediaLoader.LoadClip`.
- `VocabularyPreviewController`: the item list and Play.
- `LearningSession`: pack and mode.
- `endPanel`/`endStats`, `Toast`/`Popup`.
- `DevCommandLine` `G003_PERF` and the dev bot.
- `Tools/headless.ps1`.

## 6. Files expected to change

All paths are under `game/New Unity Project/Assets/` unless noted.

**Scripts/Game:**
- `GameConfig.cs`: `WaveCount=3`, `WavePauseSeconds=3`, `WaveFallSpeedup=1.1`, `WaveSpawnFactor=0.95`, `ComboStep=0.1`, `ComboCap=0.5`, `SpeechStaleSeconds=1.5`, and `FallSeconds(term, wave)`.
- `MeteorDefenseSession.cs`: `Wave`, `WaveResolved`, `Combo`, `MaxCombo`, `PointsFor`, `RegisterTypo(id)`, `RegisterHits(id, n)`, per-item `ItemRecord`, `ActiveSeconds`.
- `MeteorDefenseController.cs`: wave gate in `TrySpawn`, banner, HUD, typo/hit registration in `Evaluate`, speech slot and cache, SFX roles, results, review button, history call.

**New:**
- `Scripts/Game/SpeechSlot.cs`: pure pending-slot logic, testable without audio.
- `Scripts/Game/LearningHistory.cs`: record and append.

**Other scripts:**
- `Scripts/Library/VocabularyPreviewController.cs`: `ReviewItemIds` filter and title.
- `Editor/G003Builder.cs`: wave and combo labels, results panel size, review button, wave banner.
- `Scripts/Dev/DevCommandLine.cs`: `spikes33` and `spikes50` counts, postponed-spawn count in `G003_PERF`.

**Assets:** `Audio/SFX`: copies of `sfx_twoTone`, `sfx_shieldDown`, `sfx_lose`.

**Tests:**
- New: `EditMode/G008SessionTests.cs`, `EditMode/SpeechSlotTests.cs`, `EditMode/LearningHistoryTests.cs`, `PlayMode/G008FlowTests.cs`.
- Updated: existing tests that assert `Score == 100` (they become `PointsFor`-based).

**Docs:** GAMEPLAY spec §5–§6 notes, DECISIONS D-046…D-050, agent STATE, TASKS, HANDOFF and PROJECT_MAP.

## 7. Acceptance criteria and tests

**EditMode (pure logic):**
- **Waves:** the session spawns 10, holds the 11th until wave 1 fully resolves, and reports `Wave=1`. Game Over mid-wave stops the waves. `FallSeconds(term,2) == FallSeconds(term)/1.21` and the long-word allowance is kept.
- **Score:** Normal 150, 165, 180, 195, 210, 225, 225. The cap holds. Expert ×3. A wrong Enter or breach resets the combo and does not change the score. A character hit adds 0. A repeated `ResolveCorrect` is a no-op. `MaxCombo` holds.
- **Typos:** count +1 per `Step.Error`. Under the recommended O1 the combo is unchanged.
- **Accuracy:** 0/0 gives "—". Aborted meteors are excluded. Typing accuracy is computed from hits and typos.
- **Per-item:** the same item correct in wave 1 and missed in wave 3 gives one row (correct 1, missed 1) and is weak.
- **SpeechSlot:** idle plays now. Busy plus 3 rapid requests leaves 1 pending, the newest. A stale request (>1.5 s) is dropped. Pause does not age it.
- **History:** round-trip, skip a corrupt line, cap at 500, and the write-failure path returns an error without throwing.

**PlayMode (v47, bot via production path):**
- A full Easy run gives 3 wave banners, Victory, score equal to the sum of `PointsFor`, and Results fields matching the session.
- A Game Over run aborts the remaining meteors, with no late score.
- Rapid auto-destroys produce at most 1 queued speech and the correct-language clip.
- Pause during a wave transition freezes the countdown.
- The review button opens the preview with only the weak IDs and the same pack and mode. An empty set disables the button.
- Replay resets combo, wave and score.

**Regression:** full EditMode/PlayMode suites stay green. Run them once at the end, not during planning.

**Manual (owner):** feel of pacing, combo, speech and SFX by ear, and JA IME.

## 8. Risks and edge cases

- **Wave gate vs lanes:** a postponed spawn must not count as a resolved spawn, and `Requeue` is already handled. A wave waits on breaches too.
- **Last meteor:** auto-destroy triggers Victory, Results and speech in the same frame. Results must not stop that clip (D-048). A late load for an old request is still dropped.
- **Combo with typo on Fill vs Full Word:** Fill has fewer units, so typo counts are not comparable across modes. Show typo counts as raw counts.
- **IME:** composition never counts a typo (existing gate). A wrong Enter while composing is ignored (existing).
- **Breach at the same frame as auto-complete:** existing state guards keep one terminal outcome.
- **Spike source unknown:** cache clips first, then measure. Do not optimise TMP atlases without evidence.
- **History:** if the persistentDataPath is read-only, a toast is shown and play continues. A schema bump keeps old lines readable or skippable.
- **Tests asserting 100 points:** they will break by design. Update them in the same change.

## 9. Owner decisions needed

| # | Question | Recommendation |
|---|---|---|
| O1 | Does a wrong character (typo) affect combo? | No. Count it only as a statistic. |
| O2 | Approve the spec §5 wave/score numbers for the first G-008 build? | Yes, as provisional; retune after playtest. |
| O3 | Do typo-only words count as "cần ôn" in Review? | Yes (otherwise Review is often empty, since Enter is rarely used now). |
| O4 | Background music in G-008? | No. There is no licensed asset; add later. |
| O5 | Local history file, or session-only? | Local JSONL, lightweight, as above. |
| O6 | Pronunciation: one pending slot (D-048) instead of the spec's "interrupt"? | Yes. |

## 10. Performance verification plan (G-008.8)

The R1 and R2 numbers are not comparable: the R2 run had `maxMeteorViews=1` and R1 had 3. The plan:

- **Same workload for both builds:** run the R1, R2 and G-008 exes with the same args.
  - Workload A: `-g006Seed 60 -g007Difficulty Expert -g007Answer FillInTheBlank -g006Bot lose`. No kills, so the screen fills to the cap.
  - Workload B: the same with `-g006Bot win -g006BotDelay 3 -g007TypeGap 0.04`. Rapid typing with several meteors.
  - Each workload runs 60 s at 1920×1080, 1366×768 and 1280×720, with vsync on and off.
- **Log:** avg, p95, max, `spikes33`, `spikes50`, `maxMeteorViews`, postponed spawns, allocated MB.
- **Lane capacity:** if Expert never reaches 5 concurrent because of lane width, report it as a limitation with numbers. The lane layout changes only with owner approval.
- **Spikes:** log the timestamps of frames over 33 ms next to `G006_MEDIA speech` and spawn events to attribute the cause. Optimise only an attributed cause (expected: the clip cache in .4).

## 11. Work that can proceed right after authorization

G-008.1 with tests, .3, .5, .6 and .8 instrumentation. Then .2 with spec numbers, and .4 with the recommended O6 policy. .7 waits for O5. Numbers and volumes are retuned after the owner's R2 report. Visual captures are not needed when the owner playtests the exe. Capture only on request or to diagnose a defect.
