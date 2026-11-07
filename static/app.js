let lang = "en",
  currentPlan = null,
  timelineChart,
  costChart;
let chatHistory = [];
let planVariants = { en: null, ar: null },
  selectedIdeaSource = "user_input";
const SESSION_KEY = "khotwa-business-session-v1";
let restoringSession = false;
function saveSession() {
  if (restoringSession) return;
  try {
    const form = {
      idea: document.getElementById("idea").value,
      idea_source: selectedIdeaSource,
      categoryIndex: document.getElementById("category").selectedIndex,
      user_type: document.getElementById("user_type").value,
      budget: document.getElementById("budget").value,
      region: document.getElementById("region").value,
      context: document.getElementById("context").value,
    };
    const plan = currentPlan ? JSON.parse(JSON.stringify(currentPlan)) : null;
    if (plan) {
      delete plan.proof_summary;
      if (plan.state) delete plan.state.evidence;
    }
    const variants = JSON.parse(JSON.stringify(planVariants));
    for (const key of ["en", "ar"]) {
      if (variants[key]) {
        delete variants[key].proof_summary;
        if (variants[key].state) delete variants[key].state.evidence;
      }
    }
    const proof = currentPlan
      ? [...document.querySelectorAll("#proof-table tr")]
          .slice(1)
          .map((row) => {
            const interest = row.querySelector(".p-int")?.value || "",
              precommitment = row.querySelector(".p-pre")?.value || "",
              raw = row.querySelector(".p-price")?.value || "";
            return {
              interest,
              precommitment,
              price:
                raw !== "" && Number.isFinite(Number(raw)) && Number(raw) >= 0
                  ? raw
                  : "",
            };
          })
      : [];
    const selected = document.querySelector(
      '#result-nav [aria-selected="true"]',
    );
    const activePanel = selected
      ? Number(selected.id.replace("result-tab-", ""))
      : 0;
    const snapshot = JSON.stringify({
      version: 1,
      lang,
      theme:
        document.documentElement.getAttribute("data-theme") === "dark"
          ? "dark"
          : "light",
      form,
      plan,
      variants,
      activePanel,
      proof,
      investment: investmentRecovery(),
    });
    // If an idea or generated plan contains contact details or a credential, keep it in memory only.
    if (
      /(?:gsk_|sk-)[A-Za-z0-9_-]{16,}|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|(?:\+?971|0)5[0-9\s().-]{8,}/i.test(
        snapshot,
      )
    ) {
      sessionStorage.removeItem(SESSION_KEY);
      return;
    }
    sessionStorage.setItem(SESSION_KEY, snapshot);
  } catch (e) {
    console.warn("Session recovery unavailable", e && e.name);
  }
}
function restoreSession() {
  let saved;
  try {
    saved = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
  } catch (e) {
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch (_) {}
    return;
  }
  if (
    !saved ||
    saved.version !== 1 ||
    !saved.form ||
    typeof saved.form !== "object"
  )
    return;
  restoringSession = true;
  try {
    lang = saved.lang === "ar" ? "ar" : "en";
    if (saved.theme === "dark")
      document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    document.getElementById("themeBtn").textContent =
      saved.theme === "dark" ? "\u2600" : "\u263e";
    applyLang();
    const form = saved.form;
    if (form.idea && !saved.plan) setEntry("existing");
    document.getElementById("idea").value =
      typeof form.idea === "string" ? form.idea : "";
    selectedIdeaSource =
      form.idea_source === "ai_suggestion_selected"
        ? "ai_suggestion_selected"
        : "user_input";
    const category = document.getElementById("category");
    if (
      Number.isInteger(form.categoryIndex) &&
      form.categoryIndex >= 0 &&
      form.categoryIndex < category.options.length
    ) {
      category.selectedIndex = form.categoryIndex;
      category.dataset.touched = form.categoryIndex ? "true" : "";
    }
    for (const id of ["user_type", "region", "context"]) {
      const field = document.getElementById(id);
      if (
        typeof form[id] === "string" &&
        [...field.options].some((o) => o.value === form[id])
      )
        field.value = form[id];
    }
    const budget = document.getElementById("budget");
    if (Number.isFinite(Number(form.budget))) budget.value = form.budget;
    updateBudget(budget.value);
    if (
      saved.plan &&
      typeof saved.plan === "object" &&
      !Array.isArray(saved.plan) &&
      saved.plan.opportunity_score
    ) {
      if (saved.variants && typeof saved.variants === "object")
        planVariants = {
          en: saved.variants.en || null,
          ar: saved.variants.ar || null,
        };
      currentPlan = saved.plan;
      showPlan(currentPlan);
      restoreInvestment(saved.investment);
      initInvestment();
      if (saved.investment) calculateFinance();
      buildProof();
      if (Array.isArray(saved.proof))
        saved.proof.slice(0, 10).forEach((entry, i) => {
          const row = document.querySelectorAll("#proof-table tr")[i + 1];
          if (!row || !entry || typeof entry !== "object") return;
          if (["yes", "maybe", "no"].includes(entry.interest))
            row.querySelector(".p-int").value = entry.interest;
          if (
            ["interest", "intent", "reservation", "payment", "repeat"].includes(
              entry.precommitment,
            )
          )
            row.querySelector(".p-pre").value = entry.precommitment;
          if (
            entry.price !== "" &&
            Number.isFinite(Number(entry.price)) &&
            Number(entry.price) >= 0
          )
            row.querySelector(".p-price").value = entry.price;
        });
      calcProof();
      selectPanel(
        Number.isInteger(saved.activePanel) &&
          saved.activePanel >= 0 &&
          saved.activePanel < PANEL_ORDER.length
          ? saved.activePanel
          : 0,
      );
    }
    styleCharts();
  } catch (e) {
    console.warn("Session recovery failed", e && e.name);
    currentPlan = null;
    document.getElementById("results").style.display = "none";
  } finally {
    restoringSession = false;
  }
}
function escapeHtml(value) {
  return String(value == null ? "" : value).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
}
function escapePlan(value) {
  if (Array.isArray(value)) return value.map(escapePlan);
  if (value && typeof value === "object") {
    const out = Object.create(null);
    Object.keys(value).forEach((k) => (out[k] = escapePlan(value[k])));
    return out;
  }
  return typeof value === "string" ? escapeHtml(value) : value;
}
function setEntry(mode) {
  document
    .getElementById("need-idea")
    .setAttribute("aria-pressed", String(mode === "discover"));
  document
    .getElementById("have-idea")
    .setAttribute("aria-pressed", String(mode === "existing"));
  document.getElementById("discovery-card").hidden = mode !== "discover";
  document.querySelector(".input-card").hidden = mode !== "existing";
  document.getElementById("need-idea").className =
    "btn " + (mode === "discover" ? "btn-primary" : "btn-light");
  document.getElementById("have-idea").className =
    "btn " + (mode === "existing" ? "btn-primary" : "btn-light");
}
function discoveryFields() {
  return {
    skills: document.getElementById("d-skills").value.trim(),
    interests: document.getElementById("d-interests").value.trim(),
    experience: document.getElementById("d-experience").value.trim(),
    budget: document.getElementById("d-budget").value,
    region: document.getElementById("d-region").value,
    context: document.getElementById("d-context").value,
    time_available: document.getElementById("d-time").value.trim(),
    lang,
  };
}
async function discoverIdeas() {
  const btn = document.getElementById("discover-btn"),
    error = document.getElementById("discover-error"),
    box = document.getElementById("discovery-results"),
    profile = discoveryFields();
  localizedStatus("discover-error", "", "");
  if (
    [
      profile.skills,
      profile.interests,
      profile.experience,
      profile.budget,
      profile.time_available,
    ].some((v) => !String(v).trim())
  ) {
    localizedStatus(
      "discover-error",
      "Complete all founder profile fields first.",
      "أكمل جميع حقول ملفك أولاً.",
    );
    return;
  }
  btn.disabled = true;
  box.replaceChildren();
  startLoader(true);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 45000);
  try {
    const resp = await fetch("/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
      signal: ctrl.signal,
    });
    const data = await resp.json();
    if (!resp.ok || !Array.isArray(data.ideas) || data.ideas.length !== 3)
      throw Error("unavailable");
    data.ideas.forEach((idea) => {
      const card = document.createElement("article");
      card.className = "idea-card";
      const h = document.createElement("h3");
      h.textContent = idea.name;
      card.appendChild(h);
      if (profile.region && profile.region !== "UAE-wide") {
        const marketBadge = document.createElement("span");
        marketBadge.className = "source-badge input profile-match";
        marketBadge.textContent =
          (lang === "ar" ? "سوقك المختار: " : "Your selected market: ") +
          (T[lang].regions[profile.region] || profile.region);
        card.appendChild(marketBadge);
      }
      [
        [lang === "ar" ? "لماذا تناسبك" : "Why it fits", idea.fit],
        [lang === "ar" ? "عميل محتمل" : "Likely customer", idea.customer],
        [
          lang === "ar" ? "اختبار أول منخفض التكلفة" : "Low-cost first test",
          idea.first_test,
        ],
        [lang === "ar" ? "فرضية للتحقق" : "Main assumption", idea.assumption],
      ].forEach(([label, value]) => {
        const p = document.createElement("p"),
          b = document.createElement("b");
        b.textContent = label + ": ";
        p.append(b, document.createTextNode(value));
        card.appendChild(p);
      });
      const badge = document.createElement("span");
      badge.className = "source-badge assumption";
      badge.textContent =
        lang === "ar" ? "فرضية ذكاء اصطناعي" : "AI ASSUMPTION";
      card.appendChild(badge);
      const go = document.createElement("button");
      go.className = "btn btn-primary";
      go.textContent =
        lang === "ar" ? "استكشف هذه الفكرة" : "Explore this idea";
      go.onclick = () => {
        setEntry("existing");
        document.getElementById("idea").value = idea.name;
        document.getElementById("region").value = profile.region;
        document.getElementById("context").value = profile.context;
        const budget = Number(profile.budget);
        if (Number.isFinite(budget) && budget >= 0) {
          const range = document.getElementById("budget");
          range.min = Math.min(Number(range.min), budget);
          range.max = Math.max(Number(range.max), budget);
          range.step = "1";
          range.value = budget;
          updateBudget(range.value);
        }
        const category = document.getElementById("category");
        const idx = T.en.categories.findIndex(
          (c) => c.toLowerCase() === String(idea.category || "").toLowerCase(),
        );
        if (idx >= 0) {
          category.selectedIndex = idx + 1;
          category.dataset.touched = "true";
        } else suggestCategory();
        generate();
      };
      card.appendChild(go);
      box.appendChild(card);
    });
  } catch (e) {
    localizedStatus(
      "discover-error",
      "Idea suggestions are unavailable right now. Please try again.",
      "تعذر اقتراح أفكار الآن. حاول مجدداً.",
    );
  } finally {
    clearTimeout(timer);
    btn.disabled = false;
    stopLoader();
  }
}

const PANEL_ORDER = [
  "Overview",
  "Validate",
  "Customers",
  "7-Day Plan",
  "Risks",
  "Pitch",
  "Resources",
  "Investment",
];
const PANEL_IDS = {
  Overview: ["lbl-firststep", "lbl-overview", "lbl-score", "lbl-decision"],
  Validate: [
    "lbl-bys",
    "lbl-test",
    "lbl-proof",
    "lbl-validate",
    "lbl-questions",
    "lbl-wa",
    "lbl-qr",
  ],
  Customers: ["lbl-personas", "lbl-map", "lbl-why"],
  "7-Day Plan": ["lbl-7day", "lbl-fuller"],
  Risks: ["lbl-risks", "lbl-donot"],
  Pitch: ["lbl-passport", "lbl-share", "lbl-pitches"],
  Resources: ["lbl-report", "lbl-resources", "lbl-chat"],
  Investment: ["investment-guide"],
};
function setupDashboard() {
  const root = document.getElementById("results"),
    nav = document.getElementById("result-nav");
  if (root.dataset.dashboard) return;
  root.dataset.dashboard = "1";
  PANEL_ORDER.forEach((name, index) => {
    const panel = document.createElement("section");
    panel.className = "dashboard-panel";
    panel.id = "panel-" + index;
    panel.hidden = index !== 0;
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", "result-tab-" + index);
    PANEL_IDS[name].forEach((id) => {
      const node = document.getElementById(id);
      if (node) {
        let parent = node;
        while (parent.parentElement !== root && parent.parentElement)
          parent = parent.parentElement;
        if (parent.parentElement === root) panel.appendChild(parent);
      }
    });
    root.appendChild(panel);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.id = "result-tab-" + index;
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-controls", panel.id);
    btn.setAttribute("aria-selected", index === 0 ? "true" : "false");
    btn.tabIndex = index === 0 ? 0 : -1;
    btn.textContent = name;
    btn.onclick = () => selectPanel(index);
    btn.onkeydown = (e) => {
      if (["ArrowRight", "ArrowLeft", "Home", "End"].includes(e.key)) {
        e.preventDefault();
        const dir = lang === "ar" ? -1 : 1;
        const next =
          e.key === "Home"
            ? 0
            : e.key === "End"
              ? PANEL_ORDER.length - 1
              : (index +
                  (e.key === "ArrowRight" ? dir : -dir) +
                  PANEL_ORDER.length) %
                PANEL_ORDER.length;
        selectPanel(next);
        nav.children[next].focus();
      }
    };
    nav.appendChild(btn);
  });
}
function updateDashboardLabels() {
  const names =
    lang === "ar"
      ? [
          "نظرة عامة",
          "التحقق",
          "العملاء",
          "خطة ٧ أيام",
          "المخاطر",
          "العرض",
          "المصادر",
          "الاستثمار",
        ]
      : PANEL_ORDER;
  document
    .querySelectorAll("#result-nav button")
    .forEach((b, i) => (b.textContent = names[i]));
  document
    .querySelectorAll(".dashboard-panel")
    .forEach((p, i) => p.setAttribute("aria-label", names[i]));
}
function selectPanel(index) {
  if (index === 7) {
    initInvestment();
    if (!financeResult) calculateFinance();
  }
  document
    .querySelectorAll(".dashboard-panel")
    .forEach((p, i) => (p.hidden = i !== index));
  document.querySelectorAll("#result-nav button").forEach((b, i) => {
    b.setAttribute("aria-selected", i === index ? "true" : "false");
    b.tabIndex = i === index ? 0 : -1;
  });
  document.getElementById("result-tab-" + index).scrollIntoView({
    block: "nearest",
    inline: "center",
    behavior: "instant",
  });
  renderJourney();
  saveSession();
}
function ensurePlanState(plan, inputs) {
  const r = plan.readiness_report || {},
    s = plan.state || {};
  plan.state = {
    idea: inputs.idea,
    idea_source:
      inputs.idea_source === "ai_suggestion_selected"
        ? "ai_suggestion_selected"
        : "user_input",
    category: inputs.category,
    target_customer:
      (inputs.user_type && T[lang].userTypes[inputs.user_type]) ||
      r.target_customer ||
      s.target_customer ||
      "",
    target_customer_source: inputs.user_type ? "user_input" : "ai_assumption",
    region: inputs.region,
    context: inputs.context,
    customer_type: inputs.user_type,
    user_budget_aed: Number(inputs.budget) || 0,
    suggested_test_price_aed: Number(s.suggested_test_price_aed) || 0,
    estimated_test_cost_aed:
      Number(s.estimated_test_cost_aed || r.estimated_first_test_cost_aed) || 0,
    opportunity_score: plan.opportunity_score || {},
    decision: (plan.decision_engine || {}).decision || "",
    first_action: plan.first_step_today || "",
    evidence: s.evidence || { status: "not_validated", responses: 0 },
  };
  plan._category = inputs.category;
  plan._region = inputs.region;
  plan._context = inputs.context;
  plan._budget = inputs.budget;
  plan._user_type = inputs.user_type;
  if (r) {
    r.idea = inputs.idea;
    r.target_customer = plan.state.target_customer;
    r.best_first_action = plan.state.first_action;
  }
  if (plan.founder_passport)
    plan.founder_passport.first_action = plan.state.first_action;
  return plan;
}

