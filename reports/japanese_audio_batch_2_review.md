# Japanese audio staging batch 2 — IDs 006–010

## Gate and scope

The owner confirmed in this task's conversation that they had listened to all five pilot files and all five were acceptable. Before collection, the pilot run `20261029T043348Z-0dffcbe2` was revalidated against its manifest, metadata, complete MP3 frames, duration, registry association and each exact SHA-256. The per-hash listening decision is recorded in [the pilot review](japanese_audio_pilot_review.md). That decision concerns listening quality only. Distribution/usage rights remain unverified, and no production promotion was authorized.

Batch 2 used exactly `vocab-000006` through `vocab-000010` from the persisted registry and canonical Japanese readings from the saved unified dataset. No matching staged or production MP3/metadata existed at preflight. The batch used `.venv-audio`, gTTS `ja`/`com`/`slow=false`, `--timeout 12 --retries 1 --retry-delay 2 --rate-limit-delay 1`, and a unique run directory: `baseline/media-staging/audio/20261029T064854Z-e886a24d/`.

## Results

| Stable ID | English / Japanese / Vietnamese | MP3 path | Bytes | Duration | SHA-256 | Acquisition / resume | Technical / human status |
|---|---|---|---:|---:|---|---|---|
| `vocab-000006` | egg / たまご / trứng | [たまご.mp3](../baseline/media-staging/audio/20261029T064854Z-e886a24d/たまご.mp3) | 7,488 | 0.936 s | `1b719f650b81ce41d95e620d45a1f8561be7c648b8af6522f56d7d7f70e8b430` | downloaded / cache hit | Valid MP3 and metadata; owner listening approved |
| `vocab-000007` | milk / ぎゅうにゅう / sữa | [ぎゅうにゅう.mp3](../baseline/media-staging/audio/20261029T064854Z-e886a24d/ぎゅうにゅう.mp3) | 8,448 | 1.056 s | `d0b8a17db1f18d375f480fa3a4bbd4394a05bd634578673a6948819d8c3fff65` | downloaded / cache hit | Valid MP3 and metadata; owner listening approved |
| `vocab-000008` | water / みず / nước | [みず.mp3](../baseline/media-staging/audio/20261029T064854Z-e886a24d/みず.mp3) | 6,720 | 0.840 s | `e10c97b88c6228e4054d7b78fa0b63b9d2356e17697b9d98f5bca5e5bfb68694` | downloaded / cache hit | Valid MP3 and metadata; owner listening approved |
| `vocab-000009` | chicken / とりにく / thịt gà | [とりにく.mp3](../baseline/media-staging/audio/20261029T064854Z-e886a24d/とりにく.mp3) | 9,216 | 1.152 s | `aa22f2800a7b73fc46fa3172102fde7da4873149aec2020ae1885f240059b93b` | downloaded / cache hit | Valid MP3 and metadata; owner listening approved |
| `vocab-000010` | breakfast / あさごはん / bữa sáng | [あさごはん.mp3](../baseline/media-staging/audio/20261029T064854Z-e886a24d/あさごはん.mp3) | 9,216 | 1.152 s | `bdf4a28eb1eaded85ad981fb0fa70204cc8a41b379e54399eb315da3ce361f21` | downloaded / cache hit | Valid MP3 and metadata; owner listening approved |

[Run manifest](../baseline/media-staging/audio/20261029T064854Z-e886a24d/run_manifest.json) records each source row, triple, relative MP3/metadata path, provider, locale, voice, duration, size, hash, acquisition status and per-ID failure. All five `status=staged`, `cache_status=downloaded`, `resume_cache_status=cache_hit`, `validation_status=valid_mp3_and_metadata`, and `failure=null`. Metadata is under the run's `_metadata/` directory with the corresponding Japanese basename. The frame validator parsed every complete MPEG stream; metadata `key`, reading, path, size, duration, source and voice match each file.

The first CLI exited 0 and printed five successes with no error/retry messages. The run manifest does not store a separate attempt count, so the report claims no retry beyond what the CLI showed. Same-run `--resume` with exactly the same five IDs exited 0, reported five cache hits in the manifest, and produced no new download output. All five MP3 hashes matched their pre-resume values. The resume code's verified cache-hit branch does not call gTTS.

## Regression and integrity

- Focused audio/staging tests before collection: 21 tests, `OK`, exit 0.
- Full offline suite after collection: 100 tests, `OK`, exit 0.
- Vocabulary validator: 100 physical rows, 0 structural issues, exit 0.
- Read-only `build_dataset` equals the saved 100-record `unified_dataset_v1.json`, exit 0. Production audio remains 0 MP3s, all 100 dataset audio states remain `missing`, and public audio URLs remain 0.
- SHA-256 comparison of 45 pre-existing paths found 0 changes: source vocabulary, stable ID registry, semantic decisions, original Qwen cache, saved dataset, production images/metadata, original smoke audio and prior staged audio. The new run added only its manifest, five MP3s and five metadata files. No production image, audio or dataset was promoted or rewritten.
- The first read-only builder check used `.venv-audio` and exited 1 because Pillow is intentionally absent there. Repeating the check with the builder's `.venv` passed. No file was changed by the failed check.

## Owner listening decision and remaining gates

In response to a question explicitly naming all five Batch-2 IDs and readings, the owner confirmed in the current task's conversation, “đã nghe và mọi thứ ổn.” Before recording this decision, Codex rechecked the five staged MP3s against the run manifest, the report hashes above, complete frames, duration, metadata and stable registry identity. This is listening approval for those exact five SHA-256 values only; no separate review date was supplied. Usage/distribution rights and production promotion remain unresolved. Batch 3 is documented separately; no Batch-2 asset was moved into production.
