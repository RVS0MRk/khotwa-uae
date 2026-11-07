# Khotwa V2.1 — Round 2 review

Approved baseline: `d639e7ed841326b8ab62d12ea265f96d2a5e3c95` on `codex/khotwa-v2-redesign`. The branch and clean baseline were confirmed before editing. The baseline remains in history. The final local commit identifier is recorded in the review package's `manifest.json`; no push, merge or deployment is part of this round. No academic report was opened or edited. secret.txt was not modified or copied; the corrected mock suites explicitly prevent credential-file fallback.

## Changes

- Replaced the continuous Investment page with seven shared-state subpanels. Financial Overview opens first; startup, operations/cash, scenarios, stages, funding and readiness/brief remain accessible. Subnavigation supports arrows, Home/End, RTL, focus and same-tab recovery. Global calculation errors stay visible across input sections, and failed calculations remove stale chart/table results.
- Added low-volume whole-unit sensitivity with real baseline/comparison/percentage values, ranked signed profit impacts, tied-leader explanation and matching chart/table order. Monetary comparisons report the fil-rounded input actually calculated.
- Added explicit optional simplified cash flow, cash-basis disclosure, simple cash-benefit payback, optional separate licensing, negative-zero normalization and an explicit COGS accounting basis with inconsistency warnings. Existing detailed cash flow remains the default and saved records retain their known licensing-excluded subtotal with a warning.
- Added meaningful editable default volume scenarios, independent scenario reset, current/original resets, missing-value preservation and recovered selected subpanel.
- Moved the Advisor to the header, made the narrow 320 px header wrap, fixed the mobile five-stage labels, separated Today from the validation-workspace card and added three prioritized readiness gaps with reasons, actions and links.
- Made persistent export/error statuses semantic and re-localizable. Unified AED display with grouped Latin digits, two decimal fils and isolated RTL currency runs. Financial CSVs distinguish ratios, units, months and AED while preserving raw values and formula-injection protection.
- Improved both financial PDF contexts: branded headings, currency/grouping, percentage ratios, whole operational units, cash/payback/licensing assumptions, localized market/footer and table spacing. A final spacing adjustment removed orphaned financial notes; PDF workflows were rechecked afterward.
- Rechecked eight official funding resources individually, listed the current seven Khalifa financing programme names, documented conflicting official rules, updated Hub71 equity wording, replaced the old RUWAD brochure reference and flagged unresolved terms. Added eight financing-route explanations without invented grants or approval promises.
- Formatted first-party JS/CSS, separated financial navigation/details/currency/funding-route concerns, replaced empty HTML sinks and unsafe restored-map rendering with DOM nodes, removed static inline template styles and tightened stylesheet CSP. HSTS now accounts for Render's TLS termination; process-local limiter behavior is explicitly tested and documented.
- Expanded score explanations with measures, reasons for importance, provenance/status and improvement actions. Actual financial context is descriptive only; five dimensions, 25-point aggregation, missing-data behavior and the existing evidence rule are unchanged.
- Made mock tests key-independent even when config was imported earlier, documented managed Chromium setup and added the Round 2 suite to the consolidated runner. No assertion was removed to conceal a failure; changed currency/scenario assertions reflect the new specified behavior.

## Exact verification

| Executed check | Result |
|---|---|
| Standard `python -m unittest discover -v`, key unset at launch | 93 passed, 0 failed/errors, 0 skipped |
| Fresh source copy, no secret.txt, empty environment key, fresh interpreter | 93 passed, 0 failed/errors, 0 skipped |
| `scripts/run_tests.py` | Exit 0: 93 Python tests and all four Chromium suites passed |
| Original browser suite | PASS, including four business journeys, discovery, sharing/copy, safe rendering, bilingual cache, Clear/reload/isolation, Advisor and PDFs |
| Existing redesign visual suite | 36 viewport/language/theme combinations; eight dashboard tabs each; PASS (9 widths from 320 to 1920 px) |
| V2 financial browser suite | 31 check groups, 0 failed |
| New V2.1 browser suite | 24 check groups, 0 failed |
| Financial additions | 12 unittest methods, including 3,000 independently computed seeded cases; 0 mismatches |
| Syntax | 16 first-party JavaScript/test files, 0 failures |
| Python dependency consistency | `pip check`: no broken requirements |
| Final PDF spacing | The two financial browser suites and Python discovery were rerun; see final logs |

