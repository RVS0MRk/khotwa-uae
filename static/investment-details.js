// Presentation of financial assumptions and export state, separate from arithmetic.
const investmentStatuses = { export: "", error: "" };
function clearFinanceResults() {
  document.getElementById("finance-basis")?.remove();
  for (const id of [
    "finance-breakdown",
    "expense-chart",
    "break-even-chart",
    "cash-flow-chart",
    "cash-data",
    "scenario-comparison",
    "scenario-chart",
    "sensitivity-table",
    "sensitivity-chart",
  ]) {
    document
      .getElementById(id)
      ?.replaceChildren(
        uiNode(
          "p",
          "finance-empty",
          uiText(
            "Results unavailable until assumptions are calculated.",
            "النتائج غير متاحة حتى حساب الافتراضات.",
          ),
        ),
      );
  }
  setTxt("sensitivity-explanation", "");
}
function setInvestmentStatus(value, retrySeconds = 0) {
  investmentStatuses.export = value;
  investmentStatuses.retrySeconds = retrySeconds;
  renderInvestmentStatuses();
}
function renderInvestmentStatuses() {
  const messages = {
    preparing: ["Preparing report…", "جارٍ إعداد التقرير…"],
    downloaded: ["Report downloaded.", "تم تنزيل التقرير."],
    failed: [
      "Export failed. Your assumptions are still available; try again.",
      "تعذّر التصدير. افتراضاتك محفوظة؛ حاول مجدداً.",
    ],
  };
  setTxt(
    "investment-export-status",
    investmentStatuses.export === "rate_limited"
      ? rateLimitMessage(investmentStatuses.retrySeconds)
      : ft(messages[investmentStatuses.export] || ["", ""]),
  );
  setTxt(
    "finance-error",
    investmentStatuses.error
      ? uiText(
          "Unable to calculate. Check non-negative numbers, whole sales units and contingency at most 100%.",
          "تعذّر الحساب. تحقّق من الأرقام غير السالبة ووحدات البيع الصحيحة ونسبة طوارئ لا تتجاوز 100٪.",
        )
      : "",
  );
}
function cashBasisLabel(r) {
  return r.cash_flow_basis === "simplified_user_assumption"
    ? uiText(
        "Simplified assumption (selected by default for new plans; review/edit): all revenue collected and variable + fixed expenses paid in the same month.",
        "افتراض مبسط (افتراضي للخطط الجديدة؛ راجعه وعدّله): تحصيل كل الإيراد وسداد المصروفات المتغيرة والثابتة في الشهر نفسه.",
      )
    : r.cash_flow_basis === "entered_cash_flow"
      ? uiText(
          "Based on separately entered cash receipts and payments (actual or assumed as entered).",
          "بناءً على المقبوضات والمدفوعات النقدية المدخلة بشكل مستقل، فعلية أو مفترضة وفق الإدخال.",
        )
      : uiText(
          "Unavailable: cash-flow information is incomplete.",
          "غير متاح: معلومات التدفق النقدي غير مكتملة.",
        );
}
function paybackLabel(r) {
  if (r.payback_status === "no_positive_benefit")
    return uiText(
      "No positive monthly cash benefit; payback unavailable.",
      "لا توجد منفعة نقدية شهرية موجبة؛ الاسترداد غير متاح.",
    );
  return r.payback_months == null
    ? uiText(
        "Unknown: initial costs or cash flow incomplete.",
        "غير معلوم: التأسيس أو التدفق النقدي غير مكتمل.",
      )
    : Number(r.payback_months).toLocaleString("en-AE", {
        maximumFractionDigits: 2,
      }) +
        " " +
        uiText("months", "شهر");
}
function renderFinanceBasis(r) {
  let root = document.getElementById("finance-basis");
  if (!root) {
    root = uiNode("div", "finance-notice");
    root.id = "finance-basis";
    document.getElementById("finance-metrics").after(root);
  }
  root.replaceChildren(
    uiNode("p", "", cashBasisLabel(r)),
    uiNode(
      "p",
      "",
      uiText("Simple payback: ", "الاسترداد البسيط: ") + paybackLabel(r),
    ),
    uiNode(
      "small",
      "",
      uiText(
        "Initial investment = one-time expenses including entered licensing, excluding held cash buffers. Divided by positive monthly net cash benefit. Constant-cash estimate; excludes changing cash flows and time value of money.",
        "الاستثمار الأولي = مصروفات التأسيس مع الترخيص المدخل دون الاحتياطيات النقدية، مقسوماً على صافي المنفعة النقدية الشهرية الموجبة. تقدير لسيولة ثابتة دون تغير التدفقات أو القيمة الزمنية للنقود.",
      ),
    ),
  );
  if (r.rounded_fields?.length)
    root.append(
      uiNode(
        "p",
        "finance-warning",
        uiText("Rounded to fils: ", "قُرّب إلى الفلس: ") +
          r.rounded_fields.map((k) => ft(FINANCE_FIELDS[k])).join(", "),
      ),
    );
  if (
    investment.legacyLicensing &&
    r.warnings.includes("licensing_not_provided")
  )
    root.append(
      uiNode(
        "p",
        "finance-warning",
        uiText(
          "Licensing not provided: known capital is a subtotal excluding unprovided licensing. Older records retain their subtotal. Enter 0 only when genuinely zero; move existing licensing out of Other costs before adding it here.",
          "لم يُدخل الترخيص: رأس المال مجموع جزئي يستثني الترخيص غير المقدم. تحتفظ السجلات القديمة بمجموعها. أدخل صفراً فقط إن كان حقيقياً وانقل الترخيص من التكاليف الأخرى قبل إضافته هنا.",
        ),
      ),
    );
  if (r.warnings.includes("cogs_exceeds_variable"))
    root.append(
      uiNode(
        "p",
        "finance-warning",
        uiText(
          "COGS exceeds variable cost although you selected COGS as a subset. Correct the inputs or choose a separate accounting basis; gross margin is withheld.",
          "تكلفة البضاعة تتجاوز المتغيرة رغم اختيارها جزءاً منها. صحّح المدخلات أو اختر أساساً مستقلاً؛ حُجب مجمل الهامش.",
        ),
      ),
    );
}
