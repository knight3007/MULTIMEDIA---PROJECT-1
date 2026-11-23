# A-004R owner follow-up verification

Date: 2026-11-23. Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No commit or push.

## Takeover

- Codex root wrote `A004R_OWNER_FOLLOWUP_100/followup.py` and `test_followup.py`, froze the plan from the owner export `D:/Download/A004R-review-2026-11-23.json` (SHA equals `owner_review_export.json`), and ran `followup.py run` (PIDs 17616/14996, started 19:59 +07).
- The Claude Code session wrote nothing to that folder until both processes had exited (around 20:09). All 34 planned items had been attempted: 31 RANKED and 3 FAILED with DDG timeouts (057, 041, 018; search retries were 0).

## Review findings on the Codex code

1. **Bug:** 066 software has the owner note "lấy ảnh A001" with label UNREVIEWED. The A001 rule only matched PASS labels, so 066 was searched instead of kept.
2. **Gap:** for open items the gallery dropped earlier images the owner had already seen. Most visibly, the A-003 owner-accepted image for 057 eat (`A003 NORMAL-06`) was missing even though the note says "2 ảnh đều tốt"; 8 items also had valid A-004R candidates.
3. The 3 timeouts were never retried because `run` skips any ID already in the results.
4. Four new queries gave no usable candidate for technical reasons:
   - 033: "single" returned "Being Single" quotes.
   - 060: only one result (a sticker sheet).
   - 079: only one result (a text poster).
   - 080: "blocked action" returned rifles.

## Changes

- `followup.py`:
  - `amend` phase: 066 → A001_OWNER_NOTE, audited in `plan["amendments"]`. Its search result is kept but unused.
  - `retry` phase: FAILED searches with no candidates are run again with retries=2, and the failed attempt is kept in `previous_attempts`.
  - `repair` phase: 4 audited QUERY_REPAIRs. New attempts go to `images/<vid>/attempt2/` with IDs `…-FOLLOWUP-R2-NN`, so the old attempt hashes stay valid.
  - The gallery now offers `PRIOR_OWNER_REFERENCE` and the valid A-004R candidates for open items. Intro counts are now dynamic.
- `test_followup.py`: 3 → 8 tests, covering the counts (67/33), the 066 amendment audit, every A001 note being fixed, all candidate hashes including previous attempts with unique IDs, the repair audit plus all searched items being RANKED, and the eat prior reference.
- Backups made before the changes: `followup_plan.before_amend.json` and `retrieval_results.before_retry.json`.

## Results

- **Plan:** 100 IDs; 67 fixed (66 frozen + 066), 33 open for owner review.
- **Search attempts:** 34 + 3 retries + 4 repairs = 41; 7 superseded attempts are kept.
- **Current results:** 34 entries (including the unused 066), 231 candidates, 229 valid raw/JPEG pairs. All 33 open items are RANKED.
- **Retries:** 057 eat, 041 today and 018 sun are all RANKED.
- **Repairs:** 033, 060, 079 and 080 are 7/7 each. 080 is still weak (some images print "IMPOSSIBLE"); earlier impossible-triangle images are also offered.

## Checks

- Follow-up tests: 8 OK. Collector suite: 184 OK. `followup.py verify`: 100 IDs.
- A-004R `retrieval_results.json` SHA equals the plan source. Dataset SHA is `644c2dc9…`, unchanged. The export copy is identical to the Download file.
- Gallery, served by the existing 127.0.0.1:8765 server in a new pane tab that was closed afterwards:
  - 100 cards; 372/372 images load; the open filter shows 33/100.
  - Clicking eat's PRIOR_OWNER_REFERENCE sets the selector. The export has 100 reviews with the correct path and hash for eat, and 066 is carried forward as A001_OWNER_NOTE.
  - The patched functions were restored and the draft keys cleared.

## Not established

- Owner choices for the 33 open items.
- Rights (still unknown; `because` remains INTERNAL_ONLY_TEMPORARY).
- Nothing was promoted to production data.

## Display fix (owner report, 2026-11-23)

- Symptom: candidate thumbnails showed as broken images (owner screenshot, card 041 today). The HTML paths and files were correct, and both local servers (8000, 8765) returned 200. Cause: the gallery was opened in a viewer that renders the HTML without access to sibling files (the app's file preview).
- Fix: `followup.py render` now embeds each image as a 320 px JPEG data-URI thumbnail via `thumb()`, with the original path in the `title`. Export metadata (paths and hashes) is unchanged. The gallery is about 5.3 MB.
- Check: 372/372 images are embedded and loaded; follow-up tests 8 OK. The test tab was closed.