function fillSelects() {
  const t = T[lang];
  const selected = {
    categoryIndex: document.getElementById("category").selectedIndex,
    category: document.getElementById("category").value,
    user_type: document.getElementById("user_type").value,
    region: document.getElementById("region").value,
    context: document.getElementById("context").value,
  };
  const c = document.getElementById("category");
  c.replaceChildren();
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = lang === "ar" ? "اختر الفئة" : "Choose a category";
  c.appendChild(blank);
  t.categories.forEach((x) => {
    const o = document.createElement("option");
    o.textContent = x;
    c.appendChild(o);
  });
  Array.from(c.options)
    .slice(1)
    .forEach((option, index) => {
      option.value = T.en.categories[index];
    });
  const u = document.getElementById("user_type");
  u.replaceChildren();
  Object.keys(t.userTypes).forEach((k) => {
    const o = document.createElement("option");
    o.value = k;
    o.textContent = t.userTypes[k];
    u.appendChild(o);
  });
  const rg = document.getElementById("region");
  rg.replaceChildren();
  Object.keys(t.regions).forEach((k) => {
    const o = document.createElement("option");
    o.value = k;
    o.textContent = t.regions[k];
    rg.appendChild(o);
  });
  const cx = document.getElementById("context");
  cx.replaceChildren();
  Object.keys(t.contexts).forEach((k) => {
    const o = document.createElement("option");
    o.value = k;
    o.textContent = t.contexts[k];
    cx.appendChild(o);
  });
  if (selected.categoryIndex > 0) c.selectedIndex = selected.categoryIndex;
  u.value = selected.user_type;
  rg.value = selected.region || "UAE-wide";
  cx.value = selected.context || "Not sure";
  ["region", "context"].forEach((name) => {
    const target = document.getElementById("d-" + name),
      source = document.getElementById(name),
      previous = target.value;
    target.replaceChildren(
      ...[...source.options].map((o) => o.cloneNode(true)),
    );
    target.value = previous || source.value;
  });
}
function suggestCategory() {
  const c = document.getElementById("category");
  if (c.dataset.touched) return;
  const idea = document.getElementById("idea").value.toLowerCase(),
    context = document.getElementById("context").value;
  let key = "";
  if (
    /wash|clean|repair|maintenance|غسيل|تنظيف|صيانة/.test(idea) ||
    context === "Local service"
  )
    key = "Services & Maintenance";
  else if (context === "Food & beverage") key = "Food & Catering";
  else if (context === "Online") key = "Technology & Digital";
  else if (context === "Retail") key = "Retail & Trading";
  const i = T.en.categories.indexOf(key);
  if (i >= 0) c.selectedIndex = i + 1;
  document.getElementById("category-hint").textContent = key
    ? lang === "ar"
      ? "اقتراح تلقائي — يمكنك تغييره."
      : "Suggested from your idea — you can change it."
    : lang === "ar"
      ? "اختر الفئة المناسبة."
      : "Choose the category that fits your idea.";
}
document.getElementById("idea").addEventListener("input", suggestCategory);
document.getElementById("context").addEventListener("change", suggestCategory);
function fillDemos() {
  const d = document.getElementById("demo-row");
  d.replaceChildren();
  DEMOS[lang].forEach((ex) => {
    const b = document.createElement("button");
    b.className = "demo-chip";
    b.textContent = ex;
    b.onclick = () => {
      document.getElementById("idea").value = ex;
      suggestCategory();
    };
    d.appendChild(b);
  });
}
function fillSuggested() {
  const b = document.getElementById("suggested");
  b.replaceChildren();
  T[lang].suggested.forEach((q) => {
    const x = document.createElement("button");
    x.className = "chip";
    x.textContent = q;
    x.onclick = () => {
      document.getElementById("chat-input").value = q;
      askQuestion();
    };
    b.appendChild(x);
  });
}
function renderResources(region) {
  const box = document.getElementById("regional-resource");
  if (!box) return;
  box.replaceChildren();
  if (region === "Abu Dhabi" || region === "Al Ain")
    [
      [
        lang === "ar" ? "تم — خدمات حكومة أبوظبي" : "TAMM",
        "https://www.tamm.abudhabi/",
      ],
      [
        lang === "ar"
          ? "دائرة التنمية الاقتصادية في أبوظبي"
          : "Abu Dhabi Department of Economic Development",
        "https://www.added.gov.ae/en/set-up/establish-your-business",
      ],
    ].forEach(([name, url]) => {
      const row = document.createElement("div"),
        icon = document.createElement("span"),
        a = document.createElement("a");
      row.className = "res-link";
      icon.textContent = "📍";
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = name;
      row.append(icon, a);
      box.appendChild(row);
    });
}

function applyLang() {
  const t = T[lang];
  document.title =
    lang === "ar"
      ? "خطوة — من الفكرة إلى الخطوة الأولى."
      : "Khotwa — From idea to first step.";
  document.querySelector('meta[name="description"]').content =
    lang === "ar"
      ? "خطوة تساعد مؤسسي المشاريع في الإمارات على اكتشاف فكرة واختبار طلب العملاء واتخاذ الخطوة الأولى. أدوات بالعربية والإنجليزية."
      : "Khotwa (خطوة) helps UAE founders discover an idea, test real customer demand, and take their first step. Bilingual tools in English and Arabic.";
  if (currentPlan && currentPlan._local) {
    const old = currentPlan;
    currentPlan = localPlan(
      (old.readiness_report || {}).idea || currentIdea(),
      old._category || "",
      old._user_type || "",
      old._budget ?? 10000,
      old._region || "UAE-wide",
      old._context || "Not sure",
    );
    currentPlan.proof_summary = old.proof_summary;
    currentPlan.state.evidence =
      (old.state || {}).evidence || currentPlan.state.evidence;
  }
  document.getElementById("body").className = lang === "ar" ? "rtl" : "";
  document.documentElement.lang = lang;
  const set = (id, v) => {
    document.getElementById(id).textContent = v;
  };
  set(
    "category-hint",
    lang === "ar"
      ? "اختر الفئة؛ تظهر الاقتراحات أثناء الكتابة."
      : "Choose a category; suggestions appear as you type.",
  );
  document
    .querySelectorAll(".p-freq")
    .forEach((el) => (el.placeholder = lang === "ar" ? "أسبوعياً" : "weekly"));
  [
    ["themeBtn", "Toggle theme", "تغيير المظهر"],
    ["entry-choice", "Choose how to start", "اختر طريقة البدء"],
    ["result-nav", "Plan sections", "أقسام الخطة"],
    ["timeline-chart", "Timeline per step", "مدة كل خطوة"],
    ["cost-chart", "Cost breakdown", "تفصيل التكلفة"],
    ["chatLauncher", "Open Khotwa Advisor", "افتح مستشار خطوة"],
    ["chatPanel", "Khotwa Advisor", "مستشار خطوة"],
    ["chatClose", "Close advisor", "أغلق المستشار"],
    ["chat-input", "Type your question", "اكتب سؤالك"],
    ["sendBtn", "Send", "إرسال"],
  ].forEach(([id, en, ar]) =>
    document
      .getElementById(id)
      .setAttribute("aria-label", lang === "ar" ? ar : en),
  );

  set("brand-name", lang === "ar" ? "خطوة" : "Khotwa");
  set("brand-sub", lang === "ar" ? "Khotwa" : "خطوة");
  set("foot-title", lang === "ar" ? "خطوة · Khotwa" : "Khotwa · خطوة");
  document
    .querySelector(".site-nav")
    .setAttribute("aria-label", lang === "ar" ? "خطوة" : "Khotwa");
  set("title", t.title);
  set("subtitle", t.subtitle);
  set("lbl-idea", t.idea);
  set("lbl-cat", t.cat);
  set("lbl-usertype", t.usertype);
  set("lbl-region", t.regionLabel);
  set("lbl-context", t.contextLabel);
  set("genBtn", t.gen);
  set("pdfBtn", t.pdf);
  set("newBtn", t.newidea);
  set("lbl-overview", t.overview);
  set("lbl-firststep", t.firststep);
  set("lbl-score", t.score);
  set("lbl-test", t.testplan);
  set("lbl-proof", t.proof);
  set("proof-help", t.proofHelp);
  set("lbl-7day", t.sevenday);
  set("lbl-validate", t.validate);
  set("lbl-questions", t.questions);
  set("lbl-wa", t.wa);
  set("waBtn", t.copy);
  set("lbl-report", t.report);
  set("lbl-fuller", t.fuller);
  set("lbl-resources", t.resources);
  set("lbl-chat", t.chat);
  set("sendBtn", t.send);
  set("lbl-timeline", t.timeline);
  set("lbl-cost", t.cost);
  set("disclaimer", t.disclaimer);
  document.getElementById("federal-resource").textContent =
    lang === "ar"
      ? "حكومة الإمارات — خدمات وإرشادات الأعمال"
      : "UAE Government — business services and guidance";
  document.getElementById("idea").placeholder = t.placeholder;
  document.getElementById("chat-input").placeholder = t.chatPlaceholder;
  document.getElementById("langBtn").textContent = t.langBtn;
  var kt = document.getElementById("kicker-text");
  if (kt && t.kicker) kt.textContent = t.kicker;
  var ft = document.getElementById("foot-text");
  if (ft && t.foot) ft.textContent = t.foot;
  var setIf = function (id, v) {
    var el = document.getElementById(id);
    if (el && v != null) el.textContent = v;
  };
  setIf("pitch", t.pitch);
  setIf("lbl-decision", t.lblDecision);
  setIf("lbl-donot", t.lblDonot);
  setIf("lbl-donot-bad", t.lblDonotBad);
  setIf("lbl-donot-good", t.lblDonotGood);
  setIf("lbl-share", t.lblShare);
  setIf("proofDemoBtn", t.proofDemo);
  setIf("proofCsvBtn", t.proofCsv);
  setIf("proofClearBtn", t.proofClear);
  setIf("shareBtn", t.copy);
  setIf("hchip1", t.hchip1);
  setIf("hchip2", t.hchip2);
  setIf("hchip3", t.hchip3);
  setIf("hero-badge", t.heroBadge);
  setIf("fsb1", t.fsb1);
  setIf("fsb2", t.fsb2);
  setIf("fsb3", t.fsb3);
  setIf("tb1", t.tb1);
  setIf("tb2", t.tb2);
  setIf("tb3", t.tb3);
  setIf("tb4", t.tb4);
  setIf("lbl-why", t.lblWhy);
  setIf("why-intro", t.whyIntro);
  setIf("foot-collab", t.footCollab);
  setIf("hero-start", t.heroStart);
  setIf("hero-demo", t.heroDemo);
  setIf("cl-text", t.clText);
  setIf("chat-title", t.chatTitle);
  setIf("chat-sub", t.chatSub);
  setIf("chat-note", t.chatNote);
  setIf("chat-foot", t.chatFoot);
  document.getElementById("chat-input").placeholder = t.chatPlaceholder;
  setIf("lbl-bys", t.lblBys);
  setIf("bys-l1", t.bysL1);
  setIf("bys-l2", t.bysL2);
  setIf("bys-l3", t.bysL3);
  setIf("lbl-passport", t.lblPassport);
  setIf("lbl-personas", t.lblPersonas);
  setIf("lbl-risks", t.lblRisks);
  setIf("lbl-pitches", t.lblPitches);
  setIf("lbl-map", t.lblMap);
  setIf("lbl-qr", t.lblQr);
  setIf("qr-help", t.qrHelp);
  setIf("qr-cap", t.qrCap);
  fillSelects();
  fillDemos();
  fillSuggested();
  renderJourney();
  updateBudget(document.getElementById("budget").value);
  setIf("waOpenBtn", lang === "ar" ? "افتح واتساب" : "Open WhatsApp");
  setIf("passportCopyBtn", t.copy);
  setIf(
    "score-note",
    lang === "ar"
      ? "مبنية على افتراضات — حدّثها بأدلة حقيقية من العملاء."
      : "Based on assumptions — update with real customer evidence.",
  );
  setIf(
    "segments-note",
    lang === "ar"
      ? "أمثلة لشرائح تحتاج إلى اختبار — فرضية ذكاء اصطناعي"
      : "Assumed segments to test — AI assumption",
  );
  setIf(
    "need-idea",
    lang === "ar" ? "أحتاج فكرة مشروع" : "I need a business idea",
  );
  setIf(
    "have-idea",
    lang === "ar" ? "لدي فكرة بالفعل" : "I already have an idea",
  );
  setIf(
    "discovery-title",
    lang === "ar" ? "ثلاث أفكار للاختبار" : "Find three ideas to test",
  );
  setIf(
    "discovery-caveat",
    lang === "ar"
      ? "هذه اقتراحات غير مثبتة. اختبر الطلب قبل الإنفاق."
      : "These are unvalidated suggestions. Test customer demand before spending.",
  );
  setIf(
    "discover-btn",
    lang === "ar" ? "اقترح ثلاث أفكار" : "Suggest three ideas",
  );
  [
    ["d-skills-label", "Skills", "المهارات"],
    ["d-interests-label", "Interests", "الاهتمامات"],
    ["d-experience-label", "Experience", "الخبرة"],
    [
      "d-budget-label",
      "Approximate budget (AED)",
      "الميزانية التقريبية (درهم)",
    ],
    ["d-region-label", "UAE market", "سوق الإمارات"],
    ["d-context-label", "Preferred business type", "نوع المشروع المفضل"],
    ["d-time-label", "Time available each week", "الوقت المتاح أسبوعياً"],
  ].forEach(([id, en, ar]) => setIf(id, lang === "ar" ? ar : en));
  const proof = document.getElementById("proof-table");
  if (proof && proof.rows.length) {
    proof
      .querySelectorAll("th")
      .forEach(
        (el, i) =>
          (el.textContent =
            i === 5
              ? lang === "ar"
                ? "قوة الدليل"
                : "Evidence strength"
              : t.proofCols[i] || ""),
      );
    proof.querySelectorAll(".p-int").forEach((el) => {
      el.querySelector("[value=yes]").textContent = t.interested;
      el.querySelector("[value=maybe]").textContent = t.maybe;
      el.querySelector("[value=no]").textContent = t.no;
    });
    proof.querySelectorAll(".p-pre").forEach((el) => {
      [
        ["interest", "اهتمام فقط", "Sounds interesting"],
        ["intent", "نية شراء معلنة", "Stated intent to buy"],
        ["reservation", "حجز بلا دفع", "No-payment reservation"],
        ["payment", "دفع فعلي", "Actual payment"],
        ["repeat", "عميل متكرر", "Repeat customer"],
      ].forEach(
        ([value, ar, en]) =>
          (el.querySelector('[value="' + value + '"').textContent =
            lang === "ar" ? ar : en),
      );
    });
    calcProof();
  }
  if (currentPlan) {
    showPlan(currentPlan);
    if (currentPlan._local)
      localizedStatus("error", T.en.chatFail, T.ar.chatFail);
  } else renderResources(document.getElementById("region").value);
  polishLanguage();
  relocalizeStatuses();
}

