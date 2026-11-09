const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { settledVisuals } = require("./browser_stability.cjs");

const ARABIC_CASES = [
  ["صناديق غداء صحية تُطلب مسبقًا لموظفي المكاتب في أبوظبي", "Food & Catering"],
  ["مطبخ لوجبات العشاء والفطور", "Food & Catering"],
  ["حلويات وكيك للمناسبات", "Food & Catering"],
  ["مطعم للعائلات", "Food & Catering"],
  ["ورش للأطفال", "Education & Tutoring"],
  ["ورش تعليم للأطفال في البرمجة", "Education & Tutoring"],
  ["تنظيف المنازل وصيانة المكاتب", "Services & Maintenance"],
  ["ورشة صيانة السيارات", "Services & Maintenance"],
  ["متجر ملابس أطفال", "Retail & Trading"],
  ["استشارات تغذية ونمط حياة صحي", "Health & Wellness"],
  ["دُرُوس إِضافية للطلاب", "Education & Tutoring"],
  ["فنادق للعائلات", "Tourism & Hospitality"],
  ["فن ورسم يدوي", "Handicrafts & Arts"],
  ["فكرة للأطفال", "Other"],
  ["احتفال سنوي للحي", "Other"],
  ["وَتَوْصِيل الطلبات", "Services & Maintenance"],
  ["خدمة أَكْل منزلي", "Food & Catering"],
];
async function verifyV221(browser, base, root) {
  let checks = 0;
  const evidence = {
    environment: {
      platform: process.platform,
      release: require("node:os").release(),
      arch: process.arch,
      node: process.version,
      chromium: browser.version(),
      playwright: require("playwright/package.json").version,
      axe: require("axe-core/package.json").version,
    },
    categories: [],
    theme_frames: [],
    layout: [],
  };
  for (const width of [390, 1440])
    for (const locale of ["en", "ar"]) {
      const page = await browser.newPage({
        viewport: { width, height: width === 390 ? 844 : 900 },
        reducedMotion: "no-preference",
      });
      await page.goto(base, { waitUntil: "networkidle" });
      if (locale === "ar") await page.locator("#langBtn").click();
      await settledVisuals(page);
      const frames = await page.evaluate(async () => {
        const channel = (n) => {
          n /= 255;
          return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
        };
        const rgb = (value) =>
          value
            .match(/[\d.]+/g)
            .slice(0, 3)
            .map(Number);
        const luminance = (color) =>
          rgb(color)
            .map(channel)
            .reduce((s, x, i) => s + x * [0.2126, 0.7152, 0.0722][i], 0);
        const samples = [];
        for (let toggle = 0; toggle < 4; toggle++) {
          toggleTheme();
          for (let frame = 0; frame < 18; frame++) {
            const e = document.getElementById("need-idea"),
              s = getComputedStyle(e);
            const a = luminance(s.color),
              b = luminance(s.backgroundColor);
            samples.push({
              toggle,
              frame,
              theme: document.documentElement.dataset.theme || "light",
              color: s.color,
              background: s.backgroundColor,
              contrast: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
              switching:
                document.documentElement.classList.contains("theme-switching"),
              running_transitions: document
                .getAnimations()
                .filter(
                  (a) =>
                    a.constructor.name === "CSSTransition" &&
                    a.playState === "running",
                ).length,
            });
            await new Promise(requestAnimationFrame);
          }
        }
        return samples;
      });
      assert.ok(
        frames.every((s) => s.contrast >= 4.5),
        JSON.stringify(frames.filter((s) => s.contrast < 4.5)),
      );
      assert.ok(
        frames.every((s) => s.running_transitions === 0),
        "Theme changes must not create an interpolated color transition",
      );
      // All intermediate frames must be exactly one of the two settled palettes.
      for (const theme of ["light", "dark"]) {
        const palette = frames.filter((s) => s.theme === theme);
        assert.equal(
          new Set(palette.map((s) => s.color + "|" + s.background)).size,
          1,
        );
      }
      evidence.theme_frames.push({ width, locale, samples: frames });
      await settledVisuals(page);
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page
        .locator("#need-idea")
        .evaluate((e) => (e.style.transform = "translateY(0)"));
      assert.equal(
        await page
          .locator("#need-idea")
          .evaluate((e) => getComputedStyle(e).transitionDuration),
        "0s",
      );
      checks++;
      await page.locator("#have-idea").click();
      for (const [idea, expected] of ARABIC_CASES) {
        await page
          .locator("#category")
          .evaluate((e) => delete e.dataset.touched);
        await page.locator("#idea").fill(idea);
        assert.equal(
          await page.evaluate(
            () =>
              T.en.categories[
                document.getElementById("category").selectedIndex - 1
              ],
          ),
          expected,
          idea,
        );
        if (width === 390 && locale === "ar")
          evidence.categories.push({ idea, expected, result: expected });
      }
      await page.locator("#category").selectOption({ index: 8 });
      const manual = await page.locator("#category").inputValue();
      await page
        .locator("#idea")
        .fill("صناديق غداء صحية تُطلب مسبقًا لموظفي المكاتب في أبوظبي");
      assert.equal(
        await page.locator("#category").inputValue(),
        manual,
        "Manual category must remain selected",
      );
      await page.locator("#category").evaluate((e) => delete e.dataset.touched);
      await page
        .locator("#idea")
        .fill("Healthy lunch boxes for office workers in Abu Dhabi");
      await page.locator("#genBtn").click();
      await page.waitForFunction(
        () => currentPlan && !document.getElementById("genBtn").disabled,
      );
      await settledVisuals(page);
      await page.evaluate(() => {
        document.activeElement?.blur();
        scrollTo({ top: 0, behavior: "instant" });
      });
      const tabTop = await page
        .locator("#result-nav")
        .evaluate((e) => e.getBoundingClientRect().top + scrollY);
      if (width === 1440) assert.ok(tabTop <= 600, `Tab top ${tabTop}`);
      await page.evaluate(() => selectPanel(4));
      const risk = await page.locator("#panel-4 .caution-card").boundingBox(),
        panel = await page.locator("#panel-4").boundingBox();
      assert.ok(
        risk.width >= panel.width - 2,
        "Caution card spans the full row",
      );
      await page.evaluate(() => selectPanel(0));
      const typography = await page
        .locator(".score-financial-context")
        .evaluate((e) => {
          const s = getComputedStyle(e),
            other = getComputedStyle(
              e.parentElement.querySelector(".score-why"),
            );
          return {
            size: s.fontSize,
            color: s.color,
            otherSize: other.fontSize,
            otherColor: other.color,
          };
        });
      assert.equal(typography.size, typography.otherSize);
      assert.equal(typography.color, typography.otherColor);
      await page.evaluate(() => selectPanel(1));
      const price = page.locator("#proof-stats .stat-card").nth(2);
      assert.equal(await price.locator(".v").innerText(), "—");
      assert.ok(
        (await price.locator(".l").innerText()).includes(
          locale === "ar" ? "لم يُقدّم" : "Not provided",
        ),
      );
      await page.locator(".p-price").first().fill("0");
      assert.ok(
        (await price.locator(".v").innerText()).includes("0"),
        "Entered zero is distinct from missing",
      );
      await page.evaluate(() => selectPanel(7));
      assert.equal(
        await page
          .locator("#investment-panel-0 .finance-actions button")
          .count(),
        1,
      );
      await page.locator("#investment-panel-0 .finance-actions button").click();
      assert.equal(
        await page.locator("#investment-panel-1").isVisible(),
        true,
        "Detailed startup fields stay accessible",
      );
      for (const state of [
        { region: "UAE-wide", context: "Not sure" },
        { region: "Not sure", context: "Not sure" },
        { region: undefined, context: undefined },
      ]) {
        const actual = await page.evaluate(
          (s) => businessMarketParts(s),
          state,
        );
        assert.ok(!actual.some((s) => /Not sure|غير متأكد|undefined/.test(s)));
        assert.equal(new Set(actual).size, actual.length);
      }
      evidence.layout.push({
        width,
        locale,
        tab_top: tabTop,
        caution_width: risk.width,
        panel_width: panel.width,
        typography,
      });
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      checks += 2;
      await page.close();
    }
  fs.writeFileSync(
    path.join(root, "v221-checks.json"),
    JSON.stringify(evidence, null, 2),
  );
  console.log(
    `PASS V2.2.1: ${checks} added check groups; ${ARABIC_CASES.length} Arabic examples; 288 theme frames; all >=4.5:1.`,
  );
  return checks;
}
module.exports = { verifyV221 };
