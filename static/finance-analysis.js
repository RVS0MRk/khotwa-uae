function formatUnits(value) {
  return value == null
    ? uiText("Unknown", "غير معلوم")
    : new Intl.NumberFormat("en-AE", { maximumFractionDigits: 0 }).format(
        Number(value),
      );
}
function formatChangePercent(value) {
  if (value == null)
    return uiText("Not defined from zero", "غير معرف من الصفر");
  const n = Number(value),
    sign = n < 0 ? "−" : n > 0 ? "+" : "";
  const text =
    sign +
    new Intl.NumberFormat("en-AE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(n)) +
    "%";
  return lang === "ar" ? "\u2066" + text + "\u2069" : text;
}
function scenarioMetric(key, r) {
  return key === "break_even_units"
    ? breakLabel(r)
    : key === "runway_months"
      ? runwayLabel(r)
      : key === "payback_months"
        ? paybackLabel(r)
        : key === "funding_gap"
          ? fundingGapLabel(r[key])
          : money(r[key]);
}
function renderScenarioComparison() {
  const metrics = [
      "revenue",
      "operating_profit",
      "startup_capital",
      "funding_gap",
      "break_even_units",
      "runway_months",
      "payback_months",
    ],
    names = Object.keys(SCENARIOS),
    label = (k) =>
      METRICS[k]
        ? ft(METRICS[k])
        : {
            break_even_units: uiText("Break-even", "التعادل"),
            runway_months: uiText("Runway", "المدة النقدية"),
            payback_months: uiText("Payback estimate", "تقدير الاسترداد"),
          }[k];
  const changed = [],
    same = [];
  for (const key of metrics) {
    const values = names.map((name) =>
      scenarioMetric(key, financeResult.scenarios[name]),
    );
    if (new Set(values).size === 1) same.push(label(key) + ": " + values[0]);
    else changed.push(key);
  }
  table(
    "scenario-comparison",
    [uiText("Scenario", "السيناريو"), ...changed.map(label)],
    names.map((name) => [
      ft(SCENARIOS[name]),
      ...changed.map((k) => scenarioMetric(k, financeResult.scenarios[name])),
    ]),
  );
  let line = document.getElementById("scenario-same");
  if (!line) {
    line = uiNode("p", "finance-notice");
    line.id = "scenario-same";
    document.getElementById("scenario-comparison").after(line);
  }
  line.hidden = !same.length;
  line.textContent =
    uiText("Same in all scenarios: ", "متطابق في كل السيناريوهات: ") +
    same.join(" · ");
}
function renderSensitivityChart() {
  const entries = financeResult.sensitivity,
    root = document.getElementById("sensitivity-chart");
  root.replaceChildren(
    uiNode(
      "figcaption",
      "",
      uiText(
        "Profit impact around zero · both directions per assumption",
        "أثر الربح حول الصفر · اتجاهان لكل افتراض",
      ),
    ),
  );
  const scale = Math.max(
    0,
    ...entries.map((s) => Math.abs(Number(s.profit_impact || 0))),
  );
  const groups = new Map();
  for (const s of entries) {
    if (!groups.has(s.field)) groups.set(s.field, []);
    groups.get(s.field).push(s);
  }
  for (const [field, cases] of groups) {
    const row = uiNode("div", "sensitivity-assumption");
    row.append(uiNode("h4", "", ft(FINANCE_FIELDS[field])));
    for (const s of cases.sort((a, b) => a.percent - b.percent)) {
      const line = uiNode("div", "sensitivity-comparison"),
        axis = uiNode("div", "diverging-axis"),
        bar = uiNode(
          "span",
          Number(s.profit_impact) < 0 ? "negative" : "positive",
        );
      axis.setAttribute("aria-hidden", "true");
      bar.style.width =
        (scale ? (Math.abs(Number(s.profit_impact || 0)) / scale) * 50 : 0) +
        "%";
      axis.append(bar);
      line.append(
        uiNode("span", "", formatChangePercent(s.actual_percent)),
        axis,
        uiNode("span", "", money(s.profit_impact)),
      );
      row.append(line);
    }
    root.append(row);
  }
  let details = document.getElementById("sensitivity-table-details");
  if (!details) {
    details = uiNode("details", "finance-methods");
    details.id = "sensitivity-table-details";
    details.append(uiNode("summary", "", uiText("Show table", "عرض الجدول")));
    document.getElementById("sensitivity-table").before(details);
    details.append(document.getElementById("sensitivity-table"));
  }
  details.querySelector("summary").textContent = uiText(
    "Show table",
    "عرض الجدول",
  );
  const sizes = entries
    .filter((s) => s.actual_percent != null)
    .map((s) => Math.abs(Number(s.actual_percent)));
  if (sizes.length && Math.max(...sizes) - Math.min(...sizes) > 2)
    document
      .getElementById("sensitivity-explanation")
      .append(
        document.createTextNode(
          uiText(
            " Moves differ in size; whole-unit moves can exceed the target ±10%. Compare the actual percentages shown.",
            " تختلف أحجام التغيير؛ قد تتجاوز حركة الوحدات هدف ±10٪. قارن النسب الفعلية المعروضة.",
          ),
        ),
      );
}
