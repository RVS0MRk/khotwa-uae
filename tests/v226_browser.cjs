/* Actual UI regressions; server fixtures mock I/O, not the production gates. */
const assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
async function verifyV226(browser,base,root){
 const folder=path.join(root,'v226');fs.mkdirSync(folder,{recursive:true});const records=[];
 async function fresh(fixture,locale='en'){
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce',acceptDownloads:true,extraHTTPHeaders:{'X-Khotwa-Test-Fixture':fixture}}),page=await context.newPage();
  page.setDefaultTimeout(20000);await page.goto(base,{waitUntil:'networkidle'});if(locale==='ar')await page.locator('#langBtn').click();await page.locator('#have-idea').click();return{context,page};
 }
 async function generate(page,locale){await page.locator('#idea').fill(locale==='ar'?'خدمة وجبات مكتبية مقترحة في أبوظبي':'Proposed office lunch boxes in Abu Dhabi');await page.locator('#genBtn').click();await page.waitForFunction(()=>currentPlan&&!document.getElementById('genBtn').disabled);}
 {
  const{context,page}=await fresh('v226-rich');
  for(const[text,expected]of [['مطعم طبيعي للوجبات الصحية','Food & Catering'],['خدمة تنظيف منازل في الربيع','Services & Maintenance'],['Home bakery selling cakes on Instagram','Food & Catering'],['بيع الكيك المنزلي عبر انستغرام','Food & Catering']]){
   await page.locator('#idea').fill(text);assert.equal(await page.locator('#category').inputValue(),expected,text);
  }
  records.push({group:'four category regressions through actual onboarding inputs',pass:true});await context.close();
 }
 for(const locale of ['en','ar']){
  const{context,page}=await fresh('v226-rich',locale);await generate(page,locale);
  const plan=await page.evaluate(()=>currentPlan);
  assert.equal(plan.opportunity_score.assessed_count,5);assert.equal(plan.opportunity_score.total,18);
  assert.ok(!plan.idea_overview.problem.includes('Not provided'));assert.ok(!plan.idea_overview.solution.includes('Not provided'));
  if(locale==='en'){
   const raw=JSON.parse(fs.readFileSync(path.resolve('tests/fixtures/v226_rich_lunch.json'),'utf8'));
   assert.equal(plan.first_step_today,raw.first_step_today);assert.equal(plan.summary,raw.summary);
   for(const key of ['local_fit','clear_customer','low_starting_cost','easy_first_step','growth_potential'])assert.equal(plan.opportunity_score[key].reason,raw.opportunity_score[key].reason);
  }
  await page.locator('#result-tab-0').click();await page.evaluate(()=>{document.activeElement?.blur();scrollTo(0,0)});await page.screenshot({path:path.join(folder,'complete-'+locale+'.png'),fullPage:true,animations:'disabled'});
  records.push({group:locale+' complete personalized assessment',score:plan.opportunity_score.total,assessed:5,action:plan.first_step_today,problem:plan.idea_overview.problem,solution:plan.idea_overview.solution,pass:true});await context.close();
 }
 {
  const{context,page}=await fresh('v226-tainted-score');await generate(page,'en');
  assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.local_fit.score),null);assert.equal(await page.evaluate(()=>currentPlan.opportunity_score.assessed_count),4);
  const text=await page.locator('#overview-body').innerText();assert.ok(!text.includes('received the operating permit'));
  await page.screenshot({path:path.join(folder,'rejected-score-reason.png'),fullPage:true,animations:'disabled'});records.push({group:'rejected fabricated reason leaves four assessed, no retained numeric dimension',pass:true});await context.close();
 }
 for(const locale of ['en','ar']){
  const{context,page}=await fresh('v226-claims',locale);await generate(page,locale);const bad=JSON.parse(fs.readFileSync(path.resolve('tests/fixtures/v226_cases.json'),'utf8')).independent_unsafe[locale][27];
  assert.ok(!(await page.evaluate(()=>JSON.stringify(currentPlan))).includes(bad));await page.locator('#result-tab-5').click();assert.ok(!(await page.locator('#pitch-list').innerText()).includes(bad));
  await page.screenshot({path:path.join(folder,'safe-pitch-'+locale+'.png'),fullPage:true,animations:'disabled'});
  await page.locator('#chatLauncher').click();await page.locator('#chat-input').fill(locale==='ar'?'كيف أختبر الفكرة؟':'What should I test next?');await page.locator('#sendBtn').click();await page.waitForFunction(()=>!document.getElementById('sendBtn').disabled);assert.ok(!(await page.locator('#chat-messages').innerText()).includes(bad));
  await page.screenshot({path:path.join(folder,'safe-advisor-'+locale+'.png'),fullPage:true,animations:'disabled'});records.push({group:locale+' time-commitment filtered in dashboard, Pitch and Advisor',pass:true});await context.close();
 }
 fs.writeFileSync(path.join(root,'v226-checks.json'),JSON.stringify(records,null,2));console.log(`PASS V2.2.6: ${records.length} new groups; complete 18/25 EN/AR, intact instructions, score taint, category and guarantee safety`);return records.length;
}
module.exports={verifyV226};
