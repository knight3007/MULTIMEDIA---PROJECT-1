# Remote Qwen D0 experiments

Each run uses a unique directory. Preparation reads the canonical EN/JP/VN vocabulary, stable ID registry, approved semantic ledger, and the frozen Phase A/B query experiment. It never edits them.

Run `remote_qwen_probe.py prepare --run-id UNIQUE_ID` from the repository root for rows 004 rice, 009 chicken, 041 today, 054 study, and 065 swim. Repeat `--vocab-id N` to choose a smaller subset of these five. See [the API v1 contract](../../docs/REMOTE_QWEN_API_V1.md) for environment setup, offline dry run, later health and single-generation commands, and the current benchmark blocker.

Keep reviewer labels independent. The review template has empty remote candidates until a compatible benchmark run creates `review_ready.csv`; `blind_mapping.json` identifies variants and should be withheld until labeling is finished. No output here is owner approval or production media.
