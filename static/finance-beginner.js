// The quick form computes only outputs supported by the entered assumptions.
function renderFinanceStarter() {
  const root = document.getElementById("investment-panel-0");
  let card = document.getElementById("finance-starter");
  if (card && document.activeElement?.closest("#finance-starter")) return;
  if (!card) {
    card = uiNode("section", "finance-starter finance-inputs");
    card.id = "finance-starter";
    root.prepend(card);
  }
  card.replaceChildren(
    uiNode("h3", "", uiText("Start with 4 numbers", "ابدأ بـ4 أرقام")),
    uiNode(
      "p",
      "",
      uiText(
        "Define one selling unit, then enter sales and operating costs. Available funds come from your budget; edit them below.",
        "حدّد وحدة بيع ثم أدخل المبيعات وتكاليف التشغيل. تأتي الأموال المتاحة من ميزانيتك ويمكن تعديلها.",
      ),
    ),
  );
  const grid = uiNode("div", "finance-fields");
  for (const key of [
    "price",
    "units",
    "variable_cost",
    "fixed_cost",
    "available_capital",
  ]) {
    const label = financeField(
      key,
      investment.inputs[key],
      (value) => {
        investment.inputs[key] = value;
        const normal = document.getElementById("fin-" + key);
        if (normal) normal.value = value;
      },
      "quick",
    );
    if (key === "price" && investment.aiPricePrefill)
      label.append(
        uiNode(
          "small",
          "source-badge assumption",
          uiText("AI suggestion — edit", "اقتراح ذكاء اصطناعي — عدّل"),
        ),
      );
    grid.append(label);
  }
  card.append(grid);
  const calculate = uiNode(
    "button",
    "btn btn-primary",
    uiText("Calculate", "احسب"),
  );
  calculate.type = "button";
  calculate.onclick = () => calculateFinance(true);
  card.append(
    calculate,
    uiNode(
      "p",
      "finance-hint",
      uiText(
        "Runway and payback also need startup spending and reserves. Missing costs stay unknown; add them in Startup costs.",
        "تحتاج المدة النقدية والاسترداد أيضاً إلى إنفاق التأسيس والاحتياطيات. تبقى التكاليف الناقصة غير معلومة؛ أضفها في تكاليف التأسيس.",
      ),
    ),
  );
}
function beginnerFinanceResults(r) {
  renderFinanceStarter();
  const computable =
    ["revenue", "operating_profit", "contribution_per_unit"].some(
      (k) => r[k] !== null,
    ) || r.break_even_units !== null;
  const metrics = document.getElementById("finance-metrics");
  if (!computable) {
    metrics.replaceChildren(
      uiNode(
        "p",
        "finance-empty",
        uiText(
          "Add price, whole monthly units, variable cost per unit and monthly fixed costs to calculate.",
          "أضف السعر ووحدات الشهر الصحيحة وتكلفة الوحدة المتغيرة والمصروف الثابت لحساب النتائج.",
        ),
      ),
    );
    return false;
  }
  return true;
}
function fundingGapLabel(value) {
  if (value == null)
    return uiText(
      "Add startup costs to calculate",
      "أضف تكاليف التأسيس للحساب",
    );
  const n = Number(value);
  return (
    (n > 0 ? uiText("Shortfall ", "عجز ") : uiText("Surplus ", "فائض ")) +
    money(Math.abs(n))
  );
}
function detectedReadiness() {
  if (!currentPlan) return new Set();
  const v = investment.inputs || {},
    known = (k) =>
      v[k] !== "" &&
      v[k] != null &&
      Number.isFinite(Number(v[k])) &&
      Number(v[k]) >= 0;
  const d = new Set();
  if (currentPlan.state?.customer_type) d.add(1);
  if (["price", "units"].every(known)) d.add(4);
  if (
    [
      "equipment",
      "initial_software",
      "initial_marketing",
      "other_startup",
    ].every(known)
  )
    d.add(5);
  if (["variable_cost", "fixed_cost"].every(known)) d.add(6);
  if (investment.risksReviewed) d.add(7);
  if (
    Object.values(currentPlan.pitches || {}).some(
      (s) => typeof s === "string" && s.length > 12,
    )
  )
    d.add(10);
  if (!currentPlan._demo) {
    const p = currentPlan.proof_summary || {};
    if (Number(p.total_responses) > 0) d.add(2);
    if (
      Number(p.no_payment_reservations || 0) +
        Number(p.actual_payments || 0) +
        Number(p.repeat_customers || 0) >
      0
    )
      d.add(3);
  }
  return d;
}
function setupFinanceAdvanced() {
  const panel = document.getElementById("investment-panel-2");
  const details = uiNode("details", "finance-methods");
  details.id = "finance-advanced";
  const summary = uiNode("summary");
  summary.dataset.en = "Advanced / How we calculate";
  summary.dataset.ar = "متقدم / طريقة الحساب";
  summary.textContent = uiText(summary.dataset.en, summary.dataset.ar);
  details.append(summary);
  for (const id of ["cogs-basis"]) {
    const node = document.getElementById(id),
      label = document.querySelector('label[for="' + id + '"]');
    details.append(label, node);
  }
  const cashNote = uiNode(
    "p",
    "",
    uiText(
      "The separate cash-in/out method preserves payment timing. Simple mode assumes all sales and recurring expenses are collected/paid in the same month.",
      "يحافظ وضع التدفق المنفصل على توقيت الدفع. يفترض الوضع البسيط تحصيل المبيعات وسداد المتكررة في الشهر نفسه.",
    ),
  );
  cashNote.dataset.en = "The separate cash-in/out method preserves payment timing. Simple mode assumes all sales and recurring expenses are collected/paid in the same month.";
  cashNote.dataset.ar = "يحافظ وضع التدفق المنفصل على توقيت الدفع. يفترض الوضع البسيط تحصيل المبيعات وسداد المتكررة في الشهر نفسه.";
  cashNote.id = "finance-cash-timing-note";
  details.append(cashNote);
  panel.append(details);
}

function moveAdvancedFields() {
  const advanced = document.getElementById("finance-advanced");
  if (!advanced) return;
  advanced.querySelectorAll("[data-moved-finance]").forEach((n) => n.remove());
  const cogs = document.getElementById("fin-cogs_per_unit")?.closest("label");
  if (cogs) {
    cogs.dataset.movedFinance = "true";
    advanced.append(cogs);
  }
  const cash = document
    .getElementById("fin-cash_collections")
    ?.closest("fieldset");
  if (cash) {
    cash.dataset.movedFinance = "true";
    advanced.append(cash);
  }
  if (investment.inputs.cash_mode === "entered") advanced.open = true;
}
function compactFinanceMethods() {
  const basis = document.getElementById("finance-basis");
  if (!basis) return;
  const note = basis.querySelector("small");
  if (note) {
    const details = uiNode("details", "finance-methods");
    const summary = uiNode("summary");
    summary.dataset.en = "How we calculate / assumptions";
    summary.dataset.ar = "طريقة الحساب والافتراضات";
    summary.textContent = uiText(summary.dataset.en, summary.dataset.ar);
    details.append(summary, note);
    basis.append(details);
  }
  basis.querySelectorAll(".finance-warning").forEach((n) => {
    if (investment.legacyLicensing) basis.querySelector("details")?.append(n);
  });
}