function toggleLang() {
  const target = lang === "en" ? "ar" : "en";
  if (
    currentPlan &&
    !currentPlan._local &&
    planVariants[target] &&
    planVariants[target].state?.idea === currentPlan.state?.idea
  )
    currentPlan = JSON.parse(JSON.stringify(planVariants[target]));
  lang = target;
  applyLang();
  localizeV2();
  saveSession();
}
function updateBudget(v) {
  const l = lang === "ar" ? "الميزانية — " : "Budget — ";
  document.getElementById("budget-label").textContent = l + formatAED(v);
}

async function generate() {
  const idea = document.getElementById("idea").value.trim();
  if (!idea) {
    localizedStatus("error", T.en.emptyIdea || "", T.ar.emptyIdea || "");
    return;
  }
  if (!document.getElementById("category").value) {
    localizedStatus(
      "error",
      "Choose a category first.",
      "اختر فئة المشروع أولاً.",
    );
    return;
  }
  document.getElementById("genBtn").disabled = true;
  document.getElementById("genBtn").textContent = T[lang].building;
  localizedStatus("error", "", "");
  document.getElementById("results").style.display = "none";
  startLoader();
  var category = document.getElementById("category").value,
    user_type = document.getElementById("user_type").value,
    budget = document.getElementById("budget").value,
    region = document.getElementById("region").value,
    context = document.getElementById("context").value;
  try {
    var ctrl = new AbortController();
    var to = setTimeout(function () {
      ctrl.abort();
    }, 45000);
    var resp = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        idea,
        idea_source: selectedIdeaSource,
        lang,
        category,
        user_type,
        budget,
        region,
        context,
      }),
      signal: ctrl.signal,
    });
    clearTimeout(to);
    var plan = null;
    try {
      plan = await resp.json();
    } catch (pe) {
      plan = null;
    }
    if (!plan || plan.error || !plan.opportunity_score) {
      plan = localPlan(idea, category, user_type, budget, region, context);
    }
    const alternate = plan._alternate_plan;
    delete plan._alternate_plan;
    ensurePlanState(plan, {
      idea,
      idea_source: selectedIdeaSource,
      category,
      user_type,
      budget,
      region,
      context,
    });
    planVariants = { en: null, ar: null };
    if (!plan._local && alternate && alternate.opportunity_score) {
      planVariants[lang] = JSON.parse(JSON.stringify(plan));
      planVariants[lang === "en" ? "ar" : "en"] = alternate;
    }
    chatHistory = [];
    document.getElementById("chat-messages").replaceChildren();
    currentPlan = plan;
    showPlan(plan);
    selectPanel(0);
    buildProof();
    if (plan._local) localizedStatus("error", T.en.chatFail, T.ar.chatFail);
  } catch (e) {
    console.warn("generate failed, using local plan:", e && e.name);
    try {
      currentPlan = ensurePlanState(
        localPlan(idea, category, user_type, budget, region, context),
        {
          idea,
          idea_source: selectedIdeaSource,
          category,
          user_type,
          budget,
          region,
          context,
        },
      );
      planVariants = { en: null, ar: null };
      chatHistory = [];
      document.getElementById("chat-messages").replaceChildren();
      showPlan(currentPlan);
      selectPanel(0);
      buildProof();
      localizedStatus("error", T.en.chatFail, T.ar.chatFail);
    } catch (e2) {
      console.error("local plan failed", e2);
      localizedStatus("error", T.en.error, T.ar.error);
    }
  } finally {
    document.getElementById("genBtn").disabled = false;
    document.getElementById("genBtn").textContent = T[lang].gen;
    stopLoader();
  }
}

function currency() {
  return "AED";
}
function pathMoney(value) {
  if (value == null || typeof value === "boolean") return null;
  const text = String(value).replace(/\bAED\b|,|\s/gi, "");
  if (!/^\d+(?:\.\d+)?$/.test(text)) return null;
  const number = Number(text);
  return Number.isFinite(number) && number <= 1e12
    ? Math.round(number * 100) / 100
    : null;
}
function syncPathCosts(plan) {
  const steps = Array.isArray(plan.steps) ? plan.steps : [],
    costs = steps.map((step) => pathMoney(step.estimated_cost_aed));
  steps.forEach((step, i) => (step.estimated_cost_aed = costs[i]));
  const total =
    costs.length && costs.every((c) => c !== null)
      ? Math.round(costs.reduce((a, b) => a + b, 0) * 100) / 100
      : null;
  const budget =
    pathMoney((plan.state || {}).user_budget_aed ?? plan._budget) ?? 0;
  plan.total_estimated_cost_aed = total;
  plan.estimated_budget_gap_aed =
    total === null ? null : Math.round(Math.max(0, total - budget) * 100) / 100;
  Object.assign((plan.readiness_report ||= {}), {
    estimated_setup_cost_aed: total,
    estimated_budget_gap_aed: plan.estimated_budget_gap_aed,
  });
}
function renderPathCosts(plan) {
  const ar = lang === "ar",
    total = plan.total_estimated_cost_aed,
    gap = plan.estimated_budget_gap_aed;
  const amount = (v) => formatAED(v);
  const costText =
    total === null
      ? ar
        ? "لم تُقدّر بعد"
        : "Not estimated yet"
      : amount(total) + " · " + (ar ? "تقدير ذكاء اصطناعي" : "AI ESTIMATE");
  const gapText =
    gap === null ? (ar ? "غير متاحة" : "Not available") : amount(gap);
  const rows = [
    [
      ar ? "ميزانيتك" : "Your budget",
      amount(Number((plan.state || {}).user_budget_aed) || 0) +
        " · " +
        (ar ? "إدخال المستخدم" : "USER INPUT"),
    ],
    [ar ? "تكلفة الإعداد المقدرة" : "Estimated setup cost", costText],
    [ar ? "الفجوة المقدرة" : "Estimated gap", gapText],
    [
      ar ? "المدة المقدرة" : "Estimated timeline",
      plan.total_timeline_days +
        " " +
        (ar
          ? Number(plan.total_timeline_days) === 1
            ? "يوم"
            : "أيام"
          : Number(plan.total_timeline_days) === 1
            ? "day"
            : "days") +
        " · " +
        (ar ? "تقدير تخطيطي" : "planning estimate"),
    ],
  ];
  const box = document.getElementById("plan-meta");
  box.replaceChildren();
  rows.forEach(([label, text]) => {
    const span = document.createElement("span");
    span.textContent = label + ": " + text;
    box.appendChild(span);
  });
  if (gap > 0) {
    const span = document.createElement("span");
    span.textContent = ar
      ? "تحقق من الطلب قبل زيادة إنفاقك."
      : "Validate demand before increasing your spending.";
    box.appendChild(span);
  }
  const note = document.createElement("span");
  note.textContent = ar
    ? "تقدير تخطيطي — تحقق من التكاليف والمتطلبات قبل الإنفاق."
    : "Planning estimate — verify costs and requirements before spending.";
  box.appendChild(note);
  const table = document.getElementById("report-table");
  rows.slice(1, 3).forEach(([label, text]) => {
    const row = table.insertRow();
    row.insertCell().textContent = label;
    row.cells[0].className = "k";
    row.insertCell().textContent = text;
  });
  const chart = document.getElementById("cost-chart");
  let chartNote = document.getElementById("cost-chart-note");
  if (!chartNote) {
    chartNote = document.createElement("p");
    chartNote.id = "cost-chart-note";
    chart.parentElement.appendChild(chartNote);
  }
  chart.hidden = total === null || total === 0;
  chartNote.hidden = !chart.hidden;
  chartNote.textContent =
    total === null
      ? ar
        ? "لم تُقدّر بعد"
        : "Not estimated yet"
      : amount(total);
}
function executionRisk(idea, category, ar) {
  const c = idea + " " + category;
  if (/social.?media|content|marketing|محتوى|تواصل اجتماعي|تسويق/i.test(c))
    return ar
      ? [
          "تحتاج قدرة إنتاج المحتوى وتأخر موافقات العملاء واتساق التسليم إلى اختبار.",
          "اختبر نموذج جدول محتوى ومسار الموافقات مع عملاء محتملين.",
        ]
      : [
          "Content-production capacity, client approval delays and delivery consistency need testing.",
          "Test a sample content calendar and approval workflow with prospective clients.",
        ];
  if (/food|cater|meal|restaurant|طعام|وجبة|وجبات|مطعم/i.test(c))
    return ar
      ? [
          "تحتاج قدرة إعداد الوجبات وتوقيتها واتساق التسليم إلى اختبار.",
          "ضع جدولاً افتراضياً للطلبات والإعداد دون تجهيز الطعام أو بيعه.",
        ]
      : [
          "Meal preparation capacity, timing and consistent delivery need testing.",
          "Map a sample order and preparation schedule without preparing or selling food.",
        ];
  if (
    /app\b|software|digital|platform|tool|website|no.?code|AI.?powered|رقمي|تطبيق|برمج|منصة|موقع|ذكاء اصطناعي/i.test(
      c,
    )
  )
    return ar
      ? [
          "تحتاج جهود التطوير وحماية البيانات وموثوقية المخرجات والدعم إلى اختبار.",
          "اختبر نموذجاً أولياً ونهج الخصوصية والدعم مع مستخدمين محتملين.",
        ]
      : [
          "Development effort, data handling, output reliability and customer support need testing.",
          "Test a prototype, privacy approach and support workflow with prospective users.",
        ];
  if (/mobile|car.?wash|delivery|clean|متنقل|غسيل|توصيل|تنظيف/i.test(c))
    return ar
      ? [
          "تحتاج أوقات التنقل والمواعيد ولوجستيات الخدمة إلى اختبار.",
          "اختبر مساراً وجدول مواعيد افتراضيين دون تشغيل.",
        ]
      : [
          "Travel time, scheduling and service logistics need testing.",
          "Test a mock route and appointment schedule without operating.",
        ];
  return ar
    ? [
        `تحتاج القدرة على تقديم ${idea} واتساق الجودة إلى اختبار.`,
        "حدد نموذجاً لمسار تقديم العرض قبل التشغيل.",
      ]
    : [
        `Delivery capacity and quality consistency for ${idea} need testing.`,
        "Map one sample delivery workflow before operating.",
      ];
}
function fixedLabel(value) {
  if (lang !== "ar") return value;
  return (
    {
      "Customer Demand": "طلب العملاء",
      "Cost / Financial": "التكلفة / المال",
      "Trust / Adoption": "الثقة / التبني",
      Execution: "التنفيذ",
      "Regulation / Compliance": "الأنظمة / الامتثال",
      Medium: "متوسط",
      High: "مرتفع",
      Low: "منخفض",
      Unknown: "غير محدد",
      "Ready to validate": "جاهز للتحقق",
      "Ready to validate, not operate": "جاهز للتحقق، لا للتشغيل",
      "Validate more": "تحقق أكثر",
      "Review pilot evidence": "راجع أدلة التجربة",
    }[value] || value
  );
}

