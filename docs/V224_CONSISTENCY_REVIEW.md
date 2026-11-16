# Khotwa V2.2.4 final consistency correction

Date: 2026-11-16. Baseline: `fa8ee4012e2411a1f4ad35aaa227509727f9ab39`.
Branch: `codex/khotwa-v2-redesign`. Local change only; no push, merge or deployment.

## Reproduction and cause

An isolated snapshot of the required baseline reproduced five Proof responses,
including one payment selection: dashboard **18/25**, Founder PDF **Incomplete**,
and a stale no-feedback statement. This used fixture AI and the actual UI and
`/pdf` route. The diagnostic artifacts and the prior complete ChatGPT review
package were read; the historical package remains unchanged.

The browser correctly updated `idea_overview.evidence` and the Customer Need
explanation. Receipt v2 authenticated generated prose only. Export removed the
unsigned Proof-derived explanation and evidence narrative; PDF score
normalization then treated Customer Need as missing. The report's stale alias
was a suspected cause in the earlier report, but stripping at the export gate
was the reproduced cause. The PDF cover also used a fixed decision caption.

## Corrections and requirements matrix

| Requirement | Implementation | Verification |
|---|---|---|
| Current score and assessment | Receipt v3 authenticates the baseline assessment and canonical identity. Export derives the current Customer Need dimension using the existing dashboard rule. PDF displays that protected result without resetting its source/status. Browser state aliases are synchronized. | No entries 15/25; five interested responses 15/25; payment selection 18/25; Clear restores 15/25, including refresh. |
| Receipt integrity | HMAC, ledger and identity are checked. An alternate-language receipt must belong to the same canonical business. Posted totals, reasons and browser backups are ignored as score authorities. | Forged/absent signatures, changed receipt numbers, identity changes and modified ledgers fail closed. Actual PDFs remain incomplete for unauthenticated or genuinely incomplete baselines. |
| Proof evidence narrative | Export rebuilds its application-owned evidence and decision copy from bounded counts. The cover, decision, Proof summary and readiness section use the current self-report narrative. | Sixteen real browser PDF downloads, across two native languages × four states × two export languages; text checks and rendered EN/AR inspection. |
| Preserve financial and AI safety | Other score dimensions require the authenticated baseline; missing dimensions remain missing. Model prose still passes the existing safety gate and receipt filtering. No classifier/regex vocabulary was expanded. | Original safety, personalization and financial regressions; new edited-prose, incomplete-baseline and invalid-count tests; 42 direct Python–JavaScript Proof-rule comparisons. |
| Native Arabic finance | Bootstrap-created Advanced, cash-timing explanation and calculation-summary controls carry both translation attributes. | Native Arabic generation, EN→AR→EN switching and initial Arabic session restoration; 390px screenshots and axe checks. |
| Original AI language | No translation is fabricated. Personalized business prose remains in its original language when the existing translation-unavailable notice applies. Application-owned controls and Proof copy localize separately. | Existing V2.2.4 canonical round-trip/fallback regressions remain enabled and pass. |
| Accurate landing wording | “Record customer feedback” / “سجّل ملاحظات العملاء”. | Both landing languages asserted in browser tests. Proof disclosures continue to say self-reported and not independently verified. |

The receipt does **not** verify a customer, payment, business outcome, or the
truth of entered observations. Counts must be integers from zero to ten,
consistent with the ten-row UI, and mutually exclusive categories cannot exceed
the response total. They can affect only Customer Need. A complete assessment
remains provisional, not a probability of commercial success.

## Tests and evidence

All provider I/O in these tests is mocked. No real Groq requests were made.

| Command | Result |
|---|---|
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 162 test methods passed; zero failures/errors/skips. This includes 12 new consistency methods, 3,000 seeded financial arithmetic cases and the existing scoring/safety/route/PDF regressions. |
| `node test_browser.cjs` | PASS: discovery, four journeys, Copy, CSV, ten-row Proof, Clear/reload, isolation, Advisor, safe rendering, bilingual PDFs and mobile. |
| `node test_redesign.cjs` | PASS: 9 widths × EN/AR × light/dark visual matrix, keyboard, reduced motion, evidence ladder, sharing, favicon. |
| `node test_v2.cjs` | 31 checks; zero failures. |
| `node test_v21.cjs` | 24 financial/localization/accessibility/responsive groups; zero failures. |
| `node test_v22.cjs` | 77 groups, 128 main axe states, 214 main screenshots; zero failures. Includes 18 new consistency cases, 16 actual bilingual PDF downloads and two additional mobile finance axe states with zero serious/critical violations. Existing V2.2.1 checks sample 288 theme frames at >=4.5:1. |
| `node --check` across application and test JavaScript | 36 files passed. |
| `git diff --check` | Passed. |

