# Latest handoff — E2E-015 15-word multimedia run

Updated 2026-11-25 (Asia/Saigon) by Codex root. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `9f6c54e4b708b7cfb9c477f801875b1f460cc511`. No commit/push, no active write claim. Previous handoff: [history/2026-11-25_before_E2E015_HANDOFF.md](history/2026-11-25_before_E2E015_HANDOFF.md).

## Status: E2E-015 DONE

Source workbook: exact owner file `D:/Download/test_vocabulary_15_B001.xlsx`, copied byte-for-byte into `tests/fixtures/b001/test_vocabulary_15_B001.xlsx`; SHA-256 `00f0056564167dd681bc48bde482b6c91a61068e76b0f119747b1b390f0b3800`. B-002 validated all 15 rows, no diagnostics, rows 2–16, ten preserved `target_sense` values. Import `imp-6a2afe8b-ccf6-4ff9-94d0-6b05790182bf`, pack `pack-99f77dbe-c835-4ad0-bde2-3e9b422fcd30`, 15 distinct item UUIDs, normalized payload SHA-256 `f0f33617b89e24ba7eb1b004b3308fac2596fe34601a9b1ac4eb056634d26069`. Resume validation retained the same IDs.

Run: [run-bc2d5460](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/). Live Qwen, DDG retrieval, downloads, SigLIP and gTTS completed in the isolated directory. 20 actual image searches: 14 original, one recycle target-sense fallback after Qwen policy failure, five visual-semantic query corrections. Final PHOTO 6/ICON 8/SCENE 1, 15 selected images, zero NO_SUITABLE_IMAGE. 15 EN and 15 JA audio generated, none externally reused or failed, 30/30 technically valid. [Content Pack](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v46/content_pack.json) validates, 15 needs_review/pending, zero READY, 45 media assets. [Final gallery](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/final_review_gallery.html) uses this pack. [Quality report](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/e2e_15_quality_report.md) and [gallery validation](../../reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/final_gallery_validation_report.json) hold details and limitations.

The first run hit a missing image-ledger directory; the runner was fixed and resumed with the same import. The frozen v2 policy rejected `traffic light` because its validation expects a one-token concrete term, and misclassified `recycle`; bounded fallbacks were recorded without modifying frozen policy files. Visual inspection caught wrong top proposals for toothbrush, traffic light, whisper, wait and careful; one correction search per item was run. Lower-ranked retrieved alternatives were selected for traffic light, castle and wait. Original candidate files/manifests were archived in the run. These private image choices are not human approved. No manual candidate selection is required to open the gallery.

## Opening and verification

The localhost server was started on port 8766 in unified exec session 18822. If it is no longer running, start it in PowerShell:

```powershell
Set-Location -LiteralPath 'D:\MULTIMEDIA - PROJECT 1\reports\EXCEL_15_SMOKE\run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291'
& 'D:\MULTIMEDIA - PROJECT 1\.venv\Scripts\python.exe' -m http.server 8766 --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/final_review_gallery.html` in Chrome or Edge. Browser verified 15 cards/counts, EN–VI and JA–VI mode switch preserving item/image/translation, both MP3s loading and actual playback start, Japanese/Vietnamese search, filters, navigation, image enlargement, no console errors. Independent HTTP test returned 45/45 media URLs with matching SHA-256. No missing media. The final no-image UI state was not browser-exercised because all 15 have images; subjective pronunciation and learner meaning remain for owner review. Collector 206 OK, Kaggle 19 OK, B-001 fixture verifier PASS, `git diff --check` exit 0.

Files changed by E2E-015: copied fixture, `collect data script/excel_multimedia_runner.py`, `test_excel_multimedia_runner.py`, `build_final_review_gallery.py`, `final_review_gallery_template.html`, isolated run outputs/scripts/reports, and these checkpoint docs. Existing tracked worktree changes from B-003.2 and unrelated user files were present before this task and were not reset. Frozen image code/registry, original 100-word media and canonical dataset were untouched; canonical dataset SHA-256 remained `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`. No game UX/UI started.

Next owner action: open the gallery and inspect images and both pronunciations. No candidate vote, JSON export, commit or push is needed for this review.
