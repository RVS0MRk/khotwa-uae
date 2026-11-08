# Khotwa V2.2 correction review

Baseline `802149433729d58ebb191cb631c242a28dca914d` and a clean tree were verified before editing on `codex/khotwa-v2-redesign`. The final local commit is recorded in the package manifest, avoiding a self-referential commit hash in this file. No push, merge, PR, deployment, production settings change or academic-report work is included. Secret.txt was not opened, edited, copied or packaged.

## Implementation choices

The P0 corrections were implemented and tested before the later GUI/finance work. Safe model prose now survives per-field and sentence validation. The rich fixtures exceed the required 75% retention, while unsafe sentences are removed without discarding their neighbors. The generation budget remains **5,000 completion tokens**: mocked output cannot establish live GPT-OSS schema/token headroom. Advisor remains 1,200 and discovery 2,500, with JSON mode, low reasoning effort and no returned reasoning.

The four operating inputs support revenue, contribution, profit and break-even, but cannot establish initial cash spent or reserves. Numeric runway/payback therefore stay unknown until their actual required assumptions exist. This is an intentional resolution of the contradictory four-input acceptance sentence, consistent with the owner's explicit prohibition on invented financial outputs. New browser businesses disclose simplified cash timing; saved modes and the raw API's legacy default remain compatible.

Phone pages use progressive disclosure: seven-day cards, the later full path, investment stages, programme cards and the general financing-route guide retain all content behind keyboard-accessible summaries. The later full path and general route guide collapse on phones and open on desktop. This keeps the measured entire seven-day/funding pages within their height targets, rather than merely measuring their first component. A breakpoint change updates the two large disclosures. Opening the full path redraws its lazy charts. Clear removes Proof entries and optional investor notes; New idea deliberately resets the previous business. Respondent free text and Advisor chat remain excluded from recovery.

Funding corrections distinguish dated official announcements, past cohort benefits, closed intake and current criteria. RUWAD's Ministry URL could not be refreshed; its user-supplied reference is attributed and marked unretrieved, alongside the retrieved historical WAM source. No current acceptance or eligibility is inferred. See [FUNDING_SOURCES.md](FUNDING_SOURCES.md).

No new server runtime dependency was added. Existing direct dependencies and their clean-environment transitive dependencies are exactly pinned. The dev extra for WOFF generation uses the same fonttools version as the runtime pin. A clean runtime import/generation/finance/PDF smoke and dev-requirement resolution supplement the existing-environment tests. No WSGI compression layer was added because the uncompressed local landing meets the budget; live Render Brotli headers remain a later release check.

## Ticket requirements matrix

Paths in the screenshot column are inside the review ZIP's `screenshots/`; `v22/` contains the full requested matrix. A wildcard means the same view at the recorded widths/languages/themes. Automated accessibility is not a physical-device or screen-reader certification.

