# StartSmart UAE 2.0 — Test Your Idea Before You Spend

StartSmart UAE is a bilingual English/Arabic Flask website for first-time UAE founders. It offers idea discovery, a seven-tab dashboard, Founder Journey, Proof Mode, a Groq Advisor, scoring and charts, and an English/Arabic PDF founder report. Business and regulatory guidance is a starting point; users should verify requirements with the appropriate UAE authority before operating or accepting payment.

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
.\.venv\Scripts\python.exe -m unittest discover -v
node test_browser.cjs
node test_redesign.cjs
```

The browser tests start an isolated Flask server with mocked Groq responses. They require Node.js, the `playwright` package, and Chrome. The Python PDF tests also require `pypdf` as a **test-only** package (`pip install pypdf`). `test_api.py` is a separate **live** Groq connection test; run it only when you intend to make a real API request:

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

The two `git ls-files` / `git log` commands should return no secret files. Inspect any other staged or historical files that might contain credentials or private founder data without printing secrets to public logs. If a real key was ever committed, **rotate it in Groq before publishing** and remove it from repository history. For a new repository, create an empty private or public repository on GitHub, then run:

```powershell
git add .
git status --short
git diff --cached --name-only
git commit -m "Prepare StartSmart UAE for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
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

Render Free currently has 512 MB RAM and limited CPU. It sleeps after 15 minutes without traffic, so the first visit may take about a minute. Its filesystem is ephemeral. PDF generation and matplotlib charts can be slow or memory-intensive under concurrent use; one Gunicorn worker favors memory over parallel throughput. If reports time out or the service runs out of memory, inspect Render logs and use a paid instance or simplify PDF chart generation before a larger public launch. This free setup is suitable for classroom testing, not guaranteed high traffic.

## Public testing checklist

- Open the Render URL on a phone over mobile data and on a desktop; allow for a cold start.
- Check `/health` and that CSS, favicon, fonts, tabs, dark mode, and animations load.
- Test idea discovery, plan generation, all seven tabs, Founder Journey, Proof Mode, scoring, charts, and WhatsApp QR/link.
- Ask the live Groq Advisor a follow-up question; confirm that no raw JSON, Markdown, or HTML appears.
- Export English and Arabic PDFs; check Arabic shaping, chart pages, and download behavior on a phone.
- Confirm Arabic/RTL layout and narrow-screen usability.
- Try one malformed/oversized request and repeated requests; confirm JSON errors, throttling, and no secrets in responses or logs.
- Check Render logs and usage for timeouts, memory pressure, and unexpected Groq request volume.

If Groq is unavailable, plan generation can fall back to local guidance in the browser; idea discovery and live Advisor answers need Groq. The PDF report uses the bundled `fonts/Amiri-Regular.ttf` file under `fonts/OFL.txt` and does not download a font at runtime.
