/* Rich mocked journeys, screenshots, measurements and WCAG serious/critical matrix. */
const assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path");
const { spawn } = require("node:child_process");
const { chromium } = require("playwright");
const { settledVisuals } = require("./tests/browser_stability.cjs");
const { verifyV221 } = require("./tests/v221_browser.cjs");
const { verifyV222 } = require("./tests/v222_browser.cjs");
const { verifyV223 } = require("./tests/v223_browser.cjs");
const { verifyV224 } = require("./tests/v224_browser.cjs");
const root = path.resolve(
    process.env.KHOTWA_REVIEW_DIR || "outputs/v22-review",
  ),
  shots = path.join(root, "v22");
const base = "http://127.0.0.1:5007";
const tabs = [
  "overview",
  "proof",
  "customers",
  "seven-day",
  "risks",
  "pitch",
  "resources",
  "investment",
];
const subpanels = [
  "investment-overview",
  "startup-costs",
  "monthly-operations",
  "scenarios",
  "stages",
  "funding",
  "investor-readiness",
];
let checks = 0,
  audits = [],
  measurements = [],
  errors = [];
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
async function language(page, value) {
  if ((await page.evaluate(() => lang)) !== value)
    await page.locator("#langBtn").click();
}
async function top(page) {
  await page.evaluate(() => {
    document.activeElement?.blur();
    scrollTo({ top: 0, behavior: "instant" });
  });
  await pause(100);
}
async function generate(page, locale = "en", idea) {
  await language(page, locale);
  await page.evaluate(() => setEntry("existing"));
  await page
    .locator("#idea")
    .fill(
      idea ||
        (locale === "ar"
          ? "وجبات غداء صحية لموظفي المكاتب في أبوظبي"
          : "Healthy lunch boxes for office workers in Abu Dhabi"),
    );
  await page.locator("#region").selectOption("Abu Dhabi");
  await page.locator("#genBtn").click();
  await page.waitForFunction(
    () => currentPlan && !document.getElementById("genBtn").disabled,
  );
  await page.waitForTimeout(150);
}
async function actions(page) {
  if (!(await page.locator(".dashboard-actions").evaluate((e) => e.open)))
    await page.locator(".dashboard-actions summary").click();
}
async function audit(page, view, width, locale, theme) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await settledVisuals(page);
  assert.equal(
    await page
      .locator("#need-idea")
      .evaluate((e) => getComputedStyle(e).transitionDuration),
    "0s",
  );
  const violations = await page.evaluate(async () => {
    const r = await axe.run(document, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
    });
    return r.violations
      .filter((v) => ["serious", "critical"].includes(v.impact))
      .map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
        })),
      }));
  });
  audits.push({ view, width, language: locale, theme, violations });
  if (violations.length)
    console.log("AXE", view, width, locale, theme, JSON.stringify(violations));
}
async function screenshot(page, view, width, locale, theme) {
  await top(page);
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    `${view} ${width} ${locale} ${theme}: page overflow`,
  );
  await page.screenshot({
    path: path.join(shots, `${view}-${width}-${locale}-${theme}.png`),
    fullPage: true,
    animations: "disabled",
  });
}
async function journey(browser, locale) {
  const page = await browser.newPage({
    viewport: { width: 390, height: 844 },
    acceptDownloads: true,
  });
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(base, { waitUntil: "networkidle" });
  await language(page, locale);
  assert.equal(await page.locator("#cl-text").isVisible(), true);
  for (const link of await page
    .locator(".footer-links a, .footer-links button")
    .all()) {
    const box = await link.boundingBox();
    assert.ok(box.width >= 24 && box.height >= 24);
  }
  await page.locator("#have-idea").click();
  await top(page);
  assert.ok((await page.locator("#idea").boundingBox()).y < 650);
  await page.locator("#genBtn").click();
  assert.ok(await page.locator("#error").innerText());
  await page.locator("#idea").fill("A lunch idea");
  assert.equal(await page.locator("#error").innerText(), "");
  const examples = [
    ["lunch catering", "مطعم وجبات"],
    ["crop farm", "مزرعة محاصيل"],
    ["tutor class", "دروس تعليم"],
    ["software app", "تطبيق رقمي"],
    ["fitness yoga", "لياقة يوغا"],
    ["handmade art", "فن يدوي"],
    ["travel hotel", "فندق سياحة"],
    ["retail store", "متجر تجارة"],
    ["wash repair", "صيانة غسيل"],
    ["an unusual concept", "فكرة مختلفة"],
  ];
  const expected = [
    "Food & Catering",
    "Agriculture & Farming",
    "Education & Tutoring",
    "Technology & Digital",
    "Health & Wellness",
    "Handicrafts & Arts",
    "Tourism & Hospitality",
    "Retail & Trading",
    "Services & Maintenance",
    "Other",
  ];
  for (let i = 0; i < examples.length; i++) {
    await page.locator("#category").evaluate((e) => delete e.dataset.touched);
    await page.locator("#idea").fill(examples[i][locale === "ar" ? 1 : 0]);
    assert.equal(
      await page
        .locator("#category")
        .evaluate((e) => T.en.categories[e.selectedIndex - 1]),
      expected[i],
    );
  }
  await page.goBack();
  assert.equal(await page.locator("#have-idea").isVisible(), true);
  await page.locator("#need-idea").click();
  await page.locator("#d-skills").fill("Design");
  await page.locator("#d-budget").fill("4000");
  assert.equal(await page.locator("#d-experience").inputValue(), "");
  await page.locator("#discover-btn").click();
  await page.waitForFunction(
    () => document.querySelectorAll(".idea-card").length === 3,
  );
  checks++;
  await generate(page, locale);
  const raw = JSON.parse(
    fs.readFileSync(`tests/fixtures/rich_plan_${locale}.json`, "utf8"),
  );
  assert.ok(
    (await page.locator(".ai-business-name").innerText()).includes(
      raw.business_name_suggestion,
    ),
  );
  assert.ok(
    (await page.locator("#overview-body").innerText()).includes(
      raw.idea_overview.solution,
    ),
  );
  await page.evaluate(() => selectPanel(4));
  assert.equal(await page.locator("#risk-list .risk-item").count(), 5);
  assert.ok(
    (await page.locator("#risk-list").innerText()).includes(
      raw.risk_radar[0].reason,
    ),
  );
  await page.evaluate(() => selectPanel(5));
  assert.ok(
    (await page.locator("#pitch-list").innerText()).includes(
      raw.pitches.ten_sec,
    ),
  );
  const pitchText = await page.locator("#pitch-list").innerText();
  assert.ok(!/ is Start with| facing [A-Z]|\.\./.test(pitchText));
  assert.ok(
    !(await page.locator("#wa-text").innerText()).startsWith(
      locale === "ar" ? "خطوة —" : "Khotwa —",
    ),
  );
  await page.evaluate(() => selectPanel(3));
  assert.equal(
    await page.locator("#fuller-path").evaluate((e) => e.open),
    false,
  );
  await page.locator("#fuller-path > summary").click();
  assert.equal(await page.locator("#steps-list .step-card:visible").count(), 7);
  await page.locator("#fuller-path > summary").click();
  assert.ok(
    await page
      .locator(".pitch-copy")
      .first()
      .evaluate((e) => e.getBoundingClientRect().height <= 40),
  );
  await page.evaluate(() => selectPanel(1));
  assert.equal(await page.locator(".p-price").first().inputValue(), "");
  assert.notEqual(
    await page.locator(".p-freq").first().getAttribute("placeholder"),
    "weekly",
  );
  await page.locator(".p-int").first().selectOption("yes");
  await page.locator(".p-pre").first().selectOption("reservation");
  await page.locator(".p-note").first().fill("=SUM(1,2)");
  assert.equal(
    await page.locator(".p-note").first().getAttribute("maxlength"),
    "300",
  );
  await page.locator("#proof-add").click();
  await page.locator(".p-price").nth(1).fill("30");
  assert.equal(
    await page.evaluate(() => currentPlan.proof_summary.total_responses),
    2,
  );
  assert.ok(
    await page
      .locator(".table-wrap:has(#proof-table)")
      .evaluate((e) => e.scrollWidth <= e.clientWidth + 1),
  );
  const csvPromise = page.waitForEvent("download");
  await page.locator("#proofCsvBtn").click();
  const csv = fs.readFileSync(await (await csvPromise).path(), "utf8");
  assert.ok(csv.includes("'=SUM(1,2)"));
  checks++;
  await page.evaluate(() => {
    selectPanel(7);
    showInvestmentSection(0);
  });
  assert.equal(
    await page.evaluate(() => investment.inputs.cash_mode),
    "simplified",
  );
  assert.ok(await page.locator("#finance-starter .source-badge").count());
  for (const [key, value] of Object.entries({
    price: "30",
    units: "100",
    variable_cost: "12",
    fixed_cost: "500",
  }))
    await page.locator("#quick-" + key).fill(value);
  await page.locator("#finance-starter button").click();
  await page.waitForFunction(
    () => financeResult?.base?.operating_profit === "1300.00",
  );
  const result = await page.evaluate(() => financeResult.base);
  assert.equal(result.revenue, "3000.00");
  assert.equal(result.break_even_units, 28);
  assert.equal(result.runway_months, null);
  assert.equal(result.payback_months, null);
  assert.equal(
    await page.locator("#finance-advanced").evaluate((e) => e.open),
    false,
  );
  checks++;
  await page.evaluate(() => renderReadiness());
  const prioritiesBefore = await page
    .locator(".readiness-priority h4")
    .allTextContents();
  await page.evaluate(() => showInvestmentSection(1));
  for (const [key, value] of Object.entries({
    equipment: "1000",
    initial_software: "200",
    initial_marketing: "300",
    other_startup: "500",
    licensing: "100",
    working_capital: "1000",
    contingency: "200",
  }))
    await page.locator("#fin-" + key).fill(value);
  await page.locator("#calculate-finance").click();
  await page.waitForFunction(
    () => financeResult?.base?.startup_capital === "3300.00",
  );
  await page.evaluate(() => showInvestmentSection(6));
  const detected = await page.evaluate(() => [...detectedReadiness()]);
  assert.notDeepEqual(
    await page.locator(".readiness-priority h4").allTextContents(),
    prioritiesBefore,
  );
  for (const i of [2, 3, 4, 5, 6, 7, 10]) assert.ok(detected.includes(i));
  assert.ok(
    (await page.locator("#readiness-checks").innerText()).includes(
      locale === "ar" ? "مكتشف" : "Detected",
    ),
  );
  await page
    .locator("#investor-model")
    .fill("One priced lunch box per working day");
  await page
    .locator("#investor-differentiation")
    .fill("Specific office pickup windows");
  await page
    .locator("#investor-use_of_funds")
    .fill("Compare packaging before a permitted pilot");
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(
    await page.locator("#investor-model").inputValue(),
    "One priced lunch box per working day",
  );
  assert.equal(
    await page.evaluate(() => currentPlan.proof_summary.total_responses),
    2,
  );
  await page.evaluate(() => {
    selectPanel(1);
    clearProof();
  });
  assert.equal(
    await page.evaluate(() => currentPlan.proof_summary?.total_responses || 0),
    0,
  );
  assert.equal(await page.locator("#investor-model").inputValue(), "");
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(
    await page.evaluate(() => currentPlan.proof_summary.total_responses),
    0,
  );
  checks++;
  await page.route("**/pdf", (route) =>
    route.fulfill({
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "90" },
      body: '{"error":"rate_limited"}',
    }),
  );
  const alerts = [];
  page.on("dialog", async (dialog) => {
    alerts.push(dialog.message());
    await dialog.accept();
  });
  await page.evaluate(() => exportPDF());
  assert.ok(alerts[0].includes(locale === "ar" ? "دقيق" : "minute"));
  await page.route("**/investment/pdf", (route) =>
    route.fulfill({
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "90" },
      body: '{"error":"rate_limited"}',
    }),
  );
  await page.evaluate(() => exportInvestment());
  assert.ok(
    (await page.locator("#investment-export-status").innerText()).includes(
      locale === "ar" ? "دقيق" : "minute",
    ),
  );
  await language(page, locale === "ar" ? "en" : "ar");
  assert.ok(
    (await page.locator("#investment-export-status").innerText()).includes(
      locale === "ar" ? "minute" : "دقيق",
    ),
  );
  await language(page, locale);
  checks++;
  // Localized throttling must stay meaningful and never reveal raw JSON.
  await page.route("**/ask", (route) =>
    route.fulfill({
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "90" },
      body: '{"error":"rate_limited"}',
    }),
  );
  await page.locator("#chatLauncher").click();
  await page
    .locator("#chat-input")
    .fill(locale === "ar" ? "ما الخطوة؟" : "Next step?");
  await page.locator("#sendBtn").click();
  await page.waitForFunction(() => !_chatBusy);
  const throttle = await page.locator(".advisor-card").last().innerText();
  assert.ok(throttle.includes(locale === "ar" ? "دقيق" : "minute"));
  assert.ok(!throttle.includes("rate_limited"));
  await page.keyboard.press("Escape");
  checks++;
  if (locale === "en") {
    const before = [
      await page.locator("#overview-body").innerText(),
      await page.locator("#pitch-list").innerText(),
      await page.evaluate(() =>
        currentPlan.seven_day_plan.map((d) => d.action),
      ),
    ];
    await actions(page);
    await page.locator("#newBtn").click();
    await generate(page, "en", "Weekend coding classes for Sharjah students");
    assert.notEqual(
      await page.locator("#overview-body").innerText(),
      before[0],
    );
    assert.notEqual(await page.locator("#pitch-list").innerText(), before[1]);
    assert.notDeepEqual(
      await page.evaluate(() =>
        currentPlan.seven_day_plan.map((d) => d.action),
      ),
      before[2],
    );
    checks++;
  }
  const isolated = await browser.newPage();
  await isolated.goto(base);
  assert.equal(await isolated.evaluate(() => currentPlan), null);
  await isolated.close();
  checks++;
  await actions(page);
  await page.locator("#newBtn").click();
  assert.equal(await page.evaluate(() => currentPlan), null);
  assert.equal(
    await page.evaluate(() => Object.keys(investment.notes || {}).length),
    0,
  );
  await page.locator("#have-idea").click();
  await page
    .locator("#idea")
    .fill("A specific customer interview planning tool");
  await page.route("**/generate", (route) =>
    route.fulfill({
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "90" },
      body: '{"error":"rate_limited"}',
    }),
  );
  await page.locator("#genBtn").click();
  await page.waitForFunction(() => !document.getElementById("genBtn").disabled);
  assert.ok(
    (await page.locator("#error").innerText()).includes(
      locale === "ar" ? "دقيق" : "minute",
    ),
  );
  assert.equal(await page.evaluate(() => currentPlan), null);
  await page.evaluate(() => setEntry("discover"));
  await page.locator("#d-skills").fill("Design");
  await page.locator("#d-budget").fill("4000");
  await page.route("**/discover", (route) =>
    route.fulfill({
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "90" },
      body: '{"error":"rate_limited"}',
    }),
  );
  await page.locator("#discover-btn").click();
  await page.waitForFunction(
    () => !document.getElementById("discover-btn").disabled,
  );
  assert.ok(
    (await page.locator("#discover-error").innerText()).includes(
      locale === "ar" ? "دقيق" : "minute",
    ),
  );
  checks++;
  await page.locator("#privacy-open").click();
  assert.ok(
    (await page.locator("#privacy-dialog").innerText()).includes("Groq"),
  );
  await page.addScriptTag({ url: base + "/__test/axe.js" });
  await settledVisuals(page);
  const privacyViolations = await page.evaluate(async () => {
    const result = await axe.run(document);
    return result.violations
      .filter((v) => ["serious", "critical"].includes(v.impact))
      .map((v) => v.id);
  });
  assert.deepEqual(privacyViolations, []);
  await page.locator("#privacy-dialog button").click();
  checks++;
  await page.close();
  console.log(
    `PASS rich ${locale} journey: onboarding, content, proof, finance, detected readiness, recovery, Clear, New idea, quota UI`,
  );
}
async function main() {
  fs.mkdirSync(shots, { recursive: true });
  const server = spawn(
    process.env.PYTHON_EXE || "python",
    ["test_browser_server.py"],
    {
      env: { ...process.env, TEST_PORT: "5007", V22_RICH: "1" },
      windowsHide: true,
      stdio: "ignore",
    },
  );
  let browser;
  try {
    for (let i = 0; i < 80; i++) {
      try {
        if ((await fetch(base + "/health")).ok) break;
      } catch {}
      await pause(100);
    }
    browser = await chromium.launch({ headless: true });
    checks += await verifyV221(browser, base, root);
    checks += await verifyV222(browser, base, root);
    checks += await verifyV223(browser, base, root);
    checks += await verifyV224(browser, base, root);
    await journey(browser, "en");
    await journey(browser, "ar");
    // Each matrix context begins cold with no service worker or browser cache.
    for (const width of [375, 390, 768, 1440, 1920])
      for (const locale of ["en", "ar"]) {
        const context = await browser.newContext({
            viewport: { width, height: width < 768 ? 844 : 1000 },
          }),
          page = await context.newPage();
        page.on("pageerror", (e) => errors.push(e.message));
        await page.goto(base, { waitUntil: "networkidle" });
        await page.evaluate(() => document.fonts.ready);
        if (width === 390) {
          const transfer = await page.evaluate(() =>
            [
              ...performance.getEntriesByType("navigation"),
              ...performance.getEntriesByType("resource"),
            ].reduce((n, r) => n + r.transferSize, 0),
          );
          measurements.push({
            view: "landing-transfer",
            width,
            language: locale,
            bytes: transfer,
          });
          console.log("TRANSFER", locale, transfer);
          assert.ok(
            transfer <= 450 * 1024,
            "First-load transfer exceeds 450 KB",
          );
        }
        await language(page, locale);
        await screenshot(page, "landing", width, locale, "light");
        const matrix = [390, 1440].includes(width);
        if (matrix) {
          await page.addScriptTag({ url: base + "/__test/axe.js" });
          await audit(page, "landing", width, locale, "light");
        }
        for (const [button, view] of [
          ["#have-idea", "onboarding-existing"],
          ["#entry-back", null],
          ["#need-idea", "onboarding-discovery"],
        ]) {
          await page.locator(button).click();
          if (view) await screenshot(page, view, width, locale, "light");
        }
        await generate(page, locale);
        await top(page);
        const navTop = await page
          .locator("#result-nav")
          .evaluate((e) => e.getBoundingClientRect().top + scrollY);
        measurements.push({
          view: "header-to-tabs",
          width,
          language: locale,
          height: navTop,
        });
        if (width === 390) assert.ok(navTop <= 844 * 1.3);
        if (width === 1440) assert.ok(navTop <= 600);
        for (let i = 0; i < 8; i++) {
          await page.evaluate((i) => selectPanel(i), i);
          await screenshot(page, tabs[i], width, locale, "light");
          if (matrix) await audit(page, tabs[i], width, locale, "light");
          if (width === 390 && [0, 3].includes(i))
            measurements.push({
              view: tabs[i],
              language: locale,
              width,
              height: await page.evaluate(
                () => document.documentElement.scrollHeight,
              ),
            });
        }
        for (let i = 0; i < 7; i++) {
          await page.evaluate((i) => {
            selectPanel(7);
            showInvestmentSection(i);
          }, i);
          await screenshot(page, subpanels[i], width, locale, "light");
          if (matrix) await audit(page, subpanels[i], width, locale, "light");
          if (width === 390 && [4, 5].includes(i))
            measurements.push({
              view: subpanels[i],
              language: locale,
              width,
              height: await page.evaluate(
                () => document.documentElement.scrollHeight,
              ),
            });
        }
        if (width === 390) {
          await page.evaluate(() => {
            selectPanel(7);
            showInvestmentSection(0);
          });
          await screenshot(page, "investment-empty", width, locale, "light");
        }
        if (matrix) {
          await page.locator("#themeBtn").click();
          await page.evaluate(() => selectPanel(0));
          await screenshot(page, "overview", width, locale, "dark");
          // Audit the actual dark landing using a second page without business state.
          const landing = await context.newPage();
          await landing.goto(base);
          await language(landing, locale);
          await landing.locator("#themeBtn").click();
          await landing.addScriptTag({ url: base + "/__test/axe.js" });
          await audit(landing, "landing", width, locale, "dark");
          await landing.close();
          for (let i = 0; i < 8; i++) {
            await page.evaluate((i) => selectPanel(i), i);
            await audit(page, tabs[i], width, locale, "dark");
          }
          for (let i = 0; i < 7; i++) {
            await page.evaluate((i) => {
              selectPanel(7);
              showInvestmentSection(i);
            }, i);
            await screenshot(page, subpanels[i], width, locale, "dark");
            await audit(page, subpanels[i], width, locale, "dark");
          }
        }
        await context.close();
        console.log(`PASS visual matrix ${width} ${locale}`);
      }
    fs.writeFileSync(
      path.join(root, "measurements.json"),
      JSON.stringify(measurements, null, 2),
    );
    fs.writeFileSync(
      path.join(root, "axe-matrix.json"),
      JSON.stringify(audits, null, 2),
    );
    assert.equal(audits.length, 128);
    assert.equal(
      audits.reduce((n, a) => n + a.violations.length, 0),
      0,
    );
    assert.deepEqual(errors, []);
    for (const m of measurements.filter((m) => m.width === 390)) {
      if (m.view === "seven-day") assert.ok(m.height < 3000, JSON.stringify(m));
      if (m.view === "funding") assert.ok(m.height < 4000, JSON.stringify(m));
    }
    checks += 12;
    console.log(
      `PASS V2.2: ${checks} check groups; ${audits.length} axe states; ${fs.readdirSync(shots).filter((s) => s.endsWith(".png")).length} screenshots. No live Groq requests.`,
    );
  } finally {
    fs.writeFileSync(
      path.join(root, "axe-matrix.json"),
      JSON.stringify(audits, null, 2),
    );
    fs.writeFileSync(
      path.join(root, "measurements.json"),
      JSON.stringify(measurements, null, 2),
    );
    await browser?.close();
    server.kill();
  }
}
main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