function localPlan(idea, category, user_type, budget, region, context) {
  const L = T[lang].localPlan,
    ar = lang === "ar";
  const plan = {
    business_name_suggestion: idea,
    summary: L.summary.replace("{idea}", idea),
    idea_overview: {
      problem: ar
        ? "حاجة العملاء غير مؤكدة."
        : "Customer need remains unverified.",
      target_user: ar ? "شريحة محتملة للاختبار" : "Potential segment to test",
      solution: idea,
      impact: ar ? "منفعة محتملة للاختبار." : "Potential benefit to test.",
      evidence: ar
        ? "لم تُجمع أدلة من العملاء بعد."
        : "No customer evidence collected yet.",
      why_market: region + " · " + context,
    },
    first_step_today: ar
      ? "قابل خمسة عملاء محتملين واسأل عن البدائل الحالية بلا دفع."
      : "Interview five potential customers about current alternatives without taking payment.",
    opportunity_score: Object.fromEntries(
      [
        "local_fit",
        "clear_customer",
        "low_starting_cost",
        "easy_first_step",
        "growth_potential",
      ].map((k) => [
        k,
        {
          score: null,
          status: "not_assessed",
          source: "missing",
          reason: idea + ": " + L.sr,
          improve: L.si,
        },
      ]),
    ),
    readiness_report: {
      idea,
      target_customer: "",
      estimated_first_test_cost_aed: null,
      first_customer_channel: L.channel,
    },
    validation_questions: ar
      ? [
          "كيف تحل المشكلة الآن؟",
          "متى استخدمت بديلاً؟",
          "ما الذي يجعلك تجرب عرضاً جديداً؟",
          "ما مخاوف السعر أو الثقة؟",
          "هل تنضم لقائمة انتظار بلا دفع؟",
        ]
      : [
          "How do you solve this today?",
          "When did you last use an alternative?",
          "What would make you consider a new offer?",
          "What price or trust concern would stop you?",
          "Would you join a no-payment waitlist?",
        ],
    whatsapp_message: ar
      ? "مرحباً، أختبر فكرة " + idea + ". كيف تحل المشكلة الآن؟"
      : "Hi, I am testing " + idea + ". How do you solve this today?",
    _local: true,
  };
  aggregateScores(plan.opportunity_score);
  ensurePlanState(plan, { idea, category, user_type, budget, region, context });
  normalizeLocalPlan(plan, idea, region, context);
  return ensurePlanState(plan, {
    idea,
    category,
    user_type,
    budget,
    region,
    context,
  });
}

function contextSegmentNames(idea, target, category, ar) {
  const context = [idea, category].join(" ");
  const groups = [
    [
      /car|vehicle|driv|commut|ergonom|سيار|مركب|قياد/i,
      [
        "Daily commuters",
        "Ride-hailing drivers",
        "Fleet / company vehicle managers",
      ],
      [
        "المتنقلون يومياً",
        "سائقو خدمات نقل الركاب",
        "مديرو الأساطيل وسيارات الشركات",
      ],
    ],
    [
      /food|cater|meal|طعام|وجبات/i,
      ["Busy households", "Office lunch buyers", "Small event organisers"],
      ["الأسر المشغولة", "مشترو وجبات المكاتب", "منظمو الفعاليات الصغيرة"],
    ],
    [
      /tutor|educat|learn|تعليم|دروس/i,
      [
        "Students needing subject support",
        "Parents choosing learning support",
        "Adults learning new skills",
      ],
      [
        "طلاب يحتاجون دعماً دراسياً",
        "أولياء أمور يبحثون عن دعم تعليمي",
        "بالغون يتعلمون مهارات جديدة",
      ],
    ],
    [
      /digital|software|technolog|تقني|رقمي/i,
      [
        "Independent professionals",
        "Small business operators",
        "Teams managing recurring workflows",
      ],
      [
        "المهنيون المستقلون",
        "مشغلو الشركات الصغيرة",
        "فرق تدير أعمالاً متكررة",
      ],
    ],
    [
      /touris|hospitality|travel|سياح|سفر/i,
      [
        "First-time visitors",
        "Families planning short trips",
        "Local accommodation operators",
      ],
      [
        "زوار للمرة الأولى",
        "عائلات تخطط لرحلات قصيرة",
        "مشغلو أماكن الإقامة المحلية",
      ],
    ],
  ];
  for (const [pattern, en, arabic] of groups)
    if (pattern.test(context)) return ar ? arabic : en;
  const subject =
    idea || category || (ar ? "الفكرة المقترحة" : "the proposed service");
  return ar
    ? [
        `أفراد يبحثون عن ${subject}`,
        `أصحاب أعمال يحتاجون إلى ${subject}`,
        `جهات تشتري ${subject} لفرقها`,
      ]
    : [
        `Individuals seeking ${subject}`,
        `Business owners needing ${subject}`,
        `Teams purchasing ${subject} together`,
      ];
}

function localPersonaHypothesis(idea, category, index, ar) {
  const context = idea + " " + category;
  const food = ar
    ? [
        [
          "وجبات مريحة في وقت متوقع",
          "الطهي المنزلي أو الطلب الجاهز",
          "مجموعات الأسر والأحياء",
          "كيف تختار وجبتك في يوم مزدحم؟",
        ],
        [
          "طلب غداء جماعي موثوق",
          "طلبات فردية أو مقصف العمل",
          "مجموعات العمل",
          "كيف يرتب فريقك الغداء الآن؟",
        ],
        [
          "كميات مرنة لفعالية صغيرة",
          "التحضير الذاتي أو تموين قائم",
          "منظمو الفعاليات",
          "ما أصعب جزء في ترتيب الطعام لفعالية؟",
        ],
      ]
    : [
        [
          "Convenient meals at a predictable time",
          "Home cooking or takeaway",
          "Household and neighbourhood groups",
          "How do you choose a meal on a busy day?",
        ],
        [
          "Reliable group lunch ordering",
          "Individual orders or office canteens",
          "Workplace groups",
          "How does your team arrange lunch now?",
        ],
        [
          "Flexible portions for a small event",
          "Self-catering or an existing caterer",
          "Event organisers",
          "What is hardest about arranging food for an event?",
        ],
      ];
  const digital = ar
    ? [
        [
          "حضور رقمي يسهل تحديثه",
          "صفحات التواصل أو أدوات إنشاء المواقع",
          "مجموعات الأعمال المحلية",
          "كيف تحدّث حضورك الرقمي الآن؟",
        ],
        [
          "معالجة أسرع لاستفسارات العملاء",
          "رسائل يدوية أو وكالة خارجية",
          "شبكات القطاع",
          "أين تتأخر استفسارات العملاء اليوم؟",
        ],
        [
          "مسار رقمي موثوق ودعم مناسب",
          "جداول أو أدوات منفصلة",
          "شبكات المهنيين",
          "أي مهمة متكررة تريد تبسيطها؟",
        ],
      ]
    : [
        [
          "An online presence they can update",
          "Social pages or DIY site builders",
          "Local business groups",
          "How do you update your online presence now?",
        ],
        [
          "Faster customer-enquiry handling",
          "Manual messages or an agency",
          "Sector networks",
          "Where do customer enquiries get delayed?",
        ],
        [
          "Reliable digital workflow and support",
          "Spreadsheets or disconnected tools",
          "Professional networks",
          "Which recurring task would you simplify?",
        ],
      ];
  const service = ar
    ? [
        [
          "موعد خدمة يناسب جدولهم",
          "تنفيذ المهمة ذاتياً أو مزود قائم",
          "مجموعات الأحياء",
          "متى سببت لك مواعيد الخدمة صعوبة؟",
        ],
        [
          "جودة خدمة متوقعة في العمل",
          "متعهد قائم أو موظفون",
          "مديرو المرافق",
          "كيف تقيّم موثوقية مزود الخدمة؟",
        ],
        [
          "تنسيق خدمة بين مواقع متعددة",
          "حجوزات منفصلة",
          "مشغلو المواقع المتعددة",
          "ما أكبر مشكلة تنسيق بين المواقع؟",
        ],
      ]
    : [
        [
          "An appointment that fits their schedule",
          "Doing it themselves or a provider",
          "Neighbourhood groups",
          "When did scheduling last cause difficulty?",
        ],
        [
          "Predictable workplace service quality",
          "An existing contractor or staff",
          "Facility managers",
          "How do you assess service reliability?",
        ],
        [
          "Coordinated service across locations",
          "Separate bookings",
          "Multi-site operators",
          "What is the main coordination problem?",
        ],
      ];
  const generic = ar
    ? [
        [
          "طريقة أوضح لحل المشكلة",
          "حل ذاتي أو منتج حالي",
          "مقابلات مباشرة",
          "ما آخر طريقة جربتها لحل المشكلة؟",
        ],
        [
          "خيار عملي يناسب الميزانية",
          "مورد قائم أو الاستغناء عن الحل",
          "مجموعات مهنية",
          "ما الذي يجعل تغيير خيارك مجدياً؟",
        ],
        [
          "تجربة موثوقة قابلة للتكرار",
          "مزود آخر أو إحالات",
          "مستخدمون متكررون",
          "ما الذي يدفعك للعودة؟",
        ],
      ]
    : [
        [
          "A clearer way to solve the problem",
          "Self-service or a current product",
          "Direct interviews",
          "What did you try most recently?",
        ],
        [
          "A practical option within budget",
          "An existing supplier or doing without",
          "Professional groups",
          "What would make switching worthwhile?",
        ],
        [
          "A dependable repeatable experience",
          "Another provider or referrals",
          "Repeat users",
          "What would make you return?",
        ],
      ];
  const rows = /food|cater|meal|restaurant|طعام|وجبة|وجبات|مطعم/i.test(context)
    ? food
    : /website|software|digital|online|platform|app\b|no.?code|tech|موقع|تقني|رقمي|برمج|منصة|تطبيق/i.test(
          context,
        )
      ? digital
      : /service|wash|clean|repair|maintenance|delivery|خدمة|غسيل|تنظيف|صيانة|توصيل/i.test(
            context,
          )
        ? service
        : generic;
  return rows[index % 3];
}

