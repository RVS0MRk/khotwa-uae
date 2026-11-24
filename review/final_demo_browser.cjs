/* Actual offline-rehearsal routes and screenshots, never intercepted model data.
   Run with PYTHON_EXE pointing at an environment with requirements-dev installed. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require('playwright');
const {settledVisuals} = require('../tests/browser_stability.cjs');
const ROOT = path.resolve(__dirname, '..');
const OUT = path.resolve(process.env.KHOTWA_DEMO_EVIDENCE || 'outputs/final-release-20261124/presentation');
const BASE = 'http://127.0.0.1:5012';
const captions = [], checks = [], audits = [], errors = [], network = [];
const scenarios = {
  en:{idea:'Satr: bilingual digital menu layouts for small cafes near Abu Dhabi University',skills:'Arabic and English writing, basic graphic design',interests:'Helping independent cafes communicate clearly',experience:'Student design projects; no customer interviews yet',time:'Six hours per week'},
  ar:{idea:'سطر: تصميم قوائم طعام رقمية بالعربية والإنجليزية للمقاهي الصغيرة قرب جامعة أبوظبي',skills:'الكتابة بالعربية والإنجليزية والتصميم الأساسي',interests:'مساعدة المقاهي المستقلة على التواصل بوضوح',experience:'مشروعات تصميم دراسية؛ لا توجد مقابلات عملاء بعد',time:'ست ساعات أسبوعيا'}
};
const finance = {equipment:'1200',initial_software:'250',initial_marketing:'350',other_startup:'450',licensing:'300',working_capital:'1500',contingency:'250',contingency_mode:'aed',available_capital:'6000',price:'85',units:'80',variable_cost:'32',fixed_cost:'2100',cogs_per_unit:'20',cash_collections:'6800',cash_operating_outflow:'4660'};

async function capture(page, file, caption) {
  await settledVisuals(page);
  await page.screenshot({path:path.join(OUT, file+'.png'),fullPage:false,animations:'disabled'});
  captions.push({file:file+'.png',caption,mode:'Fictional, curated simulation; actual final UI, no live AI or customer research',viewport:page.viewportSize(),device_scale_factor:2});
}
async function audit(page, state) {
  await settledVisuals(page);
  assert.equal(await page.evaluate(()=>typeof axe), 'object', 'axe is browser instrumentation, loaded before document CSP');
  const violations = await page.evaluate(async()=> (await axe.run(document)).violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)})));
  const overflow = await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
  audits.push({state,violations,overflow});
  assert.deepEqual(violations,[],state);
  assert.equal(overflow,false,state+' horizontal overflow');
}
async function openActions(page) {
  const menu = page.locator('.dashboard-actions');
  if (!(await menu.evaluate(e=>e.open))) await menu.locator('summary').click();
}
async function exportFounder(page, name) {
  await page.locator('#result-tab-0').click();await openActions(page);
  const pending=page.waitForEvent('download');await page.locator('#pdfBtn').click();
  await(await pending).saveAs(path.join(OUT,name+'.pdf'));
}
async function language(page, lang) {
  if(await page.evaluate(()=>window.document.documentElement.lang)!==lang)await page.locator('#langBtn').click();
}
async function main() {
  fs.mkdirSync(OUT,{recursive:true});
  const server=spawn(process.env.PYTHON_EXE||'python',['-X','utf8','demo_server.py','--port','5012'],{cwd:ROOT,env:{...process.env,GROQ_API_KEY:'',PYTHONUTF8:'1'},windowsHide:true,stdio:['ignore',fs.openSync(path.join(OUT,'demo-server.log'),'w'),fs.openSync(path.join(OUT,'demo-errors.log'),'w')]});
  let browser;
  try {
    let ready=false;
    for(let i=0;i<80;i++) {try {const r=await fetch(BASE+'/demo-status');if(r.ok){assert.equal((await r.json()).live_ai,false);ready=true;break;}}catch{} await new Promise(r=>setTimeout(r,250));}
    assert.ok(ready,'Demo server readiness');
    browser=await chromium.launch({headless:true});
    for(const locale of ['en','ar']) {
      const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:2,reducedMotion:'reduce',acceptDownloads:true});
      await context.addInitScript({path:require.resolve('axe-core/axe.min.js')});
      const page=await context.newPage();
      page.on('pageerror',e=>errors.push(String(e)));
      page.on('request',r=>{if(!r.url().startsWith(BASE)&&!r.url().startsWith('data:'))network.push(r.url());});
      page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
      await page.goto(BASE,{waitUntil:'networkidle'});await language(page,locale);
      assert.equal(await page.locator('.demo-banner').count(),1);
      await capture(page,locale+'-01-landing','Landing page: both founder pathways, bilingual controls and explicit rehearsal banner.');
      await audit(page,locale+' landing light');
      await page.locator('#need-idea').click();
      for(const [id,key] of [['d-skills','skills'],['d-interests','interests'],['d-experience','experience'],['d-time','time']])await page.locator('#'+id).fill(scenarios[locale][key]);
      await page.locator('#d-budget').fill('6000');await page.locator('#d-region').selectOption('Abu Dhabi');await page.locator('#d-context').selectOption('B2B');
      await capture(page,locale+'-02-profile','Fictional founder profile: bilingual design skills, six hours per week, Abu Dhabi, B2B, AED 6,000 illustrative budget.');
      await page.locator('#discover-btn').click();await page.waitForFunction(()=>document.querySelectorAll('#discovery-results button').length===3);
      await page.locator('#discovery-results').scrollIntoViewIfNeeded();
      await capture(page,locale+'-03-comparison','Three curated ideas displayed side by side for comparison. These are simulated suggestions, not live AI or validated opportunities.');
      const names=await page.locator('#discovery-results h3').allTextContents();
      assert.ok(names.join(' ').includes(locale==='ar'?'سطر':'Satr'));
      await page.locator('#discovery-results button').first().click();
      await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);
      assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.total),17);
      assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.assessed_count),5);
      await page.locator('#result-tab-0').click();await page.evaluate(()=>scrollTo(0,0));
      await capture(page,locale+'-04-dashboard','Generated rehearsal dashboard: five provisional dimensions, 17/25 and zero customer observations; no inference of market validation.');
      await audit(page,locale+' dashboard light');
      await page.locator('#first-step-text').scrollIntoViewIfNeeded();
      await capture(page,locale+'-05-first-action','Personalized fictional first action: sketch a bilingual menu and interview five nearby cafe owners before selling.');
      for(let i=0;i<8;i++){await page.locator('#result-tab-'+i).click();assert.ok(await page.locator('#panel-'+i).isVisible());}
      checks.push({locale,check:'Discovery pathway, comparison, eight dashboard tabs and five assessed dimensions',pass:true});
      await page.locator('#result-tab-7').click();await page.locator('#investment-tab-0').click();
      await page.evaluate(async values=>{Object.assign(investment.inputs,values);initInvestment();await calculateFinance();},finance);
      await page.waitForFunction(()=>financeResult?.base.operating_profit==='2140.00'&&financeResult?.base.startup_capital==='4300.00');
      const financial=await page.evaluate(()=>financeResult.base);
      assert.equal(financial.break_even_units,40);assert.equal(financial.funding_gap,'-1700.00');
      assert.equal(financial.payback_months,'1.19');assert.equal(financial.runway_months,null);
      await page.locator('#investment-guide').scrollIntoViewIfNeeded();
      await capture(page,locale+'-06-investment','Investment Guide with explicit illustrative assumptions: AED 6,800 revenue, AED 2,140 operating profit, AED 4,300 startup capital, break-even 40 units. Not sales or quotations.');
      await audit(page,locale+' investment light');
      for(let i=0;i<7;i++){await page.locator('#investment-tab-'+i).click();assert.ok(await page.locator('#investment-panel-'+i).isVisible());}
      await page.locator('#investment-tab-6').click();
      let pending=page.waitForEvent('download');await page.locator('#investment-pdf').click();await(await pending).saveAs(path.join(OUT,locale+'-investment-demo.pdf'));
      pending=page.waitForEvent('download');await page.locator('#investment-csv').click();await(await pending).saveAs(path.join(OUT,locale+'-finance-demo.csv'));
      await page.locator('#result-tab-1').click();
      while(await page.locator('#proof-add').isVisible())await page.locator('#proof-add').click();
      for(let i=0;i<5;i++){
        await page.locator('.p-int').nth(i).selectOption('yes');
        await page.locator('.p-pre').nth(i).selectOption('interest');
        await page.locator('.p-note').nth(i).fill(locale==='ar'?'محاكاة تدريب فقط؛ ليست مقابلة حقيقية.':'SIMULATED rehearsal only; not a genuine interview.');
      }
      await page.waitForFunction(()=>currentPlan.proof_summary.total_responses===5);
      const observed=await page.evaluate(()=>({proof:currentPlan.proof_summary,score:currentPlan.opportunity_score}));
      checks.push({locale,check:'Five explicitly simulated self-reported observations',observed,pass:true});
      await page.locator('#proof-table').scrollIntoViewIfNeeded();
      await capture(page,locale+'-07-proof','Five fictional rehearsal responses. The interface distinguishes self-reported observations from independently verified evidence.');
      await audit(page,locale+' proof light');
      await page.reload({waitUntil:'networkidle'});
      assert.equal(await page.evaluate(()=>currentPlan.proof_summary.total_responses),5);
      // Existing privacy contract deliberately excludes free-text customer
      // notes from session recovery; only safe observation controls recover.
      assert.equal(await page.locator('.p-note').first().inputValue(),'');
      const savedScore=await page.evaluate(()=>currentPlan.opportunity_score.total);
      await page.locator('#langBtn').click();await page.locator('#langBtn').click();
      assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.total),savedScore);
      assert.equal(await page.evaluate(()=>investment.inputs.price),'85');
      await exportFounder(page,locale+'-founder-demo');
      await page.locator('#chatLauncher').click();await page.locator('#chat-input').fill(locale==='ar'?'ما سؤال المقابلة التالي؟':'What interview question should I ask next?');
      await page.locator('#sendBtn').click();await page.waitForFunction(()=>document.querySelector('.advisor-card'));
      assert.ok((await page.locator('.advisor-card').last().innerText()).includes(locale==='ar'?'محاكى':'Simulated'));
      await capture(page,locale+'-08-advisor','Structured, visibly simulated Advisor reply; provider access is blocked in this rehearsal.');
      await audit(page,locale+' advisor light');
      await page.locator('#chatClose').click();
      await page.locator('#themeBtn').click();await page.locator('#result-tab-0').click();await page.evaluate(()=>scrollTo(0,0));
      await capture(page,locale+'-09-dark','Actual final dashboard in dark mode, using the same fictional scenario.');
      await audit(page,locale+' dashboard dark');
      await page.setViewportSize({width:390,height:844});
      await capture(page,locale+'-10-mobile','390px responsive mobile emulation at 2x pixel density; no real-phone verification is claimed.');
      await audit(page,locale+' mobile dark');
      await page.locator('#themeBtn').click();await audit(page,locale+' mobile light');
      await page.locator('#result-tab-1').click();await page.locator('#proofClearBtn').click();
      await page.reload({waitUntil:'networkidle'});
      assert.equal(await page.evaluate(()=>currentPlan.proof_summary.total_responses),0);
      assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.total),17);
      checks.push({locale,check:'Finance exact outputs, exports, EN/AR round trip, refresh, Clear restores 17/25',financial,pass:true});
      await page.setViewportSize({width:1440,height:1000});
      await page.locator('#result-tab-0').click();await openActions(page);await page.locator('#newBtn').click();
      assert.equal(await page.evaluate(()=>currentPlan),null);
      await page.locator('#have-idea').click();await page.locator('#idea').fill(scenarios[locale].idea);
      await page.locator('#category').selectOption('Technology & Digital');await page.locator('#region').selectOption('Abu Dhabi');await page.locator('#context').selectOption('B2B');await page.locator('#user_type').selectOption('small_businesses');
      await page.evaluate(()=>{document.getElementById('budget').value='6000';updateBudget('6000');});
      await page.locator('#genBtn').click();await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);
      assert.ok((await page.evaluate(()=>currentPlan.state.idea)).includes(locale==='ar'?'سطر':'Satr'));
      checks.push({locale,check:'Existing-idea pathway and intentional New Idea reset',pass:true});
      await context.close();
    }
    assert.deepEqual(errors,[],'Browser errors');assert.deepEqual(network,[],'Offline application must not fetch external resources');
    console.log('PASS: actual simulated server; EN/AR both pathways, eight tabs, finance, Proof refresh/Clear, languages, themes, mobile, Advisor, watermarked exports, no external network');
  } finally {
    fs.writeFileSync(path.join(OUT,'captions.json'),JSON.stringify(captions,null,2));
    fs.writeFileSync(path.join(OUT,'demo-browser-results.json'),JSON.stringify({checks,audits,errors,external_requests:network,live_groq:false},null,2));
    if(browser)await browser.close();server.kill();
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
