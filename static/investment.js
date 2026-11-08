// Server Decimal results are authoritative. Number is used only for chart widths/formatting.
let investment = {
  key: "",
  inputs: {},
  original: null,
  scenarios: {},
  allocations: Array(6).fill(""),
  stageDone: [],
  readiness: [],
  tasks: [],
};
let financeResult = null,
  financeTimer,
  financeEpoch = 0,
  fundingData = [];
const FINANCE_FIELDS = {
  equipment: [
    "Equipment",
    "المعدات",
    "One-time purchase cost",
    "تكلفة شراء لمرة واحدة",
  ],
  initial_software: [
    "Initial software",
    "البرامج الأولية",
    "One-time setup, not subscriptions",
    "تأسيس لمرة واحدة دون الاشتراكات",
  ],
  initial_marketing: [
    "Launch marketing",
    "تسويق الإطلاق",
    "Initial campaign only",
    "الحملة الأولية فقط",
  ],
  licensing: [
    "Business licensing and registration costs (AED)",
    "تكاليف الترخيص والتسجيل (AED)",
    "Optional. Enter your own quote; exclude this amount from Other costs",
    "اختياري. أدخل عرضك واحذف المبلغ من التكاليف الأخرى",
  ],
  other_startup: [
    "Other one-time costs",
    "تكاليف تأسيس أخرى",
    "Include known setup costs once",
    "أدرج تكاليف التأسيس المعروفة مرة واحدة",
  ],
  available_capital: [
    "Available funds",
    "الأموال المتاحة",
    "Your actual available startup funds",
    "الأموال المتاحة فعلياً للبدء",
  ],
  working_capital: [
    "Working-capital buffer",
    "احتياطي رأس المال العامل",
    "Cash set aside, not an additional expense",
    "سيولة مخصصة وليست مصروفاً إضافياً",
  ],
  contingency: [
    "Contingency reserve",
    "احتياطي الطوارئ",
    "AED or selected % of one-time costs",
    "درهم أو نسبة مختارة من تكاليف التأسيس",
  ],
  price: [
    "Selling price per unit",
    "سعر بيع الوحدة",
    "Define the same unit across price and costs",
    "استخدم الوحدة نفسها للسعر والتكاليف",
  ],
  units: [
    "Monthly sales units",
    "وحدات البيع الشهرية",
    "Whole units; a hypothesis, not demand evidence",
    "وحدات صحيحة؛ فرضية وليست دليلاً على الطلب",
  ],
  variable_cost: [
    "Variable cost / unit",
    "تكلفة متغيرة للوحدة",
    "All costs that vary with one extra unit",
    "كل ما يتغيّر مع بيع وحدة إضافية",
  ],
  fixed_cost: [
    "Monthly fixed expenses",
    "المصروفات الشهرية الثابتة",
    "Rent, salaries, subscriptions; exclude variable costs",
    "إيجار ورواتب واشتراكات دون التكاليف المتغيرة",
  ],
  cogs_per_unit: [
    "COGS per unit (optional)",
    "تكلفة البضاعة للوحدة (اختياري)",
    "Accounting production/purchase cost, separate from all variable costs",
    "تكلفة الإنتاج أو الشراء المحاسبية، وقد تختلف عن كل التكاليف المتغيرة",
  ],
  cash_collections: [
    "Monthly cash collected",
    "النقد المحصّل شهرياً",
    "Actual or assumed cash receipts, not invoiced revenue",
    "المقبوضات الفعلية أو المفترضة، لا الإيراد المفوتر",
  ],
  cash_operating_outflow: [
    "Monthly cash paid out",
    "النقد المدفوع شهرياً",
    "All recurring cash payments; excludes initial spending",
    "كل المدفوعات المتكررة دون الإنفاق الأولي",
  ],
  funding_request: [
    "Funding request (optional)",
    "التمويل المطلوب (اختياري)",
    "Only an amount you choose to request",
    "المبلغ الذي تختار طلبه فقط",
  ],
};
const METRICS = {
  startup_capital: [
    "Startup capital required",
    "رأس المال المطلوب",
    "One-time costs + working capital + contingency",
    "تكاليف التأسيس + رأس المال العامل + الطوارئ",
  ],
  revenue: [
    "Monthly revenue",
    "الإيراد الشهري",
    "Units × price",
    "الوحدات × السعر",
  ],
  operating_profit: [
    "Monthly operating profit / loss",
    "الربح أو الخسارة التشغيلية",
    "Revenue − variable expenses − fixed expenses",
    "الإيراد − المصروفات المتغيرة − الثابتة",
  ],
  funding_gap: [
    "Funding shortfall / surplus",
    "عجز أو فائض التمويل",
    "Required capital − available funds; negative = surplus",
    "رأس المال المطلوب − المتاح؛ السالب فائض",
  ],
  contribution_per_unit: [
    "Contribution per unit",
    "مساهمة الوحدة",
    "Selling price − all variable cost / unit",
    "سعر البيع − كل التكلفة المتغيرة للوحدة",
  ],
  contribution_ratio: [
    "Contribution margin ratio",
    "نسبة هامش المساهمة",
    "Contribution / selling price",
    "مساهمة الوحدة ÷ سعر البيع",
  ],
  gross_profit: [
    "Gross profit",
    "مجمل الربح",
    "Revenue − units × accounting COGS / unit",
    "الإيراد − الوحدات × تكلفة البضاعة المحاسبية",
  ],
  gross_margin: [
    "Gross margin",
    "هامش مجمل الربح",
    "Gross profit / revenue; COGS basis only",
    "مجمل الربح ÷ الإيراد؛ وفق تكلفة البضاعة",
  ],
  one_time_costs: [
    "One-time expenses",
    "مصروفات التأسيس",
    "Equipment + initial software + marketing + other + entered licensing",
    "معدات + برامج أولية + تسويق + أخرى + الترخيص المدخل",
  ],
  contingency_reserve: [
    "Contingency reserve",
    "احتياطي الطوارئ",
    "AED amount or % × one-time expenses",
    "مبلغ بالدرهم أو نسبة × مصروفات التأسيس",
  ],
  variable_expenses: [
    "Monthly variable expenses",
    "المصروفات المتغيرة الشهرية",
    "Units × variable cost / unit",
    "الوحدات × التكلفة المتغيرة للوحدة",
  ],
  fixed_expenses: [
    "Monthly fixed expenses",
    "المصروفات الثابتة الشهرية",
    "User input; excludes variable expenses",
    "إدخال المستخدم دون المصروفات المتغيرة",
  ],
  operating_cash: [
    "Available operating cash",
    "السيولة التشغيلية المتاحة",
    "Available funds − initial expenses − contingency; buffer is not deducted twice",
    "المتاح − مصروفات التأسيس − الطوارئ؛ لا يُخصم رأس المال العامل مرتين",
  ],
  monthly_cash_flow: [
    "Monthly net cash flow",
    "صافي التدفق النقدي الشهري",
    "Cash collected − recurring cash paid out",
    "النقد المحصّل − المدفوعات النقدية المتكررة",
  ],
  break_even_revenue: [
    "Whole-unit break-even revenue",
    "إيراد التعادل بوحدات كاملة",
    "Minimum whole break-even units × price",
    "أقل وحدات كاملة للتعادل × السعر",
  ],
};
const SCENARIOS = {
  conservative: ["Conservative", "متحفّظ"],
  base: ["Base case", "أساسي"],
  optimistic: ["Optimistic", "متفائل"],
};
const READINESS = [
  ["Defined the customer problem", "حدّدت مشكلة العميل"],
  ["Identified target customers", "حدّدت العملاء المستهدفين"],
  ["Recorded customer interviews", "سجّلت مقابلات العملاء"],
  ["Collected behavioral demand evidence", "جمعت أدلة سلوكية على الطلب"],
  ["Defined pricing and its unit", "حدّدت السعر ووحدته"],
  ["Estimated startup expenses", "قدّرت مصروفات التأسيس"],
  ["Estimated recurring expenses", "قدّرت المصروفات المتكررة"],
  ["Identified major risks", "حدّدت المخاطر الرئيسية"],
  ["Designed a small test or pilot", "صمّمت اختباراً أو تجربة صغيرة"],
  ["Checked official setup requirements", "راجعت متطلبات التأسيس الرسمية"],
  ["Prepared a basic pitch", "أعددت عرضاً موجزاً"],
  ["Defined how funding will be used", "حدّدت استخدام التمويل"],
];
const STAGES = [
  [
    "Explore the problem",
    "استكشف المشكلة",
    "Identify one segment and its current alternatives.",
    "حدّد شريحة واحدة وبدائلها الحالية.",
    "A written problem hypothesis and interview plan.",
    "فرضية مكتوبة للمشكلة وخطة مقابلات.",
    "Risk: solving an assumed problem.",
    "الخطر: حل مشكلة مفترضة.",
  ],
  [
    "Validate demand",
    "تحقّق من الطلب",
    "Interview customers and separate stated interest from behavior.",
    "قابل العملاء وميّز الاهتمام المعلن عن السلوك.",
    "Recorded interviews and explicit evidence strength in Proof Mode.",
    "مقابلات مسجّلة وقوة دليل واضحة في وضع الإثبات.",
    "Risk: treating compliments as purchases.",
    "الخطر: اعتبار المجاملات مشتريات.",
  ],
  [
    "Build a minimum offer",
    "ابنِ عرضاً مصغّراً",
    "Define a prototype or smallest non-operational test.",
    "حدّد نموذجاً أولياً أو أصغر اختبار دون تشغيل.",
    "A testable offer with a unit price and cost list.",
    "عرض قابل للاختبار بسعر وحدة وقائمة تكاليف.",
    "Risk: building too much before learning.",
    "الخطر: بناء الكثير قبل التعلّم.",
  ],
  [
    "Run a limited pilot",
    "نفّذ تجربة محدودة",
    "Check official requirements before any commercial activity.",
    "راجع المتطلبات الرسمية قبل أي نشاط تجاري.",
    "Required approvals checked; pilot outcomes and cash recorded.",
    "مراجعة الموافقات المطلوبة وتسجيل النتائج والسيولة.",
    "Risk: operating before required approvals.",
    "الخطر: التشغيل قبل الموافقات المطلوبة.",
  ],
  [
    "Evaluate results",
    "قيّم النتائج",
    "Compare costs, feedback, delivery effort and recorded behavior.",
    "قارن التكاليف والملاحظات وجهد التنفيذ والسلوك المسجّل.",
    "Evidence summary and updated assumptions with remaining gaps.",
    "ملخص أدلة وافتراضات محدّثة وثغرات متبقية.",
    "Risk: confusing forecasts with actual cash.",
    "الخطر: الخلط بين التوقعات والسيولة الفعلية.",
  ],
  [
    "Decide on expansion",
    "قرّر التوسّع",
    "Continue, adjust, pause or scale based on what you learned.",
    "واصل أو عدّل أو توقّف أو توسّع وفق ما تعلّمته.",
    "A documented decision and next budget commitment.",
    "قرار موثّق والتزام الميزانية التالية.",
    "Risk: scaling without repeatable demand.",
    "الخطر: التوسّع دون طلب قابل للتكرار.",
  ],
];
function ft(pair) {
  return pair[lang === "ar" ? 1 : 0];
}
// Shared currency policy: Latin digits, grouped fils and the unambiguous AED code.
function money(value) {
  return value == null
    ? uiText("Not yet provided", "لم يُقدّم بعد")
    : formatAED(value);
}
function metricValue(key, value) {
  if (value == null) return uiText("Unknown", "غير معلوم");
  if (key.includes("ratio") || key === "gross_margin")
    return new Intl.NumberFormat(lang === "ar" ? "ar-AE-u-nu-latn" : "en", {
      style: "percent",
      maximumFractionDigits: 2,
    }).format(Number(value));
  return money(value);
}
function investmentRecovery() {
  return {
    fundingFilters: investment.fundingFilters || null,
    version: 2,
    notes: investment.notes || {},
    risksReviewed: !!investment.risksReviewed,
    key: investment.key,
    section: investment.section || 0,
    inputs: investment.inputs,
    original: investment.original,
    scenarios: investment.scenarios,
    allocations: investment.allocations,
    stageDone: investment.stageDone,
    readiness: investment.readiness,
    tasks: investment.tasks,
  };
}
function restoreInvestment(value) {
  if (
    !value ||
    typeof value !== "object" ||
    value.key !== currentPlan?.state?.idea
  )
    return;
  const fields = Object.keys(FINANCE_FIELDS).concat(
    "contingency_mode",
    "cash_mode",
    "cogs_basis",
  );
  const valid = (obj) =>
    obj &&
    typeof obj === "object" &&
    !Array.isArray(obj) &&
    Object.entries(obj).every(
      ([k, v]) =>
        fields.includes(k) &&
        (["contingency_mode", "cash_mode", "cogs_basis"].includes(k)
          ? {
              contingency_mode: ["aed", "percent"],
              cash_mode: ["entered", "simplified"],
              cogs_basis: ["separate", "subset_of_variable"],
            }[k].includes(v)
          : v === "" ||
            v === null ||
            (typeof v === "string" &&
              v.length < 40 &&
              /^\d+(\.\d+)?$/.test(v))),
    );
  if (!valid(value.inputs) || (value.original && !valid(value.original)))
    return;
  if (
    Object.entries(value.scenarios || {}).some(
      ([k, v]) => !SCENARIOS[k] || !valid(v),
    )
  )
    return;
  value.inputs.cash_mode ||= "entered";
  const notes =
    value.notes && typeof value.notes === "object"
      ? Object.fromEntries(
          Object.entries(value.notes).filter(
            ([k, v]) =>
              ["model", "differentiation", "use_of_funds"].includes(k) &&
              typeof v === "string" &&
              v.length <= 1000,
          ),
        )
      : {};
  investment = {
    ...investment,
    ...value,
    notes,
    risksReviewed: value.risksReviewed === true,
    fundingFilters:
      value.fundingFilters && typeof value.fundingFilters === "object"
        ? {
            emirate: String(value.fundingFilters.emirate || "UAE-wide"),
            founder: ["emirati", "resident"].includes(
              value.fundingFilters.founder,
            )
              ? value.fundingFilters.founder
              : "not_sure",
            stage: ["idea", "early_revenue", "growth"].includes(
              value.fundingFilters.stage,
            )
              ? value.fundingFilters.stage
              : "all",
          }
        : null,
    legacyLicensing: value.version !== 2 && value.inputs.licensing == null,
    section:
      Number.isInteger(value.section) && value.section >= 0 && value.section < 7
        ? value.section
        : 0,
  };
  for (const k of ["allocations", "stageDone", "readiness", "tasks"])
    if (!Array.isArray(investment[k]) || investment[k].length > 20)
      investment[k] = [];
  if (
    !investment.allocations.every(
      (v) => v === "" || v === null || /^\d+(\.\d+)?$/.test(String(v)),
    )
  )
    investment.allocations = Array(6).fill("");
  investment.allocations = Array.from(
    { length: 6 },
    (_, i) => investment.allocations[i] ?? "",
  );
  for (const [key, max] of [
    ["stageDone", 5],
    ["readiness", 11],
    ["tasks", 6],
  ])
    investment[key] = investment[key].filter(
      (v) => Number.isInteger(v) && v >= 0 && v <= max,
    );
}
function resetInvestment() {
  document
    .querySelectorAll("#investor-fields textarea")
    .forEach((n) => (n.value = ""));
  investmentStatuses.export = "";
  investmentStatuses.error = "";
  renderInvestmentStatuses();
  investment = {
    key: "",
    inputs: {},
    original: null,
    scenarios: {},
    allocations: Array(6).fill(""),
    stageDone: [],
    readiness: [],
    tasks: [],
  };
  financeResult = null;
  financeEpoch++;
}
function financePayload() {
  return {
    inputs: { ...investment.inputs },
    scenarios: structuredClone(investment.scenarios),
    allocations: [...investment.allocations],
  };
}
function financeField(key, value, onchange, prefix) {
  const spec = FINANCE_FIELDS[key],
    label = uiNode("label", "finance-field", ft(spec)),
    input = uiNode("input");
  input.type = "number";
  input.min = "0";
  input.max = "1000000000000";
  input.step = key === "units" ? "1" : "0.01";
  input.inputMode = "decimal";
  input.id = (prefix || "fin") + "-" + key;
  input.value = value ?? "";
  label.htmlFor = input.id;
  input.addEventListener("input", () => {
    input.removeAttribute("aria-invalid");
    if (key === "price" && (!prefix || prefix === "fin" || prefix === "quick"))
      investment.aiPricePrefill = false;
    onchange(input.value);
    scheduleFinance();
  });
  label.append(input, uiNode("small", "", spec[lang === "ar" ? 3 : 2]));
  return label;
}
function initInvestment() {
  if (!currentPlan) return;
  if (investment.key !== currentPlan.state.idea) {
    resetInvestment();
    investment.key = currentPlan.state.idea;
    investment.inputs.cash_mode = "simplified";
    if (Number(currentPlan.state.suggested_test_price_aed) > 0) {
      investment.inputs.price = String(
        currentPlan.state.suggested_test_price_aed,
      );
      investment.aiPricePrefill = true;
    }
    investment.inputs.available_capital = String(
      currentPlan.state.user_budget_aed,
    );
  }
  const root = document.getElementById("finance-field-groups"),
    operating = document.getElementById("finance-operating-fields");
  root.replaceChildren();
  operating.replaceChildren();
  const groups = [
    [
      ["Initial spending", "الإنفاق الأولي"],
      [
        "equipment",
        "initial_software",
        "initial_marketing",
        "other_startup",
        "licensing",
      ],
    ],
    [
      ["Capital & reserves", "رأس المال والاحتياطي"],
      [
        "available_capital",
        "working_capital",
        "contingency",
        "funding_request",
      ],
    ],
    [
      ["Monthly unit economics", "اقتصاديات الوحدة الشهرية"],
      ["price", "units", "variable_cost", "fixed_cost", "cogs_per_unit"],
    ],
    [
      ["Cash flow, separately", "التدفق النقدي بشكل مستقل"],
      ["cash_collections", "cash_operating_outflow"],
    ],
  ];
  groups.forEach(([title, keys], i) => {
    const f = uiNode("fieldset"),
      grid = uiNode("div", "finance-fields");
    f.append(uiNode("legend", "", ft(title)));
    keys.forEach((key) =>
      grid.append(
        financeField(
          key,
          investment.inputs[key],
          (v) => (investment.inputs[key] = v),
        ),
      ),
    );
    f.append(grid);
    (i < 2 ? root : operating).append(f);
  });
  document.getElementById("contingency-mode").value =
    investment.inputs.contingency_mode || "aed";
  document.getElementById("cash-mode").value =
    investment.inputs.cash_mode || "entered";
  document.getElementById("cogs-basis").value =
    investment.inputs.cogs_basis || "separate";
  renderInvestmentStatuses();
  renderScenarios();
  renderStages();
  renderReadiness();
  renderInvestorFields();
  renderFinanceStarter();
  moveAdvancedFields();
  renderFunding();
  setTxt(
    "finance-business-context",
    (currentPlan.state.idea || "") +
      " · " +
      (T[lang].regions[currentPlan.state.region] || currentPlan.state.region) +
      " · " +
      (T[lang].contexts[currentPlan.state.context] ||
        currentPlan.state.context),
  );
  showInvestmentSection(investment.section || 0, false, false);
  if (financeResult) renderFinance();
  else {
    clearFinanceResults();
    setTxt(
      "finance-next",
      uiText(
        "Start with the costs you know. Leave the rest blank; incomplete calculations remain unknown.",
        "ابدأ بالتكاليف المعروفة واترك البقية فارغة؛ تبقى الحسابات الناقصة غير معلومة.",
      ),
    );
    document
      .getElementById("finance-metrics")
      .replaceChildren(
        uiNode(
          "div",
          "finance-empty",
          uiText("Your figures will appear here.", "ستظهر أرقامك هنا."),
        ),
      );
  }
}
function scheduleFinance() {
  if (currentPlan) delete currentPlan._financial_inputs;
  financeResult = null;
  clearTimeout(financeTimer);
  financeTimer = setTimeout(calculateFinance, 450);
  saveSession();
}
async function calculateFinance(captureOriginal = false) {
  clearTimeout(financeTimer);
  const epoch = ++financeEpoch;
  investmentStatuses.error = "";
  renderInvestmentStatuses();
  const controller = new AbortController(),
    timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch("/finance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(financePayload()),
        signal: controller.signal,
      }),
      result = await response.json();
    if (epoch !== financeEpoch) return;
    if (!response.ok) {
      const input = document.getElementById("fin-" + result.field);
      input?.setAttribute("aria-invalid", "true");
      throw Error(result.field || "input");
    }
    financeResult = result;
    if (captureOriginal && !investment.original)
      investment.original = structuredClone(investment.inputs);
    currentPlan._financial_inputs = structuredClone(investment.inputs);
    renderFinance();
    saveSession();
  } catch (e) {
    if (epoch !== financeEpoch) return;
    financeResult = null;
    clearFinanceResults();
    if (currentPlan) delete currentPlan._financial_inputs;
    investmentStatuses.error = "invalid";
    renderInvestmentStatuses();
    document
      .getElementById("finance-metrics")
      .replaceChildren(
        uiNode(
          "p",
          "finance-empty",
          uiText(
            "Results unavailable until inputs are corrected.",
            "النتائج غير متاحة حتى تصحيح المدخلات.",
          ),
        ),
      );
    renderFinanceIntegration();
  } finally {
    clearTimeout(timer);
  }
}
function table(target, headers, rows) {
  const wrap = document.getElementById(target);
  wrap.tabIndex = 0;
  wrap.setAttribute("role", "region");
  wrap.setAttribute("aria-label", headers.join(" · "));
  wrap.replaceChildren();
  const t = uiNode("table", "data-table"),
    head = uiNode("thead"),
    r = uiNode("tr");
  headers.forEach((h) => {
    const th = uiNode("th", "", h);
    th.scope = "col";
    r.append(th);
  });
  head.append(r);
  t.append(head);
  const b = uiNode("tbody");
  rows.forEach((row) => {
    const tr = uiNode("tr");
    row.forEach((value) =>
      tr.append(
        uiNode("td", "", String(value ?? uiText("Unknown", "غير معلوم"))),
      ),
    );
    b.append(tr);
  });
  t.append(b);
  wrap.append(t);
}
function breakLabel(result) {
  return result.break_even_status === "unreachable"
    ? uiText(
        "Break-even not reachable under the current assumptions.",
        "لا يمكن الوصول إلى التعادل وفق الافتراضات الحالية.",
      )
    : result.break_even_units == null
      ? uiText("Unknown", "غير معلوم")
      : new Intl.NumberFormat(lang === "ar" ? "ar-AE-u-nu-latn" : "en").format(
          result.break_even_units,
        ) +
        " " +
        uiText("whole units / month", "وحدة كاملة شهرياً");
}
function runwayLabel(result) {
  return result.runway_status === "no_burn"
    ? uiText("No current monthly cash burn", "لا يوجد استنزاف نقدي شهري حالياً")
    : result.runway_status === "underfunded"
      ? uiText(
          "Initial spending is underfunded",
          "الإنفاق الأولي غير ممول بالكامل",
        )
      : result.runway_months == null
        ? uiText(
            "Cash-flow inputs incomplete",
            "مدخلات التدفق النقدي غير مكتملة",
          )
        : Number(result.runway_months).toLocaleString(
            lang === "ar" ? "ar-AE-u-nu-latn" : "en",
          ) +
          " " +
          uiText("months", "شهر");
}
function bars(id, title, entries, format = money) {
  const chart = document.getElementById(id);
  chart.replaceChildren(uiNode("figcaption", "", title));
  const known = entries.filter(([, v]) => v !== null && v !== undefined),
    max = Math.max(0, ...known.map(([, v]) => Math.abs(Number(v))));
  if (!known.length) {
    chart.append(
      uiNode(
        "p",
        "finance-empty",
        uiText(
          "Enter assumptions to build this chart.",
          "أدخل الافتراضات لإظهار الرسم.",
        ),
      ),
    );
    return;
  }
  known.forEach(([label, value]) => {
    const row = uiNode("div", "financial-bar-row"),
      bar = uiNode(
        "span",
        "financial-bar" + (Number(value) < 0 ? " negative" : ""),
      ),
      fill = uiNode("i");
    fill.style.width = max ? (Math.abs(Number(value)) / max) * 100 + "%" : "0%";
    bar.append(fill);
    bar.setAttribute("aria-hidden", "true");
    row.append(uiNode("span", "", label), bar, uiNode("b", "", format(value)));
    chart.append(row);
  });
}
function renderFinance() {
  if (!financeResult) return;
  // Base edits update unopened illustrative editors too. Do not replace a
  // scenario input while the user is typing into it.
  if (!document.activeElement?.closest(".scenario-editor")) renderScenarios();
  const r = financeResult.base,
    metrics = document.getElementById("finance-metrics");
  metrics.replaceChildren();
  const computable = beginnerFinanceResults(r);
  if (computable) {
    for (const key of [
      "startup_capital",
      "revenue",
      "operating_profit",
      "funding_gap",
      "contribution_per_unit",
      "contribution_ratio",
    ]) {
      if (r[key] === null) continue;
      const spec = METRICS[key],
        box = uiNode("article", "finance-metric");
      box.dataset.metric = key;
      box.append(
        uiNode(
          "span",
          "metric-label",
          key === "startup_capital" &&
            r.warnings.includes("licensing_not_provided")
            ? uiText(
                "Known startup subtotal (licensing missing)",
                "مجموع التأسيس المعروف (الترخيص ناقص)",
              )
            : ft(spec),
        ),
        uiNode(
          "strong",
          "",
          key === "funding_gap"
            ? fundingGapLabel(r[key])
            : metricValue(key, r[key]),
        ),
      );
      if (key === "funding_gap")
        box.classList.add(
          Number(r[key]) > 0 ? "finance-warning" : "finance-success",
        );
      metrics.append(box);
    }
    for (const [label, value, formula] of [
      [
        uiText("Break-even", "التعادل"),
        breakLabel(r),
        uiText(
          "Ceiling(fixed costs ÷ contribution / unit). Continuous units: ",
          "تقريب لأعلى (الثابتة ÷ مساهمة الوحدة). الوحدات الرياضية: ",
        ) + (r.break_even_continuous_units ?? "—"),
      ],
      [
        uiText("Cash runway", "المدة النقدية"),
        runwayLabel(r),
        uiText(
          "Operating cash ÷ monthly cash burn. Accounting profit is separate.",
          "السيولة التشغيلية ÷ الاستنزاف النقدي الشهري. الربح المحاسبي منفصل.",
        ),
      ],
    ]) {
      const box = uiNode("article", "finance-metric");
      box.append(
        uiNode("span", "metric-label", label),
        uiNode("strong", "", value),
      );
      metrics.append(box);
    }
  }
  if (computable) {
    renderFinanceBasis(r);
    compactFinanceMethods();
  } else document.getElementById("finance-basis")?.remove();
  document.getElementById("expense-chart").hidden = !computable;
  const evidence = currentPlan.proof_summary?.total_responses || 0;
  setTxt(
    "finance-next",
    evidence
      ? uiText(
          `${evidence} customer entries recorded. Check evidence strength before committing capital.`,
          `${evidence} إدخالات عملاء مسجّلة. راجع قوة الدليل قبل تخصيص رأس المال.`,
        )
      : uiText(
          "No customer entries recorded. Plan a small validation test before committing major capital.",
          "لا توجد إدخالات عملاء مسجّلة. خطّط لاختبار صغير قبل الالتزام برأس مال كبير.",
        ),
  );
  table(
    "finance-breakdown",
    [
      uiText("Calculation", "الحساب"),
      uiText("Result", "النتيجة"),
      uiText("Method", "الطريقة"),
    ],
    Object.entries(METRICS).map(([k, s]) => [
      ft(s),
      metricValue(k, r[k]),
      s[lang === "ar" ? 3 : 2],
    ]),
  );
  bars(
    "expense-chart",
    uiText(
      "Monthly expenses · AED (table below)",
      "المصروفات الشهرية · درهم (الجدول أدناه)",
    ),
    [
      [ft(METRICS.variable_expenses), r.variable_expenses],
      [ft(METRICS.fixed_expenses), r.fixed_expenses],
    ],
  );
  const names = Object.keys(SCENARIOS);
  renderScenarioComparison();
  bars(
    "scenario-chart",
    uiText(
      "Monthly operating profit / loss · AED",
      "الربح أو الخسارة التشغيلية الشهرية · درهم",
    ),
    names.map((k) => [
      ft(SCENARIOS[k]),
      financeResult.scenarios[k].operating_profit,
    ]),
  );
  table(
    "sensitivity-table",
    [
      uiText("Assumption", "الافتراض"),
      uiText("Baseline → comparison", "الأساس ← المقارنة"),
      uiText("Actual change", "التغيير الفعلي"),
      uiText("Profit impact · AED", "أثر الربح · AED"),
    ],
    financeResult.sensitivity.map((s) => [
      ft(FINANCE_FIELDS[s.field]),
      (s.discrete ? formatUnits(s.baseline) : money(s.baseline)) +
        " → " +
        (s.discrete ? formatUnits(s.comparison) : money(s.comparison)),
      s.actual_percent == null
        ? uiText("Not defined from zero", "غير معرّف من الصفر")
        : formatChangePercent(s.actual_percent),
      money(s.profit_impact),
    ]),
  );
  let explanation = document.getElementById("sensitivity-explanation");
  if (!explanation) {
    explanation = uiNode("p", "finance-notice");
    explanation.id = "sensitivity-explanation";
    document.getElementById("sensitivity-table").before(explanation);
  }
  const leaders = financeResult.sensitivity_leaders.map((k) =>
    ft(FINANCE_FIELDS[k]),
  );
  explanation.textContent = leaders.length
    ? leaders.join(" / ") +
      uiText(
        " has the largest modeled absolute effect on monthly profit (ties shown).",
        " له أكبر أثر مطلق محسوب على الربح الشهري (تُعرض التعادلات).",
      )
    : uiText(
        "No non-zero modeled profit impact is available.",
        "لا يتوفر أثر ربح محسوب غير صفري.",
      );
  renderSensitivityChart();
  const unit = (value) =>
    value == null
      ? uiText("Unknown", "غير معلوم")
      : Number(value).toLocaleString(lang === "ar" ? "ar-AE-u-nu-latn" : "en") +
        " " +
        uiText("units", "وحدة");
  bars(
    "break-even-chart",
    uiText(
      "Sales assumption vs whole-unit break-even",
      "افتراض المبيعات مقارنة بوحدات التعادل",
    ),
    [
      [uiText("Sales assumption", "افتراض المبيعات"), r.inputs.units],
      [uiText("Break-even", "التعادل"), r.break_even_units],
    ],
    unit,
  );
  bars(
    "cash-flow-chart",
    uiText(
      "Monthly cash in and out · AED",
      "النقد الداخل والخارج شهرياً · درهم",
    ),
    [
      [uiText("Cash collected", "النقد المحصّل"), r.effective_cash_collections],
      [uiText("Cash paid out", "النقد المدفوع"), r.effective_cash_payments],
    ],
  );
  table(
    "cash-data",
    [uiText("Measure", "البند"), uiText("Value", "القيمة")],
    [
      [uiText("Sales assumption", "افتراض المبيعات"), unit(r.inputs.units)],
      [uiText("Break-even", "التعادل"), breakLabel(r)],
      [
        uiText("Cash collected", "النقد المحصّل"),
        money(r.effective_cash_collections),
      ],
      [
        uiText("Cash paid out", "النقد المدفوع"),
        money(r.effective_cash_payments),
      ],
    ],
  );
  const a = financeResult.allocation;
  setTxt(
    "allocation-status",
    uiText("Known allocation: ", "التخصيص المعروف: ") +
      money(a.known_total || a.total) +
      (a.over_budget
        ? " · " +
          uiText(
            "Warning: allocation exceeds available funds.",
            "تنبيه: التخصيص يتجاوز الأموال المتاحة.",
          )
        : " · " + uiText("Remaining: ", "المتبقي: ") + money(a.remaining)),
  );
  document
    .getElementById("allocation-status")
    .classList.toggle("finance-warning", a.over_budget);
  renderFinanceIntegration();
  updateReadiness();
}
function illustrativeInputs(name, base) {
  const v = structuredClone(base);
  if (
    name !== "base" &&
    v.units !== undefined &&
    v.units !== null &&
    v.units !== ""
  ) {
    const units = Number(v.units),
      change = name === "conservative" ? -20 : 20;
    let next = Math.round(units * (1 + change / 100));
    if (next === units) next = Math.max(0, units + (change > 0 ? 1 : -1));
    v.units = String(next);
  }
  return v;
}
function renderScenarios() {
  const root = document.getElementById("scenario-editors");
  root.replaceChildren();
  Object.entries(SCENARIOS).forEach(([name, label]) => {
    const values = () =>
        investment.scenarios[name] ||
        illustrativeInputs(name, investment.inputs),
      edit = () =>
        (investment.scenarios[name] ||= illustrativeInputs(
          name,
          investment.inputs,
        ));
    const detail = uiNode("details", "scenario-editor");
    detail.append(uiNode("summary", "", ft(label)));
    const reset = uiNode(
      "button",
      "btn btn-light",
      uiText("Reset this scenario", "استعادة هذا السيناريو"),
    );
    reset.type = "button";
    reset.onclick = () => {
      delete investment.scenarios[name];
      renderScenarios();
      calculateFinance();
    };
    detail.append(reset);
    Object.keys(FINANCE_FIELDS).forEach((key) =>
      detail.append(
        financeField(key, values()[key], (v) => (edit()[key] = v), name),
      ),
    );
    for (const [key, options] of [
      [
        "contingency_mode",
        [
          ["aed", "AED", "AED"],
          ["percent", "% of one-time costs", "نسبة من التأسيس"],
        ],
      ],
      [
        "cash_mode",
        [
          ["entered", "Entered cash flow", "التدفق المدخل"],
          ["simplified", "Simplified assumption", "افتراض مبسط"],
        ],
      ],
      [
        "cogs_basis",
        [
          ["separate", "Separate COGS basis", "أساس مستقل للبضاعة"],
          [
            "subset_of_variable",
            "COGS within variable costs",
            "البضاعة ضمن التكلفة المتغيرة",
          ],
        ],
      ],
    ]) {
      const label = uiNode(
          "label",
          "",
          uiText(
            key === "cash_mode"
              ? "Cash-flow method"
              : key === "cogs_basis"
                ? "COGS basis"
                : "Contingency method",
            key === "cash_mode"
              ? "طريقة التدفق"
              : key === "cogs_basis"
                ? "أساس البضاعة"
                : "طريقة الاحتياطي",
          ),
        ),
        select = uiNode("select");
      select.id = name + "-" + key;
      label.htmlFor = select.id;
      options.forEach(([v, en, ar]) => {
        const o = uiNode("option", "", uiText(en, ar));
        o.value = v;
        select.append(o);
      });
      select.value = values()[key] || options[0][0];
      select.onchange = () => {
        edit()[key] = select.value;
        scheduleFinance();
      };
      label.append(select);
      detail.append(label);
    }
    root.append(detail);
  });
}
function renderStages() {
  const root = document.getElementById("investment-stages");
  root.replaceChildren();
  STAGES.forEach((s, i) => {
    const box = uiNode("details", "investment-stage");
    box.append(
      uiNode("span", "step-index", String(i + 1).padStart(2, "0")),
      uiNode("h4", "", s[lang === "ar" ? 1 : 0]),
      uiNode("p", "", s[lang === "ar" ? 3 : 2]),
      uiNode(
        "p",
        "",
        uiText("Success & evidence: ", "النجاح والأدلة: ") +
          s[lang === "ar" ? 5 : 4],
      ),
      uiNode("p", "", s[lang === "ar" ? 7 : 6]),
    );
    const label = uiNode(
        "label",
        "",
        uiText("Allocated budget · AED", "الميزانية المخصصة · درهم"),
      ),
      input = uiNode("input");
    input.type = "number";
    input.min = "0";
    input.step = ".01";
    input.value = investment.allocations[i] || "";
    input.id = "stage-budget-" + i;
    input.oninput = () => {
      investment.allocations[i] = input.value;
      scheduleFinance();
    };
    label.append(input);
    const check = uiNode("input");
    check.type = "checkbox";
    check.checked = investment.stageDone.includes(i);
    check.onchange = () => {
      investment.stageDone = check.checked
        ? [...investment.stageDone, i]
        : investment.stageDone.filter((n) => n !== i);
      saveSession();
    };
    const status = uiNode("label", "check-row");
    status.append(
      check,
      document.createTextNode(
        uiText("Completed · my assessment", "مكتمل · بتقييمي"),
      ),
    );
    box.append(label, status);
    const heading = uiNode("summary");
    heading.append(box.querySelector(".step-index"), box.querySelector("h4"));
    box.prepend(heading);
    box.open = innerWidth >= 768 || i === 0;
    root.append(box);
  });
}
function renderReadiness() {
  const root = document.getElementById("readiness-checks");
  root.replaceChildren();
  READINESS.forEach((pair, i) => {
    const label = uiNode("label", "check-row"),
      check = uiNode("input");
    check.type = "checkbox";
    check.checked = investment.readiness.includes(i);
    check.onchange = () => {
      investment.readiness = check.checked
        ? [...investment.readiness, i]
        : investment.readiness.filter((n) => n !== i);
      updateReadiness();
      saveSession();
    };
    label.dataset.readiness = String(i);
    label.append(
      check,
      document.createTextNode(uiText("I confirm: ", "أؤكد: ") + ft(pair)),
    );
    root.append(label);
  });
  updateReadiness();
}
function updateReadiness() {
  const detected = detectedReadiness();
  document.querySelectorAll("[data-readiness]").forEach((label) => {
    label.querySelector(".detected-status")?.remove();
    if (detected.has(Number(label.dataset.readiness)))
      label.append(
        uiNode(
          "span",
          "source-badge detected-status",
          uiText("Detected from your entries", "مكتشف من إدخالاتك"),
        ),
      );
  });
  setTxt(
    "readiness-status",
    uiText(
      `${investment.readiness.length} of 12 self-reported; ${detected.size} detected from inputs. Not independently verified.`,
      `${investment.readiness.length} من 12 بإقرارك؛ ${detected.size} مكتشف من المدخلات. دون تحقق مستقل.`,
    ),
  );
  const root = document.getElementById("readiness-next");
  root.replaceChildren(
    uiNode(
      "p",
      "",
      uiText(
        "Your next priorities · checklist answers are self-reported, not verified readiness.",
        "أولوياتك التالية · الإجابات إقرار ذاتي وليست تحققاً من الجاهزية.",
      ),
    ),
  );
  const details = [
    [
      "A clear problem makes interviews focused.",
      "وضوح المشكلة يوجّه المقابلات.",
      "Write one problem and its current alternative.",
      "اكتب مشكلة واحدة وبديلها الحالي.",
      0,
      0,
    ],
    [
      "A defined segment makes recruitment practical.",
      "تحديد الشريحة يجعل الوصول عملياً.",
      "Choose one customer segment to interview.",
      "اختر شريحة لمقابلتها.",
      2,
      0,
    ],
    [
      "Customer conversations challenge assumptions.",
      "المقابلات تختبر الافتراضات.",
      "Record interviews in Proof Mode.",
      "سجّل المقابلات في وضع الإثبات.",
      1,
      0,
    ],
    [
      "Behavior is stronger evidence than compliments.",
      "السلوك دليل أقوى من المجاملات.",
      "Test a reservation or purchase where permitted.",
      "اختبر حجزاً أو شراءً حيث يسمح.",
      1,
      0,
    ],
    [
      "A common unit keeps margins meaningful.",
      "وحدة متسقة تجعل الهوامش مفيدة.",
      "Enter price and matching unit costs.",
      "أدخل السعر وتكلفة الوحدة المتطابقة.",
      7,
      2,
    ],
    [
      "Unlisted initial costs can understate capital.",
      "التكاليف الناقصة تقلل رأس المال المحسوب.",
      "Collect setup and licensing quotes.",
      "اجمع عروض التأسيس والترخيص.",
      7,
      1,
    ],
    [
      "Recurring payments determine cash needs.",
      "المدفوعات المتكررة تحدد الحاجة النقدية.",
      "Estimate fixed, variable and cash payments.",
      "قدّر الثابتة والمتغيرة والمدفوعات.",
      7,
      2,
    ],
    [
      "Risks change the next experiment.",
      "المخاطر تغيّر التجربة التالية.",
      "Choose the risk to test first.",
      "اختر الخطر الذي تختبره أولاً.",
      4,
      0,
    ],
    [
      "A small experiment limits spending.",
      "تجربة صغيرة تحدّ الإنفاق.",
      "Choose a measurable seven-day task.",
      "اختر مهمة أسبوعية قابلة للقياس.",
      3,
      0,
    ],
    [
      "Requirements vary by activity and location.",
      "تختلف المتطلبات حسب النشاط والموقع.",
      "Check the official authority before operating.",
      "راجع الجهة الرسمية قبل التشغيل.",
      6,
      0,
    ],
    [
      "A concise pitch exposes missing information.",
      "العرض الموجز يكشف المعلومات الناقصة.",
      "Explain problem, offer and evidence clearly.",
      "اشرح المشكلة والعرض والأدلة.",
      5,
      0,
    ],
    [
      "A funding purpose links money to a milestone.",
      "استخدام التمويل يربط المال بمرحلة.",
      "Describe how funds support the next milestone.",
      "اشرح دعم الأموال للمرحلة التالية.",
      7,
      6,
    ],
  ];
  const gaps = [0, 2, 3, 4, 5, 6, 9, 11, 1, 7, 8, 10]
    .filter((i) => !investment.readiness.includes(i) && !detected.has(i))
    .slice(0, 3);
  if (!gaps.length)
    root.append(
      uiNode(
        "p",
        "",
        uiText(
          "Review evidence and official programme eligibility. Completion does not establish viability.",
          "راجع الأدلة وأهلية البرامج الرسمية. اكتمال القائمة لا يثبت الجدوى.",
        ),
      ),
    );
  gaps.forEach((i) => {
    const d = details[i],
      card = uiNode("article", "readiness-priority");
    card.append(
      uiNode("h4", "", ft(READINESS[i])),
      uiNode("p", "", d[lang === "ar" ? 1 : 0]),
      uiNode(
        "p",
        "",
        uiText("Next action: ", "الإجراء التالي: ") + d[lang === "ar" ? 3 : 2],
      ),
    );
    if (i === 2 || i === 3)
      card.append(
        uiNode(
          "small",
          "",
          uiText("Recorded customer entries: ", "إدخالات العملاء المسجّلة: ") +
            (currentPlan?.proof_summary?.total_responses || 0),
        ),
      );
    const link = uiNode(
      "button",
      "btn btn-light",
      uiText("Open relevant section →", "افتح القسم المناسب ←"),
    );
    link.onclick = () => {
      selectPanel(d[4]);
      if (d[4] === 7) showInvestmentSection(d[5], true);
      const selector = {
        2: ".p-int",
        3: ".p-pre",
        4: "#fin-price",
        5: "#fin-equipment",
        6: "#fin-fixed_cost",
        9: "#regional-resource",
        11: "#investor-use_of_funds",
      }[i];
      if (selector) document.querySelector(selector)?.focus();
    };
    card.append(link);
    root.append(card);
  });
}
function renderInvestorFields() {
  const root = document.getElementById("investor-fields"),
    values = {};
  root
    .querySelectorAll("textarea")
    .forEach((n) => (values[n.dataset.key] = n.value));
  root.replaceChildren();
  [
    ["model", "Business model / pricing unit", "نموذج العمل ووحدة التسعير"],
    ["differentiation", "Competitive differentiation", "التميّز التنافسي"],
    ["use_of_funds", "Intended use of funding", "الاستخدام المقصود للتمويل"],
  ].forEach(([key, en, ar]) => {
    const label = uiNode("label", "", uiText(en, ar)),
      input = uiNode("textarea");
    input.maxLength = 1000;
    input.dataset.key = key;
    input.id = "investor-" + key;
    input.value = investment.notes?.[key] ?? values[key] ?? "";
    input.oninput = () => {
      investment.notes ||= {};
      investment.notes[key] = input.value;
      saveSession();
    };
    input.placeholder = uiText("Not yet provided", "لم يُقدّم بعد");
    label.append(input);
    root.append(label);
  });
}
function renderFinanceIntegration() {
  if (!currentPlan) return;
  const r = financeResult?.base;
  const costRow = document.querySelectorAll("#score-bars .score-row")[2];
  if (costRow) {
    costRow.querySelector(".score-financial-context")?.remove();
    costRow.append(
      uiNode(
        "p",
        "score-financial-context",
        uiText(
          "Investment context (user assumptions, not scoring evidence): ",
          "سياق الاستثمار (افتراضات المستخدم وليست أدلة للتقييم): ",
        ) +
          (r
            ? uiText("Known startup capital ", "رأس المال المعروف ") +
              money(r.startup_capital) +
              uiText("; funding gap ", "؛ فجوة التمويل ") +
              money(r.funding_gap)
            : uiText(
                "Add costs in the Investment Guide.",
                "أضف التكاليف في دليل الاستثمار.",
              )) +
          uiText(
            " The 25-point score is unchanged.",
            " لا تتغير درجة التقييم من 25.",
          ),
      ),
    );
  }
  if (r) currentPlan._financial_inputs = structuredClone(investment.inputs);
  else delete currentPlan._financial_inputs;
  table(
    "investor-preview",
    [
      uiText("Your brief", "ملخصك"),
      uiText("Current information", "المعلومات الحالية"),
    ],
    [
      [
        uiText("Business idea · user input", "فكرة المشروع · إدخال المستخدم"),
        currentPlan.state?.idea,
      ],
      [
        uiText("Problem hypothesis", "فرضية المشكلة"),
        currentPlan.idea_overview?.problem,
      ],
      [
        uiText("Proposed solution", "الحل المقترح"),
        currentPlan.idea_overview?.solution,
      ],
      [
        uiText("Customer hypothesis", "فرضية العميل"),
        currentPlan.state?.target_customer,
      ],
      [
        uiText(
          "Recorded entries · not independently verified",
          "الإدخالات المسجّلة · لم تُتحقق مستقلاً",
        ),
        currentPlan.proof_summary?.total_responses || 0,
      ],
      [
        uiText(
          "Required capital · user assumptions",
          "رأس المال المطلوب · افتراضات المستخدم",
        ),
        money(r?.startup_capital),
      ],
      [
        uiText("Funding request · user input", "طلب التمويل · إدخال المستخدم"),
        money(investment.inputs.funding_request || null),
      ],
    ],
  );

  for (const [id, parent] of [
    ["overview-finance", "dashboard-summary"],
    ["financial-risk", "risk-list"],
    ["financial-plan-task", "day-grid"],
    ["pitch-finance", "pitch-list"],
  ]) {
    let el = document.getElementById(id);
    if (!el) {
      el = uiNode("div", "finance-notice");
      el.id = id;
      document.getElementById(parent).append(el);
    }
    el.replaceChildren();
    if (!r) {
      el.append(
        uiNode(
          "p",
          "",
          uiText(
            "Investment assumptions are incomplete. Add your costs and price in the Investment Guide.",
            "افتراضات الاستثمار غير مكتملة. أضف تكاليفك وسعرك في دليل الاستثمار.",
          ),
        ),
      );
    } else if (id === "overview-finance" || id === "pitch-finance") {
      el.append(
        uiNode(
          "p",
          "",
          uiText(
            "Financial illustration · user assumptions: ",
            "مثال مالي · افتراضات المستخدم: ",
          ) +
            ft(METRICS.startup_capital) +
            " " +
            money(r.startup_capital) +
            " · " +
            uiText("Gap: ", "الفجوة: ") +
            money(r.funding_gap) +
            " · " +
            breakLabel(r),
        ),
      );
    } else if (id === "financial-risk") {
      el.append(
        uiNode(
          "b",
          "",
          uiText(
            "Financial risk · based on your inputs",
            "المخاطر المالية · بناءً على مدخلاتك",
          ),
        ),
        uiNode(
          "p",
          "",
          r.break_even_status === "unreachable"
            ? breakLabel(r)
            : Number(r.funding_gap) > 0
              ? uiText(
                  "Startup funds are below planned capital. Reduce commitments or review the funding gap.",
                  "أموال البدء أقل من رأس المال المخطط. خفّض الالتزامات أو راجع فجوة التمويل.",
                )
              : r.operating_profit !== null && Number(r.operating_profit) < 0
                ? uiText(
                    "The entered sales level produces an operating loss. Test pricing and costs before spending.",
                    "مستوى البيع المدخل ينتج خسارة تشغيلية. اختبر السعر والتكاليف قبل الإنفاق.",
                  )
                : uiText(
                    "Review missing inputs, supplier quotes and cash timing. Profit does not verify demand.",
                    "راجع المدخلات الناقصة وعروض الموردين وتوقيت السيولة. الربح لا يثبت الطلب.",
                  ),
        ),
      );
    } else
      el.append(
        uiNode("b", "", uiText("Financial task", "مهمة مالية")),
        uiNode(
          "p",
          "",
          uiText(
            "Collect cost quotes and test the pricing unit with customers. Update the Investment Guide after the conversations.",
            "اجمع عروض تكاليف واختبر وحدة السعر مع العملاء، ثم حدّث دليل الاستثمار.",
          ),
        ),
      );
    if (id === "financial-risk") {
      el.append(
        uiNode(
          "small",
          "",
          uiText(
            "Financial assumptions inform cost explanations only. The five dimensions remain 0–5 each; estimates never earn customer-evidence points.",
            "الافتراضات المالية توضح التكاليف فقط. تبقى الأبعاد الخمسة من 0–5؛ التقديرات لا تمنح نقاط أدلة عملاء.",
          ),
        ),
      );
    }
    if (id === "overview-finance") {
      const button = uiNode(
        "button",
        "btn btn-primary",
        uiText("Open Investment Guide →", "افتح دليل الاستثمار ←"),
      );
      button.onclick = () => selectPanel(7);
      el.append(button);
    }
  }
  compactInvestmentLink();
}
async function loadFunding() {
  try {
    const response = await fetch(document.body.dataset.fundingSrc);
    fundingData = await response.json();
    renderFunding();
  } catch {
    setTxt(
      "funding-results",
      uiText(
        "Directory unavailable. Use the official UAE business resource links.",
        "الدليل غير متاح. استخدم روابط موارد الأعمال الحكومية.",
      ),
    );
  }
}
async function exportInvestment() {
  if (!currentPlan) return;
  setInvestmentStatus("preparing");
  const exportLang = lang;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 65000);
  const notes = {};
  document
    .querySelectorAll("#investor-fields textarea")
    .forEach((n) => (notes[n.dataset.key] = n.value));
  try {
    const response = await fetch("/investment/pdf", {
      method: "POST",
      signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lang: exportLang,
        finance: financePayload(),
        plan: currentPlan,
        notes,
      }),
    });
    checkServiceResponse(response);
    if (!response.ok) throw Error();
    downloadBlob(
      await response.blob(),
      "Khotwa_Investment_" + exportLang + ".pdf",
    );
    setInvestmentStatus("downloaded");
  } catch (error) {
    if (error.retrySeconds) {
      setInvestmentStatus("rate_limited", error.retrySeconds);
      return;
    }
    setInvestmentStatus("failed");
  } finally {
    clearTimeout(timeout);
  }
}
function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function exportFinanceCSV() {
  if (!financeResult) return;
  const cell = (v) =>
    '"' +
    String(v ?? "")
      .replace(/[\u2066-\u2069]/g, "")
      .replace(/^[\s]*[=+@-]/, "'$&")
      .replace(/"/g, '""') +
    '"';
  const rows = [
    ["metric", "raw_value", "display_value", "unit", "source"],
    ...Object.keys(METRICS).map((k) => [
      k,
      financeResult.base[k],
      metricValue(k, financeResult.base[k]),
      k === "contribution_ratio" || k === "gross_margin" ? "ratio" : "AED",
      "user_assumptions",
    ]),
    ...["break_even_units", "runway_months", "payback_months"].map((k) => [
      k,
      financeResult.base[k],
      financeResult.base[k],
      k === "break_even_units" ? "units" : "months",
      "user_assumptions",
    ]),
    [
      "cash_flow_basis",
      financeResult.base.cash_flow_basis,
      cashBasisLabel(financeResult.base),
      "basis",
      "user_assumptions",
    ],
  ];
  downloadBlob(
    new Blob(["\ufeff" + rows.map((r) => r.map(cell).join(",")).join("\r\n")], {
      type: "text/csv;charset=utf-8",
    }),
    "Khotwa_Financial_Assumptions.csv",
  );
}
