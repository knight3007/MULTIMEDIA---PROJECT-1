"""Read existing A-001 evidence and authored preliminary labels; never run AI/network."""
from pathlib import Path
import csv
import hashlib
import json
import sys
from dataclasses import asdict
from collections import Counter
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUDIT = ROOT / 'reports/image_pipeline_audit/20261106T102750Z-cd93f8a1'
sys.path.insert(0, str(ROOT / 'collect data script'))
from audiocollector import validate_audio

STATES = {'P': 'PASS', 'F': 'FAIL', 'R': 'NEEDS_REVIEW', 'U': 'UNKNOWN'}
QDIMS = ['correct_meaning', 'specificity', 'context_appropriateness', 'ambiguity', 'translation_consistency', 'visual_search_suitability']


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overall(values):
    for status in ['FAIL', 'UNKNOWN', 'NEEDS_REVIEW']:
        if status in values: return status
    return 'PASS'


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check_image(asset, english):
    if not asset: return {'status': 'UNKNOWN', 'error': 'MISSING_EVIDENCE: no selected image'}
    path = ROOT / asset['path']
    try:
        digest = sha(path)
        with Image.open(path) as im:
            fmt, size = im.format, list(im.size); im.verify()
        with Image.open(path) as im: im.load()
        meta = load(ROOT / asset['metadata_path'])
        good = (digest == asset['sha256'] and path.stat().st_size == asset['size_bytes']
                and fmt == 'JPEG' and size == asset['dimensions']
                and meta.get('word') == english and meta.get('search_query') == asset.get('query'))
        return {'status': 'PASS' if good else 'FAIL', 'actual_sha256': digest, 'format': fmt,
                'dimensions': size, 'metadata_matches_word_query': meta.get('word') == english and meta.get('search_query') == asset.get('query')}
    except (OSError, ValueError, KeyError) as e:
        return {'status': 'UNKNOWN', 'error': 'MISSING_EVIDENCE: ' + type(e).__name__}


def check_audio(audio, reading, row):
    try:
        path = ROOT / audio['path']; meta_path = ROOT / audio['metadata_path']
        validation = validate_audio(path); meta = load(meta_path); digest = sha(path)
        matches = (digest == audio['sha256'] and validation.size == audio['size_bytes']
                   and meta.get('word') == reading and meta.get('reading') == reading
                   and meta.get('key') == str(row) and meta.get('audio') == audio['path']
                   and meta.get('size') == validation.size and meta.get('source') == audio['provider']
                   and meta.get('locale') == 'ja' and meta.get('voice') == audio['voice']
                   and meta.get('format') == 'mp3' and validation.duration_seconds is not None
                   and abs(meta.get('duration_seconds', -1) - validation.duration_seconds) < .02)
        return {'status': 'PASS' if validation.ok and matches else 'FAIL', 'actual_sha256': digest,
                'metadata_matches_reading_id': matches, 'frame_validation': asdict(validation)}
    except (OSError, ValueError, KeyError, TypeError) as e:
        return {'status': 'UNKNOWN', 'error': 'MISSING_EVIDENCE: ' + type(e).__name__}


def stat(items, field):
    counts = {k: 0 for k in STATES.values()}
    counts.update(Counter(x[field] for x in items))
    definitive = counts['PASS'] + counts['FAIL']
    return {'denominator_all_ids': len(items), 'counts': counts,
            'percent_all_ids': {k: round(100*v/len(items), 2) for k, v in counts.items()},
            'definitive_pass_fail_denominator': definitive,
            'pass_percent_definitive_only': round(100*counts['PASS']/definitive, 2) if definitive else None,
            'new_independent_per_item_labels': 0}


