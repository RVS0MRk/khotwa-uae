# Khotwa correctness checks

## Visual pass

The redesign lives in `static/startsmart.css`, `static/startsmart.js`, and the existing Flask template. Backend routes, Groq requests/prompts, scoring, evidence calculations, PDF logic and deployment configuration were not changed in this pass.

Added a split hero and two product entry cards, a live dashboard summary, a five-stage founder journey, recommendation cards, staged loading, mobile Proof Mode cards, an evidence ladder, financial guardrails, timeline/risk/pitch/resource styling, and a mobile Advisor sheet. The favicon is the local `static/favicon.svg`; no third-party branding or animation libraries were added.

Journey semantics are deliberately conservative: Idea is current before a plan; Validate follows generation; recorded rows select Evidence; viewing Resources selects Prepare as a review focus; recorded payment/repeat behavior selects Decide for review. Only entering the idea receives a completed marker. No licensing, preparation, launch approval or validation is inferred. Clearing Proof Mode restores the appropriate state. Recommendation badges repeat the selected market, rather than asserting unverified skill/budget fit.

Motion uses short CSS entrances and an 800 ms score count-up. Proof counters show exact values immediately with a short visual transition, preserving fractional averages. Reduced motion disables these effects and animated scrolling. The former particle background, confetti, perpetual sheen and launcher pulse are removed from the rendered experience.

Run the original commands below, plus:

```powershell
node test_redesign.cjs
```

This additional suite starts its own mock server on port 5002 and checks journey states, evidence ladder levels, counter precision, score final value, loading, CSV download, Copy feedback, WhatsApp URL construction, keyboard tabs, Advisor focus/Escape/inert state, mobile sheet dimensions, favicon, reduced motion and page overflow. It saves 208 screenshots: every tab, hero, form, discovery, dashboard summary, Advisor and footer across 1366×768, 1440×900, 390×844 and 430×932, in English/Arabic and light/dark mode.

The original browser clearance assertions now measure actual two-dimensional separation between controls and the Advisor launcher. They no longer require the old unused side gutter; controls retain the full mobile content width.

Verification in this pass: all 34 Python tests, the original browser suite (including both PDF exports), and the redesign suite passed. Screenshots were inspected for all requested viewport/language/theme combinations. Test data is mocked, so switching an English fixture into Arabic preserves its existing generated English prose while localizing interface labels; user-entered business names are also preserved.

No real Groq call was made. External font/Chart.js/QR CDNs are blocked in the test environment. Numeric chart fallbacks and the QR link fallback were checked; externally loaded fonts, live charts/QR rendering, physical-phone keyboard/safe areas and production deployment still need manual verification on an unrestricted connection. Backend PDF layout was not redesigned.

## Automated checks

These tests use a dummy API key and mocked Groq responses. They never read the local key or call Groq.

### Final targeted polish checks

`test_final_polish.py` covers step-derived totals/gaps (including zero, decimal, missing and invalid estimates), two different reasoned model score vectors, explicit fallback score sources, execution risks for content/mobile/digital businesses, restaurant customer wording, and PDF totals/26.5 AED precision in both languages. PDF export re-derives costs from submitted steps, so stale totals from an older browser cannot reappear.

The browser suite also checks 23 + 30 → 26.5 and 20 + 40 → 30, unavailable-cost copy/chart state, Arabic category helpers/placeholders/resources, dark mode, Advisor clearance and horizontal tab scrolling with the selected tab visible at 390 px in LTR and RTL. Proof statistics update directly; their previous animated whole-number counter no longer overwrites fractional averages.

Scoring previously preserved valid model values, but the prompt supplied the exact 4/3/5/4/3 = 19 example reported in live testing. The schema now describes the numeric fields without those example values and requires business-specific reasons. Valid generated dimensions remain unchanged; missing/invalid dimensions use 3 with `source: fallback`, a business-specific fallback explanation, and an overall `fallback_or_mixed` source. No scores are randomized. Actual model variation still requires a live check.

The final pass uses the existing Groq configuration unchanged. Run the commands below for the full offline suite; no live request is part of it.

```powershell
cd C:\startsmart-uae-main
$env:PYTHONPATH = "$PWD\.venv\Lib\site-packages"
$env:MPLCONFIGDIR = $env:TEMP
$python = "C:\Users\aminm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python -m py_compile app.py config.py test_routes.py test_browser_server.py
& $python -m unittest discover -v

$env:PYTHON_EXE = $python
$env:NODE_PATH = "C:\Users\aminm\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
node test_browser.cjs
```

The browser test starts an isolated fixture server on port 5001 and closes it afterward. It requires Chrome and Playwright. It prints the temporary directory containing the English/Arabic screenshots and test PDFs.

Coverage:

- Python and JavaScript syntax; `/health`, `/generate`, `/ask`, `/discover`, `/pdf`.
- Unsupported regulatory claims and premature operational tests removed from generated plans.
- Model-generated evidence discarded; preliminary decisions separated from user-entered evidence.
- Costs labelled as estimates; AED 4,000 user budget, AED 5,000 setup estimate, AED 1,000 gap.
- Distinct daily success measures; lawful pilot condition in the seven-step fuller path.
- Exactly three discovery cards and automatic Explore handoff preserving category, region, context, budget, and idea.
- Proof Mode interest, intent, reservations, payment, repeat behavior, and valid numeric price averages.
- Advisor structured rendering, encoded entities, Markdown, malformed JSON fallback, and four final question scenarios.
- English/Arabic RTL at 390 px, safe user text rendering, and malformed generation fallback.
- Plan rendering survives an unavailable external chart library.

