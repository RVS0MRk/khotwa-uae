# Khotwa V2 independent review package

Baseline: `49f50e8` (clean working tree before implementation). Branch: `codex/khotwa-v2-redesign`. Prior baseline Python result: 46 passed after installing the declared missing pypdf development dependency. Baseline browser integration suite passed. No academic report content was edited. No production deployment or customer contact was performed.

The owner explicitly approved a local commit after the final staged-file audit. The final commit hash and branch are recorded in the review ZIP's `manifest.json` and `COMMIT.txt`. No push, merge or deployment is authorized. The review package includes the complete patch from the baseline to the final commit.

## Ticket coverage

| Ticket | Status | Implementation and evidence |
|---|---|---|
| KH-001 score | PASS | `scoring.py`, `static/scoring.js`, PDF boundary. Missing values remain null, totals require five assessments, legacy neutral fallback values are invalidated. Six scoring tests plus browser incomplete/RTL display. |
| KH-002 finance | PASS | `finance.py`, `/finance`, `test_finance.py`. Decimal strings, explicit rounding, independent expected results, unknown/zero separation and cash vs accounting basis. |
| KH-003 scenarios | PASS | Independent scenario inputs, one-at-a-time sensitivity, six stage allocations, warning on overspend, reset and same-tab recovery. Python and V2 Chromium journeys. |
| KH-004 funding | PASS with external caveats | Eight official-source entries in `static/funding.json`, bilingual search/filter, eligibility, support type, links and review dates. Current intake and detailed conflicting rules require provider confirmation. |
| KH-005 dashboard | PASS | Beginner summary shows idea, customer, next action, score, evidence, risk and Investment access. Forms collapse behind Edit Idea. Original seven tabs preserved and Investment added. Keyboard/RTL tests. |
| KH-006 typography | PASS for practical checks | Tokens and components replace the old override stack. Normal body 16px, secondary body 14px, labels at least 12px. Six token contrast pairs exceed 4.5:1. This is not formal WCAG certification. |
| KH-007 identity | PASS | Sand/ink/emerald system, original landing, onboarding, connected dashboard and finance components. Actual application screenshots and self-hosted actual workspace preview. |
| KH-008 architecture | PASS | Flask partials and separate translations, scoring, core behavior, investment, workspace, events and boot scripts. No frontend build service required. Template reduced from ~171 KB to a small composition file. |
| KH-009 test portability | PARTIAL | Declared Python dev dependencies, pinned Playwright package/lock, managed Chromium, dummy-key fixture setup and `scripts/run_tests.py` passed here. A fresh external `npm ci` was not performed on this host. |
| KH-010 security | PASS for reviewed boundaries | Same-origin script CSP, security headers, delegated events, escaped legacy rendering and safe new DOM construction, input caps, recomputed PDF results, customer-note exclusion from Advisor, CSV injection protection. No new persistence service. |
| KH-011 dependencies | PASS | Pinned local Chart.js/QRCode.js and licensed local fonts; no runtime CDN. Browser test aborts vendor scripts and verifies usable data alternatives. OSV queried 11 direct versions with zero matches; transitive dependency coverage is incomplete. |
| KH-012 charts | PASS | Financial charts use real calculated inputs with data tables, empty states and signed profit values. Existing timeline has a table alternative; unknown score bars say Not assessed. Keyboard and reduced-motion checks. |
| KH-013 Arabic | PASS for local mock workflows | All new financial controls, results, funding entries, errors and state are bilingual. Locale-aware AED output, RTL and retained business names. Arabic PDF output reviewed. Live model Arabic quality is not certified. |
| KH-014 integration | PASS | One financial input state feeds Overview, Risks, Plan, Pitch, Advisor context, scenario views and both PDF exports. New Idea resets it; same-business edits and refresh preserve it. |

## Evidence and review procedure

Final local results: **78 Python tests passed, 0 failed, 0 skipped**, including 18 financial tests, 6 scoring tests, 8 V2 backend tests and the 46 baseline tests. All three Chromium suites passed. The V2 suite reports 31 journey/security/responsive checks; the visual suite covers 36 viewport/language/theme combinations and eight tabs. Both founder reports (6 pages each) and investment briefs (3 pages each) were rendered and visually reviewed: **18 final PDF pages**. The full runner ended with exit code 0.

