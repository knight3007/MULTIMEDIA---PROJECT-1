# Human review package

Open `review_gallery.html` locally while keeping it inside the repository. All image/audio paths resolve to existing local files; no media is fetched from the Internet. No server/framework/model required. `gallery.js`, `gallery.css` and inline data are local. If file-origin storage is unavailable, keep the page open and Export JSON before closing. The matrix CSV/JSON is the fallback and authoritative machine-readable evidence.

1. Search by ID/word or filter AI query status. Each item shows EN/JP/VN, original Qwen query, actual query for the selected image, local image/audio, AI preliminary reasoning and metadata/hash/attribution details.
2. Enter reviewer identity. Review query and selected image independently using PASS / FAIL / NEEDS_REVIEW / UNKNOWN. No status is prefilled from AI. Owner acceptance already marks audio PASS; there is no required audio re-review control.
3. Add notes about intended sense, wrong scene/object, clutter/text, or missing evidence. For ambiguous terms, resolve context explicitly instead of assuming a single canonical meaning.
4. Drafts are saved in this browser under a run-specific key when available. Export JSON for handoff; it downloads a draft file locally and does not overwrite any source/old review. The owner must provide/export labels before they can become new evidence in a later task. Different browsers/file locations may have separate drafts.
5. Confirm exported query text/image/audio hashes still match this run before importing a future human review. This gallery does not itself approve production assets or rewrite ledgers/manifests. Inspect images even when AI says PASS.

The gallery is an academic local evaluation tool, not a public product. Do not publish restricted/unknown assets via this package. Rights inventory for all 100 items is not a quality gate; only actual public release assets require the release checks. Avoid moving the HTML out of its folder; use the CSV paths if relocating the repository.
