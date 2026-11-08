function renderFunding() {
  renderFinancingRoutes();
  const search = document.getElementById("funding-search"),
    kind = document.getElementById("funding-filter");
  if (!kind.options.length) {
    for (const [v, en, ar] of [
      ["all", "All support", "كل الدعم"],
      ["government", "Government support", "دعم حكومي"],
      ["finance", "Loans & guarantees", "قروض وضمانات"],
      ["accelerator", "Incubators & accelerators", "حاضنات ومسرّعات"],
    ]) {
      const o = uiNode("option", "", uiText(en, ar));
      o.value = v;
      kind.append(o);
    }
  } else
    for (const o of kind.options)
      o.textContent = {
        all: uiText("All support", "كل الدعم"),
        government: uiText("Government support", "دعم حكومي"),
        finance: uiText("Loans & guarantees", "قروض وضمانات"),
        accelerator: uiText("Incubators & accelerators", "حاضنات ومسرّعات"),
      }[o.value];
  investment.fundingFilters ||= {
    emirate: currentPlan?.state?.region || "UAE-wide",
    founder: "not_sure",
    stage: "all",
  };
  const specs = [
    [
      "emirate",
      "Emirate",
      "الإمارة",
      [
        ["UAE-wide", "All emirates", "كل الإمارات"],
        ...Object.keys(T.en.regions)
          .filter((x) => !["UAE-wide", "Other UAE"].includes(x))
          .map((x) => [x, T.en.regions[x], T.ar.regions[x]]),
      ],
    ],
    [
      "founder",
      "Founder status",
      "صفة المؤسس",
      [
        ["not_sure", "Not sure / all", "غير متأكد / الكل"],
        ["emirati", "Emirati", "إماراتي"],
        ["resident", "Resident", "مقيم"],
      ],
    ],
    [
      "stage",
      "Business stage",
      "مرحلة المشروع",
      [
        ["all", "All stages", "كل المراحل"],
        ["idea", "Idea", "فكرة"],
        ["early_revenue", "Early revenue", "إيراد مبكر"],
        ["growth", "Growth", "نمو"],
      ],
    ],
  ];
  const controls = document.querySelector(".directory-controls");
  for (const [key, en, ar, options] of specs) {
    let select = document.getElementById("funding-" + key),
      label = select?.parentElement;
    if (!select) {
      label = uiNode("label");
      select = uiNode("select");
      select.id = "funding-" + key;
      label.htmlFor = select.id;
      const title = uiNode("span");
      label.append(title, select);
      controls.append(label);
      select.onchange = () => {
        investment.fundingFilters[key] = select.value;
        renderFunding();
        saveSession();
      };
    }
    label.querySelector("span").textContent = uiText(en, ar);
    select.replaceChildren();
    for (const [value, english, arabic] of options) {
      const option = uiNode("option", "", uiText(english, arabic));
      option.value = value;
      select.append(option);
    }
    select.value = investment.fundingFilters[key] || options[0][0];
    if (!select.value) select.value = options[0][0];
  }
  const f = investment.fundingFilters,
    root = document.getElementById("funding-results");
  root.replaceChildren();
  search.placeholder = uiText(
    "Search support or institution",
    "ابحث عن دعم أو جهة",
  );
  const entries = fundingData.filter(
    (e) =>
      (kind.value === "all" || e.category === kind.value) &&
      JSON.stringify(e[lang])
        .toLowerCase()
        .includes(search.value.toLowerCase()) &&
      (f.emirate === "UAE-wide" ||
        e.emirates.includes("UAE") ||
        e.emirates.includes(f.emirate)) &&
      (f.founder !== "resident" ||
        !e.eligibility_tags.includes("emirati_only")) &&
      (f.stage === "all" || e.stages.includes(f.stage)),
  );
  for (const entry of entries) {
    const d = entry[lang],
      card = uiNode("details", "funding-card"),
      summary = uiNode("summary");
    card.dataset.fundingId = entry.id;
    const badge =
      entry.status === "dated_official"
        ? uiText(
            "DATED OFFICIAL · CONFIRM CURRENT TERMS",
            "رسمي مؤرخ · أكّد الشروط الحالية",
          )
        : entry.status === "partial"
          ? uiText("PARTIAL SOURCE CHECK", "مراجعة مصدر جزئية")
          : entry.status === "verified"
            ? uiText("OFFICIAL SOURCE CHECKED", "رُوجع المصدر الرسمي")
            : uiText("UNVERIFIED", "غير مُتحقق");
    summary.append(
      uiNode("span", "source-badge", badge),
      uiNode("h4", "", d.name),
      uiNode("p", "", entry.fit?.[lang] || d.target),
      uiNode("span", "details-hint", uiText("Details", "التفاصيل")),
    );
    if (entry.eligibility_tags.includes("emirati_only"))
      summary.append(
        uiNode(
          "span",
          "source-badge",
          uiText("Emirati founders only", "للمؤسسين الإماراتيين فقط"),
        ),
      );
    if (entry.intake === "closed")
      summary.append(
        uiNode(
          "span",
          "source-badge closed-intake",
          uiText(
            "Closed intake — watch for next cohort",
            "الدفعة مغلقة — تابع الدفعة التالية",
          ),
        ),
      );
    card.append(summary, uiNode("p", "", d.description));
    const dl = uiNode("dl");
    for (const [key, en, ar] of [
      ["support", "Support", "الدعم"],
      ["target", "Applicants", "المتقدمون"],
      ["scope", "Geography", "النطاق"],
      ["eligibility", "Eligibility information", "معلومات الأهلية"],
      ["limitations", "Limits / current status", "القيود والوضع الحالي"],
    ])
      dl.append(uiNode("dt", "", uiText(en, ar)), uiNode("dd", "", d[key]));
    card.append(dl);
    if (entry.programs) {
      const ul = uiNode("ul");
      entry.programs[lang].forEach((s) => ul.append(uiNode("li", "", s)));
      card.append(ul);
    }
    const links = [
      [entry.url, uiText("Official information ↗", "المعلومات الرسمية ↗")],
      [
        entry.apply,
        uiText("Application starting point ↗", "بداية التقديم ↗"),
      ],
      ...(entry.dated_sources || [])
        .filter(
          (s) =>
            s.kind === "historical_announcement" ||
            s.kind === "ministry_reference",
        )
        .map((s) => [
          s.url,
          (s.published ||
            uiText("Undated ministry reference", "مرجع وزارة غير مؤرخ")) +
            " · " +
            uiText("Source ↗", "المصدر ↗"),
        ]),
    ];
    for (const [url, label] of links)
      if (/^https:\/\//.test(url)) {
        const link = uiNode("a", "", label);
        link.href = url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        card.append(link);
      }
    card.append(
      uiNode(
        "small",
        "",
        uiText("Last checked: ", "آخر مراجعة: ") +
          (entry.checked || entry.verified),
      ),
    );
    root.append(card);
  }
  if (!entries.length)
    root.append(
      uiNode(
        "p",
        "finance-empty",
        uiText(
          "No matches. Broaden your filters; a listing never confirms eligibility.",
          "لا توجد نتائج. وسّع المرشحات؛ الإدراج لا يؤكد الأهلية.",
        ),
      ),
    );
}
