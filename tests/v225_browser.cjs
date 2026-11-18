/* Substantive content equality, recovery, export glyphs and adversarial UI. */
const assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const {spawnSync}=require('node:child_process');
const {settledVisuals}=require('./browser_stability.cjs');
async function verifyV225(browser,base,root){
 const folder=path.join(root,'v225');fs.mkdirSync(folder,{recursive:true});const records=[];
 for(const native of ['en','ar']){
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce',acceptDownloads:true,extraHTTPHeaders:{'X-Khotwa-Test-Fixture':'v225-no-translation'}}),page=await context.newPage();
  let calls=0;page.on('request',r=>{if(r.url().endsWith('/generate'))calls++});await page.goto(base,{waitUntil:'networkidle'});if(native==='ar')await page.locator('#langBtn').click();
  await page.locator('#have-idea').click();await page.locator('#idea').fill(native==='ar'?'وجبات غداء صحية لموظفي المكاتب في أبوظبي':'Healthy office lunch subscription service in Abu Dhabi');await page.locator('#genBtn').click();await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);
  const read=()=>page.evaluate(()=>({id:currentPlan._canonical_id,summary:currentPlan.summary,overview:currentPlan.idea_overview,action:currentPlan.first_step_today,pitches:currentPlan.pitches,people:currentPlan.customer_personas,days:currentPlan.seven_day_plan,risks:currentPlan.risk_radar.map((r,i)=>i===0?{...r,reason:currentPlan._preEvidenceRisk?.reason||r.reason}:r),score:currentPlan.opportunity_score}));
  // Finance and self-reported observations must survive the same round trip.
  await page.locator('#result-tab-1').click();await page.locator('.p-int').first().selectOption('yes');await page.locator('.p-pre').first().selectOption('payment');await page.locator('.p-note').first().fill('Fictional observation for V2.2.5 regression.');
  await page.locator('#result-tab-7').click();await page.locator('#investment-tab-0').click();for(const[k,v]of Object.entries({price:85,units:80,variable_cost:32,fixed_cost:2100}))await page.locator('#quick-'+k).fill(String(v));await page.locator('#finance-starter button').click();await page.waitForFunction(()=>financeResult?.base.operating_profit==='2140.00');
  const original=await read(),finance=await page.evaluate(()=>investment.inputs),proof=await page.evaluate(()=>Object.fromEntries(Object.entries(currentPlan.proof_summary).filter(([k])=>!['verdict','top_concern'].includes(k))));
  for(let i=0;i<2;i++){
   await page.locator('#langBtn').click();const now=await read();
   for(const key of ['id','summary','action','pitches','people','days','risks','score'])assert.deepEqual(now[key],original[key],native+' '+key);
   for(const key of ['problem','solution','target_user','impact','why_market'])assert.equal(now.overview[key],original.overview[key],native+' '+key);
   assert.deepEqual(await page.evaluate(()=>investment.inputs),finance);assert.deepEqual(await page.evaluate(()=>Object.fromEntries(Object.entries(currentPlan.proof_summary).filter(([k])=>!['verdict','top_concern'].includes(k)))),proof);
   assert.equal(await page.locator('.p-note').first().inputValue(),'Fictional observation for V2.2.5 regression.');
   if(i===0)assert.ok(await page.locator('#translation-notice').isVisible());
   await page.locator('#result-tab-0').click();if(!(await page.locator('.dashboard-actions').evaluate(e=>e.open)))await page.locator('.dashboard-actions summary').click();const wait=page.waitForEvent('download');await page.locator('#pdfBtn').click();const file=path.join(folder,`${native}-switch-${i}.pdf`);await(await wait).saveAs(file);
   const python=spawnSync(process.env.PYTHON_EXE||'python',['-c',"from pypdf import PdfReader;import sys; r=PdfReader(sys.argv[1]);t='\\n'.join(p.extract_text()for p in r.pages);assert '\\u25a0'not in t and '\\ufffd'not in t;print(len(r.pages))",file],{encoding:'utf8',windowsHide:true});assert.equal(python.status,0,python.stderr);
   await settledVisuals(page);await page.screenshot({path:path.join(folder,`${native}-switch-${i}.png`),fullPage:true,animations:'disabled'});
  }
  await page.reload({waitUntil:'networkidle'});const restored=await read();assert.deepEqual(restored,original);assert.deepEqual(await page.evaluate(()=>investment.inputs),finance);assert.equal(calls,1);
  records.push({native,group:'full substantive round trip and refresh; Proof/finance; no AI regeneration; readable exports',pass:true});await context.close();
 }
 for(const locale of ['en','ar']){
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce',extraHTTPHeaders:{'X-Khotwa-Test-Fixture':'v225-claims'}}),page=await context.newPage();await page.goto(base,{waitUntil:'networkidle'});if(locale==='ar')await page.locator('#langBtn').click();await page.locator('#have-idea').click();await page.locator('#idea').fill(locale==='ar'?'خدمة نخلة المقترحة للغداء المكتبي':'Proposed PalmNest office lunch subscription service');await page.locator('#genBtn').click();await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);const bad=locale==='ar'?'تملك خدمة نخلة للغداء المكتبي عقود توريد ملزمة.':'PalmNest holds binding office lunch supply contracts.';assert.ok(!(await page.evaluate(()=>JSON.stringify(currentPlan))).includes(bad));
  await page.locator('#result-tab-5').click();assert.ok(!(await page.locator('#pitch-list').innerText()).includes(bad));await page.screenshot({path:path.join(folder,`${locale}-safe-pitch.png`),fullPage:true});
  await page.locator('#chatLauncher').click();await page.locator('#chat-input').fill(locale==='ar'?'اقترح اختبار وجبات الغداء':'Suggest an office lunch test');await page.locator('#sendBtn').click();await page.waitForFunction(()=>!document.getElementById('sendBtn').disabled);assert.ok(!(await page.locator('#chat-messages').innerText()).includes(bad));await page.screenshot({path:path.join(folder,`${locale}-safe-advisor.png`),fullPage:true});
  records.push({locale,group:'incorrect noun_phrase fixture cannot reach Pitch or Advisor',pass:true});await context.close();
 }
 fs.writeFileSync(path.join(root,'v225-checks.json'),JSON.stringify(records,null,2));console.log(`PASS V2.2.5: ${records.length} new groups; substantive bilingual preservation/recovery, Proof/finance, mixed glyphs, Pitch/Advisor safety`);return records.length;
}
module.exports={verifyV225};