| Ticket | Status | Code / data | Verification | Screenshot evidence / remaining limit |
|---|---|---|---|---|
| V21-001 | PASS | `plan_content.py`, `plan_normalize.py`, `content_safety.py`, `app.py`, `startsmart.js` | `ContentTests` retention/difference/structural/discovery/route tests; two rich browser businesses | `v22/overview-*`, `v22/proof-*`, `v22/pitch-*`; live model retention not measured |
| V21-002 | PASS | `content_safety.py`, `advisor.py`, `plan_content.py`, `app.js`, `dashboard-polish.js` | EN/AR seam, word-limit, safe-topic/unsafe-assertion and Advisor-neighbor tests; rich visible risk/pitch assertions | `before/` and `after/` Pitch/Risks/Overview pairs, `v22/pitch-*`; natural-language filters are bounded heuristics |
| V21-003 | PASS | `privacy.js`, onboarding/Advisor/footer wiring | EN/AR notices and dialog, actual storage/context/log-path review; dialog and page axe checks | `v22/onboarding-*`; browser restore caveat and Groq processing disclosed |
| V21-004 | PASS | `app.py`, `request-status.js`, API callers, `investment-details.js` | Independent quota/env override tests; localized 429 for all five expensive UI callers, including export status language switching | UI test logs; process-local limits do not guarantee production spending/capacity |
| V21-005 | PASS | `onboarding.js`, `app.js`, `startsmart.js` | One-tap entry/back, stale errors, ten categories per language, optional discovery fields, neutral Proof placeholders | `v22/onboarding-existing-*`, `onboarding-discovery-*` |
| V21-006 | PASS | `startsmart.js/css`, `dashboard-polish.js`, `scoring.js` | Measured header thresholds, gauge semantics, compact Copy geometry, responsive suites | `before/header-*`, `after/header-*`, `v22/overview-*`; heights below |
| V21-007 | PASS | `finance-beginner.js`, `investment.js`, finance subpanels/styles | Four-input results + unknown startup outputs, explicit simple/advanced modes, saved detailed mode regressions | `v22/investment-overview-*`, `monthly-operations-*`, `investment-empty-*`; no invented runway/payback |
| V21-008 | PASS | `finance-beginner.js`, `investment.js`, `app.js` | Detected costs/price/risks/pitch/real entries/reservations, changed priorities, separate self-confirmation; demo excluded | `v22/investor-readiness-*`; user records are not independent verification |
| V21-009 | PASS | `proof.js`, `app.js`, responsive CSS | Phone Add response, no horizontal scrolling, 10-row desktop, Note length/CSV injection, counts/Clear/reload | `before/proof-*`, `after/proof-*`, `v22/proof-*` |
| V21-010 | PASS | `workspace.js`, `funding-routes.js`, `funding-directory.js`, day/stage DOM | Entire-page height assertions, collapsed detail reachability, preserved stage tasks/content | `v22/seven-day-*`, `funding-*`, `stages-*`; heights below |
| V21-011 | PASS | `funding.json`, `funding-directory.js`, source notes | Individual official-source checks; date/tag/status schema tests and filters | `v22/funding-*`; current eligibility/intake and RUWAD Ministry refresh remain unverified |
| V21-012 | PASS | landing partial, styles, `workspace.js` | Live HTML example, typography/overflow, visible Advisor label, preview-demo journey | `v22/landing-*`; example is explicitly fictional |
| V21-013 | PASS | `formatting.js`, `finance-analysis.js`, Proof/finance/PDF renderers | Shared AED output, signed actual percentages/units, grouped diverging sensitivity, unequal-move warning and table | `v22/scenarios-*`; original detailed table preserved |
| V21-014 | PASS | `finance-analysis.js`, `investment.js` | Only differing scenario columns; invariant metrics in one summary line; existing scenario edits/reset pass | `v22/scenarios-*` |
| V21-015 | PASS | `finance.py`, `test_v21_finance.py` | Original 3,000 independent cases + 20,000 display cases, zero/zero break-even, rounding warnings, partial allocations | Python logs, financial spec; unknowns preserved |
| V21-016 | PASS | `investment.js`, `financial_report.py` | Three-note refresh recovery, Clear/New reset, investment PDF provided-fields-first and missing-line grouping | `v22/investor-readiness-*`, all investment PDF pages |
| V21-017 | PASS | translations, JS formatters, templates/data | Static first-party digit scan; EN/AR browser display and numeric parity | All AR screenshots and PDF pages; user text is not rewritten |
| V21-018 | PASS | QR alt, labels, focusable regions, footer/contrast styles | 128-state axe matrix, two dialog audits, visible mobile Advisor and 24 px footer target checks; keyboard tests | `axe-matrix.json`, `v22/*`; no serious/critical; no screen-reader/physical-phone audit |
| V21-019 | PASS | WOFF2, asset hashes/cache, `chart-loader.js`, funding/QR deferred load | Fonts <60 KB, cache/version checks, lazy/vendor fallback tests and cold 390 transfer budget | `measurements.json`; live edge compression unverified, no dependency added |
| V21-020 | PASS | requirements and npm lockfiles | Clean runtime install/check/smoke, compatible dev resolution, exact 27-package runtime pip-audit | Dependency logs; Windows validation, no Linux load profile |
| V21-021 | PASS | prompt/normalization/Advisor/PDF modules, Flask wiring | Full regressions, Black 120 where practical, frontend syntax, 200 Node/Python score objects, escaped-persona sink guard | Test logs; long prompt literals retain readable content |
| V21-022 | PASS | `advisor_history.py`, `advisor.py`, chat client | Genuine signature, tamper/unsigned/cross-session rejection, eight-turn/1,200-char limits, Secure/HttpOnly cookie tests | Security tests; random process key resets on restart |
| V21-023 | PASS | four complete fixtures, `test_v22_content.py`, `test_v22.cjs` | Rich EN/AR full journeys, alternative business, retention/unsafe/seam tests | Full V2.2 screenshot set uses rich fixtures rather than the old sparse mock |
| V21-024 | PASS | `scripts/live_smoke.py`, testing instructions | Opt-in/key-required exit and exactly two requests verified with mocked transport | Owner command delivered; real live script deliberately not run |

## Intentional changes to older test assertions

No existing test was deleted. Black-only changes in older Python tests are formatting. The following behavior assertions/selectors were updated to match named tickets:

