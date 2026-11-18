# Khotwa (خطوة) — From idea to first step.

Khotwa is a bilingual English/Arabic Flask website for first-time UAE founders. V2.2 connects idea discovery, the original seven dashboard sections plus an Investment Guide, Founder Journey, Proof Mode, the Groq Advisor, transparent scoring, financial scenarios, and English/Arabic PDF and CSV exports. Business and regulatory guidance is a starting point; users should verify requirements with the appropriate UAE authority before operating or accepting payment.

Generated plans request English and Arabic wording in the **same** Groq JSON response. The browser keeps both versions for language switching, so switching languages does not call Groq again or reset Proof Mode. If translated fields are missing or invalid, Khotwa uses cautious localized guidance and marks that plan with `_localization_status: fallback`. The business name, selected market, budget, score and recorded evidence remain tied to the same plan. Arabic prose quality still depends on the live model response and should be reviewed in the deployed site.

## Requirements and local run

- Python **3.12** (`.python-version` selects the 3.12 series on Render).
- A Groq API key for live idea discovery, plan generation, and Advisor answers.
- A current browser. Charts, QR generation and fonts are bundled locally; text/link alternatives remain available if scripts cannot load.

On Windows, from the project folder:

```powershell
cd C:\startsmart-uae-main
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:GROQ_API_KEY = 'your-key-here'
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000/`. The `app.py` command is for local development only. A local `secret.txt` fallback is supported for existing setups, but that file must stay private. On Render, only the `GROQ_API_KEY` environment variable is used. Never put the key in source code, a GitHub secret file, the README, or a screenshot.

