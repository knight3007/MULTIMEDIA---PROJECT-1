# G-004 Content Pack fixtures

Deterministic, owner-visible error-state packs for the Vocabulary Library. They are **test-only**, not real vocabulary, and do not change any historical pack.

| Folder | Expected library state |
|---|---|
| `invalid_json/` | Manifest lỗi JSON (truncated file) |
| `unsupported_v2/` | Phiên bản chưa hỗ trợ (`contract_version` 2) |
| `empty_items/` | Manifest không hợp lệ (an empty pack is invalid in contract v1) |
| `missing_media/` | Thiếu hoặc hỏng media: the ready item copied from `tests/fixtures/b001/content_pack_states.json` without its `assets/` folder |

Regenerate with the script recorded in `docs/agent/HANDOFF.md` (G-004 section) if the contract fixture changes.
