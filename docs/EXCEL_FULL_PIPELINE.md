# Private Excel-to-multimedia runner

From the repository root in PowerShell, install `requirements.txt` and `requirements-audio.txt`, then run one command with an owner workbook:

```powershell
.\.venv\Scripts\python.exe -B "collect data script\excel_multimedia_runner.py" "C:\path\to\Vocabulary.xlsx"
```

The workbook must follow [Excel v1](contracts/excel_v1.md). The command validates it with B-002, creates an accepted private import, builds the B-003.1 processing plan, reuses exact triple-matched owner reviewed images through frozen image pipeline v2, attempts the frozen image search pipeline for unmatched rows, generates English and Japanese pronunciation with the existing gTTS wrapper, validates assets, builds a private dual-mode Content Pack, and writes one gallery. Each run gets a fresh `reports/EXCEL_FULL_PIPELINE_FINAL/run-UUID/` directory. The output path is printed. Never put a private run on a public host: image rights remain unknown, and `because` is internal only.

To resume after a provider failure, use the same workbook and the printed run directory:

```powershell
.\.venv\Scripts\python.exe -B "collect data script\excel_multimedia_runner.py" "C:\path\to\Vocabulary.xlsx" --resume "reports\EXCEL_FULL_PIPELINE_FINAL\run-UUID"
```

The importer rechecks the normalized workbook fingerprint; IDs stay fixed. Valid per-item audio with matching metadata and hash is reused. Existing assets are never silently overwritten. If media changes, a new immutable `content_pack_vN/` is created and `execution_report.json` identifies the active pack. `--force-audio` on a **new** run bypasses legacy Japanese cache reuse, without overwriting a prior run.

The final gallery is `review_gallery.html`. It selects English–Vietnamese or Japanese–Vietnamese, changes source text and pronunciation together, and keeps the same Vietnamese meaning and image. Search, status filter, and previous/next navigation are included. Missing media is shown, never fabricated. All media paths are relative to the gallery and pack. The gallery is an internal review tool; no game UI is defined.

If the owner's original Excel file is unavailable, make a **reconstructed fixture**, then run the same command:

```powershell
.\.venv\Scripts\python.exe -B "collect data script\reconstruct_benchmark_workbook.py" "reports\EXCEL_FULL_PIPELINE_FINAL\benchmark_reconstructed.xlsx"
.\.venv\Scripts\python.exe -B "collect data script\excel_multimedia_runner.py" "reports\EXCEL_FULL_PIPELINE_FINAL\benchmark_reconstructed.xlsx"
```

The fixture uses the exact row order and text in canonical `en.txt`, `jp.txt`, and `vn.txt`, and writes a provenance JSON with hashes. It is not the owner's original workbook. Validate any run's pack and gallery references with:

```powershell
.\.venv\Scripts\python.exe -B "collect data script\verify_multimedia_run.py" "reports\EXCEL_FULL_PIPELINE_FINAL\run-UUID"
```

The frozen v2 image runner returns a proposal for new unmatched images; without a reliable semantic and educational quality check, this integration records those as unavailable rather than auto-approving a SigLIP rank. Exact owner reviewed triple matches are reused with their rights restrictions. The current task explicitly preserves the earlier `sometimes` `NO_SUITABLE_IMAGE` decision; it takes precedence in this private run over the later registry entry, without altering either source record. English and Japanese MP3 integrity, duration, source text, locale, ID, metadata and hash are checked. These checks do not verify spoken phonetics. The private pack stays `failed` for an item missing either required audio mode.
