# Khotwa V2.2.8 Academic Final

This is the final bounded correction and university rehearsal release. It is not
a V3 redesign or a claim of unrestricted commercial readiness.

The starting V2.2.7 source is commit
`3de2311023d0fcfa12166861e1b44b8051ad8778`. The rollback tag is
`khotwa-before-final-20261124`. Final work uses
`codex/khotwa-final-academic-20261124`; the original redesign branch is preserved.
The final handover and archive manifests identify the exact frozen commit.

## Run the production application locally

Use Python 3.12. In a clean extraction on Linux:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
npx playwright install --with-deps chromium
unset GROQ_API_KEY
python -m unittest discover -v
export PYTHON_EXE="$PWD/.venv/bin/python"
node test_browser.cjs
node test_redesign.cjs
node test_v2.cjs
node test_v21.cjs
node test_v22.cjs
```

Mock tests require no credentials, explicitly block/replace provider calls and
never read the local credential file. `test_api.py` is a separate, intentional
live smoke test; run it only with your own authorized environment key.

Production start: `gunicorn -c gunicorn.conf.py app:app`. Set `GROQ_API_KEY` and a
private stable `KHOTWA_CONTENT_SIGNING_KEY` in the hosting environment. Never use
the offline adapter as a public deployment. The signing key is needed to keep
export receipts valid after restarts; a changed key requires regenerating plans.

## Offline presentation backup

```sh
python demo_server.py --port 5010
```

Open `http://127.0.0.1:5010`. On Windows, double-click
`START_KHOTWA_DEMO.cmd`, or run `python scripts/launch_demo.py` after installing
the development requirements. The launcher selects the existing isolated final
environment when available, then `.venv`, then Python on PATH. It does not install
software or make a deployment.

The separate adapter binds only to loopback, disables provider POST requests,
uses curated fictional Satr café-design content, and labels the website and
every PDF page as simulation. It exercises the real application routes,
normalization, financial engine, scoring, Proof Mode and HMAC verification.
It is **not live AI and not genuine customer research**. Inputs for other
businesses do not turn this fixed rehearsal into a general AI service.

`demo_data.py` contains the exact bilingual founder profile, explicit illustrative
financial assumptions and synthetic content. Licensing AED 300 is an entered
rehearsal assumption, not an official fee or quotation. Neither demonstration
scores nor simulated Proof rows establish demand, sales, willingness to pay or
product-market fit. Clear the demonstration rows before entering real observations.

The adapter creates an ignored local rehearsal signing key at
`outputs/.demo-signing-key`; it is excluded from Git and all review packages.
Do not reuse it for production. Its rehearsal-only localhost quotas are separate
from the unchanged production defaults; no paid AI requests are possible.

## Reproduce the final independent text audit

```sh
python review/reproduce_final_acceptance.py --output final-acceptance.json
```

This audit uses new ceramic/restoration examples and deliberately wrong semantic
labels. It reports survivors as well as successes. The name-field check is a
bounded syntactic improvement, not a general fact-verification system. The wider
`noun_phrase` semantic failure mode remains a commercial-release limitation.
Use the curated offline rehearsal for the controlled presentation.

The final evidence archives contain exact logs, before/after measurements,
rendered bilingual reports, actual browser screenshots, presentation instructions
and the academic handover. Automated tests are software evidence only.
