const assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path");
const { settledVisuals } = require("./browser_stability.cjs");
const notes = {
  en: [
    "AI-written text is a planning assumption. It is not evidence of customers, sales, revenue, funding, contracts or approvals. Only entries you record in Proof Mode count as evidence.",
    "Proof Mode entries are self-reported observations, not independently verified evidence. Recording them does not automatically confirm customers, payments or other business outcomes.",
  ],
  ar: [
    "النص المكتوب بالذكاء الاصطناعي افتراض للتخطيط، وليس دليلًا على عملاء أو مبيعات أو إيرادات أو تمويل أو عقود أو موافقات. وحدها الإدخالات التي تسجلها في وضع الإثبات تُعد دليلًا.",
    "إدخالات وضع الإثبات ملاحظات تُبلّغ عنها بنفسك، وليست أدلة متحققًا منها بشكل مستقل. تسجيلها لا يؤكد تلقائيًا وجود عملاء أو مدفوعات أو نتائج أعمال أخرى.",
  ],
};
async function verifyV223(browser, base, root) {
  const folder = path.join(root, "v223");
  fs.mkdirSync(folder, { recursive: true });
  const records = [];
  for (const width of [390, 1440])
    for (const locale of ["en", "ar"]) {
      const page = await browser.newPage({
        viewport: { width, height: width === 390 ? 844 : 900 },
        reducedMotion: "reduce",
      });
      await page.goto(base, { waitUntil: "networkidle" });
      if (locale === "ar") await page.locator("#langBtn").click();
      await page.locator("#have-idea").click();
      await page
        .locator("#idea")
        .fill(
          locale === "en"
            ? "Lunch boxes for office workers"
            : "وجبات غداء لموظفي المكاتب",
        );
      await page.locator("#genBtn").click();
      await page.waitForFunction(
        () => currentPlan && !document.getElementById("genBtn").disabled,
      );
      await page.addScriptTag({ url: base + "/__test/axe.js" });
      for (const theme of ["light", "dark"]) {
        if (theme === "dark") await page.locator("#themeBtn").click();
        for (const view of ["pitch", "investor", "advisor"]) {
          if (view === "pitch") await page.evaluate(() => selectPanel(5));
          if (view === "investor")
            await page.evaluate(() => {
              selectPanel(7);
              showInvestmentSection(6);
            });
          if (view === "advisor") await page.locator("#chatLauncher").click();
          await settledVisuals(page);
          const scope =
            view === "pitch"
              ? "#panel-5"
              : view === "investor"
                ? "#investment-panel-6"
                : "#chatPanel";
          const note = page.locator(scope + " .ai-disclosure");
          assert.equal(await note.count(), 1);
          for (const text of notes[locale])
            assert.ok((await note.innerText()).includes(text));
          if (view === "investor")
            assert.ok(
              await note.evaluate(
                (e) => e === e.parentElement.firstElementChild,
              ),
            );
          if (view === "advisor") {
            assert.ok(await page.locator("#chat-foot-privacy").isVisible());
            assert.ok(
              (await note.locator("p").first().innerText()).includes(
                notes[locale][1],
              ),
            );
            await note.focus();
            assert.ok(await note.evaluate((e) => document.activeElement === e));
          }
          const violations = await page.evaluate(async () => {
            const r = await axe.run(document);
            return r.violations
              .filter((v) => ["serious", "critical"].includes(v.impact))
              .map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target) }));
          });
          assert.deepEqual(
            violations,
            [],
            JSON.stringify({ width, locale, theme, view, violations }),
          );
          await page.evaluate(() => {
            document.activeElement?.blur();
            scrollTo({ top: 0, behavior: "instant" });
          });
          const file = path.join(
            folder,
            `${view}-${width}-${locale}-${theme}.png`,
          );
          if (view === "advisor")
            await page
              .locator("#chatPanel")
              .screenshot({ path: file, animations: "disabled" });
          else
            await page.screenshot({
              path: file,
              fullPage: true,
              animations: "disabled",
            });
          records.push({
            width,
            locale,
            theme,
            view,
            disclosure_present: true,
            proof_self_reported: true,
            violations,
          });
          if (view === "advisor") await page.locator("#chatClose").click();
        }
      }
      await page.close();
    }
  fs.writeFileSync(
    path.join(root, "v223-checks.json"),
    JSON.stringify(records, null, 2),
  );
  console.log(
    "PASS V2.2.3: 4 added check groups; 24 disclosure states/captures; zero serious/critical violations.",
  );
  return 4;
}
module.exports = { verifyV223 };