## Local application command

Stop the existing Flask process first, then restart it to load backend changes:

```powershell
cd C:\startsmart-uae-main
$env:PYTHONPATH = "$PWD\.venv\Lib\site-packages"
$env:MPLCONFIGDIR = $env:TEMP
& "C:\Users\aminm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
```

Open http://127.0.0.1:5000 and refresh. The existing Render configuration is unchanged.

## Next live scenario

1. Select **I need a business idea**.
2. Enter skills **AutoCAD, communication, basic engineering knowledge**; interests **Cars and technology**; experience **University student**; budget **4000**; market **Abu Dhabi**; type **Local service or digital**; time **10 hours/week**.
3. Confirm three hypothesis cards with fit, customer, non-operational validation test, assumption, and Explore button.
4. Explore a card. Confirm that its idea, budget, region, context, and category remain in the resulting plan.
5. Check the preliminary score, estimates, any budget gap, seven-day measures, Risk Radar, and conditional lawful pilot wording. There must be no invented permit names, free operational washes, or fabricated evidence.
6. In Proof Mode enter prices **20** and **40**, one interest response, one maybe, one no-payment reservation, and one stated intent. Average stated price must be **30**; interest and reservations must not count as sales. Clear the entries and confirm evidence returns to pending.
7. Ask: **What are my biggest risks?**, **Which risk should I test first?**, **How do I find my first 3 customers?**, **What licences or approvals might I need?**
8. Check English and Arabic, then download both PDFs. Verify the evidence/estimate labels and cautious official-resource wording.

## Verification limits

Live Groq was not exercised in this correctness pass. External CDN assets were blocked in the test environment; graceful plan rendering without Chart.js was verified. Real provider output variability, external chart loading, and the deployed Render service still need a live check.

## GPT-OSS transport regression pass

The shared transport in `groq_client.py` uses `reasoning_effort: low` and `include_reasoning: false`. All three app routes retain JSON object mode and parse only final `message.content`. Endpoint budgets are in `config.py`:

| Caller | Previous `max_tokens` | New `max_completion_tokens` |
| --- | ---: | ---: |
| `/ask` | 4000 | 1200 |
| `/discover` | 4000 | 2500 |
| `/generate` | 4000 | 5000 |
| `test_api.py` | 20 | 200 |

The unused non-JSON helper branch previously used 700 tokens. The shared transport no longer uses `max_tokens`.

Empty or length-limited completions fail before final-content JSON parsing. Terminal errors include the endpoint, HTTP status, finish reason, content-empty flag, exception type, a sanitized API error message and available token counts. Neither reasoning nor request headers are logged. Browser error responses remain generic.

`test_groq_transport.py` mocks the HTTP response and exercises request construction, empty/length responses on all routes, valid plan/Advisor/discovery JSON, redacted HTTP errors, invalid final JSON, timeouts and the smoke test's exact-answer requirement. The suite does not contact Groq.

To restart, stop the current Flask process with **Ctrl+C** in its terminal, then run:

```powershell
Set-Location C:\startsmart-uae-main
$env:PYTHONPATH = 'C:\startsmart-uae-main\.venv\Lib\site-packages'
$env:MPLCONFIGDIR = $env:TEMP
& 'C:\Users\aminm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' app.py
```

To run the live connection test, use a separate PowerShell terminal (uses your existing environment key or local `secret.txt`; do not paste the key):

```powershell
Set-Location C:\startsmart-uae-main
$env:PYTHONPATH = 'C:\startsmart-uae-main\.venv\Lib\site-packages'
& 'C:\Users\aminm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' test_api.py
```

Success requires HTTP 200 and final content exactly `Groq connection works` after trimming whitespace. Failure exits with a nonzero status and safe diagnostics. This live command was not run during the regression pass.

## Live-report regression pass (26 September 2026)

- `test_live_regressions.py` adds six checks (requires the test-only `pypdf` package).
- The exact reported Markdown/entity fixture is shared with the browser fixture server. The Python test mocks the provider HTTP response, exercising the real `call_groq` JSON-mode request, parsing and `/ask` serialization. The browser test verifies the final visible text, including no repeated action/caution labels.
- Every successful `/ask` response now passes a recursive final plain-text cleanup, carries `X-StartSmart-Advisor: structured-v2`, and disables caching. The HTML page also disables caching. After restarting Flask, this header distinguishes the updated backend from an older running process.
- The current parser already cleaned the exact reported fixture before this pass. The original live failure could not be reproduced: port 5000 refused connections during inspection, so its served frontend/backend version could not be checked. A stale process/template remains a possibility, not an established root cause.
- PDF text is normalized before rendering: non-breaking hyphens and other Unicode dashes become ASCII `-`; curly quotes, non-breaking spaces and unsupported check/cross markers become portable text. The fixture includes `Car‑Interior`, `ride‑hailing`, and `face‑to‑face`; extracted English and Arabic PDF text must contain no black-square/replacement character.
- Arabic export from an English plan uses shared Arabic defaults for status, seven-day actions/success measures, questions, test plan, risk table, readiness actions and fuller-path actions. Business names, evidence entries and estimates are preserved. Arabic lines wrap in logical order before shaping; chart text avoids double bidi processing in newer Matplotlib. The risk table mirrors its column widths correctly.
- Business-context segment fallbacks and preservation of specific AI segment names are covered, along with cautious “Potential benefit” copy.
- Browser-generated English and Arabic sample PDFs each have seven pages. Inspect every rendered page after PDF layout changes; the browser runner prints their temporary directory.
