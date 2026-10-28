/* UI regression tests against an isolated Flask server with a mocked provider. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const {spawn} = require('node:child_process');
const {chromium} = require('playwright');

async function main() {
  const html = fs.readFileSync('templates/index.html', 'utf8');
  for (const [, script] of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) new vm.Script(script);
  const port = process.env.TEST_PORT || '5001';
  const base = `http://127.0.0.1:${port}`;
  const server = spawn(process.env.PYTHON_EXE || 'python', ['test_browser_server.py'], {
    env: {...process.env, GROQ_API_KEY: 'test-only-placeholder', TEST_PORT: port}, windowsHide: true, stdio: 'ignore'
  });
  let browser, page;
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'startsmart-ui-'));
  try {
    for (let i = 0; i < 50; i++) {
      try { if ((await fetch(base + '/health')).ok) break; } catch {}
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    browser = await chromium.launch({channel: 'chrome', headless: true});
    page = await browser.newPage({viewport: {width: 390, height: 844}});
    const errors = [];
    page.on('pageerror', error => {errors.push(error.message); console.error('Browser error:', error.message);});
    page.on('console', message => {if (message.type()==='error') console.error('Browser console:', message.text());});
    await page.goto(base, {waitUntil: 'networkidle'});
    assert.equal(await page.title(), 'Khotwa — From idea to first step.');
    assert.equal(await page.locator('#brand-name').innerText(), 'Khotwa');
    assert.equal(await page.locator('#title').innerText(), 'From idea to first step.');
    assert.equal(await page.locator('#foot-title').innerText(), 'Khotwa · خطوة');
    assert.ok((await page.locator('meta[name="description"]').getAttribute('content')).includes('Khotwa'));
    await page.locator('#langBtn').click();
    assert.equal(await page.title(), 'خطوة — من الفكرة إلى الخطوة الأولى.');
    assert.equal(await page.locator('#brand-name').innerText(), 'خطوة');
    assert.equal(await page.locator('#title').innerText(), 'من الفكرة إلى الخطوة الأولى.');
    assert.equal(await page.locator('#foot-title').innerText(), 'خطوة · Khotwa');
    assert.ok((await page.locator('meta[name="description"]').getAttribute('content')).includes('خطوة'));
    assert.equal(await page.locator('#category-hint').innerText(), 'اختر الفئة؛ تظهر الاقتراحات أثناء الكتابة.');
    assert.equal(await page.locator('#chatLauncher').getAttribute('aria-label'), 'افتح مستشار خطوة');
    await page.locator('#genBtn').click();
    assert.ok(/[\u0600-\u06ff]/.test(await page.locator('#error').innerText()));
    await page.locator('#themeBtn').click();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    for (const id of ['#category', '#genBtn']) {
      await page.locator(id).scrollIntoViewIfNeeded();
      await page.evaluate(()=>positionAdvisorLauncher());
      const control = await page.locator(id).boundingBox(), launcher = await page.locator('#chatLauncher').boundingBox();
      assert.ok(control.x >= launcher.x + launcher.width + 8 || control.x + control.width <= launcher.x - 8 || control.y + control.height <= launcher.y - 8 || control.y >= launcher.y + launcher.height + 8, 'RTL launcher does not overlap controls');
    }
    await page.screenshot({path:path.join(output,'arabic-dark-form-390.png')});
    await page.locator('#langBtn').click();
    await page.locator('#themeBtn').click();
    await page.locator('#need-idea').click();
    await page.locator('#d-skills').fill('AutoCAD, communication, basic engineering knowledge');
    await page.locator('#d-interests').fill('Cars and technology');
    await page.locator('#d-experience').fill('University student');
    await page.locator('#d-budget').fill('4000');
    await page.locator('#d-region').selectOption('Abu Dhabi');
    await page.locator('#d-context').selectOption('Local service or digital');
    await page.locator('#d-time').fill('10 hours/week');
    await page.locator('#discover-btn').click();
    await page.waitForFunction(() => document.querySelectorAll('.idea-card').length === 3);
    assert.equal(await page.locator('.idea-card button').count(), 3);
    for (const card of await page.locator('.idea-card').all()) {
      const text = await card.innerText();
      for (const label of ['Why it fits', 'Likely customer', 'Low-cost first test', 'Main assumption', 'Explore this idea', 'AI ASSUMPTION']) assert.ok(text.includes(label), label);
    }
    await page.locator('.idea-card button').first().click();
    await page.waitForFunction(() => currentPlan && document.getElementById('results').style.display === 'block');
    const state = await page.evaluate(() => currentPlan.state);
    assert.equal(state.idea, 'Mobile car wash');
    assert.equal(state.region, 'Abu Dhabi');
    assert.equal(state.context, 'Local service or digital');
    assert.equal(state.user_budget_aed, 4000);
    assert.equal(state.category, 'Services & Maintenance');
    assert.equal(state.evidence.responses, 0);
    assert.equal(state.idea_source, 'ai_suggestion_selected');
    assert.ok((await page.locator('#overview-body').innerText()).includes('AI SUGGESTION SELECTED BY USER'));
    let extraGenerateCalls=0;
    await page.route('**/generate', route=>{extraGenerateCalls++;return route.continue();});
    const initialScore=await page.evaluate(()=>currentPlan.opportunity_score.total);
    await page.locator('#langBtn').click();
    assert.equal(await page.evaluate(()=>currentPlan._content_lang),'ar');
    assert.ok(/[\u0600-\u06ff]/.test(await page.locator('#overview-body').innerText()));
    assert.ok(/[\u0600-\u06ff]/.test(await page.locator('#score-bars').innerText()));
    assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.total),initialScore);
    assert.equal(await page.evaluate(()=>currentPlan.state.user_budget_aed),4000);
    await page.locator('#langBtn').click();
    assert.equal(await page.evaluate(()=>currentPlan._content_lang),'en');
    assert.equal(extraGenerateCalls,0,'language switching reused the generated plan');
    await page.unroute('**/generate');
    await page.evaluate(()=>{window._copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>{window._copied.push(value);}}});});
    for(const language of ['en','ar']){
      if(language==='ar')await page.locator('#langBtn').click();
      await page.evaluate(()=>{document.querySelectorAll('.pitch-copy').forEach(button=>button.click());for(const id of ['passportCopyBtn','waBtn','shareBtn'])document.getElementById(id).click();});
      await page.waitForFunction(n=>window._copied.length===n,language==='ar'?14:7);
      const copied=await page.evaluate(()=>window._copied.slice(-7));
      assert.equal(copied.length,7);
      assert.ok(copied.every(value=>value.trim().length>20));
      assert.ok(!copied.some(value=>/Preliminary score:\s*Preliminary score:|payment\.\./i.test(value)));
    }
    await page.waitForTimeout(1600);
    await page.evaluate(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('test clipboard failure');}}});document.execCommand=()=>true;document.getElementById('shareBtn').click();});
    await page.waitForFunction(()=>document.getElementById('shareBtn').textContent.includes('✓'));
    assert.ok(!(await page.locator('#waBtn').innerText()).includes('✓'));
    await page.locator('#langBtn').click();
    for (const index of [6, 0, 3]) {
      await page.evaluate(i=>selectPanel(i), index);
      await page.waitForFunction(i=>{
        const tab=document.getElementById('result-tab-'+i).getBoundingClientRect(),nav=document.getElementById('result-nav').getBoundingClientRect();
        return tab.left>=nav.left-1&&tab.right<=nav.right+1;
      },index);
    }
    assert.ok(await page.locator('#result-nav').evaluate(el=>el.scrollWidth>el.clientWidth));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=390),true);
    assert.ok((await page.locator('#score-interp').innerText()).includes('assumptions'));
    assert.equal(await page.locator('#decision-main').innerText(), 'Validate more');
    await page.locator('#result-tab-3').click();
    const meta = await page.locator('#plan-meta').innerText();
    for (const text of ['4,000 AED', '5,000 AED', '1,000 AED', 'AI ESTIMATE', 'Validate demand before increasing']) assert.ok(meta.includes(text), text);
    assert.equal(await page.locator('#steps-list .step-card').count(), 7);
    assert.equal(new Set(await page.locator('#day-grid .day-card').allTextContents()).size, 7);
    await page.locator('#result-tab-2').click();
    assert.ok((await page.locator('#persona-grid').innerText()).includes('Residential car owners'));
    assert.ok((await page.locator('#opp-map').innerText()).includes('Evidence pending'));
    await page.locator('#result-tab-1').click();
    await page.locator('.p-int').nth(0).selectOption('yes');
    await page.locator('.p-int').nth(1).selectOption('maybe');
    await page.locator('.p-pre').nth(0).selectOption('reservation');
    await page.locator('.p-pre').nth(1).selectOption('intent');
    await page.locator('.p-price').nth(0).fill('20');
    await page.locator('.p-price').nth(1).fill('40');
    await page.locator('.p-price').nth(2).fill('-100');
    const proof = await page.evaluate(() => currentPlan.proof_summary);
    assert.equal(proof.interested, 1); assert.equal(proof.maybe, 1);
    assert.equal(proof.no_payment_reservations, 1); assert.equal(proof.stated_intent, 1);
    assert.equal(proof.actual_payments, 0); assert.equal(proof.avg_price, 30); assert.equal(proof.total_responses, 2);
    assert.equal(await page.locator('#proof-stats .v').nth(2).innerText(), '30');
    await page.locator('.p-price').nth(0).fill('23');
    await page.locator('.p-price').nth(1).fill('30');
    assert.equal(await page.evaluate(()=>currentPlan.proof_summary.avg_price),26.5);
    assert.equal(await page.locator('#proof-stats .v').nth(2).innerText(),'26.5');
    await page.locator('.p-concern').first().fill('=1+1,"comma"');
    const csvDownload=page.waitForEvent('download');
    await page.locator('#proofCsvBtn').click();
    const csv=fs.readFileSync(await (await csvDownload).path(),'utf8');
    assert.ok(csv.includes('"\'=1+1,""comma"""'),'CSV escapes spreadsheet formulas, commas and quotes');
    await page.evaluate(()=>positionAdvisorLauncher());
    const priceBox=await page.locator('.p-price').nth(1).boundingBox(),launcherBox=await page.locator('#chatLauncher').boundingBox();
    assert.ok(priceBox.x+priceBox.width<=launcherBox.x-8 || priceBox.x>=launcherBox.x+launcherBox.width+8 || priceBox.y+priceBox.height<=launcherBox.y-8 || priceBox.y>=launcherBox.y+launcherBox.height+8,'LTR launcher stays outside form controls');
    assert.ok((await page.locator('#proof-verdict').innerText()).includes('not sales'));
    await page.locator('.p-pre').nth(1).selectOption('payment');
    assert.equal(await page.evaluate(() => currentPlan.decision_engine.decision), 'Review pilot evidence');
    assert.ok(!(await page.locator('#decision-reason').textContent()).includes('Pre-evidence'));
    await page.locator('#proofClearBtn').click();
    assert.equal(await page.evaluate(() => currentPlan.state.evidence.responses), 0);
    assert.equal(await page.evaluate(() => currentPlan.decision_engine.decision), 'Validate more');
    const clearDownload=page.waitForEvent('download');
    await page.locator('#proofCsvBtn').click();
    assert.ok(!(fs.readFileSync(await (await clearDownload).path(),'utf8')).includes('=1+1'));
    await page.locator('#chatLauncher').click();
    await page.locator('#chat-input').fill('What are my biggest risks?');
    await page.locator('#sendBtn').click();
    await page.waitForFunction(() => document.querySelectorAll('.advisor-card').length > 0);
    const advisor = await page.locator('.advisor-card').last().innerText();
    for (const expected of ['Test customer demand first','Demand:','Interview five potential customers.','Next action:','Record interviews.','Caution:','Regulatory requirements are unverified.']) assert.ok(advisor.includes(expected),expected);
    assert.ok(!/[#*{]|&#|<br>|```|Demand::|Next action: Next action:/.test(advisor));
    await page.locator('#chat-input').fill('malformed');await page.locator('#sendBtn').click();
    await page.waitForFunction(() => document.querySelectorAll('.advisor-card').length === 2);
    assert.ok((await page.locator('.advisor-card').last().innerText()).includes('Next validation step'));
    await page.locator('#chatClose').click();
    await page.locator('#result-tab-0').click();
    await page.locator('#overview-body').scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= 390), true);
    await page.screenshot({path: path.join(output, 'english-390.png')});
    const ergonomicResponse = await page.request.post(base + '/generate', {data:{idea:'Mobile Car‑Interior Ergonomic Consulting',category:'Services & Maintenance',budget:4000,region:'Abu Dhabi',context:'Local service',lang:'en'}});
    const ergonomicPlan = await ergonomicResponse.json();
    assert.deepEqual(ergonomicPlan.customer_personas.map(p=>p.name),['Daily commuters','Ride-hailing drivers','Fleet / company vehicle managers']);
    await page.evaluate(p=>{currentPlan=p;showPlan(p);},ergonomicPlan);
    await page.evaluate(()=>selectPanel(3));
    assert.ok((await page.locator('#plan-meta').innerText()).includes('Not estimated yet'));
    assert.ok((await page.locator('#plan-meta').innerText()).includes('Estimated gap: Not available'));
    assert.equal(await page.locator('#cost-chart').isVisible(),false);
    ergonomicPlan.steps.forEach((step,i)=>step.estimated_cost_aed=[0,0,0,0,100,300,0][i]);
    ergonomicPlan.total_estimated_cost_aed=5000;
    ergonomicPlan.state.user_budget_aed=200;
    ergonomicPlan.proof_summary={total_responses:2,avg_price:26.5};
    await page.evaluate(p=>{currentPlan=p;showPlan(p);},ergonomicPlan);
    assert.equal(await page.evaluate(()=>currentPlan.total_estimated_cost_aed),400);
    assert.equal(await page.evaluate(()=>currentPlan.estimated_budget_gap_aed),200);
    assert.ok(!(await page.locator('#plan-meta').innerText()).includes('5,000'));
    await page.evaluate(()=>selectPanel(6));
    assert.ok((await page.locator('#report-table').innerText()).includes('400 AED'));
    await page.evaluate(()=>selectPanel(0));
    assert.ok((await page.locator('#overview-body').innerText()).includes('Potential benefit'));
    assert.ok(!(await page.locator('#overview-body').innerText()).includes('injury'));
    const englishPdf = await page.request.post(base + '/pdf', {data: {...ergonomicPlan, _lang:'en'}});
    assert.equal(englishPdf.status(), 200);
    assert.ok((englishPdf.headers()['content-disposition']||'').includes('Khotwa_UAE_Founder_Report.pdf'));
    fs.writeFileSync(path.join(output,'english.pdf'),await englishPdf.body());
    await page.locator('#langBtn').click();
    await page.locator('#genBtn').click();
    await page.waitForFunction(() => !document.getElementById('genBtn').disabled && currentPlan && document.getElementById('results').style.display === 'block');
    assert.equal(await page.locator('html').getAttribute('lang'), 'ar');
    assert.ok((await page.locator('body').getAttribute('class')).includes('rtl'));
    assert.equal(await page.locator('.p-freq').first().getAttribute('placeholder'),'أسبوعياً');
    assert.ok(!(await page.locator('#overview-body').innerText()).includes('AED'));
    assert.ok(!(await page.locator('#regional-resource').innerText()).includes('Department'));
    assert.ok(!(await page.locator('#qr-code').innerText()).includes('Open WhatsApp'));
    for (const index of [6,0,3]) {
      await page.evaluate(i=>selectPanel(i),index);
      await page.waitForFunction(i=>{const b=document.getElementById('result-tab-'+i).getBoundingClientRect(),n=document.getElementById('result-nav').getBoundingClientRect();return b.left>=n.left-1&&b.right<=n.right+1},index);
    }
    await page.evaluate(()=>selectPanel(0));
    await page.locator('#overview-body').scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= 390), true);
    await page.screenshot({path: path.join(output, 'arabic-390.png')});
    const pdf = await page.request.post(base + '/pdf', {data: {...ergonomicPlan, _lang:'ar'}});
    assert.equal(pdf.status(), 200); assert.ok((await pdf.body()).subarray(0,4).equals(Buffer.from('%PDF')));
    assert.ok((pdf.headers()['content-disposition']||'').includes('Khotwa_UAE_Founder_Report.pdf'));
    fs.writeFileSync(path.join(output,'arabic.pdf'),await pdf.body());
    await page.locator('#langBtn').click();
    await page.locator('#newBtn').click();
    await page.locator('#idea').fill('malformed <img src=x onerror=alert(1)>');
    await page.locator('#category').selectOption({index:1});
    await page.locator('#genBtn').click();
    await page.waitForFunction(() => currentPlan && currentPlan._local && document.getElementById('results').style.display==='block');
    assert.equal(await page.locator('#report-table img').count(), 0);
    assert.equal(await page.locator('#overview-body img').count(), 0);
    assert.equal(new Set(await page.locator('#day-grid .day-card').evaluateAll(cards=>cards.map(c=>c.querySelector('.a:last-child')?.textContent))).size,7);
    assert.ok(new Set(await page.evaluate(()=>currentPlan.risk_radar.map(r=>r.level))).size>1);
    assert.equal(new Set(await page.evaluate(()=>currentPlan.customer_personas.map(p=>p.ask))).size,3);
    assert.equal(await page.evaluate(() => currentPlan.state.user_budget_aed), 10000);
    const recoveryContext = await browser.newContext();
    const recoveryPage = await recoveryContext.newPage();
    await recoveryPage.goto(base, {waitUntil:'networkidle'});
    await recoveryPage.locator('#idea').fill('Mobile car wash');
    await recoveryPage.locator('#category').selectOption({index:1});
    await recoveryPage.locator('#user_type').selectOption({index:1});
    await recoveryPage.locator('#region').selectOption('Abu Dhabi');
    await recoveryPage.locator('#budget').fill('4000');
    await recoveryPage.reload({waitUntil:'networkidle'});
    assert.equal(await recoveryPage.locator('#idea').inputValue(),'Mobile car wash');
    assert.equal(await recoveryPage.locator('#category').evaluate(el=>el.selectedIndex),1);
    assert.equal(await recoveryPage.locator('#region').inputValue(),'Abu Dhabi');
    assert.equal(await recoveryPage.locator('#budget').inputValue(),'4000');
    await recoveryPage.locator('#genBtn').click();
    await recoveryPage.waitForFunction(()=>currentPlan&&document.getElementById('results').style.display==='block');
    await recoveryPage.locator('#result-tab-1').click();
    await recoveryPage.locator('.p-int').first().selectOption('yes');
    await recoveryPage.locator('.p-pre').first().selectOption('reservation');
    await recoveryPage.locator('.p-price').first().fill('25');
    await recoveryPage.locator('.p-freq').first().fill('Every Thursday with Sara');
    await recoveryPage.locator('.p-concern').first().fill('Call me 0501234567');
    await recoveryPage.evaluate(()=>document.getElementById('chat-input').value='Private customer note');
    await recoveryPage.locator('#langBtn').click();
    await recoveryPage.locator('#themeBtn').click();
    const saved = await recoveryPage.evaluate(()=>sessionStorage.getItem(SESSION_KEY));
    assert.ok(saved.includes('Mobile car wash'));
    for(const privateText of ['Every Thursday with Sara','Call me 0501234567','Private customer note'])assert.ok(!saved.includes(privateText),privateText);
    const isolatedContext = await browser.newContext();
    const isolatedPage = await isolatedContext.newPage();
    await isolatedPage.goto(base,{waitUntil:'networkidle'});
    assert.equal(await isolatedPage.locator('#results').isVisible(),false);
    assert.equal(await isolatedPage.locator('#idea').inputValue(),'');
    assert.equal(await isolatedPage.evaluate(()=>sessionStorage.getItem('khotwa-business-session-v1')),null);
    await isolatedPage.locator('#idea').fill('Customer email: sara@example.com');
    assert.equal(await isolatedPage.evaluate(()=>sessionStorage.getItem(SESSION_KEY)),null);
    await isolatedPage.locator('#idea').fill('gsk_12345678901234567890');
    assert.equal(await isolatedPage.evaluate(()=>sessionStorage.getItem(SESSION_KEY)),null);
    await isolatedContext.close();
    await recoveryPage.reload({waitUntil:'networkidle'});
    assert.equal(await recoveryPage.locator('html').getAttribute('lang'),'ar');
    assert.equal(await recoveryPage.locator('html').getAttribute('data-theme'),'dark');
    assert.equal(await recoveryPage.locator('#results').isVisible(),true);
    assert.equal(await recoveryPage.evaluate(()=>currentPlan.state.idea),'Mobile car wash');
    assert.equal(await recoveryPage.locator('#idea').inputValue(),'Mobile car wash');
    assert.equal(await recoveryPage.locator('#category').evaluate(el=>el.selectedIndex),1);
    assert.equal(await recoveryPage.locator('#region').inputValue(),'Abu Dhabi');
    assert.equal(await recoveryPage.locator('#budget').inputValue(),'4000');
    assert.equal(await recoveryPage.locator('#result-tab-1').getAttribute('aria-selected'),'true');
    assert.equal(await recoveryPage.locator('.p-int').first().inputValue(),'yes');
    assert.equal(await recoveryPage.locator('.p-pre').first().inputValue(),'reservation');
    assert.equal(await recoveryPage.locator('.p-price').first().inputValue(),'25');
    assert.equal(await recoveryPage.locator('.p-freq').first().inputValue(),'');
    assert.equal(await recoveryPage.locator('.p-concern').first().inputValue(),'');
    assert.equal(await recoveryPage.evaluate(()=>currentPlan.state.evidence.responses),1);
    await recoveryPage.locator('#proofClearBtn').click();
    await recoveryPage.reload({waitUntil:'networkidle'});
    assert.equal(await recoveryPage.locator('#results').isVisible(),true);
    assert.equal(await recoveryPage.locator('.p-int').first().inputValue(),'');
    assert.equal(await recoveryPage.locator('.p-price').first().inputValue(),'');
    assert.equal(await recoveryPage.evaluate(()=>currentPlan.state.evidence.responses),0);
    await recoveryPage.locator('#newBtn').click();
    assert.equal(await recoveryPage.evaluate(()=>sessionStorage.getItem(SESSION_KEY)),null);
    await recoveryPage.reload({waitUntil:'networkidle'});
    assert.equal(await recoveryPage.locator('#results').isVisible(),false);
    assert.equal(await recoveryPage.locator('#idea').inputValue(),'');
    await recoveryContext.close();
    for(const profile of [
      {idea:'AI-Powered No-Code Website Builder for SMBs',category:'Technology & Digital',region:'Abu Dhabi',budget:'5000',risk:'data handling'},
      {idea:'Healthy meal prep for professionals',category:'Food & Catering',region:'Dubai',budget:'3000',risk:'Meal preparation'},
      {idea:'Mobile cleaning service',category:'Services & Maintenance',region:'Sharjah',budget:'4000',risk:'Travel time'},
    ]){
      const context=await browser.newContext();const journey=await context.newPage();
      try{
        await journey.goto(base,{waitUntil:'networkidle'});
        await journey.locator('#idea').fill(profile.idea);
        await journey.evaluate(category=>{document.getElementById('category').selectedIndex=T.en.categories.indexOf(category)+1;},profile.category);
        await journey.locator('#region').selectOption(profile.region);
        await journey.locator('#budget').fill(profile.budget);
        await journey.locator('#genBtn').click();
        await journey.waitForFunction(()=>currentPlan&&document.getElementById('results').style.display==='block');
        const plan=await journey.evaluate(()=>currentPlan);
        assert.equal(plan.state.idea,profile.idea);
        assert.equal(plan.state.category,profile.category);
        assert.equal(plan.state.region,profile.region);
        assert.equal(plan.state.user_budget_aed,Number(profile.budget));
        assert.ok(plan.risk_radar[3].reason.includes(profile.risk));
        assert.equal(new Set(plan.customer_personas.map(p=>p.ask)).size,3);
        assert.equal(plan.opportunity_score.total,['local_fit','clear_customer','low_starting_cost','easy_first_step','growth_potential'].reduce((n,key)=>n+plan.opportunity_score[key].score,0));
        await journey.evaluate(()=>selectPanel(6));
        const resource=await journey.locator('#regional-resource').innerText();
        assert.equal(resource.includes('Abu Dhabi Department'),profile.region==='Abu Dhabi');
        if(profile.category==='Technology & Digital'){
          for(const language of ['en','ar']){
            if(language==='ar')await journey.locator('#langBtn').click();
            const report=await journey.request.post(base+'/pdf',{data:{...await journey.evaluate(()=>currentPlan),_lang:language}});
            assert.equal(report.status(),200);
            assert.ok((await report.body()).subarray(0,4).equals(Buffer.from('%PDF')));
          }
        }
      }finally{await context.close();}
    }
    const arabicContext=await browser.newContext();const arabicPage=await arabicContext.newPage();
    try{
      await arabicPage.goto(base,{waitUntil:'networkidle'});
      await arabicPage.locator('#langBtn').click();
      await arabicPage.locator('#idea').fill('وجبات صحية للموظفين');
      await arabicPage.evaluate(()=>{document.getElementById('category').selectedIndex=T.en.categories.indexOf('Food & Catering')+1;});
      await arabicPage.locator('#region').selectOption('Dubai');
      await arabicPage.locator('#budget').fill('4000');
      const arabicGenerate=arabicPage.waitForResponse(response=>response.url().endsWith('/generate'));
      await arabicPage.locator('#genBtn').click();
      const arabicResponse=await arabicGenerate;
      assert.equal(arabicResponse.status(),200,await arabicResponse.text());
      await arabicPage.waitForFunction(()=>currentPlan&&document.getElementById('results').style.display==='block');
      assert.equal(await arabicPage.evaluate(()=>currentPlan._content_lang),'ar');
      for(const selector of ['#overview-body','#score-bars','#day-grid','#questions-list','#persona-grid','#risk-list','#pitch-list']){
        assert.ok(/[\u0600-\u06ff]/.test(await arabicPage.locator(selector).innerText()),selector);
      }
      await arabicPage.evaluate(()=>selectPanel(1));
      await arabicPage.locator('.p-int').first().selectOption('yes');
      await arabicPage.reload({waitUntil:'networkidle'});
      assert.equal(await arabicPage.evaluate(()=>currentPlan.state.idea),'وجبات صحية للموظفين');
      assert.equal(await arabicPage.evaluate(()=>currentPlan.state.evidence.responses),1);
      assert.equal(await arabicPage.locator('html').getAttribute('lang'),'ar');
    }finally{await arabicContext.close();}
    const proofContext=await browser.newContext();const proofPage=await proofContext.newPage();
    try{
      await proofPage.goto(base,{waitUntil:'networkidle'});
      await proofPage.locator('#idea').fill('Neighbourhood service concept');
      await proofPage.evaluate(()=>{document.getElementById('category').selectedIndex=T.en.categories.indexOf('Services & Maintenance')+1;});
      await proofPage.locator('#genBtn').click();
      await proofPage.waitForFunction(()=>currentPlan&&document.getElementById('results').style.display==='block');
      await proofPage.evaluate(()=>selectPanel(1));
      for(let i=0;i<10;i++){
        await proofPage.locator('.p-int').nth(i).selectOption(i<4?'yes':i<7?'maybe':'no');
        if(i<5)await proofPage.locator('.p-pre').nth(i).selectOption(['interest','intent','reservation','payment','repeat'][i]);
      }
      for(const [i,value] of [[0,'10'],[1,'20'],[2,'30'],[3,'-100'],[5,'40']])await proofPage.locator('.p-price').nth(i).fill(value);
      const proofState=await proofPage.evaluate(()=>currentPlan.proof_summary);
      assert.equal(proofState.total_responses,10);
      assert.equal(proofState.interested,4);
      assert.equal(proofState.maybe,3);
      assert.equal(proofState.no,3);
      assert.equal(proofState.stated_intent,1);
      assert.equal(proofState.no_payment_reservations,1);
      assert.equal(proofState.actual_payments,1);
      assert.equal(proofState.repeat_customers,1);
      assert.equal(proofState.avg_price,25);
      assert.equal(await proofPage.evaluate(()=>currentPlan.opportunity_score.clear_customer.score),5);
      await proofPage.reload({waitUntil:'networkidle'});
      assert.equal(await proofPage.evaluate(()=>currentPlan.proof_summary.total_responses),10);
      assert.equal(await proofPage.evaluate(()=>currentPlan.proof_summary.avg_price),25);
      await proofPage.locator('#proofClearBtn').click();
      await proofPage.reload({waitUntil:'networkidle'});
      assert.equal(await proofPage.evaluate(()=>currentPlan.state.evidence.responses),0);
      assert.equal(await proofPage.locator('.p-int').first().inputValue(),'');
    }finally{await proofContext.close();}
    assert.deepEqual(errors, []);
    console.log('PASS: syntax, discovery, bilingual cache, four business journeys, seven Copy buttons in both languages, CSV safety, ten-row Proof Mode and Clear/reload, session isolation, budget gap, scores, segments, Advisor, malformed fallback, safe rendering, English/Arabic PDFs, EN/AR 390px.');
    console.log('Screenshots: '+output);
  } catch (error) {
    console.error(error);
    if (page) {
      if(await page.locator('#error').count())console.error('Visible status:', await page.locator('#error').textContent());
      await page.screenshot({path: path.join(output, 'failure.png')}).catch(()=>{});
      console.error('Failure screenshot:', output);
    }
    throw error;
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
}
main().catch(error => {console.error(error);process.exitCode=1;});

