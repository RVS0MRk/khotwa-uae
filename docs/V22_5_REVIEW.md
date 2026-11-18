# Khotwa V2.2.5 implementation review

Implemented locally on `codex/khotwa-v2-redesign`, starting from the required clean `d1e4e6814017c0771988ab30e6e84ae650a485ed`. The machine-readable archive manifest records the final commit and tree IDs. Patch comparison starts at V2.2.3 `03a29b1be811b7b9767acd6391c66d6e4c62b871`.

This is an implementation with bounded regression evidence, not a live-provider or deployment certification. No academic report was opened or changed. No push, merge, PR or deployment was performed. The old final-QA archive remains unchanged.

## Six-ticket matrix

| Ticket | Status | Code changed | Tests | Evidence |
|---|---|---|---|---|
| V225-001 Mixed-script PDFs | PASS | `pdf_text.py`, `founder_pdf.py`, `financial_report.py` | `test_v225` shared paragraph, all Founder states and Investment methods; existing export tests; real mock-browser downloads | 16 Founder + 4 Investment PDFs; every one of 118 pages rendered; `evidence/pdf-audit.json`; all contact sheets and full pages |
| V225-002 AI publication safety | PASS for specified regression cases | `publication_policy.py`, `material_claims.py`, `provenance.py` | Wrong classification labels across model roles and all AI routes; legacy/current signatures; existing safety suites | 252 independent route probes, zero unsupported survivors; fixed independent fixtures; Pitch/Advisor screenshots |
| V225-003 Negation false positives | PASS | `publication_policy.py`, `content_safety.py`, `material_claims.py` | 14 new bilingual denials; safe future actions; neighboring positives/conditions; unchanged prior precision tables | `tests/fixtures/v225_publication.json`; Python logs; 30/30 safe route cases retained in each functioning-classifier mode |
| V225-004 Language preservation | PASS | `plan_normalize.py`; test fixtures/helpers | Native EN/AR round trips, refresh, no regeneration, canonical ID, substantive fields, scores, finance and Proof | `browser-run-*/v225-checks.json`, language-switch screenshots/PDFs; generic duplicate-translation unit cases |
| V225-005 PDF pagination | PASS for short/long test reports and matrix | `financial_report.py`, shared paragraph wrapping | Short/long EN/AR financial appendix methods; every matrix page inspected | Financial table and explanatory notes kept together; no isolated final disclaimer in tested reports; page renders |
| V225-006 Dependencies | PASS | No pin/dependency changes | Fresh isolated binary install of unchanged `requirements-dev.txt`; full Python and browser runs using its interpreter; `pip check` | `logs/pinned-environment-install.log`, version comparisons and freezes; 27/27 runtime pins match; 31 declared requirement entries match |

## Implementation and trust boundaries

The shared ReportLab paragraph keeps logical text through wrapping, shapes Arabic, resolves bidi per visual line with style ownership and selects the bundled Amiri font for Arabic runs. Latin fonts, English report alignment, numbers and existing labels remain. Original input is escaped before generated font spans. Bidi control characters are stripped; no external font download or new runtime dependency was added. Pure Latin uses ReportLab's ordinary path. Both report types use the same renderer. Tables, headings and report cover content pass through it; existing chart/footer rendering remains.

Model classifications do not establish evidence. The deterministic gate reuses the unchanged material-claim ontology and checks local predication, modality, negation and explicitly uncertain assumptions independently of a classifier label. It does not grow enterprise-success vocabulary lists. Unsafe clauses can be omitted while safe neighboring clauses survive. Legitimate questions, participial service descriptions, local denials, conditional research, provisional scoring reasons and AED amounts have precision regressions. Existing content assertions were not removed or relaxed.

Raw model provenance is discarded. User input is an attributed assumption; Proof counts are bounded self-reports; financial output is recalculated from user assumptions. There is no accepted external-achievement attestation source in this release. A signed export receipt authenticates published text/assessment and policy version; it does not prove commercial outcomes. The current publication-policy marker is signed, cannot be added to an old receipt without invalidating its HMAC, and earlier genuinely valid receipts are rechecked before reuse. Forged identity, ledger, score/signature and process-key-change cases remain covered. The current dashboard/PDF assessment is derived from authenticated baseline dimensions plus the same self-report rule.

