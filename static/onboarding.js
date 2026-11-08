// Focused entry flow; no model request is made merely by opening a form.
const CATEGORY_WORDS = [
  [
    "Food & Catering",
    /food|lunch|meal|cater|restaurant|bakery|coffee|طعام|مطعم|وجبة|وجبات|مخبز|قهوة/i,
  ],
  [
    "Agriculture & Farming",
    /farm|agricultur|crop|hydroponic|زراع|مزرع|محاصيل/i,
  ],
  [
    "Education & Tutoring",
    /tutor|course|coding|class|teach|education|تعليم|دروس|تدريس|دورة|برمجة للطلاب/i,
  ],
  [
    "Technology & Digital",
    /\bapp\b|website|\bAI\b|software|digital|no.code|تطبيق|موقع|برمجيات|ذكاء اصطناعي|رقمي/i,
  ],
  ["Health & Wellness", /health|wellness|fitness|yoga|صحة|لياقة|رياضة|يوغا/i],
  [
    "Handicrafts & Arts",
    /craft|art\b|paint|jewel|handmade|حرف|(?:^|\s)فن(?:\s|$)|رسم|مجوهر|يدوي/i,
  ],
  [
    "Tourism & Hospitality",
    /tour|travel|hotel|hospitality|سياحة|سفر|فندق|ضيافة/i,
  ],
  ["Retail & Trading", /retail|shop|store|trading|بيع|تجارة|متجر/i],
  [
    "Services & Maintenance",
    /wash|clean|repair|maintenance|delivery|غسيل|تنظيف|صيانة|إصلاح|توصيل/i,
  ],
];
function suggestCategory() {
  const c = document.getElementById("category");
  if (c.dataset.touched === "true") return;
  const idea = document.getElementById("idea").value;
  const key =
    CATEGORY_WORDS.find(([, pattern]) => pattern.test(idea))?.[0] || "Other";
  c.selectedIndex = T.en.categories.indexOf(key) + 1;
  setTxt(
    "category-hint",
    uiText(
      "Suggested from your idea — you can change it.",
      "اقتراح من فكرتك — يمكنك تغييره.",
    ),
  );
}
function focusedEntry(mode) {
  document.body.classList.toggle("focused-entry", !!mode && !currentPlan);
  const back = document.getElementById("entry-back");
  if (back) back.hidden = !mode || !!currentPlan;
}
function setupOnboarding() {
  const back = uiNode("button", "text-button", uiText("← Back", "رجوع →"));
  back.id = "entry-back";
  back.type = "button";
  back.dataset.en = "← Back";
  back.dataset.ar = "رجوع →";
  back.hidden = true;
  back.onclick = () => {
    if (history.state?.khotwaEntry) history.back();
    else setEntry(null);
  };
  document.getElementById("main").prepend(back);
  addEventListener("popstate", (e) => {
    setEntry(e.state?.khotwaEntry || null);
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  for (const id of [
    "idea",
    "category",
    "budget",
    "d-skills",
    "d-interests",
    "d-budget",
    "d-experience",
    "d-time",
  ])
    for (const event of ["input", "change"])
      document
        .getElementById(id)
        .addEventListener(event, () =>
          localizedStatus(
            id.startsWith("d-") ? "discover-error" : "error",
            "",
            "",
          ),
        );
  for (const id of ["d-experience", "d-time"]) {
    const input = document.getElementById(id);
    input.dataset.placeholderEn = "None yet is fine";
    input.dataset.placeholderAr = "لا بأس إن لم يوجد بعد";
  }
}
