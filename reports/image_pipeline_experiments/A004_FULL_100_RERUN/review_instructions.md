# A-004 owner review

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/reports/image_pipeline_experiments/A004_FULL_100_RERUN/review_gallery.html` in a browser. The page is an internal review tool, separate from Game UX/UI.

Search by word or ID, and filter by processing status. Each card shows English/Japanese/Vietnamese, the frozen query, A-001 image, A-004 proposed top image, and ranked valid alternatives. Expand the candidate section to compare scores and search rank. The AI_PRELIMINARY label is an analyst observation only.

For each ID, set the query label and image quality, choose a candidate or `NO_SUITABLE_IMAGE`, and add a note when the decision needs explanation. Seven `SKIPPED_QUERY` IDs and vocab-000008 have no new valid candidate. Enter reviewer name and select **Export JSON**. The browser downloads a draft review JSON; provide that file for a separately scoped consolidation. No choice in the gallery updates the benchmark ledger, canonical dataset, production media or public rights. The `because` override remains internal-only under D-015/D-016.

The full 100-ID ledger, including failed downloads, URLs, hashes and ranks, is in `retrieval_results.json`; the table is `candidate_rankings.csv`. `query_remediation.json` lists the seven blocked queries. The first ten partial results are preserved in `evaluation_matrix_partial_10.csv` and `evaluation_report_partial_10.md`. Local browser draft storage is convenience only; export before switching browser or clearing site data.
