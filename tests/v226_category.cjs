/* Pure production category function; no alternate detector or modified assertions. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const filename=path.resolve(__dirname,'../static/onboarding.js');
const sandbox={module:{exports:{}}};
vm.runInNewContext(fs.readFileSync(filename,'utf8')+'\nmodule.exports=detectBusinessCategory;',sandbox,{filename});
const detect=sandbox.module.exports;
const cases=[
 ['مطعم طبيعي للوجبات الصحية','Food & Catering'],
 ['خدمة تنظيف منازل في الربيع','Services & Maintenance'],
 ['Home bakery selling cakes on Instagram','Food & Catering'],
 ['بيع الكيك المنزلي عبر انستغرام','Food & Catering'],
 ['Robotics workshops for children in Sharjah.','Education & Tutoring'],
 ['ورش روبوتات للأطفال في الشارقة.','Education & Tutoring'],
 ['Selling robotics kits online','Retail & Trading'],
 ['بيع مجموعات روبوتات عبر الإنترنت','Retail & Trading'],
 ['Developing robotics software','Technology & Digital'],
 ['تطوير برمجيات للروبوتات','Technology & Digital'],
 ['Car repair workshop','Services & Maintenance'],
 ['Robotics','Other'],
 ['Teaching children robotics with kits sold separately','Education & Tutoring'],
 ['بيع خدمة غسيل سيارات','Services & Maintenance'],
 ['Selling repair parts','Retail & Trading'],
 ['خدمة صيانة في الربيع','Services & Maintenance'],
 ['جولات سياحية في دبي','Tourism & Hospitality'],
 ['موقع رقمي لتعليم البرمجة','Education & Tutoring'],
];
for(const[text,expected]of cases)assert.equal(detect(text),expected,text);
console.log(`PASS V2.2.6 categories: ${cases.length} cases, including the four reported regressions`);
