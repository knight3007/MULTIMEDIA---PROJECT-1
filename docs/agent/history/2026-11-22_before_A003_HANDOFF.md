# Latest handoff — A-002-CAUSAL "because" pilot

Updated 2026-11-22T13:10+07:00 by the Claude Code session. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`.

- **Status**: A-002-CAUSAL is DONE for the pilot scope (owner chose V3-01).
- **Write claims**: none active.
- **Previous handoff**: archived as `history/2026-11-22_before_A002_CAUSAL_HANDOFF.md`.
- **Repository**: no commit or push. Tracked diffs are still only `comand.txt` and `schedule/20-9 list`.

## Context

The owner's feedback on A002_ICON_PILOT_20 was qualitative: icon search is generally satisfactory for the other words, but "because" is unsuitable. It is recorded as such, not as 19 PASS labels.

## Results

- Target: `vocab-000081` because / なぜなら / bởi vì.
- Searches: 4 real searches (V1 `cause and effect pictogram`, V2 `reason and result visual illustration`, V3 `cause effect visual sequence illustration`, V4 `child opening umbrella in the rain illustration`), all SUCCESS.
- Downloads: 25/27 candidates; one shared URL was reused, giving 24 unique images.
- SigLIP: scored each variant against its own query. It also scored every candidate, the ORIGINAL image and the ICON candidates against one fixed causal description.
- Query-score picks: V1-05 and V2-05 are text-dominant; V3-01 = V2-01; V4-03 is a girl with an umbrella in the rain.
- AI-preliminary verdict: `NO_SUITABLE_VISUAL_FOUND`.
  - V2-01/V3-01 (rain and sun → tree) shows causality explicitly, but has CAUSE/EFFECT labels and an Adobe Stock watermark.
  - V4-02/V4-03 have no text, but the link is only implied.
  - The icon pool contains ∴/∵ dot notation, some of which means "therefore".
- Key semantic point: "because" states the effect first, then the reason. A left-to-right cause→effect picture is closer to "therefore".
- Strategy options in the report: icon search, diagram search, contextual search, multi-panel effect-then-reason, and manual curation for connectors. None is adopted.
- Verification: [record](history/2026-11-22_A002_CAUSAL_verification.md).

## Owner decision

The owner chose **V3_BEST / V3-01** in chat. It is the rain + sun → tree "CAUSE AND EFFECT" diagram (same image as V2-01) from Adobe Stock.

There is no gallery export file: the agent's export test had disabled downloads in the in-app tab the owner used. The decision is recorded in `reports/image_pipeline_experiments/A002_CAUSAL_CONCEPT_PILOT/owner_review_decision.json`, and `comparison.csv` and the report are re-rendered. A-002-CAUSAL is DONE for the pilot scope.

## Usage decision (D-015)

The owner chose to use V3-01 temporarily for **internal use only** ("Tạm dùng nội bộ"). It must not be published or included in a public release subset, because its rights are not cleared and it carries an Adobe Stock watermark and English labels.

It has not been copied into `data/image/en/`, the registry or the review ledger, and the production query strategy is unchanged. `owner_review_decision.json` records `usage_decision`.

## Next action

None pending for A-002. Each of these needs a new instruction:

- Put V3-01 into the internal dataset or pack.
- Find a cleaner replacement.
- Pilot other connectors.
- Start A-003 or B-002.

Game UX/UI remains undecided.