The reported localization defect came from accepting the same generic translation for many distinct source fields. Such duplicate placeholders are now rejected. A single authoritative personalized plan, canonical assessment and ID remain. Missing translation retains substantive source-language text with the existing disclosure. Browser comparisons cover summary, overview, pitches, action, personas, seven-day plan, risks, score, inputs and self-reported Proof state. Application-owned Proof wording may localize; original business prose is compared independently.

## Exact automated verification

All tests use synthetic mocked transport. `GROQ_API_KEY` was removed from the launching environment; the test bootstrap installs its explicit synthetic placeholder and mock classifier. No credential file or live Groq endpoint was used. Python 3.12.14, Node 24.22.1, Playwright 1.62.1, managed Chromium 151.0.7922.34 and axe-core 4.14.0 on Windows.

| Run | Result | Exact log relative to evidence root |
|---|---|---|
| existing Python environment | 175 passed; 372.524 seconds | `logs/python-existing-final.log` |
| pinned Python environment | 175 passed; 403.330 seconds | `logs/python-pinned-final.log` |
| `node test_browser.cjs` | PASS: original functional/session/security/bilingual/PDF suite | `logs/test_browser-final.log` |
| `node test_redesign.cjs` | PASS: full visual/responsive/theme/journey suite | `logs/test_redesign-final.log` |
| `node test_v2.cjs` | 31 groups passed, zero failures | `logs/test_v2-final.log` |
| `node test_v21.cjs` | 24 groups passed, zero failures | `logs/test_v21-final.log` |
| V2.2 consecutive run 1 | PASS V2.2: 81 check groups; 128 axe states; 214 screenshots. No live Groq requests. | `logs/test_v22-run-1.log` |
| V2.2 consecutive run 2 | PASS V2.2: 81 check groups; 128 axe states; 214 screenshots. No live Groq requests. | `logs/test_v22-run-2.log` |
| V2.2 consecutive run 3 | PASS V2.2: 81 check groups; 128 axe states; 214 screenshots. No live Groq requests. | `logs/test_v22-run-3.log` |
| Frontend syntax | 37 JS/CJS files passed `node --check` | `logs/frontend-syntax.log` |

The new count is **175 Python methods = all 162 prior methods + 13 new methods**. Each V2.2 run includes 128 primary axe states, requires zero serious/critical violations and retains its existing contrast/geometry assertions, plus four V2.2.5 groups. Both languages, light/dark, desktop/mobile emulation, finance, Advisor, Proof, exports and recovery are exercised. Earlier failed development runs and focused diagnostics are retained with distinct names; they are not the final verdict. The full suites were repeated after precision regressions were corrected.

Independent arithmetic: seed 20261117, **1,200 cases / 25,200 metric comparisons / zero mismatches**, plus eight missing-assumption edge cases. This covers startup/funding gap, contribution, break-even continuous/whole units, profit, margins, simplified/entered cash flow, runway and payback. All four browser financial CSVs match **76 raw metric comparisons**, all four Investment PDFs retain expected figures, and **28 independent receipt/parity cases pass**. Scenarios and UI display consistency remain covered by the existing finance/PDF/browser suites. No finance or scoring formulas changed. Evidence: `financial-independent.json`, `csv-pdf-finance-comparison.json`, `receipt-independent.json` and exact logs.

The independent safety probe reuses the prior QA's 18 unsafe and 10 legitimate examples across three routes and three classifier modes (252 cases). **162/162 unsafe route cases are omitted**. Safe cases survive 30/30 with correct classifications and 30/30 with the deliberately wrong noun-phrase classification. Classifier-unavailable mode fails closed, as intended. New fixed fixtures add eight independent loan/investor/revenue/contract examples; all 26 unsafe cases are also tested under six labels across nested output roles. These mock results are not measured live-provider accuracy.

## Export and visual evidence

The browser matrix exercises native EN and AR × no entries/five interested/payment/Clear × EN and AR report labels: all 16 Founder downloads. Five interested self-reports alone leave the provisional fixture score at 15/25; a payment selection changes Customer Need under the existing rule to 18/25; Clear restores 15/25. Narrative, assessment status, dimension values, identity and counts agree with the dashboard. Self-reports are explicitly not independently verified evidence.

