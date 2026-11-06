# Rice and chicken image replacement review — 2026-10-29

**Current status: three exact JPEGs reviewed in isolated staging; none has owner approval for production.** The original [Bing run manifest](../baseline/media-staging/images/20261029T035126Z-e1fcdb0e/run_manifest.json), [new chicken run manifest](../baseline/media-staging/images/20261029T041516Z-eea4173d/run_manifest.json), [comparison preview](chicken_image_comparison.png) and [machine-readable review record](../data/vocabulary/image_media_reviews_v1.json) preserve the separate findings. The [connectivity diagnosis](ddgs_connectivity_diagnosis.md) explains the earlier search behavior. The comparison is visual evidence only; it grants no usage or owner approval.

## Successful Bing run: `20261029T035126Z-e1fcdb0e`

Both entries have `query_provenance=human_approved`, `search_client=ddgs`, `search_backend=bing`, valid JPEG/metadata and SigLIP selection. This approves the *target search sense*, not either candidate or its license.

| ID and query | Candidate and SHA-256 | Visual finding | Rights and promotion |
|---|---|---|---|
| `vocab-000004`, `cooked rice` | [rice.jpg](../baseline/media-staging/images/20261029T035126Z-e1fcdb0e/rice.jpg), `f447aa26dc6ab0d4c22b46086a1f674b0c799273a3c73902c7c6aea1aeca3cd4`; JPEG 1024×1024 | Bowl of cooked white rice; meaning suitable, no obvious visible watermark | `verified_restricted`; owner promotion `pending` |
| `vocab-000009`, `chicken meat` | [chicken.jpg](../baseline/media-staging/images/20261029T035126Z-e1fcdb0e/chicken.jpg), `433095d063e4c5e6802a5f54c937e2783989225af31514b1a8e00163e71c726d`; JPEG 1024×740 | Raw chicken meat matches meaning, but multiple Dreamstime watermarks/copyright markings | `verified_restricted`; visual production suitability `blocked_watermark`; owner promotion `not_granted` |

### Rice source and license

- Image URL: <https://www.lemonblossoms.com/wp-content/uploads/2019/11/How-To-Cook-White-Rice-S1-1.jpg>.
- Bing source page: <https://www.lemonblossoms.com/web-stories/https-www-lemonblossoms-com-blog-how-to-cook-rice-2/>; title: “How to Cook White Rice Perfectly - Lemon Blossoms.” Metadata has no image-specific author/license. The [site copyright policy](https://www.lemonblossoms.com/disclaimers-privacy-policy/) claims photos are Kathy McDaniel/Lemon Blossoms by default, allows a linked thumbnail in a recipe roundup, requests permission for other uses, and states a default CC BY-NC-ND 3.0 license unless otherwise specified. The planned vocabulary application is outside the expressly allowed recipe-roundup case; no separate permission has been found. The default license entails attribution and other restrictions. Do not promote this JPEG without permission or a separately licensed replacement. Absence of a watermark and a Bing result are not license evidence.

### Watermarked chicken source and license

