# Media readiness v1 ? 2026-10-29

Source: current `build_dataset(root)` output, checked equal to `data/vocabulary/unified_dataset_v1.json`; production assets and metadata were read, not changed. Manifest SHA-256: `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`.

## Summary

- 100 stable vocabulary IDs. Semantic review: 3 approved, 20 needs_decision, 77 unreviewed.
- Production images: 10 JPEGs with metadata passing the current builder checks; 90 missing. Rows 4 and 9 are known wrong-sense images. The other 8 have no confirmed drift in this audit but their meanings are not independently approved.
- Production audio: 0 MP3s, 100 missing. Three validated gTTS MP3s and matching metadata exist only under `baseline/gtts-smoke-2026-10-28/` for IDs 1?3.
- No image or audio has a recorded media-specific human approval. All production image records are `needs_review`, every public asset URL is null, and no item is currently safe to expose as a reviewed game asset.
- The isolated replacement run `baseline/media-staging/images/20261029T032618Z-c2a89e06/` has no JPEG candidate: DDG timed out for both approved queries. Its `run_manifest.json` records the failures.

## Readiness by stable ID

`Image technical` means the JPEG decodes and its word/provider/query metadata passes the current builder checks. `Unverified` does not mean semantically correct. `Human media approval` means an explicit image/audio review record, which does not exist yet. `Game safe` requires a reviewed public URL and is false for all rows. `Smoke` is isolated audio, never production.

| ID | English | Image production path | Image technical | Image meaning | Human media approval | Game safe | Audio production | Smoke-only MP3 |
|---|---|---|---|---|---|---|---|---|
| vocab-000001 | apple | `data/image/en/apple.jpg` | valid JPEG + metadata (1024x678) | unverified | none recorded | no | missing | validated isolated |
| vocab-000002 | banana | `data/image/en/banana.jpg` | valid JPEG + metadata (1024x796) | unverified | none recorded | no | missing | validated isolated |
| vocab-000003 | strawberry | `data/image/en/strawberry.jpg` | valid JPEG + metadata (1024x682) | unverified | none recorded | no | missing | validated isolated |
| vocab-000004 | rice | `data/image/en/rice.jpg` | valid JPEG + metadata (1024x574) | known mismatch | none recorded | no | missing | ? |
| vocab-000005 | bread | `data/image/en/bread.jpg` | valid JPEG + metadata (1024x680) | unverified | none recorded | no | missing | ? |
| vocab-000006 | egg | `data/image/en/egg.jpg` | valid JPEG + metadata (1024x577) | unverified | none recorded | no | missing | ? |
| vocab-000007 | milk | `data/image/en/milk.jpg` | valid JPEG + metadata (1024x576) | unverified | none recorded | no | missing | ? |
| vocab-000008 | water | `data/image/en/water.jpg` | valid JPEG + metadata (1024x512) | unverified | none recorded | no | missing | ? |
| vocab-000009 | chicken | `data/image/en/chicken.jpg` | valid JPEG + metadata (1024x683) | known mismatch | none recorded | no | missing | ? |
| vocab-000010 | breakfast | `data/image/en/breakfast.jpg` | valid JPEG + metadata (1017x1017) | unverified | none recorded | no | missing | ? |
| vocab-000011 | cat | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000012 | dog | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000013 | elephant | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000014 | tree | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000015 | flower | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000016 | mountain | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000017 | river | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000018 | sun | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000019 | rain | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000020 | weather | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000021 | house | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000022 | kitchen | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000023 | school | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000024 | library | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000025 | hospital | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000026 | airport | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000027 | restaurant | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000028 | car | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000029 | bicycle | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000030 | bridge | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000031 | book | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000032 | phone | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000033 | computer | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000034 | umbrella | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000035 | shirt | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000036 | family | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000037 | mother | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000038 | friend | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000039 | teacher | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000040 | engineer | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000041 | today | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000042 | tomorrow | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000043 | yesterday | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000044 | winter | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000045 | happy | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000046 | hungry | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000047 | easy | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000048 | difficult | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000049 | beautiful | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000050 | strong | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000051 | go | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000052 | read | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000053 | write | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000054 | study | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000055 | work | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000056 | sleep | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000057 | eat | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000058 | drink | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000059 | buy | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000060 | help | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000061 | understand | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000062 | remember | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000063 | receive | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000064 | choose | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000065 | swim | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000066 | software | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000067 | database | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000068 | password | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000069 | music | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000070 | language | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000071 | problem | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000072 | business | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000073 | university | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000074 | project | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000075 | experience | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000076 | vegetable | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000077 | important | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000078 | different | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000079 | dangerous | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000080 | impossible | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000081 | because | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000082 | always | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000083 | sometimes | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000084 | together | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000085 | where | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000086 | why | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000087 | hello | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000088 | please | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000089 | thanks | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000090 | sorry | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000091 | apartment | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000092 | dictionary | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000093 | supermarket | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000094 | pharmacy | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000095 | museum | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000096 | waterfall | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000097 | firefighter | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000098 | neighbor | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000099 | daughter | ? | missing | missing | none recorded | no | missing | ? |
| vocab-000100 | grandmother | ? | missing | missing | none recorded | no | missing | ? |

## Interpretation and next gate

Technical validity, semantic fit, human approval and game exposure are separate gates. The cooked-rice and chicken-meat decisions approve target senses and search intents, not the old images or any future DDG/SigLIP selection. A staged candidate must be manually reviewed before production promotion; this run yielded none. For the other 90 missing images, collect in bounded batches only after each target sense is sufficiently clear. Japanese audio can be collected separately with the audio environment, then validated and reviewed before exposure.