def main():
    labels = list(csv.DictReader((OUT/'preliminary_labels.tsv').open(encoding='utf-8'), delimiter='|'))
    assert len(labels) == 100 and [int(x['id']) for x in labels] == list(range(1,101))
    assert all(len(x['query_codes']) == 6 and set(x['query_codes']) <= STATES.keys() for x in labels)
    qrows = list(csv.DictReader((AUDIT/'02_qwen_queries_100.csv').open(encoding='utf-8-sig')))
    lineage = {x['vocab_id']: x for x in load(AUDIT/'03_image_lineage_100.json')}
    old_image = {x['vocab_id']: x for x in csv.DictReader((AUDIT/'04_image_quality_review.csv').open(encoding='utf-8-sig'))}
    inventory = {x['vocab_id']: x for x in load(ROOT/'reports/full_media_staging_inventory_v1.json')['records']}
    dataset = {x['vocab_id']: x for x in load(ROOT/'data/vocabulary/unified_dataset_v1.json')['records']}
    decisions = load(ROOT/'data/vocabulary/semantic_decisions_v1.json')
    decision_by_id = {x['vocab_id']: x for key in ['approved','context'] for x in decisions[key]}
    inputs = {}
    baseline = load(OUT/'input_baseline.json')
    accepted_audio = {x['vocab_id']: x for x in load(OUT/'owner_audio_acceptance.json')['items']}
    def record(path):
        if path.is_file(): inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    items = []
    for n, (q, lab) in enumerate(zip(qrows, labels), 1):
        vid = q['vocab_id']; inv = inventory[vid]; lin = lineage[vid]; ds = dataset[vid]
        assert vid == f'vocab-{n:06d}' and ds['english'] == q['english']
        cache_path = ROOT/q['evidence_source_file']; cache = load(cache_path); record(cache_path)
        matches = [x for x in cache['records'] if x.get('word') == q['english'] and x.get('query') == q['parsed_qwen_query']]
        asset = inv['image'].get('primary_asset'); image = check_image(asset, q['english'])
        audio = check_audio(inv['audio'], q['japanese'], n)
        qdim = dict(zip(QDIMS, map(STATES.get, lab['query_codes'])))
        selected_source_query = asset.get('query') if asset else None
        qstatus = overall(qdim.values())
        listen = inv['audio']['owner_listening_status']
        listen_report = 'reports/japanese_audio_pilot_review.md' if n <=5 else 'reports/japanese_audio_batch_2_review.md' if n<=10 else 'reports/full_media_staging_review.md'
        report_path = ROOT/listen_report; record(report_path)
        historical_exact = (listen == 'approved_exact_hash' and audio['status']=='PASS'
                            and inv['audio']['sha256'] in report_path.read_text(encoding='utf-8'))
        accepted_hash_matches = accepted_audio[vid]['sha256'] == audio.get('actual_sha256') and accepted_audio[vid]['path'] == inv['audio']['path']
        assert accepted_hash_matches, 'Audio changed outside owner-accepted set: ' + vid
        pronunciation = 'PASS'  # Owner batch acceptance, verified against these exact current bytes.
        missing = []
        if not q['raw_qwen_output']: missing.append('MISSING_EVIDENCE: accepted raw decoded Qwen output')
        pool_applicability = 'NO_RETRIEVAL_INPUT_GATE' if n == 38 else 'CURATED_DIRECT_NO_COMPARATIVE_POOL' if n == 9 else 'SEARCH_SELECTION'
        if pool_applicability == 'SEARCH_SELECTION':
            if not lin.get('candidate_image_urls'): missing.append('MISSING_EVIDENCE: full historical candidate URL list/bytes')
            if not lin.get('candidate_scores'): missing.append('MISSING_EVIDENCE: all candidate SigLIP scores/order')
        missing.append('MISSING_EVIDENCE: exact model revision for this historical 100-ID generation')
        if not asset: missing.append('MISSING_EVIDENCE: selected image (input approval gate)')
        retrieval = (asset or {}).get('candidate_retrieval') or {}
        pool_count = retrieval.get('downloaded_candidates')
        if pool_count is None:
            try: pool_count = int(lin['downloaded_candidate_count']) if lin.get('downloaded_candidate_count') is not None else None
            except ValueError: pass
        causes = []
        if n in (4,9):
            causes.append({'classification':'QWEN_TARGET_MISMATCH','certainty':'CONFIRMED','basis':'Saved original parsed query contradicts owner-approved sense; selected replacement is human/curated, not evidence Qwen improved.'})
        elif n==38:
            causes.append({'classification':'INPUT_APPROVAL_GATE','certainty':'CONFIRMED','basis':'Saved staging history blocked absent approved image_search_intent; no image request for this item.'})
        elif qstatus=='FAIL':
            causes.append({'classification':'QWEN_QUERY_DESIGN','certainty':'SUSPECTED','basis':lab['query_reason']})
        if lab['image_relevance']=='F' and qdim['correct_meaning']=='PASS':
            causes.append({'classification':'CANDIDATE_POOL_MISMATCH' if pool_count==1 else 'RETRIEVAL_OR_RANKING','certainty':'CONFIRMED_OBSERVATION' if pool_count==1 else 'UNRESOLVED','basis':'Only one downloaded candidate was reported and selected; it is irrelevant. No better-candidate comparison exists.' if pool_count==1 else 'Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.'})
        if lab['contamination'] in ('watermark','watermark_and_text','dominant_text'):
            causes.append({'classification':'VISUAL_ACCEPTANCE_GAP','certainty':'CONFIRMED_OBSERVATION','basis':'Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it.'})
        if not causes: causes.append({'classification':'NO_CONFIRMED_ROOT_CAUSE','certainty':'UNKNOWN','basis':'Preliminary review only; inspect complete candidate evidence before causal claims.'})
        for kind in ['image','audio']:
            for key in ['path','metadata_path']:
                if inv[kind].get(key): record(ROOT/inv[kind][key])
        if asset:
            for key in ['path','metadata_path']:
                if asset.get(key): record(ROOT/asset[key])
            run_id = asset.get('source_run_id')
            if run_id: record(ROOT/'baseline/media-staging/images'/run_id/'run_manifest.json')
        a_run=inv['audio'].get('source_run_id')
        if a_run:record(ROOT/'baseline/media-staging/audio'/a_run/'run_manifest.json')
        items.append({'vocab_id':vid,'english':q['english'],'japanese':q['japanese'],'vietnamese':q['vietnamese'],
            'target_sense': ds['target_sense'], 'semantic_decision':decision_by_id.get(vid),
            'query_model':q['qwen_model'],'prompt_version_evidence':q['qwen_prompt_version'],
            'model_revision':'MISSING_EVIDENCE','generation_history':matches[0] if matches else None,
            'query_cache_matches':bool(matches),'raw_qwen_output':q['raw_qwen_output'] or None,
            'parsed_qwen_query':q['parsed_qwen_query'],'effective_image_query':q['effective_image_query'] or None,
            'selected_source_query':selected_source_query,'query_provenance':q['query_provenance'],
            'query_assessment':qdim,'query_overall':qstatus,'query_reason':lab['query_reason'],
            'assessment_author':'AI preliminary desk/visual review; not human-verified ground truth',
            'image_path':inv['image']['path'],'image_sha256':(asset or {}).get('sha256'),
            'selected_asset_evidence':asset,'production_asset_evidence':inv['image'].get('production_asset'),
            'historical_image_lineage':lin,'historical_image_review':old_image[vid],
            'image_relevance':STATES[lab['image_relevance']],'image_visual_quality':STATES[lab['image_visual']],
            'image_learning_suitability':STATES[lab['image_learning']],'image_scene_observation':lab['image_reason'],
            'image_contamination':lab['contamination'],'image_technical':image,
            'image_view_basis':'New 10-cell contact sheets of current selected hash; full-size follow-up for IDs 025/032/040/066/080/091/098' if asset else 'MISSING_EVIDENCE',
            'audio_path':inv['audio']['path'],'audio_sha256':inv['audio']['sha256'],'audio_evidence':inv['audio'],
            'audio_technical':audio,'audio_pronunciation_review':pronunciation,
            'audio_new_ai_listening':'UNKNOWN','audio_listening_report':listen_report,
            'audio_acceptance_basis':'OWNER_BATCH_ACCEPTANCE; see owner_audio_acceptance.json; not a claim of new per-file listening',
            'historical_exact_hash_listening_approval_verified':historical_exact,
            'error_attribution':causes,'downloaded_candidate_count':pool_count,'candidate_pool_applicability':pool_applicability,
            'missing_evidence':missing,'query_evidence_path':q['evidence_source_file'],
            'historical_query_row':q,'human_review':{'query':'NOT_REVIEWED','image':'NOT_REVIEWED','audio':'PASS','audio_basis':'owner batch acceptance in current session','reviewer':'','notes':''},
            'license_context_only':inv['image']['license_status']})
    assert len(items)==100 and len({x['vocab_id'] for x in items})==100
    stats={key:stat(items,key) for key in ['query_overall','image_relevance','image_visual_quality','image_learning_suitability','audio_pronunciation_review']}
    for d in QDIMS: stats['query_'+d] = stat([{'value':x['query_assessment'][d]} for x in items], 'value')
    stats['image_technical']=stat([{'value':x['image_technical']['status']} for x in items],'value')
    stats['audio_technical']=stat([{'value':x['audio_technical']['status']} for x in items],'value')
    stats['new_independent_query_image_labels']=0
    stats['owner_audio_batch_accepted']=100
    stats['new_independent_audio_listening_sessions']=0
    write_json('evaluation_matrix.json', {'run_id':OUT.name,'assessment_kind':'AI_PRELIMINARY_NOT_HUMAN_GROUND_TRUTH','items':items})
    write_json('statistics.json',stats)
    write_json('evidence_hashes.json',inputs)
    fields=['vocab_id','english','japanese','vietnamese','target_sense','query_model','prompt_version_evidence','parsed_qwen_query','effective_image_query','selected_source_query','query_overall',*['query_'+d for d in QDIMS],'query_reason','image_path','image_sha256','image_relevance','image_visual_quality','image_learning_suitability','image_contamination','image_scene_observation','image_technical','audio_path','audio_sha256','audio_technical','audio_pronunciation_review','audio_acceptance_basis','historical_exact_hash_listening_approval_verified','downloaded_candidate_count','root_cause','missing_evidence','human_query','human_image','human_audio','reviewer','reviewer_notes','license_context_only']
    with (OUT/'evaluation_matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for x in items:
            row={k:x.get(k) for k in fields};row.update({'image_technical':x['image_technical']['status'],'audio_technical':x['audio_technical']['status'],'root_cause':json.dumps(x['error_attribution'],ensure_ascii=False),'missing_evidence':'; '.join(x['missing_evidence']),'human_query':'NOT_REVIEWED','human_image':'NOT_REVIEWED','human_audio':'PASS','reviewer':'','reviewer_notes':''})
            row.update({'query_'+d:x['query_assessment'][d] for d in QDIMS});writer.writerow(row)
    for p,digest in baseline['sha256'].items(): assert sha(ROOT/p)==digest, 'Input changed: '+p
    print(json.dumps({k:v.get('counts') if isinstance(v,dict) else v for k,v in stats.items()},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
