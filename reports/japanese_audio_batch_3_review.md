# Japanese audio staging batch 3 — IDs 011–020 — 2026-11-06

## Approval gate and scope

The owner confirmed in this task's conversation, “đã nghe và mọi thứ ổn,” in answer to a question explicitly naming all five Batch-2 IDs and readings. Before collection, those five MP3s were revalidated against their report and manifest SHA-256, complete frames, duration, metadata and stable registry identity. [Batch-2 review](japanese_audio_batch_2_review.md) records listening approval for the exact five hashes. This is a listening decision only; distribution/usage rights and production promotion remain pending.

Batch 3 used exactly IDs 011–020 from the persistent registry and canonical Japanese readings from the unified dataset. Preflight found ten distinct readings and no matching staged or production MP3/metadata. The existing CLI was checked with `--help`. Collection used `.venv-audio`, `--timeout 12 --retries 1 --retry-delay 2 --rate-limit-delay 1`, and a unique isolated run directory `baseline/media-staging/audio/20261106T084604Z-7eae8a7e/`.

## Per-ID results

| Stable ID | English / Japanese / Vietnamese | Staged MP3 | Bytes | Duration | SHA-256 | Provider / locale / voice | Provenance / technical / human status |
|---|---|---|---:|---:|---|---|---|
| `vocab-000011` | cat / ねこ / mèo | [ねこ.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/ねこ.mp3) | 6,720 | 0.840 s | `417001f1b04b3accbaa6ae903c28f5560f32970ccc1d016a9dfbd48b7975501c` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000012` | dog / いぬ / chó | [いぬ.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/いぬ.mp3) | 6,144 | 0.768 s | `3b50dffbbc1fb2b503a40452b008d58f76cc2f4d13d6741547d9758091ecdb1b` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000013` | elephant / ぞう / voi | [ぞう.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/ぞう.mp3) | 5,760 | 0.720 s | `8075358ebd660a042db595e6d14dfb5f8a6a0547d3e20d4fca1444c4268dea01` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000014` | tree / き / cây | [き.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/き.mp3) | 4,800 | 0.600 s | `fef64347db91fbfc6a52df7701e5febf772a6b12cdd5b1b072025113a4a2c61c` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000015` | flower / はな / hoa | [はな.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/はな.mp3) | 6,336 | 0.792 s | `5af0a916e12cb71d0a80f9c4fc6addcdf02a46234cb66226a8ac335e51b97f13` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000016` | mountain / やま / núi | [やま.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/やま.mp3) | 6,336 | 0.792 s | `557266c79f61400dfcc3635a3b4e3bd3deec3a8f9b995da746d042908b7713c1` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000017` | river / かわ / sông | [かわ.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/かわ.mp3) | 6,336 | 0.792 s | `7e2d1a16b35ff302466fbd12b4fdc32aed96f4c17655e8782535b4e1ed5928ac` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000018` | sun / たいよう / mặt trời | [たいよう.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/たいよう.mp3) | 8,256 | 1.032 s | `7229794888cfba327a28b5170d0683b657323ee868f1005feaa767e6f29c8b97` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000019` | rain / あめ / mưa | [あめ.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/あめ.mp3) | 5,952 | 0.744 s | `4dc00051069576a81bcac0799b19dad67d1643ff8c40ecf0c6699e8d4a86724f` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |
| `vocab-000020` | weather / てんき / thời tiết | [てんき.mp3](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/てんき.mp3) | 7,872 | 0.984 s | `140ec453470000ff60a870d2d0d20c261cb127b5d8637baa5d6b9881b042db97` | `google_translate_gtts / ja / com / slow=false` | downloaded; resume cache hit; valid MP3 + metadata; listening/owner approval pending |

[Run manifest](../baseline/media-staging/audio/20261106T084604Z-7eae8a7e/run_manifest.json) records source row/triple, relative MP3 and metadata paths, provider, locale, voice, size, duration, SHA-256, cache source, validation status and failure for every ID. Metadata resides under this run's `_metadata/` directory with each Japanese basename. All ten have `status=staged`, `cache_status=downloaded`, `resume_cache_status=cache_hit`, `validation_status=valid_mp3_and_metadata` and `failure=null`. Complete MPEG frames, duration, metadata `key`, reading, relative audio path, source, locale, voice, size and stable ID association were checked against the actual files.

Initial collection exited 0 and printed ten success messages with no error or retry message. The manifest does not persist a separate attempt count, so the available evidence supports only that no retry was observed. Same-run `--resume` with exactly the same ten IDs exited 0, printed no new download result and recorded ten valid cache hits; all ten MP3 hashes matched the pre-resume values. The verified cache-hit branch skips the gTTS call.

## Regression and preservation

- Focused audio/staging tests before collection: 21 tests, `OK`, exit 0. `.venv-audio -m pip check`: exit 0. CLI `--help`: exit 0.
- Full offline suite after collection: 100 tests in 13.823 s, `OK`, exit 0.
- Vocabulary structural validator: 100 physical rows, 0 issues, exit 0.
- Read-only `build_dataset` in `.venv` equals the saved 100-record unified dataset, exit 0. Production audio remains 0 MP3s, all 100 dataset audio states remain `missing`, and public audio URLs remain 0.
- SHA-256 comparison found 0 changes among 56 pre-existing source/media files: three vocabulary sources, stable ID registry, semantic decisions, Qwen cache, saved dataset, production JPEGs/metadata, original smoke MP3s and metadata, and both previous audio staging runs. This run added only its manifest, ten MP3s and ten metadata files. No production asset or dataset was rewritten.

## Pending review

All ten Batch-3 MP3s remain pending owner listening review against the exact SHA-256 values above. Distribution/usage rights remain unresolved, and no production promotion or public URL was authorized. Stop after this batch; Batch 4 has not started.