The four final PDFs contain 18 pages (6-page founder and 3-page investment reports in each language); all pages were rendered and visually inspected.

The full runner's `final-tests.log` includes the intentional malformed-provider HTTP 500 and negative-path Python diagnostic logs. They are fixture coverage, not hidden test failures. The final spacing-only PDF change is additionally covered by `pdf-spacing-v2.log`, `pdf-spacing-v21.log` and final discovery. No live Groq request or public Render verification was performed.

At 390 px, measured Financial Overview plus its subnavigation is **1,957 px English / 1,671 px Arabic**, about 2.3 / 2.0 screens at 844 px height. Baseline captures are actual 390 x 22,571 and 1440 x 11,235 images; deeper features are now reachable through navigation rather than one long page. These numbers describe the default financial workspace, not removal of content. All seven subpanels passed both-language responsive checks at 375, 390, 768, 1440 and 1920 px. Tests also measure fonts >=12 px, six theme-token contrast pairs per theme >=4.5:1, stage bounds, fixed-element/control overlap, labels, focus, chart tables and status switching. This is not formal WCAG certification.

## KH-001 through KH-014

| Ticket | Status | Fix / code location | Evidence | Remaining concern |
|---|---|---|---|---|
| KH-001 scoring | PASS | `scoring.py`, `static/scoring.js`, `static/investment.js`: preserve aggregation and add explanations/financial context | Six retained scoring tests, V2 incomplete-score journeys, V2.1 explanation checks | AI assessments remain provisional; self-reported evidence is not independent verification |
| KH-002 finance | PASS | `finance.py`, `financial_report.py`: discrete/cash/COGS/payback/licensing/zero corrections | Retained 18 financial tests + 12 additions and 3,000 exact cases | Single-period model; no tax, credit or demand forecast |
| KH-003 scenarios | PASS | Engine defaults; `static/investment.js` independent editors/reset/recovery | V2 and V2.1 scenario edits/reset/reload; Python missing/default/tie cases | Illustrative volume assumptions only |
| KH-004 funding | PARTIAL | `static/funding.json`, `static/funding-routes.js`, `docs/FUNDING_SOURCES.md` | Eight individual official-source checks; bilingual filters/cards; eight route controls | RUWAD current terms unverified; Dubai terms partial; Sheraa intake unverified; Khalifa official conflict |
| KH-005 dashboard | PASS | `static/workspace.js`, `static/startsmart.js`, financial subpanels/header Advisor | Existing full journeys and all-tab matrix; 10 Round 2 width/language measurements | Real phone usability still requires owner testing |
| KH-006 typography | PASS | Formatted component styles, stage labels, compact subnavigation and PDF tables | Minimum font, token contrast, clipping/focus/labels; screenshots/PDF renders | Token checks do not cover every possible text/background state |
| KH-007 identity | PASS | Preserved Khotwa V2 design/tokens; scoped financial navigation/layout polish | Before/after screenshots, both themes and languages | Independent aesthetic review remains useful |
| KH-008 architecture | PASS | `formatting.js`, `investment-workspace.js`, `investment-details.js`, `funding-routes.js`; readable JS/CSS | Syntax plus complete workflows and CSP checks | Core app.js remains large; broad framework migration deliberately avoided |
| KH-009 portability | PASS | `test_support.py`, `test_test_setup.py`, `scripts/run_tests.py`, `TESTING.md` | 93 standard key-unset tests and 93 in fresh source copy; managed Chromium suites | Fresh external npm ci/Linux install not executed on this Windows host |
| KH-010 security | PASS | Safe restored map/QR DOM, reviewed legacy sinks, tighter CSP, HSTS, limiter documentation | Source/history scan, retained security regressions, two new header/worker tests, browser CSP/XSS/CSV | Basic process-local rate limiter; no distributed abuse-defense claim |
| KH-011 dependencies | PASS | Preserve bundled licensed charts/QR/fonts; no new production dependencies | Offline/vendor-failure workflows, syntax and pip consistency | No new complete transitive CVE/SBOM audit in this round |
| KH-012 charts | PASS | Ranked sensitivity chart plus matching table; existing finance/path alternatives | Changed assumptions update charts; chart/table alternatives and vendor fallback tests | Real assistive-technology review not executed |
| KH-013 Arabic | PASS | Semantic statuses, unified AED, isolated minus signs, localized PDF footer and market | EN→AR→EN, retained state, all widths/themes, final rendered PDFs | Live Groq Arabic fluency and real-phone PDF readers unverified |
| KH-014 integration | PASS | Shared investment state feeds Overview/Risks/Plan/Pitch/Advisor/PDF; optional features preserved | Full runner, both financial suites, Clear/New Idea/isolation/reload regressions | Public resource/memory/latency behavior still needs release smoke testing |

