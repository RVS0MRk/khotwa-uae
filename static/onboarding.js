// Focused entry flow; no model request is made merely by opening a form.
const CATEGORY_WORDS = [
  ["Food & Catering", /food|lunch|meal|cater|restaurant|bakery|coffee/i],
  ["Agriculture & Farming", /farm|agricultur|crop|hydroponic/i],
  ["Education & Tutoring", /tutor|course|coding|class|teach|education/i],
  ["Technology & Digital", /\bapp\b|website|\bAI\b|software|digital|no.code/i],
  ["Health & Wellness", /health|wellness|fitness|yoga/i],
  ["Handicrafts & Arts", /craft|art\b|paint|jewel|handmade/i],
  ["Tourism & Hospitality", /tour|travel|hotel|hospitality/i],
  ["Retail & Trading", /retail|shop|store|trading/i],
  ["Services & Maintenance", /wash|clean|repair|maintenance|delivery/i],
];
function arabicCategoryPattern(words) {
  // Unicode boundaries avoid matching فن inside فندق or صحة inside an unrelated
  // word. Common article/conjunction prefixes still match natural Arabic.
  return new RegExp(
    `(?:^|[^\\p{L}\\p{N}])(?:وال|ال|و)?(?:${words})(?=$|[^\\p{L}\\p{N}])`,
    "u",
  );
}
const ARABIC_CATEGORY_WORDS = [
  [
    "Food & Catering",
    "طعام|مطعم|مطاعم|وجبة|وجبات|مخبز|مخابز|قهوة|غداء|عشاء|فطور|افطار|اكل|حلويات|كيك|مطبخ|مطابخ",
  ],
  ["Agriculture & Farming", "زراعة|زراعي|زراعية|مزرعة|مزارع|محاصيل"],
  [
    "Education & Tutoring",
    "تعليم|تعليمي|تعليمية|دروس|تدريس|دورة|دورات|ورش تعليمية|ورش عمل|ورشة عمل|ورش للاطفال|ورشة للاطفال|برمجة للطلاب",
  ],
  [
    "Technology & Digital",
    "تطبيق|تطبيقات|موقع|مواقع|برمجيات|ذكاء اصطناعي|رقمي|رقمية",
  ],
  ["Health & Wellness", "صحة|صحي|صحية|تغذية|لياقة|رياضة|رياضي|رياضية|يوغا"],
  ["Handicrafts & Arts", "حرف|حرفية|فن|فنون|رسم|مجوهرات|يدوي|يدوية"],
  [
    "Tourism & Hospitality",
    "سياحة|سياحي|سياح|سائح|رحلات|سفاري|جولات|سفر|فندق|فنادق|ضيافة",
  ],
  ["Retail & Trading", "بيع|تجارة|متجر|متاجر|ملابس"],
  ["Services & Maintenance", "غسيل|غسل|تنظيف|صيانة|اصلاح|توصيل"],
].map(([category, words]) => [category, arabicCategoryPattern(words)]);
function detectBusinessCategory(idea) {
  const normalized = String(idea)
    .normalize("NFKC")
    .replace(/[\u0610-\u061a\u064b-\u065f\u0670\u0640]/g, "")
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي");
  // Use the same ordered category precedence in either language. Food context
  // wins over a healthy adjective; children alone never implies Education.
  return (
    CATEGORY_WORDS.find(
      ([category, english]) =>
        english.test(idea) ||
        ARABIC_CATEGORY_WORDS.find(([key]) => key === category)[1].test(
          normalized,
        ),
    )?.[0] || "Other"
  );
}
function suggestCategory() {
  const c = document.getElementById("category");
  if (c.dataset.touched === "true") return;
  const idea = document.getElementById("idea").value;
  const key = detectBusinessCategory(idea);
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
