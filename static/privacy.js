// Disclose both provider processing and browser recovery without claiming that
// closing a restored browser session reliably erases every browser copy.
function setupPrivacy() {
  const demo = document.body.dataset.demo === "true";
  const en = demo ?
    "Academic demonstration: responses are fixed, simulated Satr data. Nothing is sent to Groq in this mode. Recovery stays in this tab’s session storage; use New idea to clear it. Avoid personal information." :
    "Your idea and answers are sent to Groq to generate guidance. Don’t enter personal or confidential information. Recovery is kept in this tab’s session storage; use New idea to clear it. Closing the tab normally clears it, but browsers can restore sessions.";
  const ar = demo ?
    "عرض أكاديمي: الإجابات ثابتة ومحاكاة لسطر ولا تُرسل بيانات إلى Groq في هذا الوضع. تُحفظ الاستعادة في جلسة علامة التبويب؛ استخدم فكرة جديدة لمسحها. تجنب المعلومات الشخصية." :
    "تُرسل فكرتك وإجاباتك إلى Groq لإعداد الإرشاد. لا تدخل معلومات شخصية أو سرية. تُحفظ الاستعادة في جلسة علامة التبويب؛ استخدم فكرة جديدة لمسحها. الإغلاق يمسحها عادةً لكن المتصفح قد يستعيد الجلسة.";
  for (const id of ["genBtn", "discover-btn", "chat-foot"]) {
    const notice = uiNode("p", "privacy-notice");
    notice.dataset.en = en;
    notice.dataset.ar = ar;
    notice.id = id + "-privacy";
    document.getElementById(id).after(notice);
  }
  const dialog = uiNode("dialog", "privacy-dialog");
  dialog.id = "privacy-dialog";
  dialog.setAttribute("aria-labelledby", "privacy-title");
  const title = uiNode("h2");
  title.id = "privacy-title";
  title.dataset.en = "Privacy & data";
  title.dataset.ar = "الخصوصية والبيانات";
  const text = uiNode("p");
  text.dataset.en = en;
  text.dataset.ar = ar;
  const details = uiNode("p");
  details.dataset.en =
    "No accounts are required. Plans and PDFs are processed in memory on our server and are not saved there. PDFs are created on request and returned to your browser. Ideas, profile answers, plan context and Advisor questions/history are processed by Groq. An anonymous session cookie authenticates Advisor replies. The server keeps temporary request counters and access/error logs, but does not log request bodies. Groq has its own data handling policies. WhatsApp sharing sends the chosen message to WhatsApp when you open it. Avoid sensitive information in ideas, notes and questions.";
  details.dataset.ar =
    "لا يلزم حساب. تُعالج الخطط والتقارير في ذاكرة الخادم ولا تُحفظ عليه. تُنشأ التقارير عند طلبها وتُعاد إلى المتصفح. يعالج Groq الفكرة وإجابات الملف وسياق الخطة وأسئلة المستشار وسجلها. يُستخدم ملف ارتباط جلسة مجهول للتحقق من ردود المستشار. يحتفظ الخادم بعدادات طلبات مؤقتة وسجلات وصول وأخطاء دون تسجيل محتوى الطلبات. لدى Groq سياسة بيانات مستقلة. ترسل مشاركة WhatsApp الرسالة المختارة إلى WhatsApp عند فتحها. تجنب المعلومات الحساسة في الأفكار والملاحظات والأسئلة.";
  if (demo) {
    details.dataset.en = "This separate local rehearsal uses fictional Satr data and blocks provider requests. Plans and PDFs are processed in local server memory; exports are visibly labeled. Browser session recovery, anonymous reply cookies and temporary request counters still work. Do not enter genuine customer details. WhatsApp links leave this local application if opened.";
    details.dataset.ar = "يستخدم هذا التدريب المحلي المنفصل بيانات سطر الخيالية ويحجب طلبات المزود. تُعالج الخطط والتقارير في ذاكرة الخادم المحلي وتُوسم التقارير بوضوح. تعمل استعادة الجلسة وملفات ارتباط الردود المجهولة وعدادات الطلبات المؤقتة. لا تدخل تفاصيل عملاء حقيقيين. تفتح روابط WhatsApp خارج التطبيق المحلي.";
  }
  if (document.body.dataset.publicDemo === "true") {
    details.dataset.en = "This public academic mode returns fixed fictional Satr examples. It does not send your inputs to Groq. Private live access is separate. Proof entries are self-reported and are not independently authenticated. Plans and PDFs are processed in server memory; safe recovery stays in this tab. Do not enter confidential customer details. WhatsApp links leave this website.";
    details.dataset.ar = "يعرض هذا الوضع الأكاديمي العام أمثلة سطر الخيالية الثابتة ولا يرسل مدخلاتك إلى Groq. الوصول الحي الخاص منفصل. ملاحظات الإثبات ذاتية الإبلاغ ولا تُتحقق منها جهة مستقلة. تُعالج الخطط والتقارير في ذاكرة الخادم وتُحفظ الاستعادة الآمنة في علامة التبويب. لا تدخل تفاصيل سرية للعملاء. تفتح روابط WhatsApp خارج الموقع.";
  }
  const close = uiNode("button", "btn btn-light");
  close.type = "button";
  close.dataset.en = "Close";
  close.dataset.ar = "إغلاق";
  close.onclick = () => dialog.close();
  dialog.append(title, text, details, close);
  document.body.append(dialog);
  const button = uiNode("button", "text-button");
  button.id = "privacy-open";
  button.type = "button";
  button.dataset.en = "Privacy & data";
  button.dataset.ar = "الخصوصية والبيانات";
  button.onclick = () => dialog.showModal();
  document.querySelector(".footer-links").append(button);
}
