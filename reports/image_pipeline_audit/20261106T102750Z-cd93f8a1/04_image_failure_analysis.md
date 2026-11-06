# Image quality and failure-stage analysis

The 100-ID quality CSV is the review index. Its `model_assessed_unverified` label means visual inspection of local contact sheets, **not** owner approval. An empty flag means unreviewed, not suitable. Existing semantic decisions and the three exact-path asset review records remain separate.

## Observations

Prior staging inventory flagged 29 selected images. This audit's contact sheets exposed 25 additional selected images with an observable issue, for **54 provisionally flagged IDs**. The other 45 selected images have no recorded visual issue and remain unapproved; ID 038 has no image. This is not a calibrated error rate because the audit used contact sheets and no independent human labeling protocol.

Clear examples from existing files:

| ID | Query / selected image | Earliest defensible stage | Evidence and limit |
|---|---|---|---|
| 004 rice | Legacy `rice grain` production JPEG; approved sense is cooked rice | A, historical, high | Dataset and owner semantic ledger disagree with the original production query. A suitable cooked-rice staging candidate exists, but review says reuse is restricted. |
| 009 chicken | Legacy `chicken animal` production JPEG; approved sense is chicken meat | A, historical, high | Same direct query/sense conflict. The newer chicken-meat staging candidate is separately reviewed; production remains unchanged. |
| 019 rain | `rain illumination`; night resort with logo | A, medium | Qwen class is semantically wrong; final image also lacks visible rain. Cannot tell whether a suitable candidate was available. |
| 035 shirt | `shirt clothing`; anatomical nose diagram | F, high for mismatch | Query meaning is appropriate; no saved alternatives or scores to distinguish retrieval from ranking. |
| 041 today | `today timepiece`; wristwatch | A, medium | Wrong class in parsed Qwen query precedes search. |
| 043 yesterday | `yesterday place`; drama poster | A, medium | Wrong class precedes search; poster also contains text. |
| 051 go | `person going`; static portrait | F, high for mismatch | Corrective Qwen query describes action; no candidate set remains to apportion Bing versus SigLIP. |
| 065 swim | `person swimming`; static portrait | F, high for mismatch | Same retrieval/ranking evidence gap. |
| 087 hello | `hello object`; screenshot from *Hello Objects* | A, medium | Generic object class sends search toward a proper title rather than a greeting. |
| 097 firefighter | `firefighter person`; recognizable firefighter with stock marks | E, medium | Referent is recognizable, but preview marks block production suitability. Licensing still needs exact-source review. |

Other newly seen examples are ID 053 `write` (action-plan infographic), ID 061 `understand` (grammar lesson thumbnail), ID 071 `problem` (object-oriented software diagram), ID 074 `project` (software screenshot), and ID 082 `always` (exam text). Full notes and hashes are in the CSV and lineage JSON.

## Stage distribution and uncertainty

`A` = visibly implausible Qwen class or generic phrase before search; `E` = recognizable referent with watermark/reuse issue; `F` = insufficient candidate evidence. For all 100 IDs the provisional first-stage values are **A 17**, **A historical production 2**, **E 5**, **F 76**. Among the 54 currently flagged selected images, 17 are assigned A, 5 E and **32 remain F**. The two historical production A cases are now represented by separate staging candidates and are counted outside those 54 selected-image flags.

These counts are triage labels, not proven causal frequencies. In particular, no ID can be defensibly assigned `siglip_selected_wrong_candidate` because the alternative downloaded images and their scores are gone. Nor can all candidates be called irrelevant. Metadata/filename/ID checks found **zero mapping mismatches** in 102 referenced asset versions; this makes stage D unlikely in the audited files, but it does not validate visual meaning. Scores range across positive and negative logits and are not probabilities or a quality threshold.

## Evidence gaps needed for a stronger diagnosis

- Full DDGS result records per query, including source page and position.
- Bytes, hash and normalized preview of each downloaded candidate before cleanup.
- SigLIP score for every candidate, not just the winner; scoring text and model revision.
- Per-candidate fetch status and retry reason.
- Independent owner or trained reviewer labels for query correctness, top-1 and top-K relevance, text/watermarks and rights.
- Exact Qwen decoded raw text for 94 accepted results and inference revision/timestamps.

No image was promoted, relabeled as owner approved or relicensed by this audit.
