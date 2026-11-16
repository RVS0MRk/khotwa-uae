/* Real UI -> signed /generate -> current /pdf. Mock provider, no mocked exports. */
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const { spawnSync } = require('node:child_process');
const { settledVisuals } = require('./browser_stability.cjs');

async function verifyConsistency(browser, base, root) {
  const folder = path.join(root, 'consistency'); fs.mkdirSync(folder, {recursive:true});
  const records = [], errors = [];
  for (const native of ['en','ar']) {
    const context = await browser.newContext({viewport:{width:390,height:844}, reducedMotion:'reduce', acceptDownloads:true,
      extraHTTPHeaders:{'X-Khotwa-Test-Fixture':'consistent-assessment'}});
    const page = await context.newPage(); page.setDefaultTimeout(20000); page.on('pageerror', e=>errors.push(e.message));
    await page.goto(base,{waitUntil:'networkidle'});
    assert.ok(!(await page.locator('body').innerText()).includes('Real customer evidence'));
    if (native==='ar') await page.locator('#langBtn').click();
    const landingText=await page.locator('body').innerText();
    assert.ok(landingText.includes(native==='ar'?'سجّل ملاحظات العملاء':'Record customer feedback'));
    assert.ok(!landingText.includes('أدلة من عملاء حقيقيين'));
    await page.locator('#have-idea').click();
    await page.locator('#idea').fill(native==='ar'?'وجبات غداء صحية لموظفي المكاتب في أبوظبي':'Healthy lunch boxes for office workers in Abu Dhabi');
    await page.locator('#region').selectOption('Abu Dhabi');
    await page.locator('#genBtn').click();
    await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);
    const identity=await page.evaluate(()=>currentPlan._canonical_id);
    for (const stage of ['none','five','changed','clear']) {
      await page.locator('#result-tab-1').click();
      if (stage==='five') for(let i=0;i<5;i++) {
        while(await page.locator('.p-int').nth(i).isHidden()) await page.locator('#proof-add').click();
        await page.locator('.p-int').nth(i).selectOption('yes');
        await page.locator('.p-pre').nth(i).selectOption('interest');
      }
      if(stage==='changed') await page.locator('.p-pre').first().selectOption('payment');
      if(stage==='clear') await page.locator('#proofClearBtn').click();
      const total=stage==='changed'?18:15;
      for(const locale of ['en','ar']) {
        if(await page.evaluate(()=>lang)!==locale) await page.locator('#langBtn').click();
        const snapshot=await page.evaluate(()=>({score:currentPlan.opportunity_score,stateScore:currentPlan.state.opportunity_score,
          proof:currentPlan.proof_summary||{},evidence:currentPlan.idea_overview.evidence,id:currentPlan._canonical_id}));
        assert.equal(snapshot.id,identity);assert.equal(snapshot.score.total,total);assert.equal(snapshot.score.status,'provisional');
        assert.deepEqual(snapshot.score,snapshot.stateScore);
        assert.equal(snapshot.proof.total_responses||0,['five','changed'].includes(stage)?5:0);
        assert.ok(snapshot.evidence.includes(locale==='ar'?(['five','changed'].includes(stage)?'بإقرار المستخدم':'ملاحظات'):
          (['five','changed'].includes(stage)?'self-reported':'No Proof Mode observations')));
        await page.locator('#result-tab-0').click();
        if(!(await page.locator('.dashboard-actions').evaluate(e=>e.open))) await page.locator('.dashboard-actions summary').click();
        const download=page.waitForEvent('download'); await page.locator('#pdfBtn').click();
        const file=path.join(folder,`${native}-${stage}-export-${locale}.pdf`);await (await download).saveAs(file);
        const check=spawnSync(process.env.PYTHON_EXE||'python',['tests/check_pdf_consistency.py',file,String(total),locale,stage],{encoding:'utf8',windowsHide:true});
        assert.equal(check.status,0,check.stdout+'\n'+check.stderr);
        records.push({native,stage,export:locale,...snapshot,pdf:JSON.parse(check.stdout),pass:true});
        if(stage==='changed') {await settledVisuals(page);await page.screenshot({path:path.join(folder,`${native}-changed-dashboard-${locale}.png`),fullPage:true,animations:'disabled'});}
      }
      if(stage==='clear') {
        await page.reload({waitUntil:'networkidle'});
        assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.total),15);
        assert.equal(await page.evaluate(()=>currentPlan.proof_summary?.total_responses||0),0);
        assert.ok((await page.locator('.p-int').evaluateAll(nodes=>nodes.map(n=>n.value))).every(x=>x===''));
      }
    }
    // Finance nodes are constructed at bootstrap, before session-language restoration.
    await page.locator('#result-tab-7').click();await page.locator('#investment-tab-2').click();
    for(const locale of ['en','ar','en','ar']) {
      if(await page.evaluate(()=>lang)!==locale) await page.locator('#langBtn').click();
      assert.equal(await page.locator('#finance-advanced summary').innerText(),locale==='ar'?'متقدم / طريقة الحساب':'Advanced / How we calculate');
      assert.ok((await page.locator('#finance-cash-timing-note').textContent()).startsWith(locale==='ar'?'يحافظ وضع التدفق المنفصل':'The separate cash-in/out method'));
      assert.equal(await page.evaluate(()=>currentPlan._canonical_id),identity);
    }
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.evaluate(()=>lang),'ar');
    assert.equal(await page.locator('#finance-advanced summary').innerText(),'متقدم / طريقة الحساب');
    assert.ok((await page.locator('#finance-cash-timing-note').textContent()).startsWith('يحافظ'));
    await page.locator('#finance-advanced').evaluate(e=>e.open=true);
    await settledVisuals(page); await page.screenshot({path:path.join(folder,`${native}-finance-ar-mobile.png`),fullPage:true,animations:'disabled'});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.addScriptTag({url:base+'/__test/axe.js'});
    const violations=await page.evaluate(async()=>{const r=await axe.run(document);return r.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))});
    assert.deepEqual(violations,[]); records.push({native,group:'finance EN-AR-EN, initial AR recovery, mobile, axe',violations,pass:true});
    await context.close();
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(folder,'checks.json'),JSON.stringify({records,errors},null,2));
  console.log(`PASS Founder consistency: ${records.length} cases; 16 actual bilingual PDFs; score 15→18→15; signed export, Clear, Arabic finance and mobile axe`);
  return records.length;
}
module.exports={verifyConsistency};
