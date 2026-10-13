const {chromium} = require('/Users/hyoungmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {readFileSync, writeFileSync, mkdirSync} = require('node:fs');
const {createHash} = require('node:crypto');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const root = '/private/tmp/hm2-flow-spec-20261012-claude-1/flow-design/workspace';
const output = '/private/tmp/hm2-flow-browser-20261014';
mkdirSync(output, {recursive:true});
const files = ['flow.md','explore/index.html','prototype/index.html','prototype/reference.md'];
const hashes = () => Object.fromEntries(files.map(p=>[p,createHash('sha256').update(readFileSync(root+'/'+p)).digest('hex')]));
const result={source:root,before:hashes(),checks:[],errors:[],externalRequests:[]};
(async()=>{
  const browser=await chromium.launch({headless:true});
  try {
    for(const variant of ['A','B','promoted']) {
      const page=await browser.newPage({viewport:{width:1440,height:900}});
      page.on('pageerror',e=>result.errors.push({variant,message:e.message}));
      await page.route(/^https?:/,r=>{result.externalRequests.push(r.request().url());return r.abort();});
      const url=pathToFileURL(root+'/'+(variant==='promoted'?'prototype/index.html':'explore/index.html')).href+(variant==='promoted'?'':'?variant='+variant);
      await page.goto(url);
      const check=async(name,fn)=>{await fn();result.checks.push({variant,name,passed:true});};
      await check('exact-tag results',async()=>{
        await page.locator('[data-act="tag"][data-v="철학"]').click();
        assert.deepEqual(await page.locator('.notebtn strong').allTextContents(),['소크라테스의 변론 메모','니코마코스 윤리학 1권','스토아 철학과 로마']);
      });
      await check('stored note content',async()=>{
        await page.locator('[data-act="open"][data-v="n1"]').click();
        assert.match(await page.locator('.note-body').innerText(),/무지의 자각과 대화법/);
      });
      await check('tag change clears old results and note',async()=>{
        await page.locator('[data-act="tag"][data-v="역사"]').click();
        assert.deepEqual(await page.locator('.notebtn strong').allTextContents(),['로마 공화정의 몰락','스토아 철학과 로마']);
        assert.equal(await page.locator('.note-body').count(),0);
      });
      await check('note read failure differs from lookup failure',async()=>{
        await page.locator('[data-act="tag"][data-v="과학"]').click();
        await page.locator('[data-act="open"][data-v="n6"]').click();
        assert.match(await page.locator('[role="alert"]').innerText(),/노트 내용 열기 실패/);
        assert.equal(await page.locator('.state.empty').count(),0);
      });
      await check('successful empty result',async()=>{
        await page.locator('[data-act="tag"][data-v="보관함"]').click();
        assert.match(await page.locator('.state.empty').innerText(),/조회는 성공/);
        assert.equal(await page.locator('[role="alert"]').count(),0);
      });
      await check('failed lookup is not empty success',async()=>{
        await page.locator('[data-act="tag"][data-v="조회오류"]').click();
        assert.match(await page.locator('[role="alert"]').innerText(),/조회 실패/);
        assert.equal(await page.locator('.state.empty').count(),0);
      });
      await check('reset clears selection',async()=>{
        await page.locator('[data-act="reset"]').click();
        assert.equal(await page.locator('.tagbtn[aria-pressed="true"]').count(),0);
      });
      if(variant==='promoted') {
        await check('comparison controls removed',async()=>assert.equal(await page.locator('.sw,#prev,#next').count(),0));
      } else {
        await check('variant navigation updates URL and history',async()=>{
          await page.locator('#next').click();
          const other=variant==='A'?'B':'A';
          assert.equal(new URL(page.url()).searchParams.get('variant'),other);
          assert.match(await page.locator('#lbl').innerText(),new RegExp('^'+other));
          await page.goBack();
          await page.waitForFunction(v=>document.querySelector('#lbl').textContent.startsWith(v),variant);
          assert.equal(new URL(page.url()).searchParams.get('variant'),variant);
        });
      }
      for(const width of [375,768,1440]) {
        await page.setViewportSize({width,height:900});
        await check('no horizontal overflow at '+width,async()=>{
          const sizes=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:innerWidth}));
          assert.ok(sizes.scroll<=sizes.width+1,JSON.stringify(sizes));
        });
        if(width===375||width===1440)await page.screenshot({path:output+'/'+variant+'-'+width+'.png',fullPage:true});
      }
      await page.close();
    }
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.externalRequests,[]);
    result.status='passed';
  } catch(error) {result.status='failed';result.failure=String(error);process.exitCode=1;}
  finally {await browser.close();result.after=hashes();result.sourcesPreserved=JSON.stringify(result.before)===JSON.stringify(result.after);writeFileSync(output+'/result.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,checks:result.checks.length,failure:result.failure,sourcesPreserved:result.sourcesPreserved}));}
})();
