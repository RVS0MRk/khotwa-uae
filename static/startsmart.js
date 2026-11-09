// Presentation helpers: read existing plan/Proof Mode state without changing calculations.
const motionPreference = matchMedia("(prefers-reduced-motion: reduce)");
function motionBehavior() {
  return motionPreference.matches ? "instant" : "smooth";
}
function uiText(en, ar) {
  return lang === "ar" ? ar : en;
}
function uiNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}
function businessMarketParts(state) {
  const unknown =
    /^(?:not sure|unknown|undefined|null|غير متأكد|لست متأكداً|غير معلوم)$/i;
  const region =
    state.region === "UAE-wide"
      ? uiText("UAE-wide", "الإمارات")
      : T[lang].regions[state.region] || state.region || "";
  const context = T[lang].contexts[state.context] || state.context || "";
  return [region, context]
    .map((s) => s.trim())
    .filter((s, i, all) => s && !unknown.test(s) && all.indexOf(s) === i);
}
function polishLanguage() {
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  setTxt(
    "title",
    uiText("From idea to first step.", "من الفكرة إلى الخطوة الأولى."),
  );
  setTxt(
    "pitch",
    uiText(
      "Choose an idea, test real customer demand, and know what to do next — before spending heavily.",
      "اختر فكرة، واختبر طلب العملاء الحقيقي، واعرف خطوتك التالية قبل الإنفاق الكبير.",
    ),
  );
  [
    [
      "need-idea",
      "Get three ideas matched to your skills, budget and market.",
      "اكتشف ثلاث أفكار وفق مهاراتك وميزانيتك وسوقك.",
    ],
    [
      "have-idea",
      "Validate demand and build your first action plan.",
      "اختبر الطلب وابنِ خطة خطواتك الأولى.",
    ],
  ].forEach(([id, en, ar]) =>
    document
      .getElementById(id)
      .appendChild(uiNode("small", "", uiText(en, ar))),
  );
  const trust = document.getElementById("hero-trust");
  trust.replaceChildren();
  [
    ["No login required", "بلا تسجيل دخول"],
    ["Validate before spending", "تحقق قبل الإنفاق"],
    ["Real customer evidence", "أدلة من عملاء حقيقيين"],
    ["Founder report", "تقرير المؤسس"],
  ].forEach(([en, ar]) =>
    trust.appendChild(uiNode("span", "", uiText(en, ar))),
  );
  setTxt("start-validation", uiText("Start validation →", "ابدأ التحقق ←"));
  setTxt(
    "bys-l1",
    uiText("Your budget · USER INPUT", "ميزانيتك · إدخال المستخدم"),
  );
  setTxt(
    "bys-l2",
    uiText("Estimated first-test cost", "تكلفة الاختبار الأول المقدّرة"),
  );
  setTxt(
    "bys-l3",
    uiText("Budget remaining after test", "الميزانية المتبقية بعد الاختبار"),
  );
  setTxt(
    "chat-sub",
    uiText(
      "Ask about your current business plan",
      "اسأل عن خطة مشروعك الحالية",
    ),
  );
  setTxt("cl-text", uiText("Advisor", "المستشار"));
  setTxt(
    "chat-note",
    uiText(
      "Open Khotwa Advisor for a focused question about your customers, risks, pricing or official requirements.",
      "افتح مستشار خطوة للسؤال عن العملاء أو المخاطر أو التسعير أو المتطلبات الرسمية.",
    ),
  );
  document
    .getElementById("entry-choice")
    .setAttribute(
      "aria-label",
      uiText("Choose how to start", "اختر طريقة البدء"),
    );
  document
    .getElementById("result-nav")
    .setAttribute("aria-label", uiText("Plan sections", "أقسام الخطة"));
  document
    .getElementById("chatPanel")
    .setAttribute("aria-label", uiText("Khotwa Advisor", "مستشار خطوة"));
  const suggestions = [
    ["Biggest risks", "أكبر المخاطر"],
    ["First 3 strong leads", "أول ثلاثة عملاء محتملين"],
    ["Pricing test", "اختبار التسعير"],
    ["Licences & requirements", "التراخيص والمتطلبات"],
  ];
  const suggested = document.getElementById("suggested");
  suggested.replaceChildren();
  suggestions.forEach(([en, ar]) => {
    const b = uiNode("button", "chip", uiText(en, ar));
    b.type = "button";
    b.onclick = () => {
      document.getElementById("chat-input").value = b.textContent;
      askQuestion();
    };
    suggested.appendChild(b);
  });
  labelProofRows();
  renderJourney();
  renderDashboardSummary();
  decorateResources();
}
function renderJourney() {
  const j = document.getElementById("journey");
  if (!j) return;
  const proof = currentPlan?.proof_summary || {},
    responses = Number(proof.total_responses) || 0;
  const purchases =
    (Number(proof.actual_payments) || 0) +
    (Number(proof.repeat_customers) || 0);
  const preparing =
    currentPlan &&
    document.getElementById("result-tab-6")?.getAttribute("aria-selected") ===
      "true";
  // Review stage only: visiting requirements never marks preparation complete.
  const stage = !currentPlan
    ? 0
    : purchases > 0
      ? 4
      : preparing
        ? 3
        : responses > 0
          ? 2
          : 1;
  const labels =
    lang === "ar"
      ? ["الفكرة", "التحقق", "الأدلة", "الاستعداد", "القرار"]
      : ["Idea", "Validate", "Evidence", "Prepare", "Decide"];
  j.replaceChildren();
  j.dataset.stage = String(stage);
  j.setAttribute("aria-label", uiText("Founder journey", "رحلة المؤسس"));
  labels.forEach((label, i) => {
    const done = i === 0 && !!currentPlan;
    const item = uiNode(
      "div",
      "jstep " + (stage === i ? "current" : done ? "completed" : "upcoming"),
    );
    const number = uiNode(
      "span",
      "stage-number",
      done ? "✓" : String(i + 1).padStart(2, "0"),
    );
    number.setAttribute("aria-hidden", "true");
    item.append(number, uiNode("span", "stage-label", label));
    if (stage === i) item.setAttribute("aria-current", "step");
    item.setAttribute(
      "aria-label",
      label +
        " — " +
        (stage === i
          ? uiText("current", "الحالية")
          : done
            ? uiText("idea entered", "تم إدخال الفكرة")
            : uiText("not marked complete", "لم تكتمل")),
    );
    j.appendChild(item);
  });
  setTxt(
    "journey-note",
    stage === 3
      ? uiText(
          "Review official requirements. Preparation has not been marked complete.",
          "راجع المتطلبات الرسمية. لم يُسجّل اكتمال الاستعداد.",
        )
      : stage === 4
        ? uiText(
            "Review recorded purchase behavior; this is not a launch approval.",
            "راجع سلوك الشراء المسجّل؛ هذه ليست موافقة على إطلاق المشروع.",
          )
        : stage === 2
          ? uiText(
              "Customer entries recorded. Evidence strength matters more than compliments.",
              "تم تسجيل إجابات العملاء. قوة الدليل أهم من المجاملات.",
            )
          : uiText(
              "A guide to your next focus. Stages are not a completion checklist.",
              "دليل لتركيزك التالي. المراحل ليست قائمة إنجاز مكتملة.",
            ),
  );
}
function renderDashboardSummary() {
  const root = document.getElementById("dashboard-summary");
  if (!root) return;
  root.hidden = !currentPlan;
  if (!currentPlan) return;
  const s = currentPlan.state || {},
    p = currentPlan.proof_summary || {};
  const heading = root.querySelector(".summary-heading");
  const existingActions = document.querySelector(".action-row");
  if (existingActions) root.append(existingActions);
  heading.replaceChildren();
  const title = uiNode("div");
  title.append(
    uiNode("div", "section-label", uiText("YOUR BUSINESS", "مشروعك")),
    uiNode("h2", "", s.idea || currentPlan.readiness_report?.idea || ""),
    uiNode(
      "p",
      "summary-description",
      (s.target_customer || "") +
        " · " +
        (T[lang].categories[T.en.categories.indexOf(s.category)] ||
          s.category ||
          ""),
    ),
  );
  const market = uiNode("div", "summary-market");
  businessMarketParts(s).forEach((part, i) =>
    market.append(uiNode(i === 0 ? "b" : "span", "", part)),
  );
  const subtitle = uiNode(
    "p",
    "ai-business-name",
    uiText("AI suggestion: ", "اقتراح ذكاء اصطناعي: ") +
      (currentPlan.business_name_suggestion || ""),
  );
  title.append(subtitle);
  const actions = document.querySelector(".action-row");
  const menu = uiNode("details", "dashboard-actions"),
    summary = uiNode("summary", "btn btn-light", uiText("Actions", "إجراءات"));
  menu.open = innerWidth >= 769;
  menu.append(summary, actions);
  heading.append(title, market, menu);
  let evidence = uiText("No evidence recorded", "لا توجد أدلة مسجّلة");
  if (p.total_responses)
    evidence = uiText(
      p.total_responses +
        (Number(p.total_responses) === 1 ? " response" : " responses"),
      p.total_responses +
        (Number(p.total_responses) === 1 ? " إجابة" : " إجابات"),
    );
  const detail = [];
  if (p.no_payment_reservations)
    detail.push(
      uiText(
        p.no_payment_reservations + " reservations",
        p.no_payment_reservations + " حجوزات",
      ),
    );
  if (p.actual_payments)
    detail.push(
      uiText(
        p.actual_payments + " payments",
        p.actual_payments + " عمليات دفع",
      ),
    );
  if (p.repeat_customers)
    detail.push(
      uiText(
        p.repeat_customers + " repeat customers",
        p.repeat_customers + " عملاء متكررين",
      ),
    );
  const stats = root.querySelector(".summary-stats");
  stats.replaceChildren();
  [
    [
      uiText("Your budget", "ميزانيتك"),
      formatAED(s.user_budget_aed || 0),
      uiText("USER INPUT", "إدخال المستخدم"),
    ],
    [
      uiText("Preliminary score", "الدرجة المبدئية"),
      scoreLabel(currentPlan.opportunity_score),
      uiText("Mainly assumptions", "افتراضات في الغالب"),
    ],
    [
      uiText("Evidence status", "حالة الأدلة"),
      evidence,
      detail.join(" · ") ||
        uiText("From Proof Mode only", "من وضع الإثبات فقط"),
    ],
    [
      uiText("TODAY", "اليوم"),
      s.first_action || currentPlan.first_step_today || "",
      "",
    ],
  ].forEach(([label, value, sub], i) => {
    const box = uiNode("div", "summary-stat" + (i === 3 ? " today" : ""));
    box.append(
      uiNode("small", "", label),
      uiNode("strong", "", value),
      uiNode("span", "sub", sub),
    );
    stats.appendChild(box);
  });
  let risk = root.querySelector(".summary-risk");
  if (!risk) {
    risk = uiNode("p", "summary-risk");
    stats.after(risk);
  }
  risk.textContent =
    uiText("Main risk hypothesis: ", "فرضية الخطر الرئيسي: ") +
    (currentPlan.readiness_report?.main_risk ||
      uiText("Not assessed yet", "لم يُقيّم بعد"));
  const journey = document.getElementById("journey-block");
  if (journey.parentElement !== root) root.appendChild(journey);
  renderJourney();
  renderFinancialGuardrail();
  styleCharts();
  renderFinanceIntegration();
  compactInvestmentLink();
}
function renderFinancialGuardrail() {
  if (!currentPlan) return;
  const box = document.getElementById("financial-detail");
  box.replaceChildren();
  const cost = currentPlan.total_estimated_cost_aed,
    gap = currentPlan.estimated_budget_gap_aed;
  box.appendChild(
    uiNode(
      "span",
      "",
      uiText(
        "Separate setup/path estimate: ",
        "تقدير منفصل للمسار / التأسيس: ",
      ) +
        (cost == null
          ? uiText("Not estimated yet", "لم يُقدّر بعد")
          : Number(cost).toLocaleString() +
            " " +
            currency() +
            " · " +
            uiText("AI ESTIMATE", "تقدير ذكاء اصطناعي")),
    ),
  );
  if (Number(gap) > 0)
    box.appendChild(
      uiNode(
        "div",
        "budget-gap",
        uiText("Budget gap: ", "فجوة الميزانية: ") +
          Number(gap).toLocaleString() +
          " " +
          currency() +
          " — " +
          uiText(
            "Validate demand before increasing spending.",
            "تحقق من الطلب قبل زيادة الإنفاق.",
          ),
      ),
    );
  const test = Number(currentPlan.state?.estimated_test_cost_aed) || 0,
    budget = Number(currentPlan.state?.user_budget_aed) || 0;
  if (test > 0) {
    const value = document.getElementById("bys-test");
    value.replaceChildren(
      document.createTextNode(test.toLocaleString() + " " + currency()),
      uiNode(
        "span",
        "source-badge assumption",
        uiText("AI ESTIMATE", "تقدير ذكاء اصطناعي"),
      ),
    );
  }
  if (test > budget)
    box.appendChild(
      uiNode(
        "div",
        "budget-gap",
        uiText("First-test budget gap: ", "فجوة ميزانية الاختبار الأول: ") +
          (test - budget).toLocaleString() +
          " " +
          currency(),
      ),
    );
}
function labelProofRows() {
  const table = document.getElementById("proof-table");
  if (!table?.rows.length) return;
  const headings = [...table.rows[0].cells].map((c) => c.textContent);
  [...table.rows].slice(1).forEach((row, index) =>
    [...row.cells].forEach((cell, i) => {
      cell.dataset.label = headings[i];
      cell.dataset.customer = uiText("Customer", "العميل");
      const input = cell.querySelector("input,select");
      if (input)
        input.setAttribute(
          "aria-label",
          uiText("Customer ", "العميل ") + (index + 1) + " — " + headings[i],
        );
    }),
  );
}
function renderProofPolish() {
  const p = currentPlan?.proof_summary || {},
    total = Number(p.total_responses) || 0;
  setTxt(
    "proof-progress-title",
    uiText("Customer validation", "التحقق مع العملاء"),
  );
  const count = document.getElementById("proof-progress-count"),
    fraction = uiNode("bdi", "", total + " / 10");
  fraction.dir = "ltr";
  count.replaceChildren(
    fraction,
    document.createTextNode(
      uiText(
        total === 1 ? " entry recorded" : " entries recorded",
        total === 1 ? " إدخال مسجّل" : " إدخالات مسجّلة",
      ),
    ),
  );
  const progress = document.getElementById("proof-progress");
  progress.style.width = total * 10 + "%";
  progress.parentElement.setAttribute("aria-valuenow", String(total));
  progress.parentElement.setAttribute(
    "aria-label",
    uiText("Proof Mode entries recorded", "إدخالات وضع الإثبات المسجّلة"),
  );
  // Keep all original counters/order; add the three stronger evidence counts.
  const stats = document.getElementById("proof-stats");
  [
    ["stated_intent", "Stated intent", "نية شراء معلنة"],
    ["actual_payments", "Actual payment", "دفع فعلي"],
    ["repeat_customers", "Repeat behavior", "سلوك متكرر"],
  ].forEach(([key, en, ar]) => {
    const card = uiNode("div", "stat-card");
    card.dataset.evidence = key;
    const value = uiNode("div", "v", String(p[key] || 0));
    value.dataset.target = String(p[key] || 0);
    card.append(value, uiNode("div", "l", uiText(en, ar)));
    stats.appendChild(card);
  });
  const defs = [
    ["interested", "Interest", "اهتمام"],
    ["stated_intent", "Stated intent", "نية شراء"],
    ["no_payment_reservations", "Waitlist / reservation", "قائمة انتظار / حجز"],
    ["actual_payments", "Payment", "دفع"],
    ["repeat_customers", "Repeat behavior", "سلوك متكرر"],
  ];
  const highest = defs.reduce(
    (max, [key], i) => (Number(p[key]) > 0 ? i : max),
    -1,
  );
  const ladder = document.getElementById("evidence-ladder");
  ladder.setAttribute("aria-label", uiText("Evidence strength", "قوة الدليل"));
  ladder.replaceChildren();
  ladder.dataset.highest = String(highest);
  defs.forEach(([, en, ar], i) => {
    const rung = uiNode(
      "div",
      "evidence-rung" + (i === highest ? " achieved" : ""),
      uiText(en, ar),
    );
    if (i === highest)
      rung.appendChild(
        uiNode("strong", "", uiText("Highest recorded", "أعلى دليل مسجّل")),
      );
    ladder.appendChild(rung);
  });
  setTxt(
    "evidence-philosophy",
    uiText(
      "Evidence > compliments. Interest alone does not validate demand.",
      "الدليل أهم من المجاملات. الاهتمام وحده لا يثبت الطلب.",
    ),
  );
  labelProofRows();
  renderDashboardSummary();
  renderJourney();
}
function decorateResources() {
  document.querySelectorAll(".resources .res-link a").forEach((a) => {
    if (a.querySelector(".resource-purpose")) return;
    const regional = a.id !== "federal-resource";
    a.appendChild(
      uiNode(
        "span",
        "resource-purpose",
        regional
          ? uiText(
              "Activity and licensing requirements for Abu Dhabi.",
              "متطلبات الأنشطة والتراخيص في أبوظبي.",
            )
          : uiText(
              "Official guidance on starting a business in the UAE.",
              "إرشادات رسمية لبدء مشروع في الإمارات.",
            ),
      ),
    );
  });
}
function startLoader(discovery = false) {
  clearInterval(_loaderTimer);
  const wrap = document.getElementById("loader");
  document
    .getElementById(discovery ? "discovery-card" : "genBtn")
    .insertAdjacentElement(discovery ? "beforeend" : "afterend", wrap);
  wrap.classList.add("show");
  wrap.setAttribute("role", "status");
  wrap.setAttribute("aria-live", "polite");
  const messages = discovery
    ? lang === "ar"
      ? [
          "قراءة مهاراتك واهتماماتك…",
          "استكشاف فرص قابلة للاختبار…",
          "إعداد ثلاث أفكار للمراجعة…",
        ]
      : [
          "Reading your skills and interests…",
          "Exploring ideas you can test…",
          "Preparing three ideas to review…",
        ]
    : lang === "ar"
      ? [
          "فهم فكرة مشروعك…",
          "تحديد العملاء المحتملين…",
          "بناء خطة التحقق…",
          "إعداد خطوتك الأولى…",
        ]
      : [
          "Understanding your idea…",
          "Mapping the target customer…",
          "Building your validation plan…",
          "Preparing your first action…",
        ];
  const steps = document.getElementById("generation-steps");
  steps.replaceChildren(...messages.map(() => uiNode("span")));
  let i = 0;
  const paint = () => {
    setTxt("loader-text", messages[i]);
    [...steps.children].forEach((n, index) =>
      n.classList.toggle("active", index <= i),
    );
  };
  paint();
  setTxt(
    "generation-note",
    uiText(
      "Organising your request. Steps indicate the workflow, not live model telemetry.",
      "جارٍ تنظيم طلبك. المراحل توضح سير العمل ولا تمثل تقدماً لحظياً للنموذج.",
    ),
  );
  if (!motionPreference.matches)
    _loaderTimer = setInterval(() => {
      i = Math.min(i + 1, messages.length - 1);
      paint();
      if (i === messages.length - 1) clearInterval(_loaderTimer);
    }, 1800);
}
const scoreAnimations = new WeakMap();
function countUp(id, to, dur) {
  const el = document.getElementById(id);
  if (!el) return;
  cancelAnimationFrame(scoreAnimations.get(el));
  if (motionPreference.matches) {
    el.textContent = String(to);
    return;
  }
  const start = performance.now();
  function tick(now) {
    if (!el.isConnected) return;
    if (motionPreference.matches) {
      el.textContent = String(to);
      return;
    }
    const p = Math.min(1, (now - start) / dur);
    el.textContent = String(Math.round((1 - Math.pow(1 - p, 3)) * to));
    if (p < 1) scoreAnimations.set(el, requestAnimationFrame(tick));
  }
  scoreAnimations.set(el, requestAnimationFrame(tick));
}
function revealInit() {
  document.querySelectorAll(".reveal").forEach((n) => {
    n.classList.remove("reveal");
    n.style.transitionDelay = "";
  });
}
let advisorReturnFocus;
function toggleChat() {
  const panel = document.getElementById("chatPanel"),
    open = !panel.classList.contains("open");
  panel.classList.toggle("open", open);
  panel.setAttribute("aria-hidden", String(!open));
  panel.inert = !open;
  document
    .getElementById("chatLauncher")
    .setAttribute("aria-expanded", String(open));
  const mobile = matchMedia("(max-width:600px)").matches;
  panel.setAttribute("aria-modal", String(open && mobile));
  document.getElementById("chat-backdrop").hidden = !(open && mobile);
  document.body.classList.toggle("advisor-open", open && mobile);
  if (open) {
    advisorReturnFocus = document.activeElement;
    setTimeout(
      () => {
        if (
          panel.classList.contains("open") &&
          !panel.contains(document.activeElement)
        )
          document.getElementById("chat-input").focus({ preventScroll: true });
      },
      motionPreference.matches ? 0 : 220,
    );
    const messages = document.getElementById("chat-messages");
    if (!messages.dataset.greeted) {
      messages.dataset.greeted = "1";
      messages.appendChild(
        uiNode(
          "div",
          "msg-b msg-ai",
          currentPlan ? T[lang].chatGreetPlan : T[lang].chatGreetNoPlan,
        ),
      );
    }
  } else advisorReturnFocus?.focus({ preventScroll: true });
}
document.addEventListener("keydown", (e) => {
  const panel = document.getElementById("chatPanel");
  if (!panel.classList.contains("open")) return;
  if (e.key === "Escape") {
    e.preventDefault();
    toggleChat();
  }
  if (e.key === "Tab") {
    const focusable = [
      ...panel.querySelectorAll(
        "button:not(:disabled),input:not(:disabled),a[href]",
      ),
    ];
    const first = focusable[0],
      last = focusable.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
});
// Move the mobile launcher out of the way of visible form controls. This keeps the
// full content width while retaining an always reachable assistant entry point.
function positionAdvisorLauncher() {
  document.getElementById("chatLauncher").style.transform = "";
}

let launcherFrame;
addEventListener(
  "scroll",
  () => {
    cancelAnimationFrame(launcherFrame);
    launcherFrame = requestAnimationFrame(positionAdvisorLauncher);
  },
  { passive: true },
);
addEventListener("resize", positionAdvisorLauncher);

function styleCharts() {
  const color = getComputedStyle(document.documentElement)
    .getPropertyValue("--muted")
    .trim();
  const border = getComputedStyle(document.documentElement)
    .getPropertyValue("--line")
    .trim();
  if (typeof Chart !== "undefined") {
    [timelineChart, costChart].filter(Boolean).forEach((chart) => {
      chart.options.color = color;
      if (chart.options.plugins?.legend?.labels)
        chart.options.plugins.legend.labels.color = color;
      if (chart.config.type === "bar")
        for (const axis of ["x", "y"]) {
          chart.options.scales[axis].ticks.color = color;
          chart.options.scales[axis].grid.color = border;
        }
      if (motionPreference.matches) chart.options.animation = false;
      chart.update("none");
    });
  } else if (currentPlan) {
    const canvas = document.getElementById("timeline-chart");
    canvas.hidden = true;
    canvas.parentElement.style.height = "auto";
    let note = document.getElementById("timeline-fallback");
    if (!note) {
      note = uiNode("p", "chart-fallback");
      note.id = "timeline-fallback";
      canvas.after(note);
    }
    note.textContent = (currentPlan.steps || [])
      .map(
        (s) =>
          uiText("Step ", "الخطوة ") +
          s.step_number +
          ": " +
          s.timeline_days +
          " " +
          uiText("days", "أيام"),
      )
      .join(" · ");
    const cost = document.getElementById("cost-chart");
    cost.hidden = true;
    cost.parentElement.style.height = "auto";
    let costs = document.getElementById("cost-fallback");
    if (!costs) {
      costs = uiNode("p", "chart-fallback");
      costs.id = "cost-fallback";
      cost.after(costs);
    }
    costs.textContent =
      currentPlan.total_estimated_cost_aed > 0
        ? uiText("Estimated path cost: ", "تكلفة المسار المقدّرة: ") +
          formatAED(currentPlan.total_estimated_cost_aed) +
          " · " +
          uiText("See the step costs above.", "راجع تكاليف الخطوات أعلاه.")
        : "";
  }
}

function chooseEntry(mode) {
  history.pushState(
    { khotwaEntry: mode },
    "",
    location.pathname + "#start-" + mode,
  );
  setEntry(mode);
  window.scrollTo({ top: 0, behavior: "instant" });
  (mode === "discover"
    ? document.getElementById("d-skills")
    : document.getElementById("idea")
  ).focus({ preventScroll: true });
}

motionPreference.addEventListener("change", styleCharts);

window.addEventListener("resize", () => {
  const menu = document.querySelector(".dashboard-actions");
  if (menu) menu.open = innerWidth >= 769;
});
