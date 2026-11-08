// Workspace navigation and integration. Existing endpoint and feature IDs remain stable.
matchMedia("(max-width: 767px)").addEventListener("change", (event) => {
  for (const id of ["fuller-path", "financing-route-guide"]) {
    const detail = document.getElementById(id);
    if (detail) detail.open = !event.matches;
  }
});
function localizeV2() {
  document
    .querySelectorAll("[data-en][data-ar]")
    .forEach((node) => (node.textContent = node.dataset[lang]));
  document
    .querySelectorAll("[data-placeholder-en]")
    .forEach(
      (n) =>
        (n.placeholder =
          lang === "ar" ? n.dataset.placeholderAr : n.dataset.placeholderEn),
    );
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document
    .getElementById("investment-nav")
    ?.setAttribute(
      "aria-label",
      uiText("Investment sections", "أقسام الاستثمار"),
    );
  document
    .getElementById("chatLauncher")
    .setAttribute(
      "aria-label",
      uiText("Open Khotwa Advisor", "افتح مستشار خطوة"),
    );
  const preview = document.getElementById("actual-preview");
  if (preview.tagName === "IMG")
    preview.src = "/static/product-preview-" + lang + ".webp";
  preview.alt = uiText(
    "Actual Khotwa dashboard · illustrative business, no customer evidence recorded",
    "لوحة خطوة الفعلية · مشروع توضيحي بلا أدلة عملاء مسجّلة",
  );
}
function enterWorkspace() {
  const fuller = document.getElementById("fuller-path");
  fuller.open = innerWidth >= 768;
  fuller.ontoggle = () => {
    if (fuller.open && currentPlan) requestPlanCharts();
  };
  if (!fundingData.length) loadFunding();
  document.body.classList.remove("focused-entry");
  document.getElementById("entry-back").hidden = true;
  document.body.classList.add("has-plan");
  document.querySelector(".input-card").hidden = true;
  document.getElementById("discovery-card").hidden = true;
  localizeV2();
  initInvestment();
  decoratePlanTasks();
  decorateRiskDimensions();
  renderFinanceIntegration();
  setTxt(
    "first-step-text",
    uiText(
      "Record customer feedback, separate interest from action, and choose the next experiment.",
      "سجّل ملاحظات العملاء وميّز الاهتمام عن السلوك واختر التجربة التالية.",
    ),
  );
  setTxt("lbl-firststep", uiText("Your validation workspace", "مساحة التحقق"));
  showInvestmentSection(investment.section || 0);
}
function decoratePlanTasks() {
  document.querySelectorAll("#day-grid .day-card").forEach((card, i) => {
    if (card.querySelector(".day-complete")) return;
    const label = uiNode("label", "day-complete"),
      check = uiNode("input");
    check.type = "checkbox";
    check.checked = investment.tasks.includes(i);
    check.onchange = () => {
      investment.tasks = check.checked
        ? [...investment.tasks, i]
        : investment.tasks.filter((n) => n !== i);
      saveSession();
    };
    label.append(
      check,
      document.createTextNode(
        uiText("Task complete · my record", "المهمة مكتملة · بسجلي"),
      ),
    );
    card.append(label);
  });
}
function decorateRiskDimensions() {
  let data = document.getElementById("path-data");
  if (!data) {
    data = uiNode("div", "table-wrap");
    data.id = "path-data";
    document.getElementById("steps-list").after(data);
  }
  table(
    "path-data",
    [
      uiText("Step", "الخطوة"),
      uiText("Days · planning estimate", "الأيام · تقدير تخطيطي"),
      uiText("Cost · AI estimate", "التكلفة · تقدير ذكاء اصطناعي"),
    ],
    (currentPlan.steps || []).map((s) => [
      s.action,
      s.timeline_days,
      money(s.estimated_cost_aed),
    ]),
  );
}
function setupV2() {
  setupInvestmentWorkspace();
  localizeV2();
  document.getElementById("editIdea").onclick = () => {
    const card = document.querySelector(".input-card");
    card.hidden = false;
    card.scrollIntoView({ behavior: motionBehavior() });
    document.getElementById("idea").focus({ preventScroll: true });
  };
  document.getElementById("preview-demo").onclick = () => {
    const idea = uiText("Neighbourhood service concept", "فكرة خدمة للحي");
    currentPlan = localPlan(
      idea,
      "Services & Maintenance",
      "residents",
      "5000",
      "Dubai",
      "Local service",
    );
    currentPlan._demo = true;
    showPlan(currentPlan);
    buildProof();
    saveSession();
  };
  document.getElementById("finance-form").onsubmit = (e) => {
    e.preventDefault();
    calculateFinance(true);
  };
  document.getElementById("contingency-mode").onchange = (e) => {
    investment.inputs.contingency_mode = e.target.value;
    scheduleFinance();
  };
  document.getElementById("reset-finance").onclick = () => {
    investment.inputs = investment.original
      ? structuredClone(investment.original)
      : {};
    financeResult = null;
    initInvestment();
    calculateFinance();
  };
  document.getElementById("seed-scenarios").onclick = () => {
    Object.keys(SCENARIOS).forEach(
      (k) =>
        (investment.scenarios[k] = illustrativeInputs(k, investment.inputs)),
    );
    renderScenarios();
    calculateFinance();
  };
  document.getElementById("reset-scenarios").onclick = () => {
    Object.keys(SCENARIOS).forEach(
      (k) =>
        (investment.scenarios[k] = illustrativeInputs(
          k,
          investment.original || {},
        )),
    );
    renderScenarios();
    calculateFinance();
  };
  document.getElementById("investment-to-proof").onclick = () => selectPanel(1);
  document.getElementById("investment-to-plan").onclick = () => selectPanel(3);
  document.getElementById("investment-pdf").onclick = exportInvestment;
  document.getElementById("investment-csv").onclick = exportFinanceCSV;
  document.getElementById("funding-search").oninput = renderFunding;
  document.getElementById("funding-filter").onchange = renderFunding;
  document.getElementById("newBtn").addEventListener("click", () => {
    document.querySelector(".input-card").hidden = true;
    setEntry(null);
    localizeV2();
  });
}
