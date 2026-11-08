// One set of controls backs both the desktop table and responsive phone cards.
let proofVisibleCount = 1;
function updateProofCards() {
  const rows = [...document.querySelectorAll("#proof-table .proof-response")];
  rows.forEach((row, i) => {
    const filled = [...row.querySelectorAll("input,select")].some((n) =>
      n.value.trim(),
    );
    if (filled) proofVisibleCount = Math.max(proofVisibleCount, i + 1);
    row.classList.toggle("is-revealed", i < proofVisibleCount);
    const headers = [...document.querySelectorAll("#proof-table th")].map(
      (n) => n.textContent,
    );
    [...row.cells].forEach(
      (cell, j) => (cell.dataset.label = headers[j] || ""),
    );
  });
  const add = document.getElementById("proof-add");
  if (add) {
    add.hidden = proofVisibleCount >= 10;
    add.textContent = uiText("Add response", "أضف إجابة");
  }
}
function buildProof() {
  const root = document.getElementById("proof-table"),
    t = T[lang];
  root.replaceChildren();
  proofVisibleCount = 1;
  const head = uiNode("thead"),
    header = uiNode("tr");
  [
    ...t.proofCols.slice(0, 5),
    uiText("Evidence strength", "قوة الدليل"),
    uiText("Optional note", "ملاحظة اختيارية"),
  ].forEach((text) => {
    const th = uiNode("th", "", text);
    th.scope = "col";
    header.append(th);
  });
  head.append(header);
  root.append(head);
  const body = uiNode("tbody");
  for (let i = 0; i < 10; i++) {
    const row = uiNode("tr", "proof-response");
    row.append(
      uiNode(
        "td",
        "response-number",
        uiText("Response ", "الإجابة ") + (i + 1),
      ),
    );
    const specs = [
      [
        "p-int",
        "select",
        [
          ["", "—"],
          ["yes", t.interested],
          ["maybe", t.maybe],
          ["no", t.no],
        ],
      ],
      ["p-price", "number"],
      ["p-freq", "text"],
      ["p-concern", "text"],
      [
        "p-pre",
        "select",
        [
          ["", "—"],
          ["interest", uiText("Sounds interesting", "اهتمام فقط")],
          ["intent", uiText("Stated intent to buy", "نية شراء معلنة")],
          ["reservation", uiText("No-payment reservation", "حجز بلا دفع")],
          ["payment", uiText("Actual payment", "دفع فعلي")],
          ["repeat", uiText("Repeat customer", "عميل متكرر")],
        ],
      ],
      ["p-note", "text"],
    ];
    specs.forEach(([cls, type, options]) => {
      const cell = uiNode("td"),
        control = uiNode(type === "select" ? "select" : "input", cls);
      control.id = "proof-" + i + "-" + cls;
      if (type === "select")
        options.forEach(([value, label]) => {
          const opt = uiNode("option", "", label);
          opt.value = value;
          control.append(opt);
        });
      else {
        control.type = type;
        control.maxLength = cls === "p-note" ? 300 : 500;
        control.placeholder =
          cls === "p-price"
            ? uiText("e.g. 30", "مثال: 30")
            : cls === "p-freq"
              ? uiText("e.g. monthly", "مثال: شهرياً")
              : uiText("Leave blank if unknown", "اتركه فارغاً إن لم يُعرف");
        if (type === "number") {
          control.min = "0";
          control.step = "0.1";
        }
      }
      cell.append(control);
      row.append(cell);
    });
    body.append(row);
  }
  root.append(body);
  let add = document.getElementById("proof-add");
  if (!add) {
    add = uiNode("button", "btn btn-light");
    add.id = "proof-add";
    add.type = "button";
    root.closest(".table-wrap").after(add);
  }
  add.onclick = () => {
    proofVisibleCount = Math.min(10, proofVisibleCount + 1);
    updateProofCards();
    const input = document.querySelectorAll(".p-int")[proofVisibleCount - 1];
    input.focus();
  };
  calcProof();
  updateProofCards();
}