function normalizeLocalPlan(p, idea, region, context) {
  const ar = lang === "ar",
    car = /car.?wash|غسيل سيارات/i.test(idea);
  const names = car
    ? ar
      ? ["مالكو السيارات السكنية", "مديرو المكاتب والمرافق", "مشغلو الأساطيل"]
      : [
          "Residential car owners",
          "Office and facility managers",
          "Fleet operators",
        ]
    : contextSegmentNames(
        idea,
        (p.readiness_report || {}).target_customer,
        p._category,
        ar,
      );
  p.small_test_plan = {
    intro: ar
      ? "اختبر الطلب دون تشغيل أو دفع قبل التحقق الرسمي."
      : "Test demand without operating or taking payment before official checks.",
    points: ar
      ? [
          "حدد شريحة عميل واحدة",
          "قابل خمسة عملاء محتملين",
          "اختبر العرض برسالة أو صفحة بسيطة",
          "اجمع نوايا أو حجوزات بلا دفع",
          "راجع النتائج قبل الإنفاق",
        ]
      : [
          "Choose one customer segment",
          "Interview five potential customers",
          "Test the offer with a message or landing page",
          "Collect intent or no-payment waitlist signups",
          "Review results before spending",
        ],
  };
  const days = ar
    ? [
        [
          "حدد العميل المستهدف",
          "اختر شريحة ومشكلة محددة",
          "بطاقة فرضية لشريحة واحدة",
        ],
        [
          "رتب مقابلات العملاء",
          "ادعُ أشخاصاً من الشريحة واسأل من يوافق عن البدائل الحالية",
          "سجل الدعوات وأي مقابلات تمت فعلاً",
        ],
        [
          "اختبر العرض",
          "جهز رسالة بسيطة واطلب رأياً بلا بيع",
          "نسخة واحدة من رسالة العرض",
        ],
        [
          "اجمع نوايا بلا دفع",
          "اعرض قائمة انتظار أو حجزاً بلا دفع",
          "سجل النوايا أو الحجوزات إن وصلت",
        ],
        [
          "راجع الأدلة",
          "قارن الردود والاعتراضات ومخاوف السعر",
          "ملخص للأدلة والفجوات",
        ],
        [
          "تحقق من المتطلبات",
          "راجع النشاط والموافقات لدى الجهة الرسمية قبل التشغيل",
          "قائمة أسئلة للتحقق الرسمي",
        ],
        [
          "اتخذ القرار",
          "استمر أو عدّل أو توقف حسب الأدلة",
          "مذكرة قرار للخطوة التالية",
        ],
      ]
    : [
        [
          "Define target customer",
          "Choose one segment and problem",
          "One segment hypothesis card",
        ],
        [
          "Arrange customer interviews",
          "Invite people and ask those who agree about current alternatives",
          "Outreach log and notes from any completed interviews",
        ],
        [
          "Test the offer",
          "Prepare a simple message and seek feedback without selling",
          "One draft offer message",
        ],
        [
          "Collect no-payment intent",
          "Offer a no-payment waitlist or reservation",
          "Intent or reservation log if anyone responds",
        ],
        [
          "Review evidence",
          "Compare responses, objections and price concerns",
          "Evidence and gaps summary",
        ],
        [
          "Verify requirements",
          "Check activity and possible approvals with the official authority",
          "Official-check questions list",
        ],
        [
          "Decide",
          "Continue, adjust or stop based on actual evidence",
          "Next-step decision memo",
        ],
      ];
  const checks = ar
    ? [
        "تصف البطاقة المشكلة والبديل الحالي وسؤال اختبار",
        "لا تُحسب مقابلة إلا إذا حدثت فعلاً",
        "سجل الردود الفعلية أو غياب الردود",
        "ميّز الاهتمام عن النية والحجز",
        "اذكر ما سُجل وما لم يُعرف بعد",
        "لا تبدأ التشغيل قبل تأكيد المتطلبات",
        "اربط القرار بالأدلة والفجوات",
      ]
    : [
        "The card states the problem, alternative and a test question",
        "Count only interviews that actually happened",
        "Record actual responses or the lack of replies",
        "Separate interest, intent and reservation",
        "State what is recorded and unknown",
        "Do not operate before requirements are confirmed",
        "Tie the decision to evidence and gaps",
      ];
  p.seven_day_plan = days.map((d, i) => ({
    day: i + 1,
    focus: d[0],
    action: d[1],
    output: d[2],
    time_needed:
      i === 3 || i === 5
        ? ar
          ? "مدة متغيرة"
          : "Time varies"
        : i === 1
          ? ar
            ? "2–4 ساعات · تقدير"
            : "2–4h · estimate"
          : ar
            ? "1–2 ساعة · تقدير"
            : "1–2h · estimate",
    success_check: checks[i],
  }));
  p.customer_personas = names.map((name, i) => {
    const [need, alternative, channel, question] = localPersonaHypothesis(
      idea,
      p._category,
      i,
      ar,
    );
    return {
      name,
      cares_about: need,
      current_alternative: alternative,
      why_benefit: ar
        ? `قد تكون بديلاً عن ${alternative} إذا كانت ${need} مهمة لهم؛ هذا افتراض للاختبار.`
        : `May replace ${alternative} if ${need.toLowerCase()} matters; test this assumption.`,
      reach_through: channel,
      ask: question,
      source: "ai_assumption",
    };
  });
  const riskNames = ar
    ? [
        "طلب العملاء",
        "التكلفة / المال",
        "الثقة / التبني",
        "التنفيذ",
        "الأنظمة / الامتثال",
      ]
    : [
        "Customer Demand",
        "Cost / Financial",
        "Trust / Adoption",
        "Execution",
        "Regulation / Compliance",
      ];
  const reasons = ar
    ? [
        "لم تُجمع أدلة من العملاء بعد.",
        "التكاليف المقدرة غير مؤكدة.",
        "يجب اختبار مخاوف الثقة المحتملة.",
        "يجب اختبار تعقيدات المسارات والمواعيد.",
        "المتطلبات الدقيقة غير مؤكدة وتعتمد على النشاط والإمارة.",
      ]
    : [
        "No customer evidence has been collected yet.",
        "Estimated costs are unverified.",
        "Potential trust concerns should be tested.",
        "Routing and scheduling complexity should be tested.",
        "Exact requirements are unverified and depend on the activity and emirate.",
      ];
  const fixes = ar
    ? [
        "قابل العملاء وسجّل نوايا بلا دفع.",
        "تحقق من عروض الأسعار المحلية.",
        "اسأل عن أسباب التردد.",
        "اختبر جدولاً افتراضياً بلا تشغيل.",
        "تحقق من تصنيف النشاط والموافقات لدى الجهة الرسمية المختصة.",
      ]
    : [
        "Interview customers and record no-payment intent.",
        "Verify local supplier quotes.",
        "Ask why customers hesitate.",
        "Test a mock schedule without operating.",
        "Verify activity classification and approvals with the relevant official authority.",
      ];
  [reasons[3], fixes[3]] = executionRisk(idea, p._category, ar);
  p.risk_radar = riskNames.map((name, i) => ({
    name,
    level: i === 3 ? "Medium" : "Unknown",
    reason: reasons[i],
    fix: fixes[i],
    source: "ai_assumption",
  }));
  p.decision_engine = {
    decision: ar ? "تحقق أكثر" : "Validate more",
    reason: ar
      ? "قرار قبل جمع الأدلة: تحقق من الطلب والمتطلبات الرسمية."
      : "Pre-evidence decision: customer demand and official requirements need verification.",
    next_test_action: ar
      ? "قابل خمسة عملاء محتملين واجمع نوايا بلا دفع."
      : "Interview five potential customers and collect no-payment intent.",
    risk_level: "Medium",
    recommended_test_budget_aed: "",
  };
  p.do_not_start_with = ar
    ? [
        "لا تشغّل الخدمة أو تقبل الدفع قبل التحقق الرسمي.",
        "لا تشترِ معدات كبيرة قبل وجود أدلة طلب.",
      ]
    : [
        "Do not operate or accept payment before official checks.",
        "Do not buy major equipment before demand evidence.",
      ];
  p.instead_do = ar
    ? [
        "قابل عملاء محتملين.",
        "اجمع حجوزات بلا دفع.",
        "تحقق من تصنيف النشاط والموافقات رسمياً.",
      ]
    : [
        "Interview potential customers.",
        "Collect no-payment reservations.",
        "Verify activity classification and approvals officially.",
      ];
  p.readiness_report.target_customer = names[0];
  p.state.target_customer = names[0];
  p.readiness_report.main_risk = ar
    ? "الإنفاق قبل وجود أدلة عملاء أو تحقق رسمي."
    : "Spending before customer evidence or official checks.";
  p.readiness_report.what_not_to_start_with = ar
    ? "التشغيل أو الدفع قبل التحقق الرسمي."
    : "Operation or payment before official checks.";
  p.readiness_report.next_step = ar
    ? "قابل العملاء وسجّل نوايا بلا دفع؛ هذه توصية وليست متطلباً مثبتاً."
    : "Interview leads and record no-payment intent; this is a recommendation, not a proven requirement.";
  p.founder_passport = {
    status: ar ? "جاهز للتحقق، لا للتشغيل" : "Ready to validate, not operate",
    first_action: p.first_step_today,
    next_step: p.readiness_report.next_step,
  };
  const actions = ar
    ? [
        ["مقابلات العملاء", "قابل العملاء المستهدفين.", 3],
        ["اختبار الاهتمام", "أنشئ قائمة انتظار بلا دفع.", 2],
        ["مراجعة الأدلة", "قارن النوايا والاعتراضات.", 1],
        ["تحقق رسمي", "تحقق من تصنيف النشاط والموافقات لدى الجهة الرسمية.", 1],
        ["جهز تجربة قانونية", "جهز خطة بعد التحقق؛ لا تشغّل بعد.", 2],
        [
          "نفذ تجربة إذا سُمح",
          "بعد تأكيد التراخيص والموافقات المطلوبة، نفذ أصغر تجربة عملية مناسبة.",
          2,
        ],
        ["راجع وقرر", "راجع الأدلة وقرر المرحلة التالية.", 1],
      ]
    : [
        [
          "Conduct targeted interviews",
          "Ask target users about current alternatives.",
          3,
        ],
        ["Create interest test", "Use a no-payment waitlist.", 2],
        ["Review evidence", "Compare intent and objections.", 1],
        [
          "Verify official requirements",
          "Check activity classification and required approvals.",
          1,
        ],
        [
          "Prepare lawful pilot",
          "Plan only after official checks; do not operate yet.",
          2,
        ],
        [
          "Run pilot if permitted",
          "After confirming that required licences and approvals are in place, run the smallest practical pilot.",
          2,
        ],
        ["Review and decide", "Review evidence before the next phase.", 1],
      ];
  p.steps = actions.map((a, i) => ({
    step_number: i + 1,
    action: a[0],
    description: a[1],
    estimated_cost_aed: null,
    timeline_days: a[2],
    who_to_contact: ar ? "الجهة المعنية" : "Relevant people",
    location: region,
  }));
  p.total_timeline_days = p.steps.reduce((n, s) => n + s.timeline_days, 0);
  p.total_estimated_cost_aed = null;
  p.estimated_budget_gap_aed = 0;
  p.validation_before_spending = ar
    ? [
        "ميّز الاهتمام عن نية الشراء والحجز والدفع.",
        "استخدم إدخالات وضع الإثبات فقط كدليل.",
        "تحقق من التكاليف والمتطلبات قبل الإنفاق.",
      ]
    : [
        "Separate interest, intent, reservations, and payments.",
        "Use only Proof Mode entries as evidence.",
        "Verify costs and requirements before spending.",
      ];
  p.pitches = {
    ten_sec: ar
      ? `أختبر فكرة ${idea} في ${region}.`
      : `I am testing ${idea} in ${region}.`,
    thirty_sec: ar
      ? "أجري مقابلات وأختبر قائمة انتظار بلا دفع قبل التشغيل."
      : "I am interviewing leads and testing a no-payment waitlist before operating.",
    whatsapp: ar
      ? `مرحباً، أختبر فكرة ${idea}. كيف تحل المشكلة الآن؟`
      : `Hi, I am testing ${idea}. How do you solve this today?`,
    instagram: ar
      ? `نختبر فكرة ${idea}. ما البديل الحالي؟`
      : `Testing ${idea}. What alternative do you use now?`,
  };
  p.first_customer_tip = ar
    ? "ابحث عن ثلاثة عملاء محتملين لديهم نية واضحة؛ لا تعتبرهم دافعين قبل حدوث دفع فعلي وبعد التحقق الرسمي."
    : "Find three strong leads; do not call them paying customers before actual payment after official checks.";
  return p;
}

