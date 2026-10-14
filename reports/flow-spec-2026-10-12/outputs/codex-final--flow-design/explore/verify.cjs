const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const checks=[];
function test(name,fn){fn();checks.push({name,result:'PASS'})}
function load(file,query=''){
 const html=fs.readFileSync(path.join(root,file),'utf8');
 const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 const elements={};const listeners={};
 const element=id=>elements[id]??=( {innerHTML:'',textContent:'',open:false,focus(){},querySelectorAll(){return []},querySelector:element} );
 const c={document:{getElementById:element},URL,URLSearchParams,location:{href:'file://'+path.join(root,file)+query,search:query},history:{pushState(a,b,url){c.location.href=url.href;c.location.search=url.search}},window:{addEventListener(n,f){listeners[n]=f}}};
 vm.createContext(c);new vm.Script(script,{filename:file}).runInContext(c);
 return {html,script,c,e:elements,listeners,run:s=>vm.runInContext(s,c)};
}
for(const file of ['explore/index.html','prototype/index.html']){
 const x=load(file);const run=x.run;
 test(file+' inline script parses and initializes',()=>assert(x.e.app.innerHTML.includes('태그')));
 test(file+' AC-001 exact tag result set and exclusion',()=>{for(const [tag,ids] of [['사유',['n1','n2']],['디자인',['n3','n4']],['기록',['n1','n4']],['보관',[]]])assert.equal(run(`selected=${JSON.stringify(tag)};JSON.stringify(results().map(n=>n.id))`),JSON.stringify(ids))});
 test(file+' AC-002 switches result membership',()=>{run("selected='사유';resultView();selected='디자인'");const s=run('resultView()');assert(s.includes('n3')&&s.includes('n4')&&!s.includes('data-note="n1"'))});
 test(file+' AC-003 each selected note uses its own stored body',()=>{for(const id of ['n1','n2','n3','n4'])assert.equal(run(`opened='${id}';readFailure=false;readerView().includes(notes.find(n=>n.id===opened).body)`),true)});
 test(file+' AC-004 content failure identifies selected note and hides stored content',()=>{run("opened='n2';readFailure=true");const s=run('readerView()');assert(s.includes('노트 내용 열기 실패')&&s.includes('좋은 질문의 여백')&&!s.includes('빠른 답보다'))});
 test(file+' AC-005 successful empty result',()=>{run("selected='보관';lookupFailure=false");const s=run('resultView()');assert(s.includes('조회 완료 · 0개')&&!s.includes('조회 실패'))});
 test(file+' AC-006 failed lookup does not assert empty result',()=>{run('lookupFailure=true');const s=run('resultView()');assert(s.includes('태그 조회 실패')&&s.includes('아직 알 수 없습니다')&&!s.includes('0개')&&!s.includes('data-note='))});
 test(file+' demo reset clears selection, errors and opened note',()=>{run('render()');x.e['#reset'].onclick();assert.equal(run('selected===null&&opened===null&&!lookupFailure&&!readFailure'),true)});
 test(file+' no external or local-load asset dependency',()=>{assert(!/<(?:script|img|iframe|link)\b[^>]*(?:src|href)\s*=/i.test(x.html));assert(!/\b(?:fetch|import|XMLHttpRequest)\s*\(|@import|url\s*\(/.test(x.html))});
}
const a=load('explore/index.html','?variant=A'), b=load('explore/index.html','?variant=B'), unknown=load('explore/index.html','?variant=unknown');
test('variant A/B and fallback routing logic',()=>{assert(a.e.app.innerHTML.includes('class="split"'));assert(b.e.app.innerHTML.includes('class="stage"'));assert(unknown.e.app.innerHTML.includes('class="split"'))});
test('next/previous wrap with URL and preserve state',()=>{a.run("selected='사유';opened='n1'");a.e.next.onclick();assert.equal(a.c.location.search,'?variant=B');assert.equal(a.run('opened'),'n1');a.e.next.onclick();assert.equal(a.c.location.search,'?variant=A');a.e.prev.onclick();assert.equal(a.c.location.search,'?variant=B')});
test('popstate handler reads current URL',()=>{a.c.location.search='?variant=A';a.listeners.popstate();assert(a.e.app.innerHTML.includes('class="split"'))});
test('arrow handler leaves editable/widget-owned events alone',()=>{const previous=a.c.location.search;a.listeners.keydown({key:'ArrowRight',target:{closest:()=>({})},preventDefault(){throw Error('intercepted widget')}});assert.equal(a.c.location.search,previous)});
test('arrow handler switches outside controls',()=>{a.listeners.keydown({key:'ArrowRight',target:{closest:()=>null},preventDefault(){}});assert.equal(a.c.location.search,'?variant=B')});
const p=load('prototype/index.html');
test('promoted B has no A layout, variant routing, switcher or global shortcuts',()=>assert(!/layoutA|\.split|switcher|switchVariant|popstate|keydown|URLSearchParams/.test(p.html)));
test('promoted B preserves entire shared state/render/interaction code',()=>{const start='const tags=';const common=x=>x.slice(x.indexOf(start),x.indexOf('function layoutA')>=0?x.indexOf('function layoutA'):x.indexOf('function layout(){'));assert.equal(common(b.script),common(p.script))});
test('promoted B initial markup identical to selected exploration B',()=>assert.equal(b.e.app.innerHTML,p.e.app.innerHTML));
console.log(JSON.stringify({method:'Node VM with minimal DOM doubles; not a real browser',checks,passed:checks.length,unrun:['file:// browser runtime','375/768/1440 viewport visual checks and screenshots','real focus order and native keyboard behavior','actual browser reload/back/forward','console/resource errors in browser','real data integration']},null,2));
