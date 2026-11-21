# Khotwa V2.2.6 independent reproduction

These utilities execute the extracted source, not an older review archive. All
automated model transport is mocked; no credentials or live provider access are
needed. Keep the `review` directory beside `app.py` and the `tests` directory.

## Linux setup

Use Python 3.12 and Node.js 24 (the verified Windows Python was 3.12.14).
From the extracted source directory:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
npx playwright install --with-deps chromium
unset GROQ_API_KEY
export PYTHONUTF8=1
export PYTHON_EXE="$PWD/.venv/bin/python"
python -m unittest discover -v
node test_browser.cjs
node test_redesign.cjs
node test_v2.cjs
node test_v21.cjs
for n in 1 2 3; do
  KHOTWA_REVIEW_DIR="outputs/review-run-$n" node test_v22.cjs || exit 1
done
python review/reproduce_independent_probes.py
python review/reproduce_v226_acceptance.py
python review/check_v226_signed_pdfs.py
python review/generate_mock_pdfs.py
```

The development requirements include the pinned runtime requirements. Browser
suites start and stop their own localhost servers; keep ports 5001–5004 and
5007 free. Suites use installed Playwright Chromium. If using a separate browser
cache, set `PLAYWRIGHT_BROWSERS_PATH` consistently at install and execution.
PDFs use bundled fonts and ReportLab; LibreOffice and Microsoft Office are not
required. To render for visual review, install Poppler and run, for example:

```bash
mkdir -p outputs/pdf-renders
pdftoppm -r 110 -png outputs/v226-pdf-matrix/founder-ar-none-labels-en.pdf outputs/pdf-renders/ar-en
```

For a fully mocked interactive preview (no credentials):

```bash
V22_RICH=1 TEST_PORT=5005 python test_browser_server.py
```

Open `http://127.0.0.1:5005`. AI responses in this fixture server are simulated.
For normal application startup use `python app.py` locally, or the existing
production command `gunicorn --config gunicorn.conf.py app:app` on Linux.
Real AI functionality requires a separately configured `GROQ_API_KEY`; do not
use one for automated tests. Keep a stable `KHOTWA_CONTENT_SIGNING_KEY` (at least
32 bytes) and one production worker. Provider quota/cost still needs an owner
check: generation, Advisor and discovery also call the semantic verifier.

## Evidence interpretation

`reproduce_v226_acceptance.py` measures fixed original strings through the actual
generation route. Risky exclusions are explicit fixture paths, not exclusions
inferred by the policy being tested. It also tests all five incorrect labels.
The extra rich lunch fixture supplies the requested ordinary 18/25 reasons;
the original committed 15/25 rich fixture remains unchanged and is measured too.
`check_v226_signed_pdfs.py` deliberately signs rejected material inside synthetic
plans; it asserts rechecking, dimension invalidation and original receipt
integrity through both real PDF routes.

`generate_mock_pdfs.py` produces 16 Founder and four Investment reports with
the mixed-script paragraphs on cover, summary, detailed plan and investment
pages. The four Proof stages are none, five self-reported interests, one
self-reported payment, and Clear. These entries are not independently verified
facts. The browser evidence package separately contains actual UI exports.

Windows results are recorded in `docs/V22_6_REVIEW.md`; this correction round
does not claim a new Linux execution. The linguistic gate is a bounded safety
policy, not external verification or a proof of universal language coverage.
