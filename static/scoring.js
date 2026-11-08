// Same contract as scoring.py: total is unavailable until all five are assessed.
const SCORE_KEYS = [
  "local_fit",
  "clear_customer",
  "low_starting_cost",
  "easy_first_step",
  "growth_potential",
];
function aggregateScores(sc) {
  let n = 0,
    sum = 0;
  for (const k of SCORE_KEYS) {
    const item = sc[k] || {};
    const reason = typeof item.reason === "string" ? item.reason.trim() : "";
    const valid =
      item.source !== "fallback" &&
      typeof item.score === "number" &&
      Number.isInteger(item.score) &&
      item.score >= 0 &&
      item.score <= 5 &&
      reason.length >= 12 &&
      !["one line", "one-line reason"].includes(reason.toLowerCase()) &&
      !/insufficient information|not assessed|لا توجد معلومات كافية/i.test(
        reason,
      );
    if (valid) {
      n++;
      sum += item.score;
    } else {
      item.score = null;
      item.status = "not_assessed";
      item.source = "missing";
    }
    sc[k] = item;
  }
  sc.maximum = 25;
  sc.assessed_count = n;
  sc.assessed_sum = sum;
  sc.total = n === 5 ? sum : null;
  sc.status = n === 5 ? "provisional" : "incomplete";
  return sc;
}
function scoreLabel(sc) {
  return Number.isInteger(sc?.total)
    ? sc.total + "/25"
    : lang === "ar"
      ? "غير مكتمل"
      : "Incomplete";
}
function updateEvidenceScore(total, yes, intent, reservations, paid, repeat) {
  const sc = currentPlan?.opportunity_score;
  if (!sc) return;
  if (total >= 5) {
    if (!sc._before_evidence)
      sc._before_evidence = JSON.parse(JSON.stringify(sc.clear_customer || {}));
    sc.clear_customer = {
      score: paid || repeat ? 5 : reservations ? 4 : intent ? 3 : yes ? 2 : 1,
      status: "scored",
      source: "recorded_evidence",
      reason:
        lang === "ar"
          ? "بناءً على إدخالات المستخدم في وضع الإثبات؛ لم تُتحقق مستقلاً."
          : "Based on user-recorded Proof Mode entries; not independently verified.",
      improve:
        lang === "ar"
          ? "اختبر السلوك مع عينة أكبر."
          : "Test behavior with a larger sample.",
    };
  } else if (sc._before_evidence) {
    sc.clear_customer = sc._before_evidence;
    delete sc._before_evidence;
  }
  aggregateScores(sc);
}
function renderScores(sc) {
  aggregateScores(sc);
  const ar = lang === "ar",
    g = document.getElementById("gauge");
  g.replaceChildren();
  const value = uiNode(
    "b",
    "",
    Number.isInteger(sc.total) ? String(sc.total) : "—",
  );
  value.id = "gauge-num";
  const center = uiNode("div", "gv");
  center.append(value, uiNode("small", "", ar ? "من 25" : "out of 25"));
  g.append(center);
  const bars = document.getElementById("score-bars");
  bars.replaceChildren();
  const measures = ar
    ? [
        "مدى توافق الفكرة مع المؤسس والسوق",
        "وضوح الشريحة والحاجة",
        "قدرة التمويل على دعم الاختبار",
        "إمكانية تنفيذ اختبار أول",
        "إمكانات التكرار والتوسع",
      ]
    : [
        "Fit between founder, idea and market",
        "Clarity of the customer and need",
        "Affordability of an initial test",
        "Practicality of a first experiment",
        "Potential for repeatable growth",
      ];
  const why = ar
    ? [
        "الملاءمة تحدد أين تبدأ الاختبار.",
        "وضوح العميل يوجّه جمع الأدلة.",
        "تكلفة الاختبار تحدد الالتزام الأولي.",
        "سهولة التجربة تقلل كلفة التعلّم.",
        "التكرار يحدد فرص التطوير بعد التحقق.",
      ]
    : [
        "Fit helps focus the first test.",
        "A clear customer guides evidence collection.",
        "Test affordability limits the first commitment.",
        "A practical experiment reduces the cost of learning.",
        "Repeatability guides development after validation.",
      ];
  SCORE_KEYS.forEach((key, i) => {
    const item = sc[key],
      row = uiNode("article", "score-row"),
      top = uiNode("div", "score-top");
    const track = uiNode("div", "score-track"),
      fill = uiNode("div", "score-fill");
    fill.style.width = item.score === null ? "0%" : item.score * 20 + "%";
    track.append(fill);
    top.append(
      uiNode("strong", "name", T[lang].snames[key]),
      track,
      uiNode("span", "val", item.score === null ? "—" : item.score + "/5"),
    );
    row.append(
      top,
      uiNode(
        "p",
        "score-measure",
        uiText("Measures: ", "يقيس: ") + measures[i],
      ),
      uiNode(
        "p",
        "score-why",
        uiText("Why it matters: ", "الأهمية: ") + why[i],
      ),
      uiNode(
        "span",
        "source-badge",
        item.score === null
          ? ar
            ? "لم يُقيّم"
            : "NOT ASSESSED"
          : item.source === "recorded_evidence"
            ? ar
              ? "أدلة مسجّلة · مُقيّم"
              : "RECORDED EVIDENCE · SCORED"
            : ar
              ? "افتراض ذكاء اصطناعي · مبدئي"
              : "AI ASSUMPTION · PROVISIONAL",
      ),
      uiNode("p", "score-reason", item.reason || ""),
      uiNode(
        "p",
        "score-improve",
        uiText("Improve: ", "للتحسين: ") +
          (item.improve ||
            uiText(
              "Gather specific evidence before assessment.",
              "اجمع أدلة محددة قبل التقييم.",
            )),
      ),
    );
    bars.append(row);
  });
  setTxt(
    "score-interp",
    (ar
      ? `تغطية التقييم: ${sc.assessed_count} من 5. `
      : `Assessment coverage: ${sc.assessed_count} of 5. `) +
      (sc.total === null
        ? ar
          ? "النتيجة غير مكتملة؛ لا نقاط للمعلومات المفقودة."
          : "Incomplete assessment; missing information earns no points."
        : ar
          ? "درجة مبدئية وليست احتمال نجاح تجاري."
          : "Provisional assessment, not a probability of business success."),
  );
  drawScoreArc(sc);
}
function refreshScoreDisplay() {
  if (!currentPlan) return;
  const sc = currentPlan.opportunity_score;
  renderScores(sc);
  renderFinanceIntegration();
  const cell = document.querySelectorAll("#passport-table .pv2")[3];
  if (cell) cell.textContent = scoreLabel(sc);
  window._passportText = [...document.querySelectorAll("#passport-table tr")]
    .map((r) => r.cells[0].textContent + ": " + r.cells[1].textContent)
    .join("\n");
  const share = document.getElementById("share-text");
  share.textContent = composeFounderShare();
}