The one-command suite writes `outputs/v2-review/final-tests.log`. Exact final totals are recorded there. Review the source assertions rather than relying on this table. The expected 500 console message in the integration suite comes from its intentionally malformed provider fixture.

`outputs/v2-review/before/` contains actual baseline captures. Current captures include landing, onboarding, dashboard, score, scenarios and Investment at 375, 390, 768, 1440 and 1920 in English and Arabic. Additional visual-suite captures cover both themes, nine widths and all eight tabs. These are browser captures from a local Flask server with a mocked provider, not concept renders or live Groq evidence.

The directory also contains English/Arabic founder and investment PDFs, rendered page contact sheets, `dependency-audit.json`, `contrast.json` and `performance-local.json`. Performance readings are local synthetic observations, not field Core Web Vitals or Lighthouse scores. INP was not established. The complete review archive is `outputs/Khotwa_V2_review.zip` when generated; generated artifacts remain ignored by Git.

Read `FINANCIAL_SPEC.md`, run `python scripts/run_tests.py`, then independently challenge missing-input handling, score coverage, whole-unit rounding, scenario independence, reload isolation, export recalculation and Arabic layout. Inspect the diff against `49f50e8` and the new files, including the directory's source URLs.

## Security review notes

Legacy innerHTML rendering is retained only where application templates receive `escapePlan`/escaped values or application-owned constants. New financial, funding and score UI uses textContent/DOM nodes. Inline event attributes were removed; scripts cannot run inline under CSP. Harmless HTML payloads are exercised in the actual browser. Static URLs are controlled; WhatsApp uses encoded text. Exports quote CSV fields and prefix possible spreadsheet formulas.

Financial data is anonymous browser-tab state. Customer concern/frequency text, Advisor chat, keys and optional investor draft notes are excluded from session recovery. Advisor business context now allowlists numeric evidence fields instead of sending free-text customer concerns. PDF contents are delivered directly without server-side persistence. Logs retain safe diagnostic categories, not customer notes.

The existing rate limiter remains a bounded in-memory window, appropriate only to the documented single-worker instance. It validates the rightmost forwarded IP instead of a spoofable leading address. It resets on service restart and is not a distributed abuse defense. PDF work remains serialized to reduce memory contention. JSON size and collection caps remain in place. Adding more workers/instances requires a shared limiter before claiming equivalent protection.

No tracked/staged secret files were found. A read-only scan of 114 history objects matched only the known synthetic browser-test credential placeholder; no actual credential exposure was identified. This does not certify unseen remote history. `secret.txt` was not opened or changed.

## Limitations and controlled deployment

- No real Groq request, public-site test or deployment was performed. Mock tests do not establish model quality, token headroom or public response times.
- Linux Gunicorn and Render memory/cold-start behavior were not exercised on this Windows host. The existing `gunicorn -c gunicorn.conf.py app:app`, Python 3.12 series, PORT binding and one-worker deployment configuration remain in use.
- The managed Chromium download succeeded. This host lacks npm, so package metadata/lock were verified against the official registry and browser runs resolved the installed bundled Playwright through NODE_PATH. A fresh external `npm ci` was not performed here.
- The OSV check covered direct runtime/test/vendor versions, not a complete transitive SBOM audit. Contrast checks cover documented pairs, not every rendered state. Keyboard and responsive tests do not replace assistive-technology testing.
- Official Khalifa Fund funding and FAQ pages conflict on detailed age/business-age rules. Sheraa's reviewed cohort calendar and RUWAD's reviewed guide are dated. The directory flags these limits; it does not promise current intake, funding or approval.
- The three competitor reference sites were inaccessible through the web tool. No comparison ratings or screenshots were invented.
- Very long mixed-direction names and real mobile PDF readers still deserve manual review. Arabic prose from live Groq remains an external dependency.

After review, run a controlled release smoke test: both entry paths, actual Groq response, all tabs, finance example and scenario edits, refresh/Clear/New Idea, both PDF languages on a real phone, official links, `/health`, and Render logs/memory. Code and local mock evidence support independent review; they do not establish production success.