## Offline checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
.\.venv\Scripts\python.exe scripts/run_tests.py
```

The single runner executes all Python tests and all five browser suites. For Python only, add `--python-only`. Run financial tests alone with `.\.venv\Scripts\python.exe -m unittest test_finance -v`. Node.js LTS and npm are development tools; Render does not need them because browser assets are self-hosted.

The browser tests start an isolated Flask server with mocked Groq responses. They require Node.js, the `playwright` package, and Playwright-managed Chromium. A system Chrome installation is no longer required. Install Python test dependencies with `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`; `pypdf` is test-only and is not installed by Render. `test_api.py` is a separate **live** Groq connection test; run it only when you intend to make a real API request:

```powershell
.\.venv\Scripts\python.exe test_api.py
```

## Before uploading to a public GitHub repository

The project ignores `secret.txt`, `.env*`, virtual environments, caches, logs, generated PDFs/CSVs, and local output folders. **Check the staged files and all existing history yourself before pushing.** Git ignore rules do not remove files that were already committed. If this folder does not yet contain `.git`, run `git init` first; there is then no prior local Git history to inspect.

```powershell
cd C:\startsmart-uae-main
git status --short
git check-ignore -v secret.txt .env
git ls-files -- secret.txt .env
git log --all --name-only --format= -- secret.txt .env
```

The two `git ls-files` / `git log` commands should return no secret files. Inspect any other staged or historical files that might contain credentials or private founder data without printing secrets to public logs. If a real key was ever committed, **rotate it in Groq before publishing** and remove it from repository history. The existing repository is [RVS0MRk/khotwa-uae](https://github.com/RVS0MRk/khotwa-uae). After reviewing a future change, the commands are:

```powershell
git add .
git status --short
git diff --cached --name-only
git commit -m "Update Khotwa"
git push origin main
```

Review `git status --short` and `git diff --cached --name-only` **before** the commit and push. No GitHub upload or deployment is performed by this project setup.

## Deploy on Render Free

1. Sign in to Render, select **New > Web Service**, and connect the GitHub repository. Choose the `main` branch and the repository root as the root directory.
2. Select the **Python** runtime and **Free** instance type. `.python-version` requests Python 3.12.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Set **Start Command** to `gunicorn -c gunicorn.conf.py app:app`.
5. In Render's environment settings, add `GROQ_API_KEY` as a secret environment variable. Do not upload `secret.txt` or `.env`. Render supplies `PORT` and `RENDER`; do not set `FLASK_DEBUG=1`.
6. Set **Health Check Path** to `/health`, deploy, and wait for the service URL. `/health` returns `{"status":"ok"}` without calling Groq.

Gunicorn binds to `0.0.0.0:$PORT` with one worker, two threads, and a 70-second worker timeout. This lets health checks respond while another thread waits for Groq. Only one PDF is built at a time; a concurrent PDF request receives a JSON `503` response. The app sets a 256 KiB JSON request limit, short input limits, PDF collection limits, and an in-memory public request window on Render (configurable independent AI and PDF quotas; see Demo day below). The limit resets on restart and is basic cost protection, not a dedicated abuse service. The Groq HTTP timeout is 40 seconds; the browser gives live requests 45 seconds and PDF export 65 seconds.

Proof Mode values are kept in the current tab with `sessionStorage` for refresh recovery. Closing normally ends storage, but browsers may restore sessions; use New idea to intentionally clear the previous business. Free-text frequency and concern notes, Advisor chat, and API keys are excluded from recovery. Clear removes recorded rows; New Idea resets the previous business. Customer entries are user-reported and are not independently verified. PDF pagination follows content length and includes recorded Proof Mode values only when provided. User budget is labelled **USER INPUT**; model costs and prices are estimates or hypotheses.

Render Free currently has 512 MB RAM and limited CPU. It sleeps after 15 minutes without traffic, so the first visit may take about a minute. Its filesystem is ephemeral. PDF generation and matplotlib charts can be slow or memory-intensive under concurrent use; one Gunicorn worker favors memory over parallel throughput. If reports time out or the service runs out of memory, inspect Render logs and use a paid instance or simplify PDF chart generation before a larger public launch. This free setup is suitable for classroom testing, not guaranteed high traffic. See [Render's Free service limits](https://render.com/docs/free), [Python version settings](https://render.com/docs/python-version), and [Flask deployment guide](https://render.com/docs/deploy-flask).

## Public testing checklist

- Open the Render URL on a phone over mobile data and on a desktop; allow for a cold start.
- Check `/health` and that CSS, favicon, fonts, tabs, dark mode, and animations load.
- Test idea discovery, plan generation, all seven tabs, Founder Journey, Proof Mode, scoring, charts, and WhatsApp QR/link.
- Ask the live Groq Advisor a follow-up question; confirm that no raw JSON, Markdown, or HTML appears.
- Switch a generated dashboard to Arabic and back without generating again; check Arabic prose in every tab and that scores and Proof Mode values remain the same.
- Export English and Arabic PDFs; check Arabic shaping, all pages, Proof Mode values, chart pages, and download behavior on a phone.
- Confirm Arabic/RTL layout and narrow-screen usability.
- Try one malformed/oversized request and repeated requests; confirm JSON errors, throttling, and no secrets in responses or logs.
- Check Render logs and usage for timeouts, memory pressure, and unexpected Groq request volume.

If Groq is unavailable, plan generation can fall back to local guidance in the browser; idea discovery and live Advisor answers need Groq. The PDF report uses the bundled `fonts/Amiri-Regular.ttf` file under `fonts/OFL.txt` and does not download a font at runtime.

## V2.1 scoring and Investment Guide

Missing score dimensions receive **no points**, not the previous 3/5 fallback. A complete total out of 25 is shown only when all five dimensions have supported assessments. Otherwise the UI and PDF show **Incomplete**, assessed coverage, and the known subtotal in the data contract. AI judgments are provisional. Five or more recorded Proof Mode entries can update Customer Need under the existing evidence rule; these entries are user-reported and not independently verified. Legacy fallback scores are invalidated on recovery.

The Investment Guide uses `finance.py`, a pure Decimal module, through `POST /finance`. JSON money inputs and outputs use decimal strings. Blank/null is unknown, while an explicit 0 is zero. Monetary inputs and reported outputs round to fils with ROUND_HALF_UP; internal arithmetic uses Decimal, ratios use four decimals and whole break-even units round upward. All calculations are independent of Groq. The financial specification and checked example are in [FINANCIAL_SPEC.md](docs/FINANCIAL_SPEC.md).

The compact Investment Guide has seven keyboard-accessible subpanels, opening at Financial Overview. Default illustrative scenarios vary whole sales units by -20%/+20%, with a minimum one-unit move where possible; they are editable assumptions, not demand forecasts. Sensitivity targets +/-10% but displays actual baseline/comparison/percentage changes for discrete units, ranked by absolute profit effect. Each scenario resets independently. Six stage budgets, self-reported readiness and task progress recover in the same tab, including the selected financial subpanel.

New browser businesses default to the labelled simplified same-month revenue/operating-cost assumption. Saved records retain their selected mode; the raw API defaults to separate receipts/payments for compatibility. Advanced exposes separate cash timing and COGS; its basis is labelled and it never becomes actual evidence. Simple payback uses initial spending divided by positive net cash benefit. Licensing is a separate optional cost, counted once; old records keep their known subtotal with a missing-licensing warning. COGS has an explicit accounting basis. The financial specification documents formulas, unknowns, rounding and limits.

The three optional investor notes recover in this browser tab; avoid confidential information. Clear and New idea erase them. Respondent free-text notes and Advisor chat are excluded from recovery. A different business or New Idea resets investment state. Clear resets saved validation evidence while retaining the current business's financial assumptions. Export/error statuses re-render on language changes. Both languages use grouped Latin currency values with two decimal fils and the AED code; RTL currency runs are isolated to preserve minus signs.

The financial results feed Overview, Risks, Plan, Pitch and Advisor context. Founder PDFs include the optional financial summary when assumptions have been calculated; the separate investment PDF recomputes all figures. Neither PDF trusts submitted numerical results. CSVs use UTF-8 and guard against spreadsheet formula injection.

The funding directory is stored in `static/funding.json` with official sources, eligibility caveats and review dates. It separates financing from mentorship and other support. Khalifa Fund official pages conflict on some detailed eligibility rules; confirm the chosen programme through TAMM. Sheraa's published calendar is dated; current intake is not verified. Hi2's dated 2026 intake is closed; a future intake is not assumed. RUWAD has dated official references, while current terms/intake and the Ministry page's contents were not independently confirmed this round. See [funding-source checks](docs/FUNDING_SOURCES.md). Recheck directory information before a presentation or release.

### Frontend and security

`templates/index.html` composes landing, onboarding, dashboard, investment, Advisor and footer partials. `tokens.css` defines the palette and typography; `startsmart.css` and `investment.css` own component styles. Static scripts separate translations, scoring, existing application behavior, investment behavior, workspace integration, event binding and startup. No frontend build step is needed. Fonts, pinned Chart.js 4.5.1 and QRCode.js 1.0.0 are served locally with licenses. Charts have readable data alternatives; calculations, navigation and exports do not depend on a CDN.

CSP allows scripts only from this origin. Static and dynamic controls use JavaScript event listeners rather than inline event attributes. Other headers protect against framing, MIME sniffing and unnecessary device permissions. JSON size limits apply to the new routes. The single-worker in-memory limiter remains basic cost protection; it is not shared across multiple workers or service instances. Cheap `/finance` recalculation is excluded from the costly Groq/PDF quota so editing a form does not exhaust it. PDF builds remain serialized. No analytics, database or third-party persistence was added.

See [V21_REVIEW.md](docs/V21_REVIEW.md) for this round’s baseline, ticket/finding matrix, test evidence and limitations; [V21_SECURITY.md](docs/V21_SECURITY.md) records the rendering, CSP, HSTS and worker review. [V2_REVIEW.md](docs/V2_REVIEW.md) retains the prior audit. Live Groq quality, Linux Gunicorn startup, real-phone readers and Render memory behavior still require a controlled release smoke test. This implementation does not deploy itself.

## V2.2 correction round and demo day

Personalized safe AI prose is preserved field by field; unsupported evidence/fees/operating advice is removed sentence by sentence. Missing descriptions stay missing. Both entry journeys are focused steps with Back. Phone Proof Mode uses response cards, and the Investment Guide opens with a four-number starter. Those four operating assumptions support revenue, profit and break-even; **runway/payback still require startup spending/reserves** and remain unknown until enough inputs exist. New users are never assigned invented zero startup costs.

Configure these optional Render environment variables deliberately, based on your provider budget and classroom/public traffic:

| Variable | Default per 10 minutes |
|---|---:|
| `KHOTWA_AI_GLOBAL_PER_10MIN` | 400 across this process |
| `KHOTWA_AI_CLIENT_PER_10MIN` | 30 AI calls per client |
| `KHOTWA_PDF_CLIENT_PER_10MIN` | 20 PDF exports per client, separately |

Higher limits are not automatically safe for production or Groq costs. Restarts reset counters; additional workers multiply process-local allowances. `/finance` does not consume these quotas. Keep one Gunicorn worker unless a shared limiter is added. Bilingual wait messages display the remaining retry time. [V22_SECURITY.md](docs/V22_SECURITY.md) records privacy/data flow, anonymous Advisor signatures, quota boundaries, caching and release limits.

The owner-only `python scripts/live_smoke.py --confirm-live` requires an explicitly set environment key and makes exactly two billable requests (EN/AR). It reports latency, token diagnostics and content retention without printing plans or secrets. It is not part of automated tests. Mock success does not establish live-model quality or public deployment capacity. [TESTING.md](TESTING.md) covers commands; [V22_REVIEW.md](docs/V22_REVIEW.md) records this round's exact evidence. No deployment is part of this correction round.

## V2.2.4 reliability corrections

AI routes now apply a bounded independent content check and source-aware publication rules. Proof observations remain self-reported; financial projections are not actual revenue, and funding listings are not approvals. Verification failure uses conservative planning templates. Each route may consume two provider requests; both count toward the existing production allowances. No limits were raised and no automatic retry loop was added.

Exports authenticate published model/application text and the original provisional assessment. Version 3 receipts bind the baseline score to its canonical business identity. Founder PDFs derive the current Customer Need score and evidence narrative from bounded, self-reported Proof counts using the same dashboard rule. Posted score totals, explanations and browser backups cannot authenticate an assessment. Proof observations remain unverified self-reports.

Configure the optional private `KHOTWA_CONTENT_SIGNING_KEY` environment variable with a random value of at least 32 bytes to keep receipts valid across restarts; never put its value in Git. Without it, a random process key is used. Old, unsigned or edited narrative is omitted from exports, while user inputs and recalculated financial data remain. Version 2 receipts can authenticate original prose but did not sign numeric assessments; regenerate an older plan to obtain a complete authenticated score export. A restart/key change also requires regeneration when it invalidates the receipt.

Language switching preserves one canonical assessment and original personalized content when translation is missing, with a visible notice. Robotics category suggestions and visible quick-finance validation are corrected. See [V22_4_REVIEW.md](docs/V22_4_REVIEW.md) for the seven-ticket matrix, test evidence, data contract and remaining safety limitations. V2.2.4 live Groq quality is **NOT VERIFIED**; the explicitly opt-in `python scripts/live_v224.py --confirm-live` procedure is bounded to 40 provider attempts and stops on failure. It is separate from all mock tests.

The final consistency correction is documented in [V224_CONSISTENCY_REVIEW.md](docs/V224_CONSISTENCY_REVIEW.md), including the Proof/dashboard/Founder PDF contract, native Arabic finance controls, exact test results and remaining limitations.

## V2.2.5 corrections

Founder and Investment PDFs share logical line wrapping, Arabic shaping and mixed-script font runs. English report layout can retain readable Arabic business content when translation is unavailable. Repeated catch-all translations cannot replace distinct personalized source fields. Financial explanations stay with their results table.

Publication checks now apply deterministic clause-level rules independently of the semantic classifier's label. Local denials and conditional research remain useful planning content; a model label cannot authenticate achieved business outcomes. Version 3 receipts sign the publication-policy version as well as the original assessment. Earlier valid receipts still verify cryptographically, but their text is rechecked under the current publication policy before export. User assumptions, calculated projections and self-reported Proof counts retain their separate source paths; none becomes independent external evidence.

See [V22_5_REVIEW.md](docs/V22_5_REVIEW.md) for the six-ticket implementation, exact verification and limits. These bounded, mock-tested checks are not a guarantee of live-model factual accuracy. Production quotas, financial formulas and deployment settings are unchanged.