- Image URL: <https://thumbs.dreamstime.com/z/fresh-chicken-meat-wooden-board-top-view-83865597.jpg>. Bing supplied a [CartoonDealer source-page URL](https://cartoondealer.com/image/167897397/raw-chicken-meat-isolated-white-background-healthy-eating-fresh-chicken-meat-white-background.html) and title “Raw Chicken Meat Isolated On A White Background. Healthy Eating Fresh ...”; that title/page do not reliably identify the actual JPEG, and no author/license is present in metadata. The exact JPEG itself displays Dreamstime markings.
- [Dreamstime terms](https://www.dreamstime.com/terms) allow watermarked media solely for internal purchase evaluation, prohibit use in final/distributed/online materials and prohibit altering/removing the watermark. Attribution does not authorize reuse. Keep this JPEG as staged evidence; do not crop, blur or otherwise hide its watermark. The exact photographer and any purchased license remain unverified.

## New chicken candidate: `20261029T041516Z-eea4173d`

- Selected `--vocab-id vocab-000009` only; one direct, individually verified source passed through the existing download/JPEG-normalization/SigLIP path. `search_client=curated_direct`, `search_backend=curated_direct`; no DDGS search, rice requery, Qwen rewrite or production write. Query and target sense remain `chicken meat` / `human_approved`.
- [Staged chicken.jpg](../baseline/media-staging/images/20261029T041516Z-eea4173d/chicken.jpg): SHA-256 `f897f975b60a61a1f98050fb71f84481dcf789475a86508bc046318f02078ccc`, JPEG RGB 1024×682. It visibly shows raw chicken breast and slices on a cutting board, matching the target sense, with no visible watermark. The single-candidate SigLIP score was `-1.875`; this score is not approval.
- Original image URL: <https://upload.wikimedia.org/wikipedia/commons/1/1e/Kycklingfil%C3%A9.jpg>. The individual [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:Kycklingfil%C3%A9.jpg) names **Dnor** as author, describes the photograph as own work and raw chicken breast, and records the copyright holder's public-domain self-release for use for any purpose without conditions. The license applies to this file specifically. No attribution is required by that release; retain Dnor, the source URL and license page for provenance. Review category: `verified_permitted` on the available source evidence.
- Visual production suitability: `suitable`; owner promotion approval: `pending`. No image was promoted, and the saved dataset still exposes no public image URL or game-ready status.

## Earlier failed run

**Historical status: BLOCKED by DDGS timeouts; no replacement candidate was generated in that run.** The isolated attempt used `collect data script/stage_image_replacements.py` with the owner-approved queries, `--timeout 8 --retries 1 --retry-delay 1 --page-size 3`. It exited 1. The only file in `baseline/media-staging/images/20261029T032618Z-c2a89e06/` is `run_manifest.json`; there is no contact sheet from that run. No image was approved for promotion.

| ID | Original vocabulary and approved meaning | Existing production image | Approved query | Staged candidate | Technical validation | Human image approval |
|---|---|---|---|---|---|---|
| `vocab-000004` | `rice / ごはん / cơm`; cooked rice | [`rice.jpg`](../data/image/en/rice.jpg), rice-grain mismatch; SHA-256 `eee870cf096e8c0aa8e4ebaa78fc8e26c8ed3259d9fdfac9b72162b62d338bd5` | `cooked rice` | None | DDG timed out at `https://duckduckgo.com/?q=cooked+rice`; no JPEG to validate | Pending |
| `vocab-000009` | `chicken / とりにく / thịt gà`; chicken meat | [`chicken.jpg`](../data/image/en/chicken.jpg), live-bird mismatch; SHA-256 `bbd47693a081f8220edd4dc0c7b1e563466cab8485399f0de51c66a46e837387` | `chicken meat` | None | DDG timed out at the Bing image endpoint used by `ddgs`; no JPEG to validate | Pending |

The complete error strings, query provenance, requested candidate counts and empty staged paths are in the [isolated run manifest](../baseline/media-staging/images/20261029T032618Z-c2a89e06/run_manifest.json). A model query, DDG retrieval, JPEG validation or SigLIP score does not constitute human approval. Existing JPEGs and metadata, Qwen cache and unified dataset have the same SHA-256 values before and after this run.

## Remaining promotion gates

1. Confirm the chosen staged candidate's ID, word, approved target sense, exact query, retrieval provenance, decodable JPEG dimensions, metadata, source license and SHA-256. The comparison preview is available for chicken.
2. Obtain an explicit per-image owner decision that names the staged run, candidate path/hash and intended meaning. Keep a rejected candidate in staging as evidence; do not expose it.
3. Copy the previous production JPEG and metadata to a unique backup directory and verify backup hashes. Never replace them before the backup is recoverable.
4. Promote only the approved staged candidate and matching metadata through same-directory temporary files and atomic replacements. Record the media review decision separately from `query_provenance=human_approved`, which approves the **search intent**, not the image itself.
5. Rebuild the unified dataset and confirm the stable ID, approved target sense, production image path, matching query and review state. The current builder always marks present images `needs_review` with null public URL; a persisted media-review record and tested builder rule are prerequisites before it can report `available` or game-safe.
6. Run focused collector/builder tests, the full offline regression suite and a manual image check; verify old backups and unchanged unrelated assets.

No promotion was executed in this task.
