# Latest handoff — pre-G003 gameplay mechanics documentation

## SKILL-ZIP-001 checkpoint (2026-11-26)

User-requested export completed: `C:/Users/dotha/Downloads/skills-export-2026-11-26.zip` contains 118 installed skill directories with source namespaces and `manifest.json`; 765 ZIP entries, 31,071,000 bytes. CRC check passed, and source/destination SHA-256 both equal `E91C8668FDBE54BD1705EE934C26AC854E80AFEA8920C31AB806EEB25D51392A`. No project implementation or media changed. The earlier gameplay handoff and its owner-review gates remain below. No active write claim or next action for this export.

Updated 2026-11-26 (Asia/Saigon) by Codex root. Repository `D:/MULTIMEDIA - PROJECT 1`, `main`/`57b6ccb09d25945eb4301f41af2342eb37ea2bda`. Pre-existing unrelated tracked edits and untracked media remain. The prior G-002 handoff is preserved in [history](history/2026-11-26_before_GAMEPLAY_SPEC_HANDOFF.md). No active write claim, commit or push.

## Status and scope

**Documentation execution complete; G-002.1 and G-002 overall OWNER_REVIEW_REQUIRED. G-003 not started.** Created [Gameplay Mechanics Spec v0.1](../game/GAMEPLAY_MECHANICS_SPEC_v0.1.md) from the owner-reviewed planning proposal. It covers the existing GDD capability IDs, Content Pack readiness, question compatibility, EN/JA input, Fill-in-the-Blank, spawn and targeting, provisional difficulty/score/waves, audio, state diagrams, results, and deterministic acceptance scenarios. Linked it from the [GDD draft](../game/GDD_v0.1.md), updated [INDEX](INDEX.md), [PROJECT_MAP](PROJECT_MAP.md), [STATE](STATE.md), [TASKS](TASKS.md), and recorded D-028 in [DECISIONS](DECISIONS.md) as PREFERRED for planning. The source Content Pack/Excel contracts, AI Pipeline, Docker, Unity project and assets were not changed.

Owner planning choices: finite 3-wave × 10-spawn session, No Hint retains Vietnamese meaning, Text Only adds first source character, native Windows IME first, Auto Aim + Tab, per-meteor partial text, wrong answer only on Enter, wrong Enter resets combo without HP damage. Numerical balance and runtime rules remain proposals until owner review/playtest; no choice authorizes Unity implementation. The spec routes invalid pack loading to S02 Library with a diagnostic, consistent with [User Flow](../game/USER_FLOW_v0.1.md). The protected [background plan](../../game/background/background_idea.md) remains primary and unchanged; G-002 visual Option A is still proposed.

## Verification and limitations

- Checked branch, HEAD and working tree before editing. Final check found 292 local Markdown links resolving across eight touched/current documents, no trailing whitespace, and `git diff --check` reported no whitespace errors. Protected-background SHA-256 remains `B33CC9780FC82664608A621BFEE7EC30DCBB6B1D450F2AB11BCAF9F637298DF4`; the 1,580-file `game/UXUI/` fingerprint remains `ed81407f781bef9efa4b210b93229fe1e4964b0512e1d120bf81d43af703547b`. The scoped changes are documentation only; unrelated pre-existing worktree changes remain. No application test or Unity build was run.
- Existing real trial Content Packs reported zero `ready` items. The runtime must not silently play `needs_review` items. A reviewed ready pack or separately authorized labeled synthetic prototype is needed for later gameplay testing.
- No Windows Unity IME, text rendering, sound listening, frame rate or gameplay feel was verified. No performance benchmark exists for the owner's machine.

## Next action

Owner reviews the complete mechanics draft and remaining G-002 visual/typography proposals. Resolve provisional tuning and lecturer acceptance of Windows Desktop. G-003 needs separate scope/authorization and usable test content. Do not begin Unity, asset import, gameplay/Flashcard implementation, AI/Docker/contract edits, commit or push from this handoff.
