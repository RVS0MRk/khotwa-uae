# Testing Khotwa V2.2.3

Use Python 3.12 and Node.js 20 or newer. Run commands from the repository root. The application has no frontend build step.

## Setup

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
$env:PYTHON_EXE = (Resolve-Path .\.venv\Scripts\python.exe).Path
Remove-Item Env:GROQ_API_KEY -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts/run_tests.py
```

Linux/macOS:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm ci
npx playwright install --with-deps chromium
unset GROQ_API_KEY
.venv/bin/python -m unittest discover -v
.venv/bin/python scripts/run_tests.py
```

The consolidated runner uses its own Python interpreter for each fixture server and runs Python discovery followed by all five browser suites. It stops on failure. `--python-only` omits browsers. Every browser suite launches Playwright-managed Chromium; a system Chrome installation is neither needed nor selected. Missing browsers produce Playwright's install diagnostic. Tests do not attach to the running production or development website.

## Organization and environment

- `test_support.py`: mock-only bootstrap. It installs a synthetic key before application import and repairs already-imported config/application values. Tests do not rely on import order or local credentials. It is not imported by production or the live smoke script.
- `test_test_setup.py`: starts a fresh interpreter with the key unset, pre-imports empty config and forbids `secret.txt` reads before loading the application through the mock bootstrap.
- Standard discovery covers routes, provider transport, scoring, security, deployment boundaries and financial/PDF behavior.
- `test_finance.py` retains the 18 V2 financial examples. `test_v21_finance.py` adds low-volume sensitivity, cash modes, COGS, licensing, payback, scenarios, formatting and 3,000 reproducible independent arithmetic cases (seed 2107).
- `test_v21_security.py` checks HSTS/CSP and models two independent worker rate-limit stores to expose the documented per-process limitation.
- `test_browser.cjs`: discovery, four business journeys, Proof Mode/Clear/reload/isolation, sharing, Advisor, safe rendering, bilingual cache and both PDF languages.
- `test_redesign.cjs`: keyboard, evidence ladder, loading, motion and a 9-width x 2-language x 2-theme screenshot matrix, including eight dashboard tabs.
- `test_v2.cjs`: financial workflows, scenario edits/reset, staged allocations, readiness, recovery, funding filters, CSV/PDF failure and vendor fallback.
- `test_v21.cjs`: seven financial subpanels, discrete cases, simplified mode, individual scenario reset, semantic status localization, recovered subpanel, five widths in both languages, minimum fonts, token contrast, clipping, focus, labels and chart tables.

`GROQ_API_KEY` may be absent for every mock suite. Browser fixture servers set their synthetic value through `test_support`; `TEST_PORT` selects their isolated local port. `PYTHON_EXE` is optional for direct browser commands and points at the project's interpreter when `python` on PATH is different. The runner sets it automatically. `NODE_PATH` is unnecessary after normal `npm ci`. In V2.2 this workstation ran a real clean `npm ci` with the locked Playwright/axe packages, using an integrity-verified npm CLI with its bundled Node 24.22.1. Production has no npm/build requirement.

Run suites individually:

```sh
python -m unittest test_finance test_v21_finance test_v21_security -v
node test_browser.cjs
node test_redesign.cjs
node test_v2.cjs
node test_v21.cjs
node test_v22.cjs
```

V2.2.1 adds `test_v221_safety.py` and the table in
`tests/fixtures/v221_safety.json`. These check English/Arabic assertions,
negations, conditions, goals, every raw model string field, Advisor/discovery,
and both PDF boundaries. The original personalization and financial assertions
remain. Run the safety checks independently with:

```sh
python -m unittest test_v221_safety -v
```

`test_v22.cjs` also runs `tests/v221_browser.cjs`: Arabic category suggestions,
manual selection, missing versus zero price, all six layout corrections and
full-motion frame sampling during theme changes. The axe helper activates the
audited page, emulates reduced motion, verifies transitions are disabled, and
waits for fonts, the theme-switch marker and finite animations to settle using
a bounded rendering-state check. Theme frames are tested separately with
reduced motion explicitly off. No arbitrary accessibility sleep is used.

For the three consecutive release runs, set `KHOTWA_REVIEW_DIR` to a separate
ignored directory each time (otherwise captures are overwritten):

```powershell
$env:PYTHON_EXE = (Resolve-Path .\.venv\Scripts\python.exe).Path
Remove-Item Env:GROQ_API_KEY -ErrorAction SilentlyContinue
1..3 | ForEach-Object {
    $env:KHOTWA_REVIEW_DIR = "outputs/v221-review/windows-$_"
    node test_v22.cjs
    if ($LASTEXITCODE -ne 0) { throw "Browser run $_ failed" }
}
```

```sh
export PYTHON_EXE="$PWD/.venv/bin/python"
unset GROQ_API_KEY
for run in 1 2 3; do
  KHOTWA_REVIEW_DIR="outputs/v221-review/linux-$run" node test_v22.cjs || exit 1
done
```

The review records actual OS/browser versions and per-run results. A portable
test implementation does not establish a Linux result: Linux/Chromium 153
must be run on an available Linux host or CI before claiming that verification.

V2/V2.1 artifacts are ignored under `outputs/`. The older browser suites print their temporary screenshot directories. No customer data is used. The one intentional HTTP 500 in `test_browser.cjs` is its malformed-provider fixture, not a suite failure. Diagnostic ERROR logs in Python similarly exercise failures intentionally.

## Live integration and deployment

