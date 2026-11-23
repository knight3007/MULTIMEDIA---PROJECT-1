# A-004R gallery usability fix — 2026-11-23

Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. Existing uncommitted work preserved; no commit or push. The owner showed the `sleep` card: four large comparison panels were visible, but the seven ranked candidates were only listed by ID and score. That made visual selection impractical.

## Change

- Updated `reports/image_pipeline_experiments/A004R_CONDITIONAL_100/finalize_a004r.py` and regenerated `review_gallery.html` and its manifest artifact hash. Every valid ranked candidate is shown as a clickable thumbnail with rank, ID and score. Fresh-result lists open by default. Selecting a thumbnail updates the existing `selected_candidate_id` control, local draft and JSON export fields; changing the dropdown updates the thumbnail highlight.
- The four large A-001/A-004/A-004R/owner panels remain comparison references. Candidate selection is restricted to the actual ranked candidate list, so reference pictures are not silently substituted for a candidate. `NO_SUITABLE_IMAGE` remains an explicit selection.
- The gallery describes review steps in Vietnamese. No retrieval, Qwen, SigLIP, image approval or production integration ran. Export schema and frozen routing hash are unchanged.

## Verification

- `.venv/Scripts/python.exe -B reports/image_pipeline_experiments/A004R_CONDITIONAL_100/finalize_a004r.py`: regenerated 100-ID gallery and manifest with 449 ranking rows.
- `.venv/Scripts/python.exe -B reports/image_pipeline_experiments/A004R_CONDITIONAL_100/run_a004r.py verify`: `Frozen routing verified 100 IDs`.
- `.venv/Scripts/python.exe -B -m unittest discover -s reports/image_pipeline_experiments/A004R_CONDITIONAL_100 -p test_*.py -q`: 5 OK. `git diff --check`: exit 0 with pre-existing line-ending warnings.
- Browser test in a separate hidden tab: 100 cards loaded, `sleep` displayed seven actual candidate thumbnails, click updated the selector and `aria-pressed` highlight, dropdown/current draft restored, exported metadata mapped the chosen ID to its JPEG path and SHA-256, and console had zero errors/warnings. The original owner tab was not reloaded. A test click was reverted to the owner's saved `sleep` candidate `vocab-000056-A004R-03` (rank 4). Other existing draft selections were untouched. The reviewer name is not stored in the page's draft and may require re-entry after owner refresh.
- Protected SHA-256 unchanged: canonical dataset `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; A-003.3 owner manifest `fa478187a3ddf454e5ae5f3d25a87e839585e32d16a6c26c9a3104664e3d651f`; internal-only override `00770e7c7c2fee26b2d4eda515ab51c3a82f927938043c150eff2feba5319799`; A-004 retrieval `028b186818b34f6133380a267c63a554be217b5f565475746b9835f7eb7966c8`.

## Current artifact hashes

| File | SHA-256 |
|---|---|
| `finalize_a004r.py` | `6a8671dbc16ca521397ec2728b4843c62c725e632ac2d589546fe28562a38a54` |
| `review_gallery.html` | `cc6c5ec16c2387e02f12d38257340875801a182adc90ca6bc9a91c946f06dd19` |
| `experiment_manifest.json` | `9067a87b3c340de9df396d662a59356fa60027f256ba8ba65f17027987a0bd46` |

The original A-004R completion hashes remain in `2026-11-23_A004R_verification.md` as the historical snapshot. Owner review and JSON consolidation are pending; no new selection has been approved.
