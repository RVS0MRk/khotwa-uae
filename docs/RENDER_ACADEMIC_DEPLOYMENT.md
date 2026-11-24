# Academic final: protected public Render deployment

The frozen academic release is `24eaa98b5c114168b1b8efda5644047e72033e46`,
branch `codex/khotwa-final-academic-20261124`, tag
`khotwa-academic-final-20261124`. Deployment changes belong to the separate
`codex/khotwa-academic-render-20261124` branch. Do not rewrite the frozen release.

## Existing service

- Public URL: https://khotwa-uae.onrender.com/
- Render service: `srv-dbgk2l6i0phs73al1hqg`, Python, Oregon, **Free**.
- Build: `pip install -r requirements-render.txt`
- Start: `gunicorn -c gunicorn.conf.py render_service:app`
- Health check: `/health`
- Root directory: empty (repository root).
- Auto deploy: off; deploy a reviewed commit manually.
- One worker, two threads, 70-second worker timeout. The config binds
  `0.0.0.0:$PORT` (Render supplies PORT; default 10000).
- `/health` reports the academic commit, actual `RENDER_GIT_COMMIT`, Python,
  Linux platform, and the two explicit AI modes. No debug mode.

## Environment (Render dashboard only; never Git)

- Preserve the existing `GROQ_API_KEY` without revealing or copying it.
- `KHOTWA_CONTENT_SIGNING_KEY`: independently generated, random, stable, at
  least 32 characters. Required at startup. Replacing it invalidates old export
  receipts and private sessions; keep it stable across redeployments.
- `KHOTWA_LIVE_ACCESS_TOKEN`: a separate random value of at least 32 characters.
  Only the owner should have it. Do not publish it, put it in a URL, or enter the
  Groq API key in the live-login form. Rotating this value invalidates sessions.
- `PYTHON_VERSION=3.12.10` (matches the tested Windows Python environment).
- `KHOTWA_LIVE_PROVIDER_CALLS_PER_10MIN=24`
- `KHOTWA_LIVE_PROVIDER_CALLS_PER_DAY=120`
- Render supplies `RENDER=true`, `RENDER_EXTERNAL_URL`, `PORT`, and
  `RENDER_GIT_COMMIT`; do not replace them with local values.

The private budgets count actual provider calls, including semantic verification
calls, not just button clicks. Original input limits and route/provider rate
limits still apply. Budgets are in memory, require one worker, and reset at
restart. They are usage protection, not a guaranteed billing cap. Raising them
requires review of provider quotas and costs. No paid plan is needed or enabled.

## Honest AI modes and safety boundary

The documented semantic `noun_phrase` material-claim limitation remains in the
frozen academic code. Unrestricted public live generation is **not** approved.

`/` is a visibly labeled academic simulation using only fixed fictional Satr
examples. No public generation, discovery, or Advisor request is sent to Groq.
Finance, scores, charts, Proof Mode and exports use the real application code.
Proof entries remain self-reported observations, never independently verified
evidence. Every public exported PDF has a simulation/self-report footer.

`/live` requires the owner's separate private token (POST form, not URL). A
signed Secure/HttpOnly/SameSite=Strict cookie expires in one hour. Login is
throttled. Live POSTs must select the live channel and pass authentication and
same-origin checks. Each page fixes its channel, even if another tab logs in.
Session-recovery storage and export mode signatures are separate for demo/live.
The original receipt/HMAC and publication checks remain intact.

New private generations really call Groq. Built-in example plans remain
examples. Live errors do **not** substitute simulated provider responses; local
fallback guidance, if displayed by the frozen UI, is explicitly distinguished.
Only safe timing/status/token-count diagnostics are returned to the private UI.
Never enter personal customer details or confidential information in either mode.

## Verification

Mocked regressions require no credentials:

```powershell
python -m unittest discover -v
npm ci
npx playwright install chromium
npm run test:browser
```

Deployment adapter isolation tests: `python -m unittest test_render_deployment -v`.
The new adapter tests run in isolated subprocesses, prohibit live network calls,
and check public/live separation, failures, budgets, cookies and signed exports.

After deployment verify `/health` against the deployment commit. Exercise both
founder pathways in English/Arabic, all tabs, editable finance, Proof save/clear,
refresh, Advisor, light/dark/mobile, and Founder/Investment PDF plus CSV. Inspect
downloaded PDF labels and content. Separately log into `/live` using the owner
token and record genuine Groq status, finish reason and timing for each language.
Do not describe mocked/curated tests as live-provider verification.

## Rollback and emergency presentation

Before this deployment, the working public deployment was
`dep-dbgrcph42hec739895q0`, commit
`49f50e86b9e24799bcf51e2f260a57cf64e09936` on `main`.

In Render, open this service's Deploys, select that successful deployment and
choose Rollback. Confirm its health and URL. Restore branch `main`, build
`pip install -r requirements.txt`, start `gunicorn app:app`, and the prior empty
health path only if needed for subsequent rebuilds. Keep auto deploy off.
Rolling back an image does not itself restore environment/settings; retain the
saved baseline. Do not delete the previous successful deployment or force-push.

The frozen `START_KHOTWA_DEMO.cmd`, its Git tag, and original final review and
presentation archives remain the emergency offline backup. Do not replace them
with this production adapter. Free Render can sleep after inactivity and take
time to wake. Warm the public URL before the presentation and keep the offline
demo ready. PDF requests are serialized to reduce matplotlib memory pressure;
one concurrent request can receive `pdf_busy` and should be retried later.
