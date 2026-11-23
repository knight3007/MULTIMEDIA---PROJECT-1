# B-004.1 offline Content Pack builder

This is a private/offline implementation of [Content Pack v1](contracts/content_pack_v1.md). It accepts an accepted B-002 import JSON, a B-003.1 processing manifest, or an existing Content Pack v1 JSON. It never runs AI, retrieves media, or changes source records.

From the repository root in PowerShell:

```powershell
# Validate a pack and its referenced local assets; no output written.
.\.venv\Scripts\python.exe -B "collect data script\content_pack_builder.py" "path\to\content_pack.json"

# Build a new private pack from an accepted B-002 record.
.\.venv\Scripts\python.exe -B "collect data script\content_pack_builder.py" "path\to\accepted_import.json" --output "path\to\new_private_pack"

# Build from B-003.1, cross-checking its imported item IDs and text.
.\.venv\Scripts\python.exe -B "collect data script\content_pack_builder.py" "path\to\processing_manifest.json" --import-record "path\to\accepted_import.json" --output "path\to\new_private_pack"

# Check public eligibility metadata. This validates only; public export is blocked.
.\.venv\Scripts\python.exe -B "collect data script\content_pack_builder.py" "path\to\content_pack.json" --mode public
```

`--asset-root` overrides the directory containing the source JSON when source assets reside elsewhere. Existing asset references must already use the contract path `assets/<sha256>.<extension>` and match bytes, size, signature/type and SHA-256. The builder copies each referenced asset once into the new pack. It rejects absent, symlinked or escaping references. It never overwrites an output directory. The resulting directory contains `content_pack.json`, `validation_report.json`, and `assets/` only when assets exist. Paths in the JSON are pack relative; moving the whole directory preserves them. Exit code 0 means validation/build succeeded; 1 means diagnostics or input/output error.

The [three-item example](../reports/b004_1_private_demo/fixture_private_pack/content_pack.json) uses the actual B-002/B-003.1 synthetic fixture import. Its [report](../reports/b004_1_private_demo/fixture_private_pack/validation_report.json) says all three imported rows are `pending`, with image and audio missing and zero game-ready items. This is a valid *draft structure*, not playable or approved content. The separate B-001 fixture pack tests copying two synthetic media files, relocation and checksum validation; its simulated review evidence is never interpreted as real owner approval.

The validator checks contract version, required/unknown fields, UUIDv4 identities, normalized language text, duplicate rows, states, quality/review evidence, distribution metadata, media paths and bytes. An accepted `NO_SUITABLE_IMAGE` can remain a failed item with image null and an image-stage error; the importer does not invent a replacement or drop the row. Public-mode validation requires `test_only=false` and every included item ready with distribution permitted and nonempty evidence. **Public pack writing is disabled**: B-003.1 has no real approved assets or per-asset distribution evidence, and its free-text provenance has no trusted public sanitization pipeline. A single aggregate `distribution.evidence` string cannot independently establish rights for both assets. Neither a ranked candidate nor human image selection grants public rights.

An unchanged initial B-003.1 manifest maps to pack version 1. Any later processing snapshot with changed status or media must provide an explicit `pack_version`; the exporter will not silently reuse version 1 for changed content.

Run tests:

```powershell
.\.venv\Scripts\python.exe -B -m unittest "collect data script/test_content_pack_builder.py" -q
.\.venv\Scripts\python.exe -B -m unittest discover -s "collect data script" -p "test_*.py" -q
.\.venv\Scripts\python.exe -B tests/fixtures/b001/verify_fixtures.py
```

Remaining B-004 integration: B-003.2 must produce actual import-local media, technical checks, per-item content review and immutable state transitions. A future owner-authorized release path must establish distribution permission for each included image/audio asset and sanitize public metadata, then produce an eligible subset with a new pack version. Game UX/UI remains undecided.
