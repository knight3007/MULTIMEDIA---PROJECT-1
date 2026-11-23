# Agent context index

Start: [AGENTS.md](../../AGENTS.md) → [STATE](STATE.md) → [TASKS](TASKS.md) → [HANDOFF](HANDOFF.md). Then verify branch/HEAD/status; load only the task's references. [PROJECT_MAP](PROJECT_MAP.md) locates source/tests; [DECISIONS](DECISIONS.md) records status and rationale. This index is routing, not a second task list.

## Authority and old context

Current user instruction → confirmed decisions → [scope adjustment](../../reports/phase0_quality_review/00_scope_adjustment.md) and [revised roadmap](../../reports/phase0_quality_review/01_revised_roadmap.md) → task-specific evidence. Architecture reassessment reports are historical proposals where superseded. Source/Git determine actual implementation. If a checkpoint disagrees with Git, inspect relevant changes before proceeding; do not silently overwrite other work.

[PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md) is an older broad snapshot (including obsolete SAPI/500-row descriptions); [CODEX_PROGRESS.md](../../CODEX_PROGRESS.md) is historical execution evidence. [tasks/plan.md](../../tasks/plan.md) and [tasks/todo.md](../../tasks/todo.md) describe the completed DDG change. Keep all; add future current tasks/checkpoints here, not competing live lists in those files. Research schedules are ideas, not authorization. The original AGENTS guide is preserved in [history](history/2026-11-22_AGENTS_before_context.md).

## Read by task

| Need | Minimal reference |
|---|---|
| Next task / ownership / authorization | [TASKS](TASKS.md), [HANDOFF](HANDOFF.md) |
| Track A: query and image quality | Latest [A-001 summary](../../reports/phase0_quality_review/a001_20261122/01_evaluation_summary.md), [100-ID matrix](../../reports/phase0_quality_review/a001_20261122/evaluation_matrix.csv), [local review gallery](../../reports/phase0_quality_review/a001_20261122/review_gallery.html). Audio accepted PASS by owner; human query/image labels pending. Earlier [initial findings](../../reports/phase0_quality_review/02_initial_quality_findings.md) remain history. |
| Image pipeline lineage | [Image audit](../../reports/image_pipeline_audit/20261106T102750Z-cd93f8a1/audit_statistics.json), [full staging review](../../reports/full_media_staging_review.md); open only relevant IDs/assets |
| Audio | [Full staging review](../../reports/full_media_staging_review.md), [inventory](../../reports/full_media_staging_inventory_v1.json), relevant audio module/tests in map |
| Track B: Excel, pack, game | B-001 specifications: [Excel v1](../contracts/excel_v1.md), [pack v1](../contracts/content_pack_v1.md), [integration/adapters](../contracts/integration_notes.md), [fixtures](../../tests/fixtures/b001/README.md). [Revised roadmap](../../reports/phase0_quality_review/01_revised_roadmap.md); no runtime yet |
| Production data contract | [DATA_CONTRACT_V1](../DATA_CONTRACT_V1.md), actual builder/source via map; proposals below historical sections are not implementation |
| Deployment / AI hosting | [AI assessment](../../reports/architecture_reassessment/03_ai_infrastructure_assessment.md), release gates in revised roadmap; Pages/Docker are proposals |
| Kaggle batch | [D2 context](../KAGGLE_BATCH_AUTOMATION_CONTEXT.md) and [architecture](../KAGGLE_BATCH_AUTOMATION_ARCHITECTURE.md); live GPU gates remain closed |
| Original architecture study | [Executive summary](../../reports/architecture_reassessment/06_executive_summary.md); follow scope adjustment for newer quality/license policy |

## Checkpoint policy

At task/milestone/phase/handoff/session boundaries, synchronize STATE, TASKS, HANDOFF. Record commands, actual outcomes and untested areas. Archive an outgoing handoff only at a meaningful checkpoint; never log every read/command. History is evidence, not a second current state. For abrupt interruption, reconcile Git diff/status and task output before marking completion. No automatic commit/push. No fixed token-savings claim: startup size and dry-run read count can be measured, actual token savings have not been measured.
