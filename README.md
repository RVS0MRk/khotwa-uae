# Khotwa (خطوة) — From idea to first step.

Khotwa is a bilingual English/Arabic Flask website for first-time UAE founders. V2 connects idea discovery, the original seven dashboard sections plus an Investment Guide, Founder Journey, Proof Mode, the Groq Advisor, transparent scoring, financial scenarios, and English/Arabic PDF and CSV exports. Business and regulatory guidance is a starting point; users should verify requirements with the appropriate UAE authority before operating or accepting payment.

Generated plans request English and Arabic wording in the **same** Groq JSON response. The browser keeps both versions for language switching, so switching languages does not call Groq again or reset Proof Mode. If translated fields are missing or invalid, Khotwa uses cautious localized guidance and marks that plan with `_localization_status: fallback`. The business name, selected market, budget, score and recorded evidence remain tied to the same plan. Arabic prose quality still depends on the live model response and should be reviewed in the deployed site.

## Requirements and local run

- Python **3.12** (`.python-version` selects the 3.12 series on Render).
- A Groq API key for live idea discovery, plan generation, and Advisor answers.
- A current browser. Charts and QR generation use external CDN scripts; the page provides text/link fallbacks if those scripts are unavailable.

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

The single runner executes all Python tests and all three browser suites. For Python only, add `--python-only`. Run financial tests alone with `.\.venv\Scripts\python.exe -m unittest test_finance -v`. Node.js LTS and npm are development tools; Render does not need them because browser assets are self-hosted.

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

Gunicorn binds to `0.0.0.0:$PORT` with one worker, two threads, and a 70-second worker timeout. This lets health checks respond while another thread waits for Groq. Only one PDF is built at a time; a concurrent PDF request receives a JSON `503` response. The app sets a 256 KiB JSON request limit, short input limits, PDF collection limits, and an in-memory public request window on Render (30 costly requests per client and 150 total per 10 minutes). The limit resets on restart and is basic cost protection, not a dedicated abuse service. The Groq HTTP timeout is 40 seconds; the browser gives live requests 45 seconds and PDF export 65 seconds.

Proof Mode values are kept in the current tab with `sessionStorage` for refresh recovery. Free-text frequency and concern notes, Advisor chat, and API keys are excluded from recovery. Clear removes recorded rows; New Idea resets the previous business. Customer entries are user-reported and are not independently verified. PDF pagination follows content length and includes recorded Proof Mode values only when provided. User budget is labelled **USER INPUT**; model costs and prices are estimates or hypotheses.

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

## V2 scoring and Investment Guide

Missing score dimensions receive **no points**, not the previous 3/5 fallback. A complete total out of 25 is shown only when all five dimensions have supported assessments. Otherwise the UI and PDF show **Incomplete**, assessed coverage, and the known subtotal in the data contract. AI judgments are provisional. Five or more recorded Proof Mode entries can update Customer Need under the existing evidence rule; these entries are user-reported and not independently verified. Legacy fallback scores are invalidated on recovery.

The Investment Guide uses `finance.py`, a pure Decimal module, through `POST /finance`. JSON money inputs and outputs use decimal strings. Blank/null is unknown, while an explicit 0 is zero. Monetary inputs and reported outputs round to fils with ROUND_HALF_UP; internal arithmetic uses Decimal, ratios use four decimals and whole break-even units round upward. All calculations are independent of Groq. The financial specification and checked example are in [FINANCIAL_SPEC.md](docs/FINANCIAL_SPEC.md).

The three scenarios begin with the same entered assumptions; labels do not invent pessimistic or optimistic sales forecasts. Copy current assumptions, edit each scenario independently, and reset to the first explicitly calculated assumptions. Sensitivity changes one input at a time by ±10%. Six stage budgets, self-reported completion, readiness checks and seven-day task progress recover in the current tab. Financial notes for the investor brief remain in memory only. A different business or New Idea resets its investment state. Clear resets customer evidence while retaining the current business's financial assumptions.

The financial results feed Overview, Risks, Plan, Pitch and Advisor context. Founder PDFs include the optional financial summary when assumptions have been calculated; the separate investment PDF recomputes all figures. Neither PDF trusts submitted numerical results. CSVs use UTF-8 and guard against spreadsheet formula injection.

The funding directory is stored in `static/funding.json` with official sources, eligibility caveats and review dates. It separates financing from mentorship and other support. Khalifa Fund official pages conflict on some detailed eligibility rules; confirm the chosen programme through TAMM. Sheraa's reviewed calendar and RUWAD's guide are dated; current intakes and financial terms are not asserted. Recheck directory information before a presentation or release.

### Frontend and security

`templates/index.html` composes landing, onboarding, dashboard, investment, Advisor and footer partials. `tokens.css` defines the palette and typography; `startsmart.css` and `investment.css` own component styles. Static scripts separate translations, scoring, existing application behavior, investment behavior, workspace integration, event binding and startup. No frontend build step is needed. Fonts, pinned Chart.js 4.5.1 and QRCode.js 1.0.0 are served locally with licenses. Charts have readable data alternatives; calculations, navigation and exports do not depend on a CDN.

CSP allows scripts only from this origin. Static and dynamic controls use JavaScript event listeners rather than inline event attributes. Other headers protect against framing, MIME sniffing and unnecessary device permissions. JSON size limits apply to the new routes. The single-worker in-memory limiter remains basic cost protection; it is not shared across multiple workers or service instances. Cheap `/finance` recalculation is excluded from the costly Groq/PDF quota so editing a form does not exhaust it. PDF builds remain serialized. No analytics, database or third-party persistence was added.

See [V2_REVIEW.md](docs/V2_REVIEW.md) for baseline, ticket coverage, evidence paths, security review and known limitations. Live Groq quality, Linux Gunicorn startup, real-phone readers and Render memory behavior still require a controlled release smoke test. This implementation does not deploy itself.