Windows 11, Python 3.12.14, Node 24.22.1, Playwright 1.62.1,
Chromium 151.0.7922.34 and axe-core 4.14.0. Tests use the existing `.venv`.
Set `PYTHON_EXE` to its absolute interpreter path for direct browser runs. On
this workstation `PLAYWRIGHT_BROWSERS_PATH` points to the existing managed
browser cache. Test servers use separate local ports, never the production URL.

Exact stdout/stderr and per-suite exits/timings are in the review archive's
`logs/`. `browser/consistency/checks.json` records each score, status, canonical
identity, Proof summary and PDF result. Additional `browser/*checks.json`,
`axe-matrix.json` and `measurements.json` preserve the existing suite evidence.
All 16 new PDFs and their extracted text are included. Selected before/after
mobile screenshots, complete EN/AR changed-report renders/contact sheets,
zero/five/Clear cover renders and the baseline reproduction are included.

Poppler emitted missing display-font warnings for Symbol/ArialUnicode during
chart rendering; rendering completed and the actual inspected EN/AR charts and
text remained legible. These warnings are preserved in `logs/pdf-render.log`.
The base browser suite intentionally exercises malformed generation and logs a
mock 500 console resource message; its expected error-handling assertions pass.

## Changed-file inventory

| File | Purpose |
|---|---|
| `provenance.py` | Version 3 signed baseline/identity/decision and compatible v2 prose verification. |
| `scoring.py` | Bounded self-report counts, deterministic export assessment and bilingual evidence text. |
| `material_claims.py` | Derive current export state after receipt verification; preserve prose gate and current source ledger. |
| `founder_pdf.py` | Same-business localization, requested-language application copy, protected score/status and current cover/readiness narrative. |
| `static/scoring.js` | Shared evidence wording and canonical state score synchronization. |
| `static/app.js` | Dashboard/readiness evidence narrative alignment. |
| `static/finance-beginner.js` | Relocalize dynamically created finance controls and explanation. |
| `static/startsmart.js` | Accurate landing evidence wording in EN/AR. |
| `test_consistency.py` | Integrity, scoring parity and real PDF content regressions. |
| `tests/consistency_browser.cjs` | End-to-end Proof/export, localization, refresh, mobile and accessibility checks. |
| `tests/check_pdf_consistency.py` | Independent checks of downloaded PDF artifacts. |
| `test_browser_server.py` | Isolated complete-assessment Arabic fixture for these regressions; mock only. |
| `test_v22.cjs` | Include the new browser cases in the established suite. |
| `README.md` | Receipt compatibility/recovery guidance and review link. |
| `TESTING.md` | New verification coverage and current version heading. |
| `docs/V224_CONSISTENCY_REVIEW.md` | This matrix, inventory, results and limitations. |

## Remaining limitations

- **Older sessions:** v2 receipts can authenticate original prose, but never
  signed the numeric baseline. Regenerate an older business for a complete
  authenticated score export. An unsigned/tampered assessment stays incomplete.
- **Process restarts:** without a stable private `KHOTWA_CONTENT_SIGNING_KEY`,
  restarting invalidates prior receipts. Configure that optional secret outside
  Git for cross-restart validity. No key or deployment setting was changed here.
- **Live AI:** current live Groq quality, latency, verifier accuracy and quota
  behavior were not tested. Fixture success is not live-model verification.
- **Production:** Linux/Gunicorn execution, Render cold starts, memory/concurrency,
  physical phones and hardware screen readers were not tested in this Windows
  correction round. Existing process-local rate limits remain unchanged.
- **Finance and funding:** the existing educational projection scope remains;
  missing assumptions stay unknown. Current funding intake/eligibility was not
  reverified and historical listings are not approvals.

No academic reports, secrets, production settings, review archives, commits on
remote branches or production websites were modified. Generated evidence stays
under ignored `outputs/`, outside the source commit.