## All 15 Claude findings

| # | Finding | Status / correction | Direct regression evidence |
|---|---|---|---|
| 1 | Low-volume sensitivity zero impact | PASS: minimum one-unit move where possible, actual percent and comparisons | `test_discrete_sensitivity_small_and_large_volumes`, zero case; V2.1 three-unit browser case |
| 2 | Runway unavailable to beginners | PASS: explicitly selected simplified cash mode, labelled basis, detailed default retained | Cash-mode/runway Python cases; browser selects simplified mode |
| 3 | Export status language stale | PASS: semantic status state re-rendered with language | V2.1 real download EN→AR→EN and error switching |
| 4 | Key-unset discovery fails | PASS: mock bootstrap repairs early config import; no secret fallback | Standard/fresh-copy logs and guarded subprocess test |
| 5 | Investment excessively long | PASS: seven progressive subpanels, overview first | Baseline/after captures and measured overview heights |
| 6 | Initial scenarios identical | PASS: editable -20%/+20% volume defaults with honest discrete handling | Default/missing/zero Python cases; editor/reset/recovery browser cases |
| 7 | Negative zero | PASS: normalize engine/report values and UI zero display | Explicit money/ratio zero and browser formatting checks |
| 8 | COGS inconsistency | PASS: separate accounting basis permitted; selected subset inconsistency warns/withholds gross margin | `test_accounting_cogs_basis` |
| 9 | Advisor overlap | PASS: static header placement, narrow header wrap | Five widths x both languages, fixed overlap checks, 320 px visual matrix |
| 10 | Duplicate first-step paragraph | PASS: Today retains action; validation workspace gets distinct purpose | V2.1 unequal card text assertion and dashboard screenshots |
| 11 | Clipped mobile stage tracker | PASS: five compact wrapping labels with accessible full descriptions | Stage label bounds/scroll widths in both languages |
| 12 | Inconsistent Arabic AED | PASS: same grouped Latin digits, two decimals, AED; RTL isolate | Browser zero/thousands/negative/decimal cases; final Arabic screenshots/PDFs |
| 13 | Financial PDF weaknesses | PASS: money/percent/unit meaning, assumptions, footer, spacing | Tamper/recalculation tests, real exports and rendered final pages |
| 14 | Sensitivity unranked | PASS: descending absolute profit impact, ties, same chart/table list | Sorted/tie Python assertions and browser chart/table workflow |
| 15 | Generic readiness guidance | PASS: top three remaining checklist gaps with why/action/section and relevant entry counts | Checklist edit changes recommended gap; linked buttons and self-report labels |

## Artifacts and changed files

The review ZIP includes a full public-source snapshot, reproducible binary-safe patch against the approved baseline, Git change list, commit/branch manifest, final logs, before/after captures, all final PDFs and page renders, and this ticket/finding matrix. Generated files remain ignored, not committed. `changed-files.txt` and `change-stat.txt` give the complete file inventory; implementation groups are described above. `TESTING.md`, `FINANCIAL_SPEC.md`, funding-source and security notes are included separately from any academic work.

## Remaining limits and release boundary

No known failing local regression remains. Funding verification limits are explicit in the directory and KH-004 is PARTIAL; no provider approval or current intake is promised. No real Groq call, external npm ci, Linux Gunicorn run, Render edge/load/cold-start/memory test, screen-reader certification or real-phone PDF review was performed. This host used the bundled Node/Playwright runtime and installed managed Chromium; reproducible normal setup commands are documented.

The in-memory quota and PDF serialization are per process. Keep the existing one-worker configuration; shared protection is required before scaling workers/replicas. Free-service PDF/matplotlib memory and timeout risk still needs a controlled release check. Source safety scanning is evidence about this local tree/history, not unseen remotes. The local code is prepared for independent review, not automatically approved for public deployment. No production website was modified.
