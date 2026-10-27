/* StartSmart 2.0: state, accessibility, motion and the requested visual matrix.
   Uses the existing isolated mock server; never contacts Groq. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
async function main(){
  const port='5002',base='http://127.0.0.1:'+port;
  const server=spawn(process.env.PYTHON_EXE||'python',['test_browser_server.py'],{env:{...process.env,TEST_PORT:port,GROQ_API_KEY:'test-only-placeholder'},windowsHide:true,stdio:'ignore'});
  const output=fs.mkdtempSync(path.join(os.tmpdir(),'startsmart-2-'));let browser;
  try{
    for(let i=0;i<60;i++){try{if((await fetch(base+'/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
    browser=await chromium.launch({channel:'chrome',headless:true});
    const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(base);await page.waitForFunction(()=>typeof polishLanguage==='function');
    assert.equal(await page.locator('#journey').getAttribute('data-stage'),'0');
    assert.equal((await page.request.get(base+'/static/favicon.svg')).status(),200);
    assert.equal(await page.locator('#chatPanel').evaluate(e=>e.inert),true);
    await page.locator('#idea').fill('Mobile car wash');await page.locator('#category').selectOption({index:5});
    // Hold the mocked HTTP response to inspect loading rather than relying on timing.
    await page.route('**/generate',async route=>{const response=await route.fetch();await new Promise(r=>setTimeout(r,2500));await route.fulfill({response});});
    await page.locator('#genBtn').click();await page.waitForFunction(()=>document.getElementById('loader').classList.contains('show'));
    assert.equal(await page.locator('#generation-steps span').count(),4);
    assert.ok(!(await page.locator('#loader').innerText()).includes('%'));
    await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);
    await page.unroute('**/generate');await page.waitForTimeout(1000);
    assert.equal(await page.locator('#journey').getAttribute('data-stage'),'1');
    assert.equal(await page.locator('#gauge-num').innerText(),String(await page.evaluate(()=>currentPlan.opportunity_score.total)));
    await page.evaluate(()=>selectPanel(1));await page.locator('.p-int').first().selectOption('yes');
    assert.equal(await page.locator('#journey').getAttribute('data-stage'),'2');
    assert.equal(await page.locator('#evidence-ladder').getAttribute('data-highest'),'0');
    await page.locator('.p-price').nth(0).fill('23');await page.locator('.p-price').nth(1).fill('30');
    assert.equal(await page.locator('#proof-progress-count').innerText(),'2 / 10 conversations recorded');
    assert.equal(await page.locator('#proof-stats .v').nth(2).innerText(),'26.5');
    await page.locator('.p-pre').first().selectOption('reservation');
    assert.equal(await page.locator('#evidence-ladder').getAttribute('data-highest'),'2');
    await page.evaluate(()=>selectPanel(6));assert.equal(await page.locator('#journey').getAttribute('data-stage'),'3');
    assert.equal(await page.locator('#journey .completed').count(),1);
    await page.evaluate(()=>selectPanel(1));await page.locator('.p-pre').first().selectOption('payment');
    assert.equal(await page.locator('#journey').getAttribute('data-stage'),'4');
    assert.equal(await page.locator('[data-evidence=actual_payments] .v').innerText(),'1');
    await page.locator('.p-pre').nth(1).selectOption('repeat');
    assert.equal(await page.locator('#evidence-ladder').getAttribute('data-highest'),'4');
    const downloadPromise=page.waitForEvent('download');await page.locator('#proofCsvBtn').click();const download=await downloadPromise;assert.ok(download.suggestedFilename().endsWith('.csv'));
    await page.locator('#chatLauncher').click();const sheet=await page.locator('#chatPanel').boundingBox();assert.ok(sheet.width===390&&sheet.height>750);
    assert.equal(await page.locator('#chatPanel').getAttribute('aria-modal'),'true');await page.waitForFunction(()=>document.getElementById('chat-input')===document.activeElement);
    await page.keyboard.press('Escape');assert.equal(await page.locator('#chatPanel').evaluate(e=>e.inert),true);
    await page.evaluate(()=>selectPanel(5));await page.locator('.pitch-copy').first().click();await page.waitForFunction(()=>document.querySelector('.pitch-copy').textContent.includes('✓'));
    await page.evaluate(()=>{selectPanel(1);window._testOpen=window.open;window.open=url=>{window._openedUrl=url;};});await page.locator('#waOpenBtn').click();assert.ok((await page.evaluate(()=>window._openedUrl)).startsWith('https://wa.me/?text='));await page.evaluate(()=>window.open=window._testOpen);
    await page.emulateMedia({reducedMotion:'reduce'});await page.evaluate(()=>{countUp('gauge-num',currentPlan.opportunity_score.total,800);selectPanel(0);});
    assert.equal(await page.locator('#gauge-num').innerText(),String(await page.evaluate(()=>currentPlan.opportunity_score.total)));
    assert.equal(await page.locator('.score-fill').first().evaluate(e=>getComputedStyle(e).animationName),'none');
    await page.locator('#result-tab-0').focus();await page.keyboard.press('End');assert.equal(await page.locator('#result-tab-6').getAttribute('aria-selected'),'true');
    await page.evaluate(()=>{clearProof();selectPanel(0);});assert.equal(await page.locator('#journey').getAttribute('data-stage'),'1');
    // Capture every requested viewport × language × theme. All tabs receive a full panel capture.
    const sizes=[[1366,768],[1440,900],[390,844],[430,932]];
    for(const [width,height] of sizes){
      await page.setViewportSize({width,height});
      for(const language of ['en','ar'])for(const theme of ['light','dark']){
        const prefix=`${width}-${height}-${language}-${theme}`;
        await page.evaluate(({language,theme})=>{lang=language;document.documentElement.setAttribute('data-theme',theme);applyLang();setEntry('existing');}, {language,theme});
        assert.equal(await page.locator('#brand-name').innerText(),language==='ar'?'خطوة':'Khotwa');
        assert.equal(await page.locator('#title').innerText(),language==='ar'?'من الفكرة إلى الخطوة الأولى.':'From idea to first step.');
        assert.ok((await page.title()).startsWith(language==='ar'?'خطوة':'Khotwa'));
        assert.ok((await page.locator('#wa-text').innerText()).startsWith(language==='ar'?'خطوة —':'Khotwa —'));
        await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
        await page.screenshot({path:path.join(output,prefix+'-hero.png')});
        await page.locator('.input-card').screenshot({path:path.join(output,prefix+'-form.png')});
        await page.evaluate(()=>selectPanel(0));await page.locator('#dashboard-summary').screenshot({path:path.join(output,prefix+'-summary.png')});
        for(let i=0;i<7;i++){
          await page.evaluate(i=>selectPanel(i),i);await page.waitForFunction(i=>{const b=document.getElementById('result-tab-'+i).getBoundingClientRect(),n=document.getElementById('result-nav').getBoundingClientRect();return b.left>=n.left-1&&b.right<=n.right+1;},i);
          assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,prefix+' panel '+i+' page overflow');
          await page.locator('#panel-'+i).screenshot({path:path.join(output,prefix+'-tab'+i+'.png')});
          if(width<600&&i===1)assert.equal(await page.locator('#proof-table tr').nth(1).evaluate(e=>getComputedStyle(e).display),'grid');
        }
        await page.locator('#chatLauncher').click();await page.locator('#chat-input').fill(language==='ar'?'ما المخاطر؟':'What are the risks?');await page.locator('#sendBtn').click();await page.waitForFunction(()=>!_chatBusy);
        await page.locator('#chatPanel').screenshot({path:path.join(output,prefix+'-advisor.png')});await page.keyboard.press('Escape');
        await page.locator('footer').screenshot({path:path.join(output,prefix+'-footer.png')});
        await page.evaluate(()=>{setEntry('discover');document.getElementById('d-skills').value='Design';document.getElementById('d-interests').value='Cars';document.getElementById('d-experience').value='Student';document.getElementById('d-budget').value='4000';document.getElementById('d-time').value='10';});
        await page.locator('#discover-btn').click();await page.waitForFunction(()=>document.querySelectorAll('.idea-card').length===3);
        await page.locator('#discovery-card').screenshot({path:path.join(output,prefix+'-discovery.png')});
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,prefix+' discovery overflow');
      }
      console.log('PASS visual matrix: '+width+'×'+height+' EN/AR light/dark');
    }
    assert.deepEqual(errors,[]);console.log('PASS journey, evidence ladder, counters, score final value, loading, CSV, WhatsApp, copy, bottom sheet, keyboard, reduced motion, favicon.');
    console.log('Visual QA: '+output);
  }finally{if(browser)await browser.close();server.kill();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