- `test_routes.test_ask_uses_plan_and_recent_history` and `test_quality_upgrade.test_advisor_multi_part_recall_and_user_budget_source`: obtain a genuine server-issued assistant signature/cookie instead of injecting an unsigned assistant reply (V21-022). Forwarded role/content assertions remain.
- `test_browser.cjs` / `test_redesign.cjs`: reveal phone respondents through Add response before editing later rows; assert cards have no horizontal scroll; neutral Arabic monthly example replaces the old data-like weekly placeholder (005/009). Proof average displays grouped two-decimal AED rather than a bare float (013).
- Mobile Edit/New actions open Actions first (006). The seven-day distinct-action assertion reads the action rather than the newly displayed repeated time-estimate line; full-path cost/chart checks expand the phone disclosure (010). New idea still returns to entry choice; direct `resetApp()` intentionally opens its form.
- WhatsApp outreach no longer begins with the Khotwa brand; shareable founder summary remains branded (002).
- V2/V2.1 detailed COGS/cash entry opens Advanced and selects separate cash timing where required; all arithmetic expectations remain (007). Sensitivity's detailed table is opened before reading it (013).
- V2 investor notes now recover after refresh rather than disappearing; Clear/New reset is asserted separately (016).
- Funding tests broaden the emirate filter before asserting all eight entries, expand a programme before reading its details, and expect RUWAD's dated-official badge instead of the old unverified badge (010/011).
- V2.1 overflow assertions gained width/language/panel diagnostics; no threshold was relaxed. The funding grid now allows actual shrinking at narrow widths.

## Exact verification and measurements

The final review package's `logs/`, `content-retention.json`, `measurements.json`, `axe-matrix.json` and `pdfs/pdf-summary.json` are the machine-readable evidence. All Python and browser processes started with the environment key unset/empty; test-only bootstrap supplies a synthetic key and mock transport. No live Groq test was performed. Deliberate error-fixture ERROR/HTTP 500 logs are expected, not failed assertions.

| Check | Final result |
|---|---|
| `python -m unittest discover -v` | 116 tests passed; 0 failures/errors/skips |
| `node test_browser.cjs` | PASS: one integrated regression run, including four business journeys, bilingual PDFs, safety, sessions and Proof Mode |
| `node test_redesign.cjs` | PASS: nine viewport check groups (36 language/theme cases), plus the functional interaction/motion/keyboard group |
| `node test_v2.cjs` | 31 check groups passed; 0 failures |
| `node test_v21.cjs` | 24 check groups passed; 0 failures |
| `node test_v22.cjs` | 31 check groups passed; 128 axe states; 214 PNG captures |
| axe serious/critical | 0 across all 128 landing/tab/subpanel states; privacy dialogs also passed in both languages |
| Financial randomized checks | Retained 3,000 independent arithmetic cases + 20,000 display-reconciliation cases passed |
| Python/JavaScript scoring | 200 generated objects matched |
| Rich AI strings retained | EN 153/155 (98.71%); alternative EN 153/155 (98.71%); AR 146/155 (94.19%) |
| Dependencies | 27 exactly pinned runtime packages; pip-audit: 0 known vulnerabilities; pip check clean in both environments; dev requirements resolve |
| Fonts | Inter WOFF2 33,176 bytes; Arabic WOFF2 50,084 bytes; full PDF font retained |
| PDFs | Founder EN 7 pages / AR 6; investment EN 3 / AR 3. All 19 pages rendered and visually inspected; all three founder charts present |
| Additional checks | Frontend Node syntax passed; clean-runtime mock generation/finance/EN+AR PDFs passed with network forbidden |
| Precommit scan | 139 unique historical text blobs examined; 0 credential-pattern hits, 0 private/unignored generated paths, 0 academic changes. No secret-file read |

The requested light screenshots are 18 views × 5 widths × 2 languages = 180. Dark Overview plus seven investment subpanels at 390/1440 in both languages add 32; two explicit empty-state captures make 214. Matching before/after screenshots add 24 baseline + 24 final images, including headers, at 390/1440 EN/AR. Older suites also generated their own temporary/ignored artifacts; their logs record locations. The review ZIP includes the complete V2.2 matrix and comparison set rather than duplicating those older matrices.

| Entire document height / position | EN | AR |
|---|---:|---:|
| Overview at 390 | 5,681.00 px | 5,016.00 px |
| 7-Day Plan at 390 | 2,834.00 px | 2,560.00 px |
| Funding at 390 | 3,354.00 px | 3,167.00 px |
| Stages at 390 | 3,130.00 px | 2,891.00 px |
| Top to tabs at 390 | 919.84 px | 839.66 px |
| Top to tabs at 1440 | 577.58 px | 577.58 px |

Cold local landing transfer at 390: **430,028 bytes (419.95 KiB)** in each recorded language run, below 450 KiB. These browser transfer measurements include navigation/resources before generation, with no server compression, no cache and no service worker. This is a local asset measurement, not a live network-speed or Core Web Vitals claim. The font/QR/funding choices keep both languages within the same budget.


## Remaining release checks

Owner-run live EN/AR generation/retention/latency, real Render HTTPS/compression/cache headers, free-instance PDF memory/timeouts, Linux Gunicorn operation, real phones and screen readers remain unverified. Current funding terms/intakes require checking at application time; the RUWAD Ministry fetch was incomplete. Mock retention does not establish live language quality or the safety of a smaller token budget. Rate-limit defaults are configurable classroom safeguards, not permission to raise production spending. The review package includes no secrets, local environment, academic report, generated customer data, push or deployment.
