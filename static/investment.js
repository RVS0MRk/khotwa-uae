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
    return new Intl.NumberFormat(lang === "ar" ? "ar-AE" : "en", {
      style: "percent",
      maximumFractionDigits: 2,
    }).format(Number(value));
  return money(value);
}
function investmentRecovery() {
  return {
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
  investment = {
    ...investment,
    ...value,
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
      : new Intl.NumberFormat(lang === "ar" ? "ar-AE" : "en").format(
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
            lang === "ar" ? "ar-AE" : "en",
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
  for (const key of [
    "startup_capital",
    "revenue",
    "operating_profit",
    "funding_gap",
    "contribution_per_unit",
    "contribution_ratio",
  ]) {
    const spec = METRICS[key],
      box = uiNode("article", "finance-metric");
    box.dataset.metric = key;
    box.append(
      uiNode("span", "metric-label", ft(spec)),
      uiNode("strong", "", metricValue(key, r[key])),
      uiNode("small", "", spec[lang === "ar" ? 3 : 2]),
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
      uiNode("small", "", formula),
    );
    metrics.append(box);
  }
  renderFinanceBasis(r);
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
  table(
    "scenario-comparison",
    [
      uiText("Scenario", "السيناريو"),
      ft(METRICS.revenue),
      ft(METRICS.operating_profit),
      uiText("Break-even", "التعادل"),
      ft(METRICS.startup_capital),
      uiText("Funding gap", "فجوة التمويل"),
      uiText("Runway", "المدة النقدية"),
    ],
    names.map((k) => {
      const s = financeResult.scenarios[k];
      return [
        ft(SCENARIOS[k]),
        money(s.revenue),
        money(s.operating_profit),
        breakLabel(s),
        money(s.startup_capital),
        money(s.funding_gap),
        runwayLabel(s),
      ];
    }),
  );
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
      s.baseline +
        " → " +
        s.comparison +
        (s.discrete ? " " + uiText("units", "وحدة") : " AED"),
      s.actual_percent == null
        ? uiText("Not defined from zero", "غير معرّف من الصفر")
        : s.actual_percent + "%",
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
  bars(
    "sensitivity-chart",
    uiText(
      "Ranked profit impacts · same order as table",
      "آثار الربح مرتبة · بترتيب الجدول نفسه",
    ),
    financeResult.sensitivity.map((s) => [
      ft(FINANCE_FIELDS[s.field]) + " " + s.baseline + " → " + s.comparison,
      s.profit_impact,
    ]),
  );
  const unit = (value) =>
    value == null
      ? uiText("Unknown", "غير معلوم")
      : Number(value).toLocaleString(lang === "ar" ? "ar-AE" : "en") +
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
    const box = uiNode("article", "investment-stage");
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
    box.append(
      label,
      status,
      uiNode("p", "", uiText("Next: ", "التالي: ") + s[lang === "ar" ? 3 : 2]),
    );
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
    label.append(check, document.createTextNode(ft(pair)));
    root.append(label);
  });
  updateReadiness();
}
function updateReadiness() {
  setTxt(
    "readiness-status",
    uiText(
      `${investment.readiness.length} of 12 preparation items reported complete.`,
      `${investment.readiness.length} من 12 بند استعداد أُقرّ باكتماله.`,
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
  const gaps = READINESS.map((_, i) => i)
    .filter((i) => !investment.readiness.includes(i))
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
    input.value = values[key] || "";
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
            ". The 25-point score is unchanged.",
            ". لا تتغير درجة التقييم من 25.",
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
}
async function loadFunding() {
  try {
    const response = await fetch("/static/funding.json");
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
function renderFunding() {
  renderFinancingRoutes();
  const search = document.getElementById("funding-search"),
    filter = document.getElementById("funding-filter"),
    selected = filter.value;
  search.placeholder = uiText(
    "Search support, emirate or institution…",
    "ابحث عن الدعم أو الإمارة أو المؤسسة…",
  );
  filter.replaceChildren();
  [
    ["all", "All support", "كل أنواع الدعم"],
    ["government", "Government support", "دعم حكومي"],
    ["finance", "Loans & guarantees", "قروض وضمانات"],
    ["accelerator", "Incubators & accelerators", "حاضنات ومسرّعات"],
  ].forEach(([value, en, ar]) => {
    const o = uiNode("option", "", uiText(en, ar));
    o.value = value;
    filter.append(o);
  });
  filter.value = selected || "all";
  const root = document.getElementById("funding-results");
  root.replaceChildren();
  fundingData
    .filter(
      (e) =>
        (filter.value === "all" || e.category === filter.value) &&
        JSON.stringify(e).toLowerCase().includes(search.value.toLowerCase()),
    )
    .forEach((entry) => {
      const d = entry[lang],
        card = uiNode("article", "funding-card");
      card.append(
        uiNode(
          "span",
          "source-badge",
          entry.status === "verified"
            ? uiText("OFFICIAL SOURCE CHECKED", "رُوجع المصدر الرسمي")
            : entry.status === "partial"
              ? uiText("PARTIAL · CONFIRM TERMS", "مراجعة جزئية · أكّد الشروط")
              : uiText("UNVERIFIED", "غير مُتحقق"),
        ),
        uiNode("h4", "", d.name),
        uiNode("p", "", d.description),
      );
      const dl = uiNode("dl");
      [
        ["support", "Support", "الدعم"],
        ["target", "Applicants", "المتقدمون"],
        ["scope", "Geography", "النطاق"],
        ["eligibility", "Eligibility & nationality", "الأهلية والجنسية"],
        ["limitations", "Limitations", "القيود"],
      ].forEach(([key, en, ar]) =>
        dl.append(uiNode("dt", "", uiText(en, ar)), uiNode("dd", "", d[key])),
      );
      card.append(dl);
      if (entry.programs) {
        const list = uiNode("ul", "funding-programs");
        entry.programs[lang].forEach((name) =>
          list.append(uiNode("li", "", name)),
        );
        card.append(list);
      }
      for (const [url, label] of [
        [entry.url, uiText("Official information ↗", "المعلومات الرسمية ↗")],
        [
          entry.apply,
          uiText("Application starting point ↗", "بداية التقديم ↗"),
        ],
      ]) {
        if (!/^https:\/\//.test(url)) continue;
        const a = uiNode("a", "", label);
        a.href = url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        card.append(a);
      }
      card.append(
        uiNode(
          "small",
          "",
          uiText("Last checked: ", "آخر مراجعة: ") +
            (entry.checked ||
              entry.verified ||
              uiText("Not verified", "غير مُتحقق")),
        ),
      );
      root.append(card);
    });
  if (!root.childElementCount)
    root.append(
      uiNode(
        "p",
        "finance-empty",
        uiText("No matching resources.", "لا توجد موارد مطابقة."),
      ),
    );
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
    if (!response.ok) throw Error();
    downloadBlob(
      await response.blob(),
      "Khotwa_Investment_" + exportLang + ".pdf",
    );
    setInvestmentStatus("downloaded");
  } catch {
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
