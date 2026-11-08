# V2.2 changed-file inventory

Baseline: `802149433729d58ebb191cb631c242a28dca914d`. This list includes new modules and removed full browser TTFs; the server PDF TTF and licenses are retained. No academic, private or generated output path is included in the commit.

## Backend and calculation modules

- `advisor.py`
- `advisor_history.py`
- `app.py`
- `content_safety.py`
- `finance.py`
- `financial_report.py`
- `founder_pdf.py`
- `groq_client.py`
- `plan_content.py`
- `plan_normalize.py`
- `plan_utils.py`
- `prompts.py`
- `scoring.py`

## Browser code, templates and assets

- `static/app.js`
- `static/bootstrap.js`
- `static/chart-loader.js`
- `static/dashboard-polish.js`
- `static/events.js`
- `static/finance-analysis.js`
- `static/finance-beginner.js`
- `static/fonts/arabic.ttf`
- `static/fonts/arabic.woff2`
- `static/fonts/inter-latin.ttf`
- `static/fonts/inter-latin.woff2`
- `static/funding-directory.js`
- `static/funding-routes.js`
- `static/funding.json`
- `static/investment-details.js`
- `static/investment-workspace.js`
- `static/investment.css`
- `static/investment.js`
- `static/onboarding.js`
- `static/privacy.js`
- `static/proof.js`
- `static/request-status.js`
- `static/scoring.js`
- `static/startsmart.css`
- `static/startsmart.js`
- `static/tokens.css`
- `static/workspace.js`
- `templates/index.html`
- `templates/partials/dashboard.html`
- `templates/partials/investment.html`
- `templates/partials/landing.html`

## Automated tests and fixtures

- `test_api.py`
- `test_browser.cjs`
- `test_browser_server.py`
- `test_deployment.py`
- `test_final_polish.py`
- `test_finance.py`
- `test_groq_transport.py`
- `test_live_regressions.py`
- `test_quality_upgrade.py`
- `test_redesign.cjs`
- `test_routes.py`
- `test_scoring.py`
- `test_support.py`
- `test_test_setup.py`
- `test_v2.cjs`
- `test_v21.cjs`
- `test_v21_finance.py`
- `test_v21_security.py`
- `test_v22.cjs`
- `test_v22_content.py`
- `test_v22_engineering.py`
- `test_v22_security.py`
- `test_v2_backend.py`
- `tests/fixtures/rich_plan_alt_en.json`
- `tests/fixtures/rich_plan_ar.json`
- `tests/fixtures/rich_plan_en.json`
- `tests/fixtures/unsafe_plan_en.json`

## Configuration, scripts and engineering documentation

- `README.md`
- `TESTING.md`
- `docs/FINANCIAL_SPEC.md`
- `docs/FUNDING_SOURCES.md`
- `docs/V22_CHANGED_FILES.md`
- `docs/V22_REVIEW.md`
- `docs/V22_SECURITY.md`
- `package-lock.json`
- `package.json`
- `requirements-dev.txt`
- `requirements.txt`
- `scripts/live_smoke.py`
- `scripts/run_tests.py`

Formatting-only changes accompany the module extraction in existing Python tests, `groq_client.py`, `scoring.py` and `test_api.py`. Behavioral changes to older assertions are listed individually in V22_REVIEW.md. Internal legacy asset filenames remain unchanged. The authoritative add/modify/delete status and line statistics are in the review package patch and changed-files.txt.
