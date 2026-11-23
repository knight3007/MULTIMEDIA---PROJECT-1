'use strict';
const run = JSON.parse(document.getElementById('review-data').textContent);
const key = 'multimedia-A001-'+run.run_id;
let reviews = {};
let storageAvailable = true;
try { reviews = JSON.parse(localStorage.getItem(key)||'{}'); } catch { storageAvailable = false; }
const list=document.getElementById('items');
const statuses=['NOT_REVIEWED','PASS','FAIL','NEEDS_REVIEW','UNKNOWN'];
const root='../../../';
const localPath=p=>root+p.split('/').map(encodeURIComponent).join('/');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function select(id,field,value){return `<label>${field} — human<select aria-label="${id} human ${field}" data-field="${field}">${statuses.map(s=>`<option ${s===value?'selected':''}>${s}</option>`).join('')}</select></label>`;}
for(const x of run.items){
 const rv=reviews[x.vocab_id]||{};
 const card=document.createElement('article');card.className='item';card.id=x.vocab_id;
 card.dataset.search=[x.vocab_id,x.english,x.japanese,x.vietnamese,x.parsed_qwen_query].join(' ').toLowerCase();
 card.dataset.query=x.query_overall;
 const image=x.image_path?`<img src="${esc(localPath(x.image_path))}" alt="Selected image for ${esc(x.english)} — AI assessment ${x.image_relevance}"><a href="${esc(localPath(x.image_path))}" target="_blank" rel="noopener">Mở ảnh gốc local</a>`:'<p class="missing">MISSING_EVIDENCE: chưa có ảnh</p>';
 card.innerHTML=`<div class="item-head"><h2>${esc(x.vocab_id)} · ${esc(x.english)}</h2><span class="tag ${x.query_overall}">AI query: ${x.query_overall}</span></div><p lang="ja">${esc(x.japanese)}</p><p>${esc(x.vietnamese)}</p><div class="body"><div class="media">${image}${x.audio_path?`<audio controls preload="none" aria-label="Japanese audio ${esc(x.vocab_id)}" src="${esc(localPath(x.audio_path))}"></audio>`:'<p>Audio: MISSING_EVIDENCE</p>'}<small>Ảnh ${x.image_technical.status}; audio kỹ thuật ${x.audio_technical.status}. Audio đã được chủ dự án chấp nhận PASS.</small></div><div><dl class="meta"><dt>Qwen query gốc</dt><dd>${esc(x.parsed_qwen_query)}</dd><dt>Query thực tế của ảnh đang chọn</dt><dd>${esc(x.selected_source_query||'MISSING_EVIDENCE')}</dd><dt>AI preliminary — query</dt><dd>${esc(x.query_reason)}</dd><dt>AI preliminary — ảnh</dt><dd>Liên quan: ${x.image_relevance} · hiển thị: ${x.image_visual_quality} · học từ: ${x.image_learning_suitability}<br>${esc(x.image_scene_observation)}</dd><dt>Audio — owner acceptance</dt><dd>PASS theo xác nhận cả bộ 100 audio trong phiên A-001. Không yêu cầu nghe duyệt lại và không có lượt nghe AI mới.</dd></dl><details><summary>Bằng chứng, hash và attribution</summary><div class="detail">${esc(JSON.stringify({image_sha256:x.image_sha256,audio_sha256:x.audio_sha256,query_model:x.query_model,prompt:x.prompt_version_evidence,query_dimensions:x.query_assessment,semantic_decision:x.semantic_decision,selected_score:x.selected_asset_evidence?.siglip_selection,attribution:x.error_attribution,missing:x.missing_evidence,license_context_only:x.license_context_only},null,2))}</div></details></div></div><div class="review"><p><strong>Human review query/ảnh — chưa tự phê duyệt</strong></p><div class="review-grid">${['query','image'].map(f=>select(x.vocab_id,f,rv[f]||'NOT_REVIEWED')).join('')}</div><label class="notes">Reviewer notes<textarea aria-label="${x.vocab_id} reviewer notes" data-field="notes">${esc(rv.notes||'')}</textarea></label></div>`;
 card.querySelectorAll('[data-field]').forEach(el=>el.addEventListener('input',()=>{
   const item=reviews[x.vocab_id]||{query:'NOT_REVIEWED',image:'NOT_REVIEWED',audio:'PASS',audio_basis:'owner batch acceptance',notes:''};
   item[el.dataset.field]=el.value;item.updated_at=new Date().toISOString();item.reviewer=document.getElementById('reviewer').value.trim();item.image_sha256=x.image_sha256;item.audio_sha256=x.audio_sha256;item.query_text=x.parsed_qwen_query;
   reviews[x.vocab_id]=item;save();
 }));
 list.append(card);
}
function save(){try{localStorage.setItem(key,JSON.stringify(reviews));}catch{storageAvailable=false;}update();}
function update(){
 const search=document.getElementById('search').value.toLowerCase().trim(),filter=document.getElementById('filter').value;
 let visible=0;list.querySelectorAll('.item').forEach(el=>{const show=(!search||el.dataset.search.includes(search))&&(!filter||el.dataset.query===filter);el.hidden=!show;if(show)visible++;});
 document.getElementById('count').textContent=`${visible}/100 items hiển thị; ${Object.keys(reviews).length} item có bản nháp review.`;
 document.getElementById('storage').textContent=storageAvailable?'Bản nháp lưu trong trình duyệt này; dùng Export JSON để bàn giao.':'Không truy cập được localStorage; vẫn có thể Export JSON trước khi đóng trang.';
}
document.getElementById('search').addEventListener('input',update);
document.getElementById('filter').addEventListener('change',update);
document.getElementById('export').addEventListener('click',()=>{
 const reviewer=document.getElementById('reviewer').value.trim();
 if(!reviewer){document.getElementById('storage').textContent='Nhập tên reviewer trước khi export. Đây vẫn là bản nháp, không tự ghi đè nhãn nguồn.';document.getElementById('reviewer').focus();return;}
 const output={run_id:run.run_id,exported_at:new Date().toISOString(),reviewer,kind:'HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL',reviews};
 const url=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)],{type:'application/json;charset=utf-8'}));
 const a=document.createElement('a');a.href=url;a.download='A001-human-review-draft.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
update();
