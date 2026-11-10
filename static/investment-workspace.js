// Progressive financial navigation; all V2 tools remain in one shared state.
const INVESTMENT_SECTIONS = [
  ["Financial overview", "النظرة المالية"],
  ["Startup costs", "تكاليف التأسيس"],
  ["Profit & cash flow", "الربح والتدفق النقدي"],
  ["Scenarios & sensitivity", "السيناريوهات والحساسية"],
  ["Investment stages", "مراحل الاستثمار"],
  ["Funding opportunities", "فرص التمويل"],
  ["Readiness & investor brief", "الاستعداد وملخص المستثمر"],
];
function setupInvestmentWorkspace() {
  const root = document.getElementById("investment-guide");
  const oldNav = root.querySelector(".investment-sections");
  const nav = uiNode("nav", "investment-tabs");
  nav.id = "investment-nav";
  nav.setAttribute("role", "tablist");
  oldNav.replaceWith(nav);
  // Calculation errors must remain visible from either input section.
  nav.after(document.getElementById("finance-error"));
  const layout = root.querySelector(".finance-layout"),
    form = document.getElementById("finance-form"),
    results = layout.lastElementChild;
  const sections = [...root.querySelectorAll(":scope > .finance-section")];
  const panels = INVESTMENT_SECTIONS.map((pair, i) => {
    const p = uiNode("section", "investment-panel");
    p.id = "investment-panel-" + i;
    p.setAttribute("role", "tabpanel");
    p.setAttribute("aria-labelledby", "investment-tab-" + i);
    root.append(p);
    return p;
  });
  panels[0].append(results);
  const intro = uiNode("div", "finance-actions");
  [[1, "Add startup costs", "أضف تكاليف التأسيس"]].forEach(([i, en, ar]) => {
    const b = uiNode("button", "btn btn-light");
    b.dataset.en = en;
    b.dataset.ar = ar;
    b.onclick = () => showInvestmentSection(i, true);
    intro.append(b);
  });
  results.prepend(intro);
  const methods = uiNode("details", "finance-methods"),
    summary = uiNode("summary");
  summary.dataset.en = "All calculations & formulas";
  summary.dataset.ar = "كل الحسابات والصيغ";
  methods.append(summary, document.getElementById("finance-breakdown"));
  results.append(methods);
  panels[1].append(form);
  const operating = uiNode("div", "finance-inputs");
  operating.id = "finance-operating-fields";
  panels[2].append(operating);
  const modeLabel = uiNode("label");
  modeLabel.dataset.en = "Cash-flow method";
  modeLabel.dataset.ar = "طريقة التدفق النقدي";
  modeLabel.htmlFor = "cash-mode";
  const mode = uiNode("select");
  mode.id = "cash-mode";
  [
    [
      "entered",
      "I'll enter cash in/out separately (advanced)",
      "سأدخل المقبوضات والمدفوعات بشكل منفصل (متقدم)",
    ],
    [
      "simplified",
      "Assume customers pay in the same month (simple)",
      "أفترض دفع العملاء في الشهر نفسه (بسيط)",
    ],
  ].forEach(([v, en, ar]) => {
    const o = uiNode("option");
    o.value = v;
    o.dataset.en = en;
    o.dataset.ar = ar;
    mode.append(o);
  });
  mode.onchange = () => {
    investment.inputs.cash_mode = mode.value;
    if (mode.value === "entered")
      document.getElementById("finance-advanced").open = true;
    scheduleFinance();
  };
  const cashHelp = uiNode("p", "finance-notice");
  cashHelp.dataset.en =
    "Simplified mode is optional and assumes every sale is collected and every operating expense is paid in the same month. It does not measure actual cash flow.";
  cashHelp.dataset.ar =
    "الوضع المبسط اختياري ويفترض تحصيل كل المبيعات وسداد كل المصروفات التشغيلية في الشهر نفسه. لا يقيس التدفق النقدي الفعلي.";
  const cogsLabel = uiNode("label");
  cogsLabel.dataset.en = "COGS accounting basis";
  cogsLabel.dataset.ar = "أساس تكلفة البضاعة المحاسبي";
  cogsLabel.htmlFor = "cogs-basis";
  const cogs = uiNode("select");
  cogs.id = "cogs-basis";
  [
    [
      "separate",
      "Separate accounting basis (may include fixed production costs)",
      "أساس محاسبي مستقل (قد يشمل تكاليف إنتاج ثابتة)",
    ],
    [
      "subset_of_variable",
      "COGS is included within variable cost per unit",
      "تكلفة البضاعة جزء من التكلفة المتغيرة للوحدة",
    ],
  ].forEach(([v, en, ar]) => {
    const o = uiNode("option");
    o.value = v;
    o.dataset.en = en;
    o.dataset.ar = ar;
    cogs.append(o);
  });
  cogs.onchange = () => {
    investment.inputs.cogs_basis = cogs.value;
    scheduleFinance();
  };
  const calculate = uiNode("button", "btn btn-primary");
  calculate.id = "finance-recalculate";
  calculate.dataset.en = "Calculate my plan";
  calculate.dataset.ar = "احسب خطتي";
  calculate.onclick = () => calculateFinance(true);
  panels[2].append(modeLabel, mode, cashHelp, cogsLabel, cogs, calculate);
  panels[2].append(sections[0]); // break-even/cash charts and their table
  panels[3].append(sections[1], sections[2]);
  const sensitivity = uiNode("figure", "finance-visual");
  sensitivity.id = "sensitivity-chart";
  sections[2].append(sensitivity);
  panels[4].append(sections[3]);
  panels[5].append(sections[5]);
  panels[6].append(sections[4], sections[6]);
  panels[6].prepend(sections[6].querySelector(".ai-disclosure"));
  layout.remove();
  INVESTMENT_SECTIONS.forEach((pair, i) => {
    const button = uiNode("button");
    button.id = "investment-tab-" + i;
    button.dataset.en = pair[0];
    button.dataset.ar = pair[1];
    button.setAttribute("role", "tab");
    button.setAttribute("aria-controls", "investment-panel-" + i);
    button.onclick = () => showInvestmentSection(i);
    button.onkeydown = (e) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      e.preventDefault();
      const dir = lang === "ar" ? -1 : 1,
        next =
          e.key === "Home"
            ? 0
            : e.key === "End"
              ? 6
              : (i + (e.key === "ArrowRight" ? dir : -dir) + 7) % 7;
      showInvestmentSection(next);
      document.getElementById("investment-tab-" + next).focus();
    };
    nav.append(button);
  });
  showInvestmentSection(investment.section || 0);
}
function showInvestmentSection(index, focus = false, persist = true) {
  index = Number.isInteger(index) && index >= 0 && index < 7 ? index : 0;
  investment.section = index;
  document
    .querySelectorAll(".investment-panel")
    .forEach((p, i) => (p.hidden = i !== index));
  document.querySelectorAll("#investment-nav button").forEach((b, i) => {
    b.setAttribute("aria-selected", String(i === index));
    b.tabIndex = i === index ? 0 : -1;
  });
  if (focus)
    document
      .getElementById("investment-nav")
      .scrollIntoView({ block: "start", behavior: "instant" });
  if (currentPlan && persist) saveSession();
}
