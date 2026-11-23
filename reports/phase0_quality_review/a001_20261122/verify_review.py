"""Verify A-001 report integrity/provenance, not semantic correctness."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]


def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))


def main():
    items=read('evaluation_matrix.json')['items']; stats=read('statistics.json')
    assert len(items)==100 and [x['vocab_id'] for x in items]==[f'vocab-{i:06d}' for i in range(1,101)]
    csvrows=list(csv.DictReader((OUT/'evaluation_matrix.csv').open(encoding='utf-8-sig')))
    assert len(csvrows)==100 and len({x['vocab_id'] for x in csvrows})==100
    statuses={'PASS','FAIL','NEEDS_REVIEW','UNKNOWN'}
    for field in ['query_overall','image_relevance','image_visual_quality','image_learning_suitability','audio_pronunciation_review']:
        counter=Counter(x[field] for x in items)
        assert dict(stats[field]['counts'])=={s:counter[s] for s in statuses}
        assert sum(counter.values())==100 and set(counter)<=statuses
        assert stats[field]['definitive_pass_fail_denominator']==counter['PASS']+counter['FAIL']
    assert sum(x['query_cache_matches'] for x in items)==100
    assert sum(x['image_technical']['status']=='PASS' for x in items)==99
    assert items[37]['image_path'] is None and items[37]['image_learning_suitability']=='UNKNOWN'
    assert sum(x['audio_technical']['status']=='PASS' for x in items)==100
    accepted={x['vocab_id']:x for x in read('owner_audio_acceptance.json')['items']}
    assert len(accepted)==100
    for x,row in zip(items,csvrows):
        assert row['vocab_id']==x['vocab_id'] and row['query_overall']==x['query_overall']
        assert x['human_review']['query']=='NOT_REVIEWED' and x['human_review']['image']=='NOT_REVIEWED'
        assert x['human_review']['audio']=='PASS' and x['audio_pronunciation_review']=='PASS'
        assert accepted[x['vocab_id']]['sha256']==x['audio_sha256']==x['audio_technical']['actual_sha256']
        assert not any('listening' in s for s in x['missing_evidence'])
        for field in ['image_path','audio_path']:
            if x[field]: assert (ROOT/x[field]).is_file()
        assert set(x['query_assessment'].values())<=statuses
        assert len(x['query_assessment'])==6
    for source,digest in read('input_baseline.json')['sha256'].items():
        assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==digest,source
    for source,digest in read('evidence_hashes.json').items():
        assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==digest,source
    assert stats['new_independent_query_image_labels']==0
    assert stats['owner_audio_batch_accepted']==100
    html=(OUT/'review_gallery.html').read_text(encoding='utf-8')
    assert 'connect-src \'none\'' in html and 'id="review-data"' in html
    js=(OUT/'gallery.js').read_text(encoding='utf-8')
    assert 'fetch(' not in js and 'XMLHttpRequest' not in js and 'https://' not in js
    assert "['query','image'].map" in js  # Audio already accepted by owner.
    template=list(csv.DictReader((OUT/'human_review_template.csv').open(encoding='utf-8-sig')))
    assert len(template)==100 and all(x['human_query']=='NOT_REVIEWED' and x['human_image']=='NOT_REVIEWED' and not x['reviewer'] for x in template)
    assert read('browser_verification.json')['status']=='PASS'
    print('PASS: 100-ID CSV/JSON consistency, stat denominators, 99 image/100 audio technical checks, owner audio hash binding, no invented human query/image labels, local gallery, baseline/evidence preservation')


if __name__=='__main__': main()
