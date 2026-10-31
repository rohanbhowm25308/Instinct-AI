/* Independent laboratories for modules 06-15. No fake external results. */
(()=>{
const $=id=>document.getElementById(id), E=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labs={
 code:['Code Surgeon','Inspect source code without executing it. Python supports syntax and optional Bandit security checks.'],
 timeline:['Truth Time Machine','Browse real, timestamped investigations recorded in your account.'],
 trust:['Trust Pulse','Measure evidence coverage for your claims; this is not a truth probability.'],
 recover:['Phoenix Recovery','Compare an original answer with a rewrite constrained to supported evidence.'],
 redteam:['Red Team Arena','Generate adversarial tests and optionally evaluate them against a Groq assistant.'],
 certificate:['Proof-of-Truth','Create an auditable SHA-256 evidence report and download the record.'],
 conflict:['Model Conflict Radar','Compare two model answers side by side and analyze disagreements.'],
 history:['Agent Black Box','Inspect saved investigation events and their exact recorded outputs.'],
 voice:['Voice-to-Truth','Transcribe speech in your browser, edit it, then check factual claims.'],
 mission:['Trust Mission Control','Monitor your own audit history, evidence coverage and detected risks.']
};
const special=$('specialWorkspace'),generic=$('genericWorkspace'),select=$('module');
const inp=(id,label,placeholder,rows=5)=>`<label class="lab-field" for="${id}">${label}</label><textarea class="lab-input" id="${id}" rows="${rows}" placeholder="${E(placeholder)}"></textarea>`;
const btn=(id,text)=>`<button type="button" class="lab-button" id="${id}">${text}</button>`;
const tile=(title,body,cls='')=>`<div class="lab-tile ${cls}"><h4>${E(title)}</h4>${body}</div>`;
const text=s=>`<p>${E(s)}</p>`;
const show=(html)=>{$('labResults').innerHTML=html};
const warning=(s)=>tile('Notice',text(s),'lab-error');
const summary=(d)=>{let h='';if(d.error)return warning(d.error);if(d.warning)h+=warning(d.warning);for(const w of d.warnings||[])h+=warning(w);if(d.note)h+=tile('Method & limitations',text(d.note));return h};
async function api(mod,data={}){const b=$('labRun');if(b){b.disabled=true;b.textContent='Processing…'}show(tile('Processing','<p>Analyzing your input…</p>'));try{const r=await fetch('/api/'+mod,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const d=await r.json();if(!r.ok||d.error){show(warning(d.error||'Request failed'));return null}return d}catch(e){show(warning('Network error: '+e.message));return null}finally{if(b){b.disabled=false;b.textContent='Run '+labs[mod][0]+' →'}}}
function renderClaims(d){let h=summary(d);if(d.counts)h+=`<div class="lab-metrics">${Object.entries(d.counts).map(([k,v])=>tile(k,`<div class="lab-number">${v}</div>`)).join('')}</div>`;for(const c of d.claims||[]){let sources=(c.evidence||[]).map(x=>{let url='';try{const u=new URL(x.url);if(['https:','http:'].includes(u.protocol))url=u.href}catch{}return url?`<p><a target="_blank" rel="noopener noreferrer" href="${E(url)}">${E(x.title||url)}</a><br>${E(x.description||'')}</p>`:''}).join('');h+=tile(c.status.toUpperCase(),text(c.claim)+text(c.reason)+sources)}return h}
function renderEvents(d,history=false){let h=summary(d);if(!d.events?.length)return h+tile('No records yet',text('Run an investigation to create an audit record.'));h+='<div class="lab-timeline">';for(const e of d.events)h+=tile(e.kind,`<p>${E(e.created)}</p><p class="lab-small">SHA-256: ${E(e.input_hash)}</p><button class="lab-button lab-ghost" data-audit="${E(e.id)}">${history?'Inspect full event':'View snapshot'}</button>`);return h+'</div>'}
function render(mod){if(!labs[mod]){special.hidden=true;generic.hidden=false;return}generic.hidden=true;special.hidden=false;let [title,desc]=labs[mod];let content=`<h3>${E(title)}</h3><p class="lab-sub">${E(desc)}</p>`;
if(mod==='code')content+=`<label class="lab-field">PROGRAMMING LANGUAGE</label><select id="labLang"><option value="python">Python</option><option value="javascript">JavaScript</option><option value="java">Java</option><option value="cpp">C++</option><option value="other">Other</option></select>`+inp('labA','SOURCE CODE','Paste source code for static analysis…',9);
if(mod==='trust')content+=inp('labA','CLAIMS TO ASSESS','Enter factual statements to check…',6);
if(mod==='recover')content+=inp('labA','ORIGINAL AI RESPONSE','Paste the answer that needs an evidence-constrained revision…',7);
if(mod==='redteam')content+=inp('labA','ASSISTANT CONTEXT / TEST TARGET','Optional: describe the assistant behavior to evaluate…',5);
if(mod==='certificate')content+=inp('labA','CONTENT TO AUDIT','Paste factual claims to generate an evidence audit record…',6);
if(mod==='conflict')content+=`<div class="lab-row"><div>${inp('labA','MODEL A RESPONSE','Paste first answer…',7)}</div><div>${inp('labB','MODEL B RESPONSE','Paste second answer…',7)}</div></div>`;
if(mod==='voice')content+=inp('labA','VOICE TRANSCRIPT','Use the microphone, or type a factual claim…',6)+`<div class="lab-actions">${btn('labMic','🎙 Start microphone')}</div><p class="lab-small">Browser speech recognition may be unavailable; review the transcript before verification.</p>`;
if(mod==='mission')content+=`<p class="lab-small">This dashboard uses your saved investigation records only. It does not invent external monitoring data.</p>`;
content+=`<div class="lab-actions">${btn('labRun',mod==='timeline'||mod==='history'||mod==='mission'?'Load '+title+' →':'Run '+title+' →')}</div><div id="labResults" class="lab-results" aria-live="polite"><div class="lab-tile">Ready. ${E(desc)}</div></div>`;
special.innerHTML=content;
$('labRun').onclick=async()=>{
const a=$('labA')?.value.trim()||'',b=$('labB')?.value.trim()||'';if(!a&&!['timeline','history','mission','redteam'].includes(mod)){show(warning('Enter content before running this feature.'));return}if(mod==='conflict'&&!b){show(warning('Paste both model answers.'));return}
const d=await api(mod,{text:a,language:$('labLang')?.value||'python',answers:[a,b]});if(!d)return;let h=summary(d);
if(mod==='code'){h+=`<div class="lab-metrics">${tile('Security findings',`<div class="lab-number">${d.findings?.length||0}</div>`)}${tile('Language',text(d.language))}</div>`;h+=d.findings?.length?d.findings.map(f=>tile(f.type,`<p>Line ${E(f.line||'?')}</p><p class="lab-code">${E(f.excerpt)}</p>`)).join(''):tile('No issues found',text('No issues matched the implemented checks. This does not prove the code is secure.'));}
else if(mod==='timeline'||mod==='history')h=renderEvents(d,mod==='history');
else if(mod==='mission'){h+=`<div class="lab-metrics">${[['Investigations',d.total_events],['Security findings',d.security_findings],['Supported claims',d.supported_claims],['Unverified claims',d.unverified_claims]].map(([n,v])=>tile(n,`<div class="lab-number">${v}</div>`)).join('')}</div>`;h+=tile('Activity by module',Object.entries(d.by_module||{}).map(([k,v])=>`<span class="lab-badge">${E(k)}: ${v}</span>`).join('')||'No activity yet');h+=`<div class="lab-timeline">${(d.latest||[]).map(x=>tile(x.module,text(x.at))).join('')}</div>`;}
else if(mod==='trust'){h=renderClaims(d)+tile('Evidence coverage',`<div class="lab-number">${d.coverage_percent??0}%</div><p>Supported claims / assessed claims. Not a probability of truth.</p>`);}
else if(mod==='recover'){h=renderClaims(d)+`<div class="lab-row"><div>${tile('Original response',text(a))}</div><div>${tile('Evidence-constrained rewrite',text(d.revised_answer||d.recovery_note||'Unavailable'))}</div></div>`;if(d.recovery_warning)h+=warning(d.recovery_warning);}
else if(mod==='certificate'){h=renderClaims(d);if(d.certificate)h+=tile('Proof-of-Truth audit',`<p>Created: ${E(d.certificate.generated_at)}</p><p class="lab-code">SHA-256: ${E(d.certificate.sha256)}</p><p>${E(d.certificate.scope)}</p><div class="lab-actions"><a class="lab-button" href="/api/download-report/${encodeURIComponent(d.event_id)}">Download audit JSON</a></div>`);}
else if(mod==='conflict'){h+=`<div class="lab-row"><div>${tile('Model A',text(a))}</div><div>${tile('Model B',text(b))}</div></div>`+tile('Disagreement analysis',text(d.analysis||d.warning||'Groq analysis unavailable'));}
else if(mod==='redteam'){h+=`<div class="lab-metrics">${(d.test_prompts||[]).map((p,i)=>tile('Adversarial test '+(i+1),text(p))).join('')}</div>`;h+=(d.model_responses||[]).map(x=>tile('Groq test response',text(x.test)+text(x.response||x.warning||'Unavailable'))).join('');}
else if(mod==='voice')h=renderClaims(d)+tile('Reviewed transcript',text(d.transcript||a));
show(h||tile('No output',text('The service returned no result.')));
};
if(mod==='voice')$('labMic').onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){show(warning('Browser speech recognition is not supported here. Type your transcript instead.'));return}const rec=new SR();rec.lang=navigator.language||'en-US';rec.onresult=e=>{$('labA').value=e.results[0][0].transcript};rec.onerror=e=>show(warning('Speech recognition failed: '+e.error));rec.start()};
}
const observer=new MutationObserver(()=>render(select.value));observer.observe(select,{attributes:true,attributeFilter:['value']});select.addEventListener('change',()=>render(select.value));
// Existing cards set select.value without dispatching change; intercept card clicks in capture phase.
$('featureCards').addEventListener('click',()=>setTimeout(()=>render(select.value),0),true);
$('historyBtn').addEventListener('click',()=>setTimeout(()=>render('timeline'),0));
render(select.value);
special.addEventListener('click',async e=>{const b=e.target.closest('[data-audit]');if(!b)return;try{const r=await fetch('/api/report/'+encodeURIComponent(b.dataset.audit));const d=await r.json();show(tile('Recorded investigation',`<pre class="lab-code">${E(JSON.stringify(d,null,2))}</pre>`)+`<a class="lab-button" href="/api/download-report/${encodeURIComponent(b.dataset.audit)}">Download record</a>`)}catch(err){show(warning(err.message))}});
})();
