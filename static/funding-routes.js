// General education, not programme eligibility or an offer of financing.
const FINANCING_ROUTES = [
  [
    "Bootstrapping",
    "التمويل الذاتي",
    "Use your own funds or retained earnings. Keeps ownership; growth is limited by available cash and you bear the loss. Useful for a small affordable test.",
    "استخدم أموالك أو الأرباح المحتجزة. تحتفظ بالملكية لكن النمو محدود بالسيولة وتتحمل الخسارة. مناسب لاختبار صغير ميسور.",
  ],
  [
    "Bank financing",
    "التمويل المصرفي",
    "Borrow and repay under agreed terms. Keeps equity but adds repayments, costs and possible security requirements. Consider only with a credible repayment plan; approval is assessed by the lender.",
    "اقترض واسدد وفق الشروط. تحتفظ بالملكية مع التزام بالسداد وتكاليف وضمانات محتملة. يحتاج خطة سداد معقولة وتقييم المقرض.",
  ],
  [
    "Government-backed support",
    "الدعم الحكومي",
    "May be loans, guarantees, procurement access or services. Can improve access; eligibility and application work vary. Match the specific programme to your stage and nationality criteria.",
    "قد يكون قروضاً أو ضمانات أو مشتريات أو خدمات. يحسّن الوصول مع شروط وتقديم مختلفين. طابق البرنامج بمرحلتك وشروط الجنسية.",
  ],
  [
    "Angel investment",
    "الاستثمار الملائكي",
    "An individual invests for an ownership interest under negotiated terms. Can bring experience and capital; reduces your ownership and adds investor expectations. Often considered for an early scalable business.",
    "يستثمر فرد مقابل حصة بشروط متفاوض عليها. يوفر خبرة ورأس مال مع تخفيض ملكيتك وتوقعات المستثمر. يُدرس لمشروع مبكر قابل للتوسع.",
  ],
  [
    "Venture capital",
    "رأس المال الجريء",
    "A fund invests for equity and substantial growth potential. Larger resources and networks; dilution, governance terms and growth pressure. Typically suited to a scalable model rather than every small business.",
    "يستثمر صندوق مقابل ملكية وإمكانات نمو كبيرة. موارد وشبكات مع تخفيف الملكية وشروط حوكمة وضغط نمو. يناسب نموذجاً قابلاً للتوسع وليس كل مشروع صغير.",
  ],
  [
    "Incubators & accelerators",
    "الحاضنات والمسرّعات",
    "Structured mentoring, workspace and introductions; cash is programme-specific. Useful for building skills and networks; time, location, fees or equity terms may apply. Read each programme's terms.",
    "إرشاد منظم ومساحة وتعارف؛ النقد حسب البرنامج. مفيد للمهارات والشبكات مع التزام وقت أو موقع أو رسوم أو ملكية محتملة. اقرأ الشروط.",
  ],
  [
    "Grants",
    "المنح",
    "A non-repayable award only where an actual programme offers one. Preserves equity but can have competitive selection, restricted uses and reporting duties. No grant entitlement or currently open grant is implied here.",
    "مبلغ غير مسترد فقط إذا طرحه برنامج فعلي. يحافظ على الملكية مع منافسة وقيود استخدام وتقارير محتملة. لا يعني استحقاقاً أو منحة مفتوحة حالياً.",
  ],
  [
    "Crowdfunding",
    "التمويل الجماعي",
    "Many contributors support a project under a platform's model. May broaden reach but creates fees, disclosure and repayment or equity obligations. UAE loan-based crowdfunding is regulated by CBUAE outside financial free zones; verify the platform's licence and applicable regulator before use.",
    "يساهم عدة أشخاص وفق نموذج المنصة. يوسّع الوصول مع رسوم وإفصاح والتزامات سداد أو ملكية. ينظم المصرف المركزي التمويل الجماعي بالقروض خارج المناطق الحرة المالية؛ تحقّق من ترخيص المنصة والجهة المختصة قبل الاستخدام.",
  ],
];
function renderFinancingRoutes() {
  let root = document.getElementById("financing-routes");
  if (!root) {
    root = uiNode("section", "financing-routes");
    root.id = "financing-routes";
    document.getElementById("funding-directory").prepend(root);
  }
  root.replaceChildren(
    uiNode("h3", "", uiText("Choose a financing route", "اختر مسار التمويل")),
    uiNode(
      "p",
      "",
      uiText(
        "Compare the trade-offs before choosing a programme. General education; no approval or investment is promised.",
        "قارن الالتزامات قبل اختيار برنامج. معلومات تعليمية دون ضمان تمويل أو استثمار.",
      ),
    ),
  );
  FINANCING_ROUTES.forEach(([en, ar, english, arabic]) => {
    const detail = uiNode("details", "finance-methods");
    detail.append(
      uiNode("summary", "", uiText(en, ar)),
      uiNode("p", "", uiText(english, arabic)),
    );
    root.append(detail);
  });
  const source = uiNode(
    "a",
    "",
    uiText(
      "CBUAE crowdfunding regulation ↗",
      "نظام التمويل الجماعي للمصرف المركزي ↗",
    ),
  );
  source.href = "https://rulebook.centralbank.ae/en/entiresection/1577";
  source.target = "_blank";
  source.rel = "noopener noreferrer";
  root.append(source);
}