V2.2.3 adds `test_v223.py` and `tests/v223_browser.cjs`. The new checks retain all
existing tests and verify fixed AI/provenance notes on browser outputs and page 1
of both PDFs in both languages, executive-summary assumption labels, the two
precision cases in all five plan fields and Advisor/PDF output, and possessive
Arabic normalization. `tests/fixtures/v223_pattern_lock.json` locks all nine
existing compiled detector patterns to the V2.2.2 baseline: vocabulary was not
expanded. The V2.2.2 held-out fixture and its lock remain unchanged.

```sh
python -m unittest test_v223 -v
python scripts/evaluate_v222_safety.py
```

The notices are application-owned, not filtered model fields. They explicitly
say Proof Mode observations are self-reported and not independently verified;
recording an entry does not automatically confirm a business outcome. The
Advisor note is keyboard-scrollable to preserve room for the conversation.
The V2.2 browser suite automatically includes 24 additional disclosure states.

V2.2.2 adds `test_v222_safety.py`, the unchanged V2.2.1 test file with its expanded
fixture, and the separate pre-authored `tests/fixtures/v222_heldout.json`.
The held-out acceptance test requires at least 90% removal of fabricated
outcomes and 100% survival of safe sentences. It does not assert that every
held-out unsafe case passes. See `docs/V22_2_REVIEW.md` for the actual miss.
The fixture's SHA-256 is checked with LF-normalized text so fresh LF/CRLF
checkouts use the same immutable-content comparison.

```sh
python -m unittest test_v221_safety test_v222_safety test_v222_heldout -v
python scripts/evaluate_v222_safety.py
python scripts/evaluate_v222_safety.py --fixture tests/fixtures/v221_safety.json
```

The evaluator imports only the local filter: it reads no key, imports no Flask
configuration and calls no provider. Its JSON includes each result and source
hashes. `test_v22.cjs` now retains all prior checks and adds footer geometry,
eight footer captures and Arabic tourism/education precedence checks. Use the
three-run commands above with separate `KHOTWA_REVIEW_DIR` directories.

`test_api.py` is an explicit live Groq connection check, not a unittest test case. Run `python test_api.py` only with an intentionally configured environment key. It consumes a real request. Mock suite success does not establish model fluency, real response latency, Render resource usage or real phone behavior. Do not use `secret.txt` to run automated checks.

Production uses `gunicorn -c gunicorn.conf.py app:app`, one worker and two threads. Windows test servers are local fixtures, not Gunicorn/Render validation. See `docs/V21_SECURITY.md` for rate limits and HTTPS-edge assumptions.

## Formatting and syntax

First-party JS and CSS were formatted with Prettier 3.6.2. For later edits:

```sh
npx prettier@3.6.2 --write "static/*.js" "static/*.css" test_v2.cjs test_v21.cjs
node --check static/app.js
python -m pip check
```

Do not reformat vendored minified libraries. Browser geometry and contrast measurements supplement screenshots; they are not a formal accessibility certification or a substitute for screen-reader and real-device testing. Exact executed results and logs for this round are in `docs/V21_REVIEW.md` and the review ZIP.

## V2.2 checks and artifacts

`test_v22_content.py` measures safe-string retention (>=75%), distinct rich plans, sentence-level safety, structural repairs, grammar/word limits and discovery per-idea content. It also checks that personalized Advisor sentences survive next to rejected claims. `test_v22_security.py` covers separate quota windows, configurable defaults and HMAC history/session boundaries. `test_v22_engineering.py` checks 200 Python/Node score objects, assets/digits/cache, the untouched escaped persona sink, funding metadata, all founder chart images and the owner-only script using mocked transport.

`test_v21_finance.py` retains 3,000 independent arithmetic cases and adds 20,000 seeded display-consistency cases (seed 2208), rounded-contingency propagation, zero-contribution/zero-fixed-cost break-even, partial stage allocations and honest missing startup inputs.

`test_v22.cjs` uses complete rich EN/AR fixtures, two business ideas and mocked Groq only. It checks onboarding/back/categories/optional discovery, content, phone Proof/CSV, four-number finance and missing startup outputs, detected readiness, notes recovery/Clear/New idea, tab isolation and localized throttling. It writes the requested five-width EN/AR light screenshots and desktop/mobile dark Overview/Investment screenshots to `outputs/v22-review/v22`. Its axe-core matrix is landing + eight tabs + seven investment panels, EN/AR, light/dark, 390/1440 (128 states), with zero serious/critical required. It records header/page heights and cold transfer bytes in JSON. Capture paths and exact results belong to this machine; no field performance/accessibility certification is implied.

For dependency/syntax checks:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
Get-ChildItem static -Filter *.js | ForEach-Object { node --check $_.FullName }
```

### Owner-only live investigation — never CI

```powershell
# Set GROQ_API_KEY privately in this shell first; do not paste it into logs.
.\.venv\Scripts\python.exe scripts/live_smoke.py --confirm-live
```

Without both the flag and an environment key, this exits before making a request. With them it makes exactly two requests, one EN and one AR, with the existing JSON schema and 5,000-token generation budget; it never reads secret.txt. Output contains only language, latency, final-content token diagnostics and the ratio of cleaned model strings retained by normalization. That ratio includes unsafe/model-structural strings in its denominator, so a low live ratio requires investigation rather than weakening safety. Provider errors are reported by type/diagnostics, never raw model text, reasoning or keys. The unittest exercises this script with mock responses; **the real opt-in command was not run for V2.2**.

Four rich PDFs and all rendered page PNGs are in the review package. Rendering used Poppler and visual inspection; Python also verifies founder score/timeline/cost images exist. No real customer data or academic report is included in test artifacts.