function showPlan(rawPlan) {
  syncPathCosts(rawPlan);
  setupDashboard();
  updateDashboardLabels();
  const p = escapePlan(rawPlan);
  const t = T[lang];
  const state = rawPlan.state || {};
  const legend = document.getElementById("source-legend");
  legend.replaceChildren();
  [
    ["USER INPUT", "input"],
    ["AI SUGGESTION SELECTED BY USER", "assumption"],
    ["AI ASSUMPTION", "assumption"],
    ["RECORDED CUSTOMER EVIDENCE", "evidence"],
  ].forEach(([label, cls]) => {
    const b = document.createElement("span");
    b.className = "source-badge " + cls;
    b.textContent =
      lang === "ar"
        ? {
            "USER INPUT": "إدخال المستخدم",
            "AI SUGGESTION SELECTED BY USER":
              "اقتراح ذكاء اصطناعي اختاره المستخدم",
            "AI ASSUMPTION": "افتراض ذكاء اصطناعي",
            "RECORDED CUSTOMER EVIDENCE": "أدلة العملاء المسجلة",
          }[label]
        : label;
    legend.appendChild(b);
  });
  const jb = document.getElementById("overview-body");
  jb.replaceChildren();
  const js = p.idea_overview || {};
  [
    [lang === "ar" ? "الفكرة" : "Idea", state.idea],
    [
      lang === "ar" ? "الفئة" : "Category",
      T[lang].categories[T.en.categories.indexOf(state.category)] ||
        state.category,
    ],
    [
      lang === "ar" ? "السوق" : "Selected market",
      T[lang].regions[state.region] || state.region,
    ],
    [
      lang === "ar" ? "نوع المشروع" : "Business type",
      T[lang].contexts[state.context] || state.context,
    ],
    [
      lang === "ar" ? "ميزانيتك" : "Your budget",
      formatAED(state.user_budget_aed || 0),
    ],
    [
      state.target_customer_source === "user_input"
        ? lang === "ar"
          ? "العميل المختار"
          : "Selected customer"
        : lang === "ar"
          ? "العميل المستهدف (افتراض)"
          : "Target customer (assumption)",
      state.target_customer,
    ],
  ].forEach(([key, value]) => {
    const row = document.createElement("div"),
      k = document.createElement("span"),
      v = document.createElement("span"),
      b = document.createElement("span");
    row.className = "overview-row";
    k.className = "jk";
    v.className = "jv";
    k.textContent = key;
    v.textContent = value || "—";
    b.className =
      "source-badge " +
      (key.includes("assumption") || key.includes("افتراض")
        ? "assumption"
        : "input");
    b.textContent =
      key.includes("assumption") || key.includes("افتراض")
        ? lang === "ar"
          ? "افتراض"
          : "AI ASSUMPTION"
        : lang === "ar"
          ? "إدخال المستخدم"
          : "USER INPUT";
    v.append(" ", b);
    row.append(k, v);
    jb.appendChild(row);
  });
  {
    const row = document.createElement("div"),
      k = document.createElement("span"),
      v = document.createElement("span"),
      b = document.createElement("span"),
      priced = Number(state.suggested_test_price_aed) > 0;
    row.className = "overview-row";
    k.className = "jk";
    v.className = "jv";
    k.textContent = lang === "ar" ? "سعر اختبار مقترح" : "Suggested test price";
    v.textContent = priced
      ? formatAED(state.suggested_test_price_aed) + " "
      : lang === "ar"
        ? "لم يُقترح بعد "
        : "Not proposed yet ";
    b.className = "source-badge " + (priced ? "assumption" : "unvalidated");
    b.textContent = priced
      ? lang === "ar"
        ? "افتراض"
        : "AI ASSUMPTION"
      : lang === "ar"
        ? "غير مُتحقق"
        : "UNVALIDATED";
    v.appendChild(b);
    row.append(k, v);
    jb.appendChild(row);
  }
  Object.keys(t.jk).forEach((k) => {
    if (js[k])
      jb.innerHTML += `<div class="overview-row"><span class="jk">${t.jk[k]}</span><span class="jv" ${k === "evidence" ? 'id="overview-evidence"' : ""}>${js[k]}</span></div>`;
  });
  if (state.idea_source === "ai_suggestion_selected") {
    const badge = jb.querySelector(".overview-row .source-badge");
    if (badge) {
      badge.className = "source-badge assumption";
      badge.textContent =
        lang === "ar"
          ? "اقتراح ذكاء اصطناعي اختاره المستخدم"
          : "AI SUGGESTION SELECTED BY USER";
    }
  }
  document.getElementById("first-step-text").textContent =
    rawPlan.first_step_today || "";
  const sc = rawPlan.opportunity_score || {};
  aggregateScores(sc);
  renderScores(sc);
  const tp = p.small_test_plan || {};
  document.getElementById("test-intro").textContent =
    (rawPlan.small_test_plan || {}).intro || "";
  const tl = document.getElementById("test-list");
  tl.replaceChildren();
  (tp.points || []).forEach((x) => {
    tl.innerHTML += `<li>${x}</li>`;
  });
  const dg = document.getElementById("day-grid");
  dg.replaceChildren();
  (p.seven_day_plan || []).forEach((d) => {
    var extra = "";
    if (d.output)
      extra += `<div class="a" style="margin-top:.3rem"><b>${t.dayOut}:</b> ${d.output}</div>`;
    if (d.success_check)
      extra += `<div class="a" style="color:var(--uae-green)"><b>${t.daySucc}:</b> ${d.success_check}</div>`;
    var tm = d.time_needed
      ? `<span style="float:right;font-size:14px;color:var(--muted)">${d.time_needed}</span>`
      : "";
    dg.innerHTML += `<div class="day-card"><div class="d">${lang === "ar" ? "اليوم" : "Day"} ${d.day}</div>${tm}<div class="f">${d.focus}</div><div class="a">${d.action}</div>${extra}</div>`;
  });
  const vl = document.getElementById("validate-list");
  vl.replaceChildren();
  (p.validation_before_spending || []).forEach((x) => {
    vl.innerHTML += `<li>${x}</li>`;
  });
  const ql = document.getElementById("questions-list");
  ql.replaceChildren();
  (p.validation_questions || []).forEach((q) => {
    ql.innerHTML += `<li>${q}</li>`;
  });
  let waMsg = rawPlan.whatsapp_message || "";
  const ideaVal = document.getElementById("idea").value.trim();
  if (ideaVal && waMsg.includes("[idea]"))
    waMsg = waMsg.replace("[idea]", ideaVal);
  else if (
    ideaVal &&
    !waMsg.toLowerCase().includes(ideaVal.toLowerCase().slice(0, 12))
  )
    waMsg = waMsg + " (" + ideaVal + ")";
  document.getElementById("wa-text").textContent =
    (lang === "ar"
      ? "خطوة — من الفكرة إلى الخطوة الأولى.\n"
      : "Khotwa — From idea to first step.\n") + waMsg;
  const rt = document.getElementById("report-table");
  rt.replaceChildren();
  const r = p.readiness_report || {};
  Object.keys(t.rkeys).forEach((k) => {
    let val = k === "idea" ? escapeHtml(state.idea) : r[k];
    let label = t.rkeys[k];
    if (k === "target_customer")
      label +=
        state.target_customer_source === "user_input"
          ? lang === "ar"
            ? " · إدخال المستخدم"
            : " · USER INPUT"
          : lang === "ar"
            ? " · افتراض ذكاء اصطناعي"
            : " · AI ASSUMPTION";
    if (k === "main_risk")
      label += lang === "ar" ? " · افتراض تخطيطي" : " · planning assumption";
    if (k === "next_step")
      label += lang === "ar" ? " · إجراء موصى به" : " · recommended action";
    if (k === "estimated_first_test_cost_aed" && val != null)
      val =
        formatAED(state.estimated_test_cost_aed || val) +
        " · " +
        (lang === "ar" ? "تقدير ذكاء اصطناعي" : "AI ESTIMATE");
    rt.innerHTML += `<tr><td class="k">${label}</td><td class="v">${val || "-"}</td></tr>`;
  });
  rt.innerHTML +=
    '<tr id="readiness-evidence"><td class="k">' +
    (lang === "ar" ? "أدلة العملاء" : "CUSTOMER EVIDENCE") +
    '</td><td class="v" id="readiness-evidence-text">' +
    escapeHtml(
      (rawPlan.idea_overview || {}).evidence ||
        (lang === "ar"
          ? "لم تُجمع أدلة من العملاء بعد."
          : "No customer evidence collected yet."),
    ) +
    "</td></tr>";
  const list = document.getElementById("steps-list");
  list.replaceChildren();
  (p.steps || []).forEach((s) => {
    const duration =
      lang === "ar"
        ? Number(s.timeline_days) === 1
          ? "يوم"
          : "أيام"
        : Number(s.timeline_days) === 1
          ? "day"
          : "days";
    list.innerHTML += `<div class="step-card"><div class="step-num">${s.step_number}</div><div class="step-body"><h3>${s.action}</h3><p>${s.description}</p><div class="tags"><span class="tag">${s.location}</span><span class="tag">${s.who_to_contact}</span><span class="tag">${s.estimated_cost_aed == null ? (lang === "ar" ? "لم تُقدر التكلفة بعد" : "Cost not estimated yet") : formatAED(s.estimated_cost_aed) + " · " + (lang === "ar" ? "تقدير ذكاء اصطناعي" : "AI ESTIMATE")}</span><span class="tag">${s.timeline_days} ${duration} · ${lang === "ar" ? "تقدير تخطيطي" : "planning estimate"}</span></div></div></div>`;
  });
  renderPathCosts(rawPlan);
  document.getElementById("tip").innerHTML =
    `<strong>${t.firstTip}:</strong> ${p.first_customer_tip}`;
  if (timelineChart) {
    timelineChart.destroy();
    timelineChart = null;
  }
  if (costChart) {
    costChart.destroy();
    costChart = null;
  }
  if (typeof Chart !== "undefined") {
    timelineChart = new Chart(document.getElementById("timeline-chart"), {
      type: "bar",
      data: {
        labels: p.steps.map(
          (s) => (lang === "ar" ? "خطوة " : "Step ") + s.step_number,
        ),
        datasets: [
          {
            data: p.steps.map((s) => s.timeline_days),
            backgroundColor: "#378ADD",
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
      },
    });
    if (
      rawPlan.total_estimated_cost_aed !== null &&
      rawPlan.total_estimated_cost_aed > 0
    )
      costChart = new Chart(document.getElementById("cost-chart"), {
        type: "doughnut",
        data: {
          labels: p.steps.map((s) => s.action),
          datasets: [
            {
              data: p.steps.map((s) => s.estimated_cost_aed),
              backgroundColor: [
                "#534AB7",
                "#1D9E75",
                "#D85A30",
                "#378ADD",
                "#BA7517",
              ],
              borderWidth: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom", labels: { font: { size: 12 } } },
          },
        },
      });
  }
  // decision engine
  var de = p.decision_engine || {};
  var dm = document.getElementById("decision-main");
  if (de.decision) {
    document.getElementById("decision-card").style.display = "block";
    dm.textContent = fixedLabel((rawPlan.decision_engine || {}).decision || "");
    document.getElementById("decision-reason").textContent =
      (rawPlan.decision_engine || {}).reason || "";
    document.getElementById("decision-next").textContent = (
      rawPlan.decision_engine || {}
    ).next_test_action
      ? t.nexttest + ": " + rawPlan.decision_engine.next_test_action
      : "";
    var dmeta = "";
    if (de.risk_level)
      dmeta += `<span><b>${t.risklevel}:</b> ${fixedLabel(de.risk_level)}</span>`;
    if (de.recommended_test_budget_aed)
      dmeta += `<span><b>${t.testbudget} · ${lang === "ar" ? "تقدير ذكاء اصطناعي" : "AI ESTIMATE"}:</b> ${formatAED(de.recommended_test_budget_aed)}</span>`;
    document.getElementById("decision-meta").innerHTML = dmeta;
  } else {
    document.getElementById("decision-card").style.display = "none";
  }
  // do not start / instead
  var dnl = document.getElementById("donot-list");
  dnl.replaceChildren();
  (p.do_not_start_with || []).forEach((x) => {
    dnl.innerHTML += `<li>${x}</li>`;
  });
  var inl = document.getElementById("instead-list");
  inl.replaceChildren();
  (p.instead_do || []).forEach((x) => {
    inl.innerHTML += `<li>${x}</li>`;
  });
  // shareable summary
  var sc2 = p.opportunity_score || {};
  var st = scoreLabel(rawPlan.opportunity_score);
  var verdict = st >= 20 ? t.strong : st >= 15 ? t.medium : t.weak;
  var shareTxt = t.shareTpl
    .replace(
      "{idea}",
      (rawPlan.readiness_report || {}).idea || rawPlan.summary || "",
    )
    .replace(
      "{step}",
      (rawPlan.first_step_today || "").replace(/[.!؟\s]+$/g, ""),
    )
    .replace("{score}", st)
    .replace("{verdict}", verdict.replace(/[.!؟\s]+$/g, ""));
  document.getElementById("share-text").textContent = shareTxt;
  var wg = document.getElementById("why-grid");
  if (wg) {
    wg.replaceChildren();
    const values = [
      [
        lang === "ar" ? "السوق المختار" : "Selected market",
        T[lang].regions[state.region] || state.region,
      ],
      [
        lang === "ar" ? "نوع المشروع" : "Business type",
        T[lang].contexts[state.context] || state.context,
      ],
      [
        lang === "ar" ? "قناة أولى محتملة" : "Likely first channel",
        (rawPlan.readiness_report || {}).first_customer_channel || "—",
      ],
      [
        lang === "ar" ? "طريقة التحقق" : "Validation approach",
        lang === "ar"
          ? "مقابلات وحجوزات بلا دفع"
          : "Interviews and no-payment reservations",
      ],
      [
        lang === "ar" ? "تحقق رسمي" : "Official checks",
        ["Abu Dhabi", "Al Ain"].includes(state.region)
          ? lang === "ar"
            ? "تم / دائرة التنمية الاقتصادية في أبوظبي"
            : "TAMM / ADDED"
          : lang === "ar"
            ? "الجهة الرسمية المختصة"
            : "Relevant official authority",
      ],
    ];
    values.forEach(([k, v]) => {
      const card = document.createElement("div"),
        b = document.createElement("b"),
        line = document.createElement("div");
      card.className = "local-item";
      b.textContent = k;
      line.textContent = v;
      card.append(b, line);
      wg.appendChild(card);
    });
  }
  renderExtras(rawPlan, rawPlan.readiness_report || {}, st);
  renderResources(rawPlan._region || document.getElementById("region").value);
  document.getElementById("results").style.display = "block";
  enterWorkspace();
  revealInit();
  renderDashboardSummary();
  decorateResources();
  document
    .getElementById("results")
    .scrollIntoView({ behavior: motionBehavior() });
}

function renderExtras(rawPlan, r, st) {
  var p = escapePlan(rawPlan);
  r = p.readiness_report || {};
  var t = T[lang];
  // Before You Spend
  try {
    var budget = Number((rawPlan.state || {}).user_budget_aed) || 0;
    var testCost = Number((rawPlan.state || {}).estimated_test_cost_aed) || 0;
    var protect = Math.max(0, budget - testCost);
    setTxt("bys-spend", formatAED(budget));
    setTxt(
      "bys-test",
      testCost
        ? formatAED(testCost) +
            " · " +
            (lang === "ar" ? "تقدير ذكاء اصطناعي" : "AI ESTIMATE")
        : lang === "ar"
          ? "لم يُقدّر بعد"
          : "Not estimated yet",
    );
    setTxt(
      "bys-protect",
      testCost
        ? formatAED(protect)
        : lang === "ar"
          ? "لم تُقدّر بعد"
          : "Not estimated yet",
    );
  } catch (e) {
    console.warn("bys", e);
  }
  // Founder Passport
  try {
    var pp = p.founder_passport || {};
    var de = p.decision_engine || {};
    var rows = [
      [t.ppIdea, r.idea || p.summary || ""],
      [t.ppStatus, fixedLabel(pp.status || "Ready to validate")],
      [t.ppFirst, pp.first_action || p.first_step_today || ""],
      [t.ppScore, scoreLabel(rawPlan.opportunity_score)],
      [t.ppDecision, fixedLabel(de.decision || "")],
      [t.ppChannel, r.first_customer_channel || ""],
      [
        t.ppCost,
        r.estimated_first_test_cost_aed != null
          ? formatAED(r.estimated_first_test_cost_aed) +
            " · " +
            (lang === "ar" ? "تقدير ذكاء اصطناعي" : "AI ESTIMATE")
          : "-",
      ],
      [t.ppNext, pp.next_step || r.next_step || ""],
    ];
    var ptbl = document.getElementById("passport-table");
    ptbl.replaceChildren();
    rows.forEach(function (rw) {
      ptbl.innerHTML += `<tr><td class="pk2">${rw[0]}</td><td class="pv2">${rw[1] || "-"}</td></tr>`;
    });
    window._passportText = rows
      .map(function (rw) {
        return rw[0] + ": " + (rw[1] || "-");
      })
      .join("\n");
  } catch (e) {
    console.warn("passport", e);
  }
  // Personas
  try {
    var pg = document.getElementById("persona-grid");
    pg.replaceChildren();
    (p.customer_personas || []).slice(0, 3).forEach(function (per) {
      pg.innerHTML += `<div class="persona"><div class="pname">${per.name || ""} <span class="source-badge assumption">${lang === "ar" ? "افتراض ذكاء اصطناعي · ليس عميلاً محدداً" : "AI ASSUMPTION · NOT AN IDENTIFIED LEAD"}</span></div><div class="prow"><b>${t.cares}:</b> ${per.cares_about || ""}</div>${per.current_alternative ? `<div class="prow"><b>${lang === "ar" ? "البديل الحالي المحتمل" : "Possible current alternative"}:</b> ${per.current_alternative}</div>` : ""}${per.why_benefit ? `<div class="prow"><b>${lang === "ar" ? "لماذا قد يستفيد" : "Why they might benefit"}:</b> ${per.why_benefit}</div>` : ""}<div class="prow"><b>${t.reach}:</b> ${per.reach_through || ""}</div><div class="prow"><b>${t.askp}:</b> ${per.ask || ""}</div></div>`;
    });
  } catch (e) {
    console.warn("personas", e);
  }
  // Risk radar
  try {
    var rl = document.getElementById("risk-list");
    rl.replaceChildren();
    (p.risk_radar || []).forEach(function (rk) {
      var lv = (rk.level || "").toLowerCase();
      var cls = /(high|مرتفع)/.test(lv)
        ? "rl-high"
        : /(med|متوسط)/.test(lv)
          ? "rl-medium"
          : /(low|منخفض)/.test(lv)
            ? "rl-low"
            : "rl-unknown";
      rl.innerHTML += `<div class="risk-item"><span class="risk-name">${fixedLabel(rk.name || "")}</span><span class="risk-level ${cls}">${fixedLabel(rk.level || "")}</span><span class="risk-detail"><b>${rk.reason || ""}</b><span class="risk-next">${lang === "ar" ? "الخطوة التالية: " : "Next action: "}${rk.fix || ""}</span></span></div>`;
    });
  } catch (e) {
    console.warn("risks", e);
  }
  // Pitches
  try {
    var pit = p.pitches || {};
    var pl = document.getElementById("pitch-list");
    pl.replaceChildren();
    var defs = [
      ["10s", pit.ten_sec],
      ["30s", pit.thirty_sec],
      ["WhatsApp", pit.whatsapp],
      ["Instagram", pit.instagram],
    ];
    defs.forEach(function (d) {
      if (!d[1]) return;
      var id = "pitch-" + d[0];
      pl.innerHTML += `<div class="pitch-item"><div class="pitch-body"><div class="pitch-label">${lang === "ar" ? { "10s": "10 ثوانٍ", "30s": "30 ثانية", WhatsApp: "واتساب", Instagram: "إنستغرام" }[d[0]] : d[0]}</div><div class="pitch-text" id="${id}">${d[1]}</div></div><button class="pitch-copy" data-copy="${id}">${t.copy}</button></div>`;
    });
  } catch (e) {
    console.warn("pitches", e);
  }
  // Opportunity map
  try {
    var selectedRegion =
      p._region ||
      (document.getElementById("region") || {}).value ||
      "UAE-wide";
    var selectedContext =
      p._context ||
      (document.getElementById("context") || {}).value ||
      "Not sure";
    var proof = rawPlan.proof_summary || {},
      hasEvidence = Number(proof.total_responses) > 0;
    var mapNodes = [
      T[lang].regions[selectedRegion] || selectedRegion,
      ((rawPlan.readiness_report || {}).target_customer || t.mapNodes[1]) +
        (lang === "ar" ? " · افتراض" : " · AI ASSUMPTION"),
      T[lang].contexts[selectedContext] || selectedContext,
      lang === "ar"
        ? "مقابلات وقائمة انتظار بلا دفع"
        : "Interviews and no-payment waitlist",
      hasEvidence
        ? lang === "ar"
          ? "أدلة أدخلها المستخدم"
          : "User-entered customer evidence"
        : lang === "ar"
          ? "الأدلة قيد الانتظار"
          : "Evidence pending",
      lang === "ar" ? "القرار: تحقق أكثر" : "Decision: Validate more",
    ];
    var om = document.getElementById("opp-map");
    om.replaceChildren();
    mapNodes.forEach(function (n, i) {
      const cls = i === 0 ? "start" : i === mapNodes.length - 1 ? "end" : "";
      // The selected market/context may come from restored browser state.
      om.append(uiNode("div", "opp-node " + cls, n));
      if (i < mapNodes.length - 1) om.append(uiNode("div", "opp-arrow", "↓"));
    });
  } catch (e) {
    console.warn("map", e);
  }
  // QR code
  try {
    renderQR();
  } catch (e) {
    console.warn("qr", e);
  }
}

function renderQR() {
  var box = document.getElementById("qr-code");
  if (!box) return;
  box.replaceChildren();
  var msg = (document.getElementById("wa-text") || {}).textContent || "";
  var url =
    "https://wa.me/?text=" + encodeURIComponent(msg || "Khotwa UAE validation");
  if (typeof QRCode !== "undefined") {
    new QRCode(box, {
      text: url,
      width: 140,
      height: 140,
      correctLevel: QRCode.CorrectLevel.M,
    });
  } else {
    const link = uiNode(
      "a",
      "",
      uiText("Open WhatsApp test link", "افتح رابط اختبار واتساب"),
    );
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    box.append(link);
  }
}

function setTxt(id, v) {
  var el = document.getElementById(id);
  if (el) el.textContent = v;
}
function copyText(id, btn) {
  var el = document.getElementById(id);
  if (!el) return;
  var txt = el.textContent || "";
  var done = function () {
    var o = btn.textContent;
    btn.textContent = "✓ " + T[lang].copied;
    setTimeout(function () {
      btn.textContent = T[lang].copy;
    }, 1400);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(txt)
      .then(done)
      .catch(function () {
        if (fallbackCopy(txt)) done();
      });
  } else if (fallbackCopy(txt)) done();
}
function copyPassport() {
  var txt = window._passportText || "";
  var btn = document.getElementById("passportCopyBtn");
  var done = function () {
    btn.textContent = "✓ " + T[lang].copied;
    setTimeout(function () {
      btn.textContent = T[lang].copy;
    }, 1400);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(txt)
      .then(done)
      .catch(function () {
        if (fallbackCopy(txt)) done();
      });
  } else if (fallbackCopy(txt)) done();
}

function buildProof() {
  const t = T[lang];
  const tbl = document.getElementById("proof-table");
  let head = "<tr>";
  t.proofCols.forEach(
    (c, i) =>
      (head += `<th>${i === 5 ? (lang === "ar" ? "قوة الدليل" : "Evidence strength") : c}</th>`),
  );
  head += "</tr>";
  let rows = "";
  for (let i = 1; i <= 10; i++) {
    rows += `<tr>
<td>${i}</td>
<td><select class="p-int"><option value="">-</option><option value="yes">${t.interested}</option><option value="maybe">${t.maybe}</option><option value="no">${t.no}</option></select></td>
<td><input type="number" min="0" step="0.1" class="p-price" placeholder="0"></td>
<td><input type="text" class="p-freq" maxlength="500" placeholder="${lang === "ar" ? "أسبوعياً" : "weekly"}"></td>
<td><input type="text" class="p-concern" maxlength="500" placeholder="-"></td>
<td><select class="p-pre"><option value="">-</option><option value="interest">${lang === "ar" ? "اهتمام فقط" : "Sounds interesting"}</option><option value="intent">${lang === "ar" ? "نية شراء معلنة" : "Stated intent to buy"}</option><option value="reservation">${lang === "ar" ? "حجز بلا دفع" : "No-payment reservation"}</option><option value="payment">${lang === "ar" ? "دفع فعلي" : "Actual payment"}</option><option value="repeat">${lang === "ar" ? "عميل متكرر" : "Repeat customer"}</option></select></td>
</tr>`;
  }
  tbl.innerHTML = head + rows;
  calcProof();
}

function calcProof() {
  const t = T[lang];
  const ints = [...document.querySelectorAll(".p-int")].map((s) => s.value);
  const priceInputs = [...document.querySelectorAll(".p-price")],
    validPrices = priceInputs.map(
      (s) =>
        s.value.trim() !== "" &&
        Number.isFinite(Number(s.value)) &&
        Number(s.value) >= 0,
    );
  const prices = priceInputs
    .filter((s, i) => validPrices[i])
    .map((s) => Number(s.value));
  const pres = [...document.querySelectorAll(".p-pre")].map((s) => s.value);
  const concerns = [...document.querySelectorAll(".p-concern")]
    .map((s) => (s.value || "").trim())
    .filter(Boolean);
  const nYes = ints.filter(
    (v, i) => v === "yes" || (!v && pres[i] === "interest"),
  ).length;
  const nMaybe = ints.filter((v) => v === "maybe").length;
  const nNo = ints.filter((v) => v === "no").length;
  const nPre = pres.filter((v) => v === "reservation").length,
    nIntent = pres.filter((v) => v === "intent").length,
    nPaid = pres.filter((v) => v === "payment").length,
    nRepeat = pres.filter((v) => v === "repeat").length;
  const total = ints
    .map(
      (v, i) =>
        v ||
        pres[i] ||
        validPrices[i] ||
        document.querySelectorAll(".p-concern")[i].value.trim() ||
        document.querySelectorAll(".p-freq")[i].value.trim(),
    )
    .filter(Boolean).length;
  const avg = prices.length
    ? Math.round((prices.reduce((a, b) => a + b, 0) / prices.length) * 10) / 10
    : 0;
  // top concern = most frequent
  let topConcern = "-";
  if (concerns.length) {
    const freq = {};
    concerns.forEach((c) => {
      const k = c.toLowerCase();
      freq[k] = (freq[k] || 0) + 1;
    });
    topConcern = Object.keys(freq).sort((a, b) => freq[b] - freq[a])[0];
  }
  const stats = document.getElementById("proof-stats");
  stats.innerHTML = `<div class="stat-card"><div class="v" data-target="${nYes}">${nYes}</div><div class="l">${t.stInterested} /10</div></div>
<div class="stat-card"><div class="v" data-target="${nMaybe}">${nMaybe}</div><div class="l">${t.stMaybe} /10</div></div>
<div class="stat-card"><div class="v" data-target="${avg}">${avg}</div><div class="l">${t.stAvg}</div></div>
<div class="stat-card"><div class="v" data-target="${nPre}">${nPre}</div><div class="l">${lang === "ar" ? "حجوزات بلا دفع" : "No-payment reservations"} /10</div></div>`;
  animateCounters();
  const verdict = document.getElementById("proof-verdict");
  let vtext;
  const strength = document.getElementById("evidence-strength");
  strength.textContent =
    total === 0
      ? lang === "ar"
        ? "لم تُجمع أدلة من العملاء بعد. الفكرة غير مُتحقق منها."
        : "No customer evidence collected yet. Not validated yet."
      : lang === "ar"
        ? `إجابات ${total} · اهتمام ${nYes} · نية شراء ${nIntent} · حجوزات بلا دفع ${nPre} · دفع فعلي ${nPaid} · عميل متكرر ${nRepeat}`
        : `${total} entries · ${nYes} interested · ${nIntent} stated intent · ${nPre} no-payment reservations · ${nPaid} actual payments · ${nRepeat} repeat customers`;
  const evidenceNode = document.querySelectorAll("#opp-map .opp-node")[4];
  if (evidenceNode)
    evidenceNode.textContent = total
      ? lang === "ar"
        ? "أدلة أدخلها المستخدم"
        : "User-entered customer evidence"
      : lang === "ar"
        ? "الأدلة قيد الانتظار"
        : "Evidence pending";
  if (total === 0) {
    verdict.className = "proof-verdict pv-test";
    vtext =
      lang === "ar"
        ? "غير مُتحقق منها بعد — اختبر الفرضية مع عملاء حقيقيين."
        : "Not validated yet — test this hypothesis with real customers.";
  } else if (nPaid + nRepeat > 0) {
    verdict.className = "proof-verdict pv-go";
    vtext =
      lang === "ar"
        ? "سُجل سلوك شراء فعلي. راجع حجمه واستمر في الاختبار."
        : "Actual purchase behavior recorded. Review its scale and keep testing.";
  } else if (nPre > 0) {
    verdict.className = "proof-verdict pv-test";
    vtext =
      lang === "ar"
        ? "توجد حجوزات بلا دفع. هذا أقوى من المجاملات لكنه ليس عملية بيع."
        : "No-payment reservations recorded. Stronger than compliments, but not sales.";
  } else {
    verdict.className = "proof-verdict pv-test";
    vtext =
      lang === "ar"
        ? "هذه آراء ونوايا معلنة فقط، وليست إثباتاً للطلب."
        : "Opinions and stated intent only; demand is not validated.";
  }
  verdict.textContent = vtext;
  // store summary onto currentPlan for the PDF
  if (currentPlan) {
    currentPlan.proof_summary = {
      total_responses: total,
      interested: nYes,
      maybe: nMaybe,
      no: nNo,
      avg_price: avg,
      no_payment_reservations: nPre,
      stated_intent: nIntent,
      actual_payments: nPaid,
      repeat_customers: nRepeat,
      top_concern: topConcern,
      verdict: vtext,
    };
    currentPlan.state.evidence = {
      status: total ? "customer_evidence" : "not_validated",
      responses: total,
      strength: nRepeat
        ? "repeat"
        : nPaid
          ? "payment"
          : nPre
            ? "reservation"
            : nIntent
              ? "intent"
              : "interest",
      average_stated_price_aed: avg,
    };
    updateEvidenceScore(total, nYes, nIntent, nPre, nPaid, nRepeat);
    refreshScoreDisplay();
    syncEvidencePresentation(total, nPaid + nRepeat, vtext);
  }
  renderProofPolish();
  saveSession();
}
function syncEvidencePresentation(total, purchases, verdict) {
  if (!currentPlan) return;
  const ar = lang === "ar",
    p = currentPlan;
  const evidence = total
    ? ar
      ? "أدلة أدخلها المستخدم: " + total + " إجابات. " + verdict
      : "User-entered customer evidence: " + total + " responses. " + verdict
    : ar
      ? "لم تُجمع أدلة من العملاء بعد."
      : "No customer evidence collected yet.";
  if (p.idea_overview) p.idea_overview.evidence = evidence;
  setTxt("overview-evidence", evidence);
  setTxt("readiness-evidence-text", evidence);
  if (p.risk_radar && p.risk_radar[0]) p.risk_radar[0].reason = evidence;
  const riskReason = document.querySelector("#risk-list .risk-detail b");
  if (riskReason) riskReason.textContent = evidence;
  const de = p.decision_engine || {};
  de.decision = purchases
    ? ar
      ? "راجع أدلة التجربة"
      : "Review pilot evidence"
    : ar
      ? "تحقق أكثر"
      : "Validate more";
  de.reason = total
    ? evidence
    : ar
      ? "قرار قبل جمع الأدلة: تحقق من الطلب والمتطلبات الرسمية."
      : "Pre-evidence decision: customer demand and official requirements need verification.";
  de.next_test_action = total
    ? ar
      ? "راجع الأدلة وتحقق من المتطلبات الرسمية قبل أي تجربة تشغيلية."
      : "Review the evidence and verify official requirements before any operational test."
    : ar
      ? "قابل خمسة عملاء محتملين واجمع نوايا بلا دفع."
      : "Interview five potential customers and collect no-payment intent.";
  p.decision_engine = de;
  p.state.decision = de.decision;
  setTxt("decision-main", de.decision);
  setTxt("decision-reason", de.reason);
  setTxt("decision-next", T[lang].nexttest + ": " + de.next_test_action);
  const passportDecision = document.querySelectorAll("#passport-table .pv2")[4];
  if (passportDecision) passportDecision.textContent = de.decision;
  window._passportText = [...document.querySelectorAll("#passport-table tr")]
    .map((tr) => tr.cells[0].textContent + ": " + tr.cells[1].textContent)
    .join("\n");
  const last = document.querySelectorAll("#opp-map .opp-node")[5];
  if (last) last.textContent = (ar ? "القرار: " : "Decision: ") + de.decision;
}

function clearProof() {
  buildProof();
  if (currentPlan) delete currentPlan.proof_summary;
  saveSession();
}

function exportCSV() {
  const ints = [...document.querySelectorAll(".p-int")].map((s) => s.value);
  const prices = [...document.querySelectorAll(".p-price")].map((s) => s.value);
  const freqs = [...document.querySelectorAll(".p-freq")].map((s) => s.value);
  const concs = [...document.querySelectorAll(".p-concern")].map(
    (s) => s.value,
  );
  const pres = [...document.querySelectorAll(".p-pre")].map((s) => s.value);
  const csvCell = (value) => {
    let text = String(value ?? "");
    if (/^[\s\uFEFF]*[=+@-]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  };
  let csv = "row,interested,price_aed,frequency,concern,evidence_strength\r\n";
  for (let i = 0; i < 10; i++) {
    const cells = [
      i + 1,
      ints[i] || "",
      prices[i] || "",
      freqs[i] || "",
      concs[i] || "",
      pres[i] || "",
    ];
    csv += cells.map(csvCell).join(",") + "\r\n";
  }
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "Khotwa_UAE_Validation_Data.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function copyShare() {
  const txt = document.getElementById("share-text").textContent || "";
  function done() {
    document.getElementById("shareBtn").textContent = "✓ " + T[lang].copied;
    setTimeout(() => {
      document.getElementById("shareBtn").textContent = T[lang].copy;
    }, 1500);
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(txt)
      .then(done)
      .catch(() => {
        if (fallbackCopy(txt)) done();
      });
  } else if (fallbackCopy(txt)) done();
}

function waText() {
  return document.getElementById("wa-text").textContent || "";
}
function copyDone() {
  document.getElementById("waBtn").textContent = "✓ " + T[lang].copied;
  setTimeout(() => {
    document.getElementById("waBtn").textContent = T[lang].copy;
  }, 1500);
}
function copyWA() {
  const txt = waText();
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(txt)
      .then(copyDone)
      .catch(() => {
        if (fallbackCopy(txt)) copyDone();
      });
  } else if (fallbackCopy(txt)) copyDone();
}
function fallbackCopy(txt) {
  const ta = document.createElement("textarea");
  ta.value = txt;
  ta.style.position = "fixed";
  ta.style.top = "-9999px";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (e) {}
  document.body.removeChild(ta);
  if (!copied) alert(txt);
  return copied;
}
function openWA() {
  const url = "https://wa.me/?text=" + encodeURIComponent(waText());
  window.open(url, "_blank");
}

function currentIdea() {
  var el = document.getElementById("idea");
  var v = el ? (el.value || "").trim() : "";
  if (!v && currentPlan && currentPlan.readiness_report)
    v = currentPlan.readiness_report.idea || "";
  return v;
}

var _chatBusy = false;
function advisorFallback() {
  return lang === "ar"
    ? {
        title: "الخطوة التالية",
        summary: "المستشار غير متاح الآن.",
        points: [],
        next_action:
          "اسأل خمسة عملاء محتملين كيف يحلون المشكلة حالياً وسجل إجاباتهم.",
        caution: "تحقق من المتطلبات الرسمية قبل الدفع أو التشغيل التجاري.",
      }
    : {
        title: "Next validation step",
        summary: "The Advisor is unavailable right now.",
        points: [],
        next_action:
          "Ask five potential customers how they solve this today and record their answers.",
        caution:
          "Verify official requirements before payment or commercial operation.",
      };
}
function renderAdvisorCard(node, answer) {
  node.replaceChildren();
  node.className = "advisor-card";
  const h = document.createElement("h3"),
    summary = document.createElement("p");
  h.textContent =
    answer.title || (lang === "ar" ? "مستشار خطوة" : "Khotwa Advisor");
  summary.textContent = answer.summary || "";
  node.append(h, summary);
  (Array.isArray(answer.points) ? answer.points : [])
    .slice(0, 5)
    .forEach((point) => {
      const p = document.createElement("div"),
        b = document.createElement("b"),
        body = document.createElement("span");
      p.className = "advisor-point";
      b.textContent = (point.title || "").replace(/[:：]\s*$/, "") + ": ";
      body.textContent = point.text || "";
      p.append(b, body);
      node.appendChild(p);
    });
  if (answer.next_action) {
    const next = document.createElement("div"),
      b = document.createElement("b");
    next.className = "advisor-action";
    b.textContent = lang === "ar" ? "الخطوة التالية: " : "Next action: ";
    const text = document.createElement("span");
    text.textContent = answer.next_action;
    next.append(b, text);
    node.appendChild(next);
  }
  if (answer.caution) {
    const c = document.createElement("div"),
      b = document.createElement("b");
    c.className = "advisor-caution";
    b.textContent = lang === "ar" ? "تنبيه: " : "Caution: ";
    const text = document.createElement("span");
    text.textContent = answer.caution;
    c.append(b, text);
    node.appendChild(c);
  }
}
async function askQuestion() {
  if (_chatBusy) return;
  var input = document.getElementById("chat-input");
  if (!input) return;
  var q = (input.value || "").trim();
  if (!q) return;
  var box = document.getElementById("chat-messages");
  if (!box) return;
  input.value = "";
  _chatBusy = true;
  var sendBtn = document.getElementById("sendBtn");
  if (sendBtn) sendBtn.disabled = true;
  var u = document.createElement("div");
  u.className = "msg-b msg-user";
  u.textContent = q;
  box.appendChild(u);
  var ai = document.createElement("div");
  ai.className = "msg-b msg-ai";
  ai.textContent = T[lang].thinking || "…";
  box.appendChild(ai);
  box.scrollTop = box.scrollHeight;
  var answered = false;
  function finish(answer) {
    if (answered) return;
    answered = true;
    renderAdvisorCard(ai, answer);
    chatHistory.push(
      { role: "user", content: q },
      { role: "assistant", content: JSON.stringify(answer) },
    );
    chatHistory = chatHistory.slice(-8);
    box.scrollTop = box.scrollHeight;
    _chatBusy = false;
    if (sendBtn) sendBtn.disabled = false;
  }
  try {
    var ctx = currentPlan
      ? JSON.stringify(currentPlan)
      : JSON.stringify({
          idea: currentIdea(),
          category: (document.getElementById("category") || {}).value,
          user_type: (document.getElementById("user_type") || {}).value,
          budget: (document.getElementById("budget") || {}).value,
          _region: (document.getElementById("region") || {}).value,
          _context: (document.getElementById("context") || {}).value,
        });
    var ctrl = new AbortController();
    var to = setTimeout(function () {
      ctrl.abort();
    }, 45000);
    var resp = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: q,
        lang,
        plan_context: ctx,
        history: chatHistory,
      }),
      signal: ctrl.signal,
    });
    clearTimeout(to);
    var data = null;
    try {
      data = await resp.json();
    } catch (parseErr) {
      data = null;
    }
    var ans =
      resp.ok && data && data.answer && typeof data.answer === "object"
        ? data.answer
        : null;
    finish(ans || advisorFallback());
  } catch (e) {
    console.error("ask error (using local advisor):", e && e.name);
    finish(advisorFallback());
  }
}

