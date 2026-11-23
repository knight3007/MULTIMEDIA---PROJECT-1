# B-001 verification checkpoint

Date: 2026-11-22T10:00:32+07:00, Asia/Saigon. Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. Owner Codex root; task scope contract documentation and test fixtures. No active ownership remains after completion. Incoming handoff archived as `2026-11-22_before_B001_HANDOFF.md` (verbatim; its links resolve relative to original docs/agent location).

## Deliverables and checks

- `docs/contracts/excel_v1.md`: field/type/validation/duplicate/Unicode/row-error and import/item identity rules. Invalid workbook/import is atomic; benchmark identity preserved.
- `docs/contracts/content_pack_v1.md`: normative JSON shape, five item states, transitions and revision/invalidation; local readiness separate from public eligibility; safe local asset paths and offline caching.
- `docs/contracts/integration_notes.md`: source-grounded compatibility/adapters and row→pack trace; no existing pipeline schema replaced.
- `tests/fixtures/b001/`: five `.xlsx` workbooks, expected.json, content_pack_states.json, README.md, verify_fixtures.py, hash-addressed PNG square and WAV tone. Synthetic test_only states are not AI, pronunciation or owner quality approvals.
- Updated current context: INDEX, PROJECT_MAP, TASKS, STATE, DECISIONS, HANDOFF. Added baseline JSON, archived prior handoff and this record in history; AGENTS unchanged during B-001.

Executed `.\.venv\Scripts\python.exe -B tests/fixtures/b001/verify_fixtures.py`, exit 0:

```text
PASS: 5 XLSX fixtures; 5 pack states; media sizes/hashes; 7 negative mutations; 101-item example; namespaces and local references
```

Fixture checker verifies accepted/duplicate/blank/Unicode row vectors, UUID namespaces, unique identities, required fields/enums, ready review/quality/technical guards, file sizes/SHA-256, local MIME/path consistency, failed error representation, rejection of seven invalid mutations and a 101-item in-memory shape. It also checks common accidental path/token patterns; this is not a universal secret detector. No claim that a production parser or complete schema/state-machine implementation was tested.

Five workbooks were authored/exported with bundled Artifact Tool 2.8.58+, inspected and rendered; each Vocabulary sheet was visually reviewed. Japanese/Vietnamese text and headers display legibly; blank row and missing-column fixtures intentionally retain those defects. Previews/builder remained in OS temp. Runtime emitted an informational WebAssembly content-type fallback; exports/rendering completed successfully. No dependency was installed.

Final inline Python document check: local links for new contracts/current context resolve, Markdown whitespace clean, STATE below 100 lines, baseline protected source/data/report hashes unchanged; fixture verifier rerun after final edits. Git branch/HEAD unchanged and tracked diff paths remain only pre-existing comand.txt / schedule/20-9 list. New contract/fixture/context work is uncommitted. No full audit/media scan, model, gTTS, network collection, application behavior change, commit or push.

## Acceptance and remaining gaps

B-001 DONE as specification/fixture task. Exact parser/framework/host and deployment resource budgets remain open; contract defaults are PROPOSED for implementation (D-011), not ratified automatically. Full 100-image copyright audit is not a prerequisite. Runtime/public exporter must enforce trusted review and appropriate rights for its release subset. Kanji reading conversion remains out of v1; review pronunciation. App unit suites and real browser/provider/model behavior were not run in B-001; historical 160+19 tests remain historical only.

Next: wait for user instruction. B-002 can then select stack/parser, implement isolated adapters and offline vertical slice from these contracts. A-001 can independently resume semantic review. No automatic transition to either task from this checkpoint.
