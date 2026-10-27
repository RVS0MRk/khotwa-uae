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
    await page.locator('#langBtn').click();
    assert.equal(await page.locator('#category-hint').innerText(), 'اختر الفئة؛ تظهر الاقتراحات أثناء الكتابة.');
    assert.equal(await page.locator('#chatLauncher').getAttribute('aria-label'), 'افتح مستشار ستارت سمارت');
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
    assert.equal(englishPdf.status(), 200);fs.writeFileSync(path.join(output,'english.pdf'),await englishPdf.body());
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
    fs.writeFileSync(path.join(output,'arabic.pdf'),await pdf.body());
    await page.locator('#langBtn').click();
    await page.locator('#newBtn').click();
    await page.locator('#idea').fill('malformed <img src=x onerror=alert(1)>');
    await page.locator('#genBtn').click();
    await page.waitForFunction(() => currentPlan && currentPlan._local && document.getElementById('results').style.display==='block');
    assert.equal(await page.locator('#report-table img').count(), 0);
    assert.equal(await page.locator('#overview-body img').count(), 0);
    assert.equal(await page.evaluate(() => currentPlan.state.user_budget_aed), 4000);
    assert.deepEqual(errors, []);
    console.log('PASS: syntax, discovery, state preservation, budget gap, scores, segments, Proof Mode, Advisor, malformed fallback, safe rendering, Arabic PDF, EN/AR 390px.');
    console.log('Screenshots: '+output);
  } catch (error) {
    if (page) {
      console.error('Visible status:', await page.locator('#error').textContent());
      await page.screenshot({path: path.join(output, 'failure.png')});
      console.error('Failure screenshot:', output);
    }
    throw error;
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
}
main().catch(error => {console.error(error);process.exitCode=1;});