async function exportPDF() {
  if (!currentPlan) return;
  const btn = document.getElementById("pdfBtn");
  const orig = btn.textContent;
  btn.textContent = "...";
  btn.disabled = true;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 65000);
  try {
    const resp = await fetch("/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({}, currentPlan, { _lang: lang })),
      signal: ctrl.signal,
    });
    if (!resp.ok) throw new Error("pdf failed");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "Khotwa_UAE_Founder_Report.pdf";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error("PDF error", e);
    alert(T[lang].error);
  } finally {
    clearTimeout(timer);
    btn.textContent = T[lang].pdf;
    btn.disabled = false;
  }
}

function resetApp() {
  resetInvestment();
  document.body.classList.remove("has-plan");
  currentPlan = null;
  planVariants = { en: null, ar: null };
  document
    .getElementById("journey-home")
    .appendChild(document.getElementById("journey-block"));
  renderJourney();
  renderDashboardSummary();
  chatHistory = [];
  localizedStatus("error", "", "");
  document.getElementById("chat-messages").replaceChildren();
  document.getElementById("results").style.display = "none";
  document.getElementById("idea").value = "";
  document.getElementById("category").selectedIndex = 0;
  document.getElementById("category").dataset.touched = "";
  document.getElementById("user_type").selectedIndex = 0;
  document.getElementById("region").selectedIndex = 0;
  document.getElementById("context").selectedIndex = 0;
  document.getElementById("budget").value = 10000;
  updateBudget(10000);
  document.getElementById("proof-table").replaceChildren();
  document.getElementById("discovery-results").replaceChildren();
  setEntry("existing");
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch (e) {}
  window.scrollTo({ top: 0, behavior: motionBehavior() });
}

