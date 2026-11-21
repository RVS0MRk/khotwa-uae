// Focused entry flow; no model request is made merely by opening a form.
const CATEGORY_WORDS = [
  ["Food & Catering", /food|lunch|meal|cater|restaurant|bakery|coffee/i],
  ["Agriculture & Farming", /farm|agricultur|crop|hydroponic/i],
  ["Education & Tutoring", /tutor|course|coding|class|teach|education/i],
  ["Technology & Digital", /\bapp\b|website|\bAI\b|software|digital|no.code/i],
  ["Health & Wellness", /health|wellness|fitness|yoga/i],
  ["Handicrafts & Arts", /craft|art\b|paint|jewel|handmade/i],
  ["Tourism & Hospitality", /tour|travel|hotel|hospitality/i],
  ["Retail & Trading", /\b(?:retail|shop|store|trading)\b/i],
  ["Services & Maintenance", /wash|clean|repair|maintenance|delivery/i],
];
function arabicCategoryPattern(words) {
  // Unicode boundaries avoid matching فن inside فندق or صحة inside an unrelated
  // word. Common article/conjunction prefixes still match natural Arabic.
  return new RegExp(
    `(?:^|[^\\p{L}\\p{N}])(?:وال|بال|لل|ال|و|ل|ب)?(?:${words})(?=$|[^\\p{L}\\p{N}])`,
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
  // Prefer the earliest explicit primary activity over a product/topic word.
  // A workshop is education only in a learning context, not a repair shop.
  const intents = [
    ["Education & Tutoring", /\b(?:teach\w*|tutor\w*|classes?|courses?|training)\b|\bworkshops?\b(?=.{0,65}\b(?:children|kids|students|robotics|coding|learning)\b)/iu, arabicCategoryPattern("تعليم|تدريس|دروس|دورات|(?:ورش|ورشة)(?=.{0,65}(?:روبوت|اطفال|طلاب|تعليم))")],
    ["Retail & Trading", /\b(?:sell\w*|retail|trading|shops?|stores?)\b/iu, arabicCategoryPattern("بيع|متجر|متاجر|تجارة")],
    ["Technology & Digital", /\b(?:develop\w*|build\w*)\b(?=.{0,50}\b(?:software|apps?|platform)\b)|\bsoftware\b/iu, arabicCategoryPattern("(?:تطوير|برمجة)(?=.{0,50}(?:برمجيات|تطبيق|نظام|روبوت))")],
  ].flatMap(([category, english, arabic]) => [english, arabic].map(pattern => ({ category, index: normalized.search(pattern) }))).filter(x => x.index >= 0).sort((a,b) => a.index-b.index);
  if (intents.length) {
    const first = intents[0].category;
    // A generic selling verb does not change the underlying food/service
    // activity. Explicit education/development intent retains its precedence.
    if (first === "Retail & Trading") {
      const food = CATEGORY_WORDS[0][1].test(normalized) || ARABIC_CATEGORY_WORDS[0][1].test(normalized);
      const service = /\b(?:wash(?:ing)?|clean(?:ing)?|repair(?:ing)?|maintenance)\b(?!\s+(?:kits?|parts?|equipment)\b)/i.test(normalized) || arabicCategoryPattern("غسيل|غسل|تنظيف|صيانة|اصلاح").test(normalized);
      if (food) return "Food & Catering";
      if (service) return "Services & Maintenance";
    }
    return first;
  }
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
