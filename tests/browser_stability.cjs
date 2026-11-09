// Rendering state, not an elapsed-time guess: portable across Chromium hosts.
async function settledVisuals(page) {
  // Chromium may suspend rAF on a background tab (the dark landing audit
  // temporarily opens a second page). Activate the audited surface first.
  await page.bringToFront();
  // Poll actual animation state with Playwright's bounded wait. An animation's
  // finished promise can remain unresolved if its document becomes inactive.
  await page.waitForFunction(
    () =>
      document.fonts.status === "loaded" &&
      !document.documentElement.classList.contains("theme-switching") &&
      document
        .getAnimations()
        .every(
          (a) =>
            a.playState !== "running" ||
            !Number.isFinite(a.effect?.getComputedTiming().endTime),
        ),
  );
}
module.exports = { settledVisuals };