function toggleTheme() {
  var r = document.documentElement;
  var dark = r.getAttribute("data-theme") === "dark";
  if (dark) {
    r.removeAttribute("data-theme");
    document.getElementById("themeBtn").textContent = "\u263e";
  } else {
    r.setAttribute("data-theme", "dark");
    document.getElementById("themeBtn").textContent = "\u2600";
  }
  styleCharts();
  saveSession();
}
var _loaderTimer;
function stopLoader() {
  clearInterval(_loaderTimer);
  var w = document.getElementById("loader");
  if (w) w.classList.remove("show");
}

// ---- animate proof counters ----
function animateCounters() {
  document.querySelectorAll("#proof-stats .v").forEach((el) => {
    el.textContent = el.dataset.target;
  });
}

// ---- floating chat ----
function heroStart() {
  setEntry("existing");
  document
    .querySelector(".input-card")
    .scrollIntoView({ behavior: motionBehavior() });
  setTimeout(function () {
    document.getElementById("idea").focus();
  }, 400);
}
function runDemoStory() {
  setEntry("existing");
  document.getElementById("idea").value = DEMOS[lang][0];
  var ut = document.getElementById("user_type");
  if (ut) ut.value = "residents";
  var rg = document.getElementById("region");
  if (rg) rg.value = "Dubai";
  var cx = document.getElementById("context");
  if (cx) cx.value = "Local service";
  document.getElementById("category").dataset.touched = "";
  suggestCategory();
  document.getElementById("budget").value = 10000;
  updateBudget(10000);
  document
    .querySelector(".input-card")
    .scrollIntoView({ behavior: motionBehavior() });
  generate();
}
