# Japanese audio production-staging pilot — 2026-10-29

**Result:** 5/5 MP3s staged under `baseline/media-staging/audio/20261029T043348Z-0dffcbe2/`; three verified smoke files reused, two freshly downloaded. [Run manifest](../baseline/media-staging/audio/20261029T043348Z-0dffcbe2/run_manifest.json) binds each file to its stable vocabulary ID, source row and SHA-256. No production MP3 or dataset was changed. The owner subsequently confirmed listening approval for all five exact files; usage rights and production promotion remain pending.

The run used `.venv-audio`, gTTS 2.5.4, `lang=ja`, `tld=com`, `slow=false`, timeout 12 seconds, one retry and one second between new requests. `ごはん` failed to connect on the first attempt, then passed the bounded retry. `パン` passed on its first attempt. A second `--resume` run took 0.204 seconds, verified five cache hits and made no new provider request; the manifest retains initial `reused_smoke`/`downloaded` provenance.

| Stable ID | Reading | Staged MP3 | Duration | SHA-256 | Origin | Technical / listening / owner status |
|---|---|---|---:|---|---|---|
| `vocab-000001` | りんご | [りんご.mp3](../baseline/media-staging/audio/20261029T043348Z-0dffcbe2/りんご.mp3) | 0.936 s | `6a455497070ac66d9c2c7da22cf09181b0d90ecfc40d3e9faa65526a5ca49f07` | Verified smoke copy | Valid MP3 + metadata; owner listening approved |
| `vocab-000002` | バナナ | [バナナ.mp3](../baseline/media-staging/audio/20261029T043348Z-0dffcbe2/バナナ.mp3) | 0.888 s | `40f021c5937c13d3b2025841e767cb1a2cf2bd5730ecff60d1607e4873750ae4` | Verified smoke copy | Valid MP3 + metadata; owner listening approved |
| `vocab-000003` | いちご | [いちご.mp3](../baseline/media-staging/audio/20261029T043348Z-0dffcbe2/いちご.mp3) | 0.936 s | `94552122dbcd8df727ea0ec7873b094e4830e83212ca92ebca0caa6f16db49d9` | Verified smoke copy | Valid MP3 + metadata; owner listening approved |
| `vocab-000004` | ごはん | [ごはん.mp3](../baseline/media-staging/audio/20261029T043348Z-0dffcbe2/ごはん.mp3) | 0.864 s | `0480fd9bcc975fb04c780f9857dae3d4bb5298cbd40867649573a56f65db9cbf` | New gTTS download | Valid MP3 + metadata; owner listening approved |
| `vocab-000005` | パン | [パン.mp3](../baseline/media-staging/audio/20261029T043348Z-0dffcbe2/パン.mp3) | 0.672 s | `caa798268034256e20ae6d183245830d4852ebaf31ffa9db8bbc541cb0a1e663` | New gTTS download | Valid MP3 + metadata; owner listening approved |

Technical validation used `audiocollector.validate_audio` to parse MPEG frames and duration, checked each file size and SHA-256 against the run manifest, verified metadata `key`, reading, provider `google_translate_gtts`, locale `ja`, voice settings and relative staging path, and matched each entry against the current 100-row ID registry. The three smoke originals and their metadata were not changed.

The owner stated in this task's conversation, “tôi đã nghe qua 5 file rồi và cả 5 file đều ok,” in answer to a question explicitly naming the five pilot MP3s (IDs 001–005). Before recording that decision, Codex revalidated each staged file and matched its SHA-256 to the run manifest and the table above. This is owner listening approval for those exact five hashes only; no separate review date was supplied. Distribution/usage rights and production promotion remain pending.

## How to listen

The owner completed the pilot listening review. For future rechecks, open each MP3 from the table in a local audio player, in ID order. Compare what is heard with the Japanese reading in the same row; check intelligibility, pronunciation, clipping and unexpected silence. On Windows, `Invoke-Item -LiteralPath 'baseline/media-staging/audio/20261029T043348Z-0dffcbe2/りんご.mp3'` opens a file in the configured player; repeat with the other four filenames. No listening review was performed by Codex.

## Usage-rights boundary

[gTTS documentation](https://gtts.readthedocs.io/en/latest/module.html) describes MP3 generation through Google Translate's speech feature; this is not the Google Cloud Text-to-Speech service. [Google's general terms](https://policies.google.com/terms) do not establish a specific redistribution grant for these downloaded speech files in this application. Product-use and redistribution permission therefore remain **unverified**; successful download and technical validation are not a license. Resolve this before public distribution or promotion intended for public release.
