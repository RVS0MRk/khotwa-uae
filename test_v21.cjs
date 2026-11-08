/* Round 2 browser measurements supplement, rather than replace, visual review. */
const assert = require("node:assert/strict");
const fs = require("node:fs"),
  path = require("node:path");
const { spawn } = require("node:child_process");
const { chromium } = require("playwright");

async function openActions(page) {
  const menu = page.locator(".dashboard-actions");
  if (
    (await menu.count()) &&
    !((await menu.getAttribute("open")) !== null) &&
    (await menu.locator("summary").isVisible())
  )
    await menu.locator("summary").click();
}
async function revealProof(page) {
  while (await page.locator("#proof-add").isVisible())
    await page.locator("#proof-add").click();
}

async function main() {
  const base = "http://127.0.0.1:5004",
    output = path.resolve("outputs/v21-review/after");
  fs.mkdirSync(output, { recursive: true });
  const server = spawn(
    process.env.PYTHON_EXE || "python",
    ["test_browser_server.py"],
    {
      env: { ...process.env, TEST_PORT: "5004" },
      windowsHide: true,
      stdio: "ignore",
    },
  );
  let browser,
    checks = 0;
  const measurements = [];
  try {
    for (let i = 0; i < 80; i++) {
      try {
        if ((await fetch(base + "/health")).ok) break;
      } catch {}
      await new Promise((r) => setTimeout(r, 100));
    }
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({
        viewport: { width: 390, height: 844 },
      }),
      errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.addInitScript(() =>
      document.addEventListener("securitypolicyviolation", (e) =>
        (window.__csp ||= []).push(e.violatedDirective),
      ),
    );
    await page.route("**/*", (route) =>
      route.request().url().startsWith(base) ? route.continue() : route.abort(),
    );
    await page.goto(base, { waitUntil: "networkidle" });
    await page.locator("#preview-demo").click();
    await page.evaluate(() => selectPanel(7));
    assert.equal(
      await page.locator("#investment-tab-0").getAttribute("aria-selected"),
      "true",
    );
    assert.equal(await page.locator(".investment-panel:visible").count(), 1);
    checks++;
    const values = {
      equipment: "1000",
      initial_software: "200",
      initial_marketing: "300",
      other_startup: "500",
      licensing: "100",
      working_capital: "1000",
      contingency: "200",
      available_capital: "5000",
      price: "50",
      units: "3",
      variable_cost: "20",
      fixed_cost: "1200",
      cogs_per_unit: "15",
    };
    for (const [key, value] of Object.entries(values)) {
      await page
        .locator(
          "#investment-tab-" +
            ([
              "price",
              "units",
              "variable_cost",
              "fixed_cost",
              "cogs_per_unit",
            ].includes(key)
              ? 2
              : 1),
        )
        .click();
      if (key === "cogs_per_unit" || key.startsWith("cash_")) {
        if (key.startsWith("cash_"))
          await page.locator("#cash-mode").selectOption("entered");
        await page
          .locator("#finance-advanced")
          .evaluate((e) => (e.open = true));
      }
      await page.locator("#fin-" + key).fill(value);
    }
    await page.locator("#cash-mode").selectOption("simplified");
    await page.locator("#finance-recalculate").click();
    await page.waitForFunction(
      () => financeResult?.base?.startup_capital === "3300.00",
    );
    assert.equal(
      await page.evaluate(() => financeResult.base.cash_flow_basis),
      "simplified_user_assumption",
    );
    await page.locator("#investment-tab-3").click();
    const sensitivity = await page.evaluate(() =>
      financeResult.sensitivity.filter((s) => s.field === "units"),
    );
    assert.deepEqual(
      sensitivity.map((s) => Number(s.comparison)).sort(),
      [2, 4],
    );
    await page.locator("#sensitivity-table-details summary").click();
    assert.ok(
      (await page.locator("#sensitivity-table").innerText()).includes("33.33%"),
    );
    assert.ok(
      (await page.locator("#sensitivity-explanation").innerText()).includes(
        "largest",
      ),
    );
    checks++;
    await page.locator(".scenario-editor").first().locator("summary").click();
    assert.equal(await page.locator("#conservative-units").inputValue(), "2");
    await page.locator("#conservative-units").fill("1");
    await page.waitForFunction(
      () => financeResult?.scenarios.conservative.inputs.units === "1",
    );
    assert.equal(await page.locator("#fin-units").inputValue(), "3");
    await page.locator(".scenario-editor").first().getByRole("button").click();
    await page.waitForFunction(
      () => financeResult?.scenarios.conservative.inputs.units === "2",
    );
    checks++;
    await page.locator("#investment-tab-6").click();
    assert.equal(await page.locator(".readiness-priority").count(), 3);
    const before = await page
      .locator(".readiness-priority h4")
      .first()
      .innerText();
    await page.locator("#readiness-checks input").first().check();
    assert.notEqual(
      await page.locator(".readiness-priority h4").first().innerText(),
      before,
    );
    assert.equal(await page.locator(".readiness-priority button").count(), 3);
    checks++;
    const currency = await page.evaluate(() =>
      ["0", "-0.00", "5000.5", "-3200.25"].map(formatAED),
    );
    assert.deepEqual(currency, [
      "0.00 AED",
      "0.00 AED",
      "5,000.50 AED",
      "-3,200.25 AED",
    ]);
    checks++;
    // A real generated PDF and its existing success status must re-localize.
    for (const language of ["en", "ar"]) {
      if ((await page.evaluate(() => lang)) !== language)
        await page.locator("#langBtn").click();
      const download = page.waitForEvent("download");
      await page.locator("#investment-pdf").click();
      fs.copyFileSync(
        await (await download).path(),
        path.join(output, "investment-" + language + ".pdf"),
      );
      await page.waitForFunction(
        () => investmentStatuses.export === "downloaded",
      );
      assert.equal(
        await page.locator("#investment-export-status").innerText(),
        language === "en" ? "Report downloaded." : "تم تنزيل التقرير.",
      );
      const founder = await page.request.post(base + "/pdf", {
        data: { ...(await page.evaluate(() => currentPlan)), _lang: language },
      });
      assert.equal(founder.status(), 200);
      fs.writeFileSync(
        path.join(output, "founder-" + language + ".pdf"),
        await founder.body(),
      );
      checks++;
    }
    await page.locator("#langBtn").click();
    assert.equal(
      await page.locator("#investment-export-status").innerText(),
      "Report downloaded.",
    );
    // Failure statuses also survive EN → AR → EN.
    await page.locator("#investment-tab-2").click();
    await page.locator("#fin-price").fill("-1");
    await page.locator("#finance-recalculate").click();
    await page.waitForFunction(() => investmentStatuses.error);
    await page.locator("#langBtn").click();
    assert.ok(
      (await page.locator("#finance-error").innerText()).includes("تعذّر"),
    );
    await page.locator("#langBtn").click();
    assert.ok(
      (await page.locator("#finance-error").innerText()).includes("Unable"),
    );
    await page.locator("#fin-price").fill("50");
    await page.locator("#finance-recalculate").click();
    await page.waitForFunction(() => financeResult?.base?.revenue === "150.00");
    checks++;
    await page.locator("#investment-tab-4").click();
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForFunction(() => financeResult?.base?.revenue === "150.00");
    assert.equal(
      await page.locator("#investment-tab-4").getAttribute("aria-selected"),
      "true",
    );
    assert.equal(await page.locator("#fin-licensing").inputValue(), "100");
    checks++;
    for (const width of [375, 390, 768, 1440, 1920])
      for (const language of ["en", "ar"]) {
        await page.setViewportSize({ width, height: 844 });
        if ((await page.evaluate(() => lang)) !== language)
          await page.locator("#langBtn").click();
        await page.evaluate(() => {
          selectPanel(7);
          showInvestmentSection(0);
          window.scrollTo({ top: 0, behavior: "instant" });
        });
        await page.screenshot({
          path: path.join(output, `investment-${width}-${language}.png`),
          fullPage: true,
        });
        const layout = await page.evaluate(() => {
          const nav = document.getElementById("investment-nav"),
            panel = document.getElementById("investment-panel-0");
          const fonts = [...document.querySelectorAll("body *")]
            .filter(
              (e) =>
                e.getClientRects().length &&
                e.textContent.trim() &&
                !["SCRIPT", "STYLE"].includes(e.tagName) &&
                e.children.length === 0,
            )
            .filter((e) => parseFloat(getComputedStyle(e).fontSize) < 12)
            .map((e) => ({
              id: e.id,
              cls: e.className,
              size: getComputedStyle(e).fontSize,
            }));
          const stages = [...document.querySelectorAll(".stage-label")].map(
            (e) => ({
              width: e.clientWidth,
              scroll: e.scrollWidth,
              rect: e.getBoundingClientRect().toJSON(),
              parent: e.parentElement.getBoundingClientRect().toJSON(),
            }),
          );
          return {
            width: innerWidth,
            overflow: document.documentElement.scrollWidth,
            overviewHeight: panel.offsetHeight + nav.offsetHeight,
            fonts,
            stages,
            fixedOverlaps: [...document.querySelectorAll("body *")]
              .filter(
                (e) =>
                  getComputedStyle(e).position === "fixed" &&
                  e.getClientRects().length &&
                  e.getBoundingClientRect().bottom > 0 &&
                  e.getBoundingClientRect().top < innerHeight &&
                  !e.closest("#chatPanel"),
              )
              .flatMap((f) =>
                [...document.querySelectorAll("button,input,select,textarea")]
                  .filter((c) => {
                    if (f === c || f.contains(c) || !c.getClientRects().length)
                      return false;
                    const a = f.getBoundingClientRect(),
                      b = c.getBoundingClientRect();
                    return (
                      a.width > 0 &&
                      a.height > 0 &&
                      b.top >= 0 &&
                      b.bottom <= innerHeight &&
                      a.left < b.right &&
                      a.right > b.left &&
                      a.top < b.bottom &&
                      a.bottom > b.top
                    );
                  })
                  .map((c) => ({ fixed: f.id || f.className, control: c.id })),
              ),
            advisorPosition: getComputedStyle(
              document.getElementById("chatLauncher"),
            ).position,
          };
        });
        assert.ok(
          layout.overflow <= width,
          `${width} ${language} page overflow`,
        );
        assert.deepEqual(
          layout.fonts,
          [],
          `${width} ${language} fonts below 12px`,
        );
        assert.equal(layout.advisorPosition, "static");
        assert.deepEqual(
          layout.fixedOverlaps,
          [],
          "fixed element overlaps controls",
        );
        for (const label of layout.stages) {
          assert.ok(label.scroll <= label.width + 1, "clipped stage text");
          assert.ok(
            label.rect.left >= label.parent.left - 1 &&
              label.rect.right <= label.parent.right + 1,
            "stage outside its step",
          );
        }
        if (width < 600)
          assert.ok(
            layout.overviewHeight < 6 * 844,
            "default overview exceeds six screens",
          );
        for (let section = 0; section < 7; section++) {
          await page.locator("#investment-tab-" + section).click();
          const issues = await page.evaluate(() =>
            [
              ...document.querySelectorAll(
                ".investment-panel input,.investment-panel select,.investment-panel textarea",
              ),
            ]
              .filter(
                (e) =>
                  e.getClientRects().length &&
                  !e.labels?.length &&
                  !e.getAttribute("aria-label") &&
                  !e.getAttribute("aria-labelledby"),
              )
              .map((e) => e.id),
          );
          assert.deepEqual(issues, [], "unlabelled financial controls");
          assert.ok(
            await page.evaluate(
              () => document.documentElement.scrollWidth <= innerWidth,
            ),
            `${width} ${language} investment ${section}: page overflow`,
          );
        }
        await page.locator("#investment-tab-0").focus();
        await page.keyboard.press("End");
        assert.equal(
          await page.locator("#investment-tab-6").getAttribute("aria-selected"),
          "true",
        );
        assert.equal(
          await page
            .locator("#investment-tab-6")
            .evaluate((e) => getComputedStyle(e).outlineStyle),
          "solid",
        );
        measurements.push({
          width,
          language,
          overviewHeight: layout.overviewHeight,
          minimumFont: 12,
          sections: 7,
        });
        checks++;
      }
    // Contrast of the actual theme tokens (normal text requires 4.5:1).
    for (const theme of ["light", "dark"]) {
      const ratios = await page.evaluate((theme) => {
        document.documentElement.setAttribute("data-theme", theme);
        const s = getComputedStyle(document.documentElement),
          rgb = (v) => {
            const x = document.createElement("span");
            x.style.color = s.getPropertyValue(v);
            document.body.append(x);
            const c = getComputedStyle(x)
              .color.match(/[\d.]+/g)
              .slice(0, 3)
              .map(Number);
            x.remove();
            return c;
          };
        const luminance = (c) =>
          c
            .map((v) => {
              v /= 255;
              return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
            })
            .reduce((n, v, i) => n + v * [0.2126, 0.7152, 0.0722][i], 0);
        return [
          ["--text", "--card"],
          ["--text", "--paper"],
          ["--muted", "--card"],
          ["--muted", "--paper"],
          ["--blue", "--card"],
          ["--warning", "--warning-bg"],
        ].map(([fg, bg]) => {
          const a = luminance(rgb(fg)),
            b = luminance(rgb(bg));
          return {
            fg,
            bg,
            ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
          };
        });
      }, theme);
      for (const r of ratios)
        assert.ok(r.ratio >= 4.5, `${theme} ${JSON.stringify(r)}`);
      measurements.push({ theme, ratios });
      checks++;
    }
    await page.evaluate(() => {
      selectPanel(7);
      showInvestmentSection(2);
    });
    for (const [chart, table] of [
      ["#break-even-chart", "#cash-data table"],
      ["#cash-flow-chart", "#cash-data table"],
    ]) {
      assert.ok((await page.locator(chart + " figcaption").innerText()).length);
      assert.equal(await page.locator(table).count(), 1);
    }
    checks++;
    await page.evaluate(() => {
      showInvestmentSection(3);
    });
    assert.equal(await page.locator("#sensitivity-table table").count(), 1);
    assert.equal(await page.locator("#scenario-comparison table").count(), 1);
    await page.evaluate(() => {
      showInvestmentSection(5);
    });
    assert.equal(await page.locator("#financing-routes details").count(), 8);
    await page.locator("#funding-emirate").selectOption("UAE-wide");
    assert.equal(await page.locator(".funding-card").count(), 8);
    assert.ok(
      (await page.locator(".funding-card").nth(6).innerText()).includes(
        await page.evaluate(() =>
          lang === "ar"
            ? "رسمي مؤرخ · أكّد الشروط الحالية"
            : "DATED OFFICIAL · CONFIRM CURRENT TERMS",
        ),
      ),
    );
    checks++;
    await page.evaluate(() => {
      selectPanel(0);
      window.scrollTo({ top: 0, behavior: "instant" });
    });
    await page.screenshot({
      path: path.join(output, "dashboard-1920-ar.png"),
      fullPage: true,
    });
    assert.notEqual(
      await page.locator("#first-step-text").innerText(),
      await page.evaluate(() => currentPlan.first_step_today),
    );
    assert.equal(await page.locator(".score-why").count(), 5);
    checks++;
    assert.deepEqual(errors, []);
    assert.deepEqual(await page.evaluate(() => window.__csp || []), []);
    fs.writeFileSync(
      path.join(output, "measurements.json"),
      JSON.stringify(measurements, null, 2),
    );
    console.log(
      `PASS V2.1: ${checks} financial/localization/accessibility/responsive check groups; 0 failures. Screenshots/PDFs: ${output}`,
    );
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
}
main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
