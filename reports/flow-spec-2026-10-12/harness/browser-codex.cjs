const {chromium}=require('/Users/hyoungmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'), crypto=require('node:crypto'), {pathToFileURL}=require('node:url'), assert=require('node:assert/strict');
const root='/private/tmp/hm2-flow-spec-20261014-codex-2/flow-design/workspace';
const output='/private/tmp/hm2-flow-browser-codex-20261014';fs.mkdirSync(output,{recursive:true});
const files=['explore/index.html','prototype/index.html'];
const hashes=()=>Object.fromEntries(files.map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(root+'/'+p)).digest('hex')]));
const result={before:hashes(),checks:[],errors:[],externalRequests:[]};
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const variant of ['A','B','promoted']){
   const p=await browser.newPage({viewport:{width:1440,height:900}});
   p.on('pageerror',e=>result.errors.push({variant,message:e.message}));
   await p.route(/^https?:/,r=>{result.externalRequests.push(r.request().url());return r.abort()});
   await p.goto(pathToFileURL(root+'/'+(variant==='promoted'?'prototype/index.html':'explore/index.html')).href+(variant==='promoted'?'':'?variant='+variant));
   const check=async(name,fn)=>{await fn();result.checks.push({variant,name,passed:true})};
   const tag=async(name)=>{
    if(!await p.locator('[data-tag]').count()){
     if(await p.locator('#back').count())await p.locator('#back').click();
     await p.locator('#tagsBack').click();
    }
    await p.locator('[data-tag="'+name+'"]').click();
   };
   const setting=async(id,value)=>{await p.locator('.demo').evaluate(e=>e.open=true);await p.locator('#'+id).selectOption(value)};
   await check('exact tag results',async()=>{await tag('사유');assert.deepEqual(await p.locator('[data-note]').evaluateAll(es=>es.map(e=>e.dataset.note)),['n1','n2'])});
   await check('opens stored note',async()=>{await p.locator('[data-note="n1"]').click();assert.match(await p.locator('.reader').innerText(),/생각을 남기는 이유/)});
   await check('changed tag removes prior results',async()=>{await tag('디자인');assert.deepEqual(await p.locator('[data-note]').evaluateAll(es=>es.map(e=>e.dataset.note)),['n3','n4']);assert.equal(await p.locator('.reader').count(),0)});
   await check('content failure distinct',async()=>{await setting('read','fail');await p.locator('[data-note="n3"]').click();assert.match(await p.locator('[role="alert"]').innerText(),/노트 내용 열기 실패/)});
   await check('empty successful lookup',async()=>{await tag('보관');assert.match(await p.locator('#app').innerText(),/조회 완료 · 0개/);assert.equal(await p.locator('[role="alert"]').count(),0)});
   await check('lookup failure is not empty',async()=>{await setting('lookup','fail');assert.match(await p.locator('[role="alert"]').innerText(),/태그 조회 실패/);assert.doesNotMatch(await p.locator('#app').innerText(),/조회 완료 · 0개/)});
   await check('reset clears selection',async()=>{await p.locator('#reset').click();assert.equal(await p.locator('[data-tag][aria-pressed="true"]').count(),0)});
   if(variant==='promoted')await check('comparison removed',async()=>assert.equal(await p.locator('.switcher,#prev,#next').count(),0));
   else{
    await check('URL and history follow variant',async()=>{await p.locator('#next').click();const other=variant==='A'?'B':'A';assert.equal(new URL(p.url()).searchParams.get('variant'),other);await p.goBack();await p.waitForFunction(v=>document.querySelector('#variantLabel').textContent.startsWith(v),variant)});
    await check('select arrow key does not switch variant',async()=>{await p.locator('.demo').evaluate(e=>e.open=true);await p.locator('#lookup').focus();await p.keyboard.press('ArrowRight');assert.equal(new URL(p.url()).searchParams.get('variant'),variant)});
   }
   for(const width of [375,768,1440]){
    await p.setViewportSize({width,height:900});
    await check('no horizontal overflow '+width,async()=>assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)));
    if(width!==768)await p.screenshot({path:output+'/'+variant+'-'+width+'.png',fullPage:true});
   }
   await p.close();
  }
  assert.deepEqual(result.errors,[]);assert.deepEqual(result.externalRequests,[]);result.status='passed';
 }catch(e){result.status='failed';result.failure=String(e);process.exitCode=1}
 finally{await browser.close();result.after=hashes();result.sourcesPreserved=JSON.stringify(result.before)===JSON.stringify(result.after);fs.writeFileSync(output+'/result.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,checks:result.checks.length,failure:result.failure,sourcesPreserved:result.sourcesPreserved}))}
})();
