const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { settledVisuals } = require("./browser_stability.cjs");

const tourism = [
  ["رحلات سفاري في صحراء ليوا للسياح", "Tourism & Hospitality"],
  ["جولات مرشدة لسائح يزور العين", "Tourism & Hospitality"],
  ["تنظيم رحلات سياح إلى المتاحف", "Tourism & Hospitality"],
  ["رحلات مدرسية تعليمية", "Education & Tutoring"],
];
async function verifyV222(browser, base, root) {
  const evidence = [];
  const folder = path.join(root, "v222");
  fs.mkdirSync(folder, { recursive: true });
  for (const width of [390, 1440])
    for (const locale of ["en", "ar"]) {
      const page = await browser.newPage({
        viewport: { width, height: 900 },
        reducedMotion: "reduce",
      });
      await page.goto(base, { waitUntil: "networkidle" });
      if (locale === "ar") await page.locator("#langBtn").click();
      for (const theme of ["light", "dark"]) {
        if (theme === "dark") await page.locator("#themeBtn").click();
        await settledVisuals(page);
        const geometry = await page
          .locator(".footer-links")
          .evaluate((nav) => ({
            columnGap: getComputedStyle(nav).columnGap,
            links: [...nav.children].map((e) => {
              const r = e.getBoundingClientRect();
              return {
                id: e.id,
                text: e.textContent,
                x: r.x,
                y: r.y,
                width: r.width,
                height: r.height,
                center: r.y + r.height / 2,
              };
            }),
          }));
        assert.equal(geometry.columnGap, "20px");
        for (const link of geometry.links)
          assert.ok(
            link.width >= 24 && link.height >= 24,
            JSON.stringify(link),
          );
        const rows = [];
        for (const link of geometry.links) {
          let row = rows.find((r) => Math.abs(r[0].center - link.center) < 3);
          if (!row) rows.push((row = []));
          row.push(link);
        }
        for (const row of rows) {
          row.sort((a, b) => a.x - b.x);
          for (let i = 1; i < row.length; i++)
            assert.ok(
              Math.abs(row[i].x - row[i - 1].x - row[i - 1].width - 20) < 1,
              "Inconsistent footer gap",
            );
        }
        assert.ok(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        );
        await page.evaluate(() => document.activeElement?.blur());
        await page.locator("footer").screenshot({
          path: path.join(folder, `footer-${width}-${locale}-${theme}.png`),
          animations: "disabled",
        });
        evidence.push({ width, locale, theme, geometry });
      }
      await page.locator("#have-idea").click();
      for (const [idea, category] of tourism) {
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
          category,
          idea,
        );
      }
      await page.close();
    }
  fs.writeFileSync(
    path.join(root, "v222-checks.json"),
    JSON.stringify({ footer: evidence, tourism }, null, 2),
  );
  console.log(
    "PASS V2.2.2: 4 added check groups; 8 footer captures; 4 tourism/education cases in each viewport/language.",
  );
  return 4;
}
module.exports = { verifyV222 };
