function compactInvestmentLink() {
  if (!currentPlan) return;
  const today = document.querySelector(".summary-stat.today"),
    box = document.getElementById("overview-finance");
  if (!today || !box) return;
  const button = uiNode(
    "button",
    "text-button",
    uiText("Review financial assumptions →", "راجع الافتراضات المالية ←"),
  );
  button.onclick = () => selectPanel(7);
  box.replaceChildren(button);
  today.append(box);
}
function composeFounderShare() {
  if (!currentPlan) return "";
  const sentence = (s) =>
    String(s || "")
      .trim()
      .replace(/[.!؟]+$/, "") + ".";
  return (
    uiText("Khotwa — ", "خطوة — ") +
    sentence(currentPlan.state?.idea) +
    "\n" +
    sentence(currentPlan.first_step_today) +
    "\n" +
    uiText("Assessment: ", "التقييم: ") +
    scoreLabel(currentPlan.opportunity_score)
  );
}
function drawScoreArc(sc) {
  const gauge = document.getElementById("gauge"),
    ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 160 160");
  svg.setAttribute("class", "score-arc");
  svg.setAttribute("role", "img");
  svg.setAttribute(
    "aria-label",
    sc.total == null
      ? uiText(
          `${sc.assessed_count} of 5 dimensions assessed; incomplete`,
          `${sc.assessed_count} من 5 أبعاد مقيمة؛ غير مكتمل`,
        )
      : uiText(`${sc.total} of 25, provisional`, `${sc.total} من 25، مبدئي`),
  );
  const defs = document.createElementNS(ns, "defs"),
    pattern = document.createElementNS(ns, "pattern");
  pattern.id = "score-hatch";
  pattern.setAttribute("width", "6");
  pattern.setAttribute("height", "6");
  pattern.setAttribute("patternUnits", "userSpaceOnUse");
  const path = document.createElementNS(ns, "path");
  path.setAttribute("d", "M-1 1 L1 -1 M0 6 L6 0 M5 7 L7 5");
  path.setAttribute("stroke", "currentColor");
  path.setAttribute("stroke-width", "2");
  pattern.append(path);
  defs.append(pattern);
  svg.append(defs);
  const circumference = 2 * Math.PI * 64;
  for (const [amount, offset, color] of [
    [1, 0, "var(--line)"],
    [(sc.assessed_sum || 0) / 25, 0, "var(--blue)"],
    [(5 - sc.assessed_count) / 5, sc.assessed_count / 5, "url(#score-hatch)"],
  ]) {
    const circle = document.createElementNS(ns, "circle");
    for (const [k, v] of Object.entries({
      cx: 80,
      cy: 80,
      r: 64,
      fill: "none",
      stroke: color,
      "stroke-width": 12,
      "stroke-dasharray": `${amount * circumference} ${circumference}`,
      "stroke-dashoffset": -offset * circumference,
      transform: "rotate(-90 80 80)",
    }))
      circle.setAttribute(k, String(v));
    svg.append(circle);
  }
  gauge.prepend(svg);
  document.querySelectorAll(".score-row").forEach((row) => {
    for (const selector of [
      ".score-reason",
      ".score-improve",
      ".source-badge",
      ".score-measure",
      ".score-why",
    ]) {
      const element = row.querySelector(selector);
      if (element) row.append(element);
    }
  });
}