All 20 reports (118 pages) were rendered with Poppler and inspected as full-page contact sheets, with full-resolution checks of the affected Arabic→English cover and Seven-Day pages. Extracted text contains zero U+25A0/U+FFFD substitutions. Amiri is embedded for retained Arabic in English reports, with English labels and LTR tables preserved. Actual mixed text, numbers and punctuation are visible; extraction alone is not the acceptance test. All page PNGs, all four affected cover/Seven-Day pairs and before/after evidence are in the archive. Poppler emits `Symbol`/`ArialUnicode` fallback warnings; these did not produce substituted body glyphs or visible clipping in the inspected pages. Long tables may continue with repeated headers; the financial disclaimer stays with its table.

The extra independent browser matrix covers 40 native/language/theme/width states at 375/390/768/1440/1920, with zero JavaScript errors. Mobile finance screenshots and language-switch screenshots are included. Existing horizontally scrolling finance tables remain keyboard reachable; no redesign was performed.

## Dependency investigation

The existing environment has these nine deviations; the isolated install of the unchanged pins succeeds and has no runtime-pin deviations. Both environments return `No broken requirements found` from `pip check`. This demonstrates local-environment drift, not a demonstrated packaging defect. No version was automatically changed and no vulnerability is inferred from a mismatch.

| Package | Existing environment | Committed pin / fresh environment |
|---|---|---|
| certifi | 2026.7.22 | 2026.10.23 |
| charset-normalizer | 3.5.1 | 3.5.2 |
| click | 8.5.0 | 8.5.1 |
| MarkupSafe | 3.0.3 | 3.0.4 |
| numpy | 2.5.3 | 2.5.4 |
| pillow | 12.3.0 | 13.0.0 |
| python-dateutil | 2.9.0.post0 | 4.0.0 |
| tzdata | not installed | 2026.6 |
| Werkzeug | 3.1.8 | 3.1.9 |

The isolated environment is `outputs/v225-pinned-env-20261118`, excluded from Git and the archive. All declared dev/runtime entries match there. Installed Node metadata matches the lock for three applicable packages; Darwin-only optional `fsevents` is absent on Windows. All ten bundled assets/fonts match committed binaries/code or license line-ending normalization. There was no fresh npm tarball-integrity or vulnerability audit.

## Changed files and delivery

Runtime: `content_safety.py`, `financial_report.py`, `founder_pdf.py`, `material_claims.py`, `pdf_text.py`, `plan_normalize.py`, `provenance.py`, `publication_policy.py`.

Tests: `test_browser_server.py`, `test_v22.cjs`, `test_v225.py`, `tests/fixtures/v225_publication.json`, `tests/v225_browser.cjs`.

Documentation: `README.md`, `TESTING.md`, `docs/V22_5_REVIEW.md`.

The ZIP contains the complete committed source, full binary-capable patch from V2.2.3, every intermediate commit, inventory, requirements/lock, fixtures, exact logs, PDF matrix, every page render, screenshots, safety/dependency evidence and a checksum manifest with `pushed:false`, `deployed:false`. The ZIP is `outputs/Khotwa_V2.2.5_Claude_review.zip`; its external SHA-256 and verification result accompany it. The final commit hash is recorded in the manifest to avoid a self-referential committed document.

## Remaining limits

Live Groq output quality/availability and generalization beyond the finite fixtures are **NOT VERIFIED**. The deterministic rules are conservative bounded language checks, not a universal semantic verifier or factual attestation system. Classification failure can reduce personalization. Legitimate old receipts with unsafe prose require regeneration; a missing/stale signing key also requires regeneration for authenticated assessment exports.

Linux/Gunicorn, Render deployment/free-tier memory, real phones, Safari/Firefox, screen readers and formal native-speaker linguistic review are **NOT VERIFIED** in this Windows/Chromium run. Large PDF generation still consumes CPU/memory; no new production capacity claim is made. Unknown financial inputs remain unknown. Funding information is not an eligibility/approval guarantee. Independent Claude review remains the next stage; this local patch does not authorize publication or deployment.
