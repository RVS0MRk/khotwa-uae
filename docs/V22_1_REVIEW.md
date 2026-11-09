# Khotwa V2.2.1 correction review

Baseline: `c19cb86c4c67d29a9b5846f6529316612b76fe10`.
Branch: `codex/khotwa-v2-redesign`. Baseline HEAD/branch and a clean tree were
verified before editing. The final local SHA is recorded in the review archive's
`manifest.json` and `commits.txt`; the packaged copy of this document includes
that SHA after commit. This avoids a self-referential hash in the committed file.

No push, merge, pull request, deployment, production change or academic-report
work is part of this correction. No runtime dependency was added. Secret.txt
was not read, edited or packaged.

## Ticket matrix

| Ticket | Result | Files changed | Tests | Evidence |
|---|---|---|---|---|
| V22-001 | PASS | `content_safety.py`, `plan_content.py`, `founder_pdf.py`, `financial_report.py`, `test_v221_safety.py`, `tests/fixtures/v221_safety.json` | Independent language table; 1,122 individual model-field injections; Advisor/discovery; EN/AR PDFs; original content/finance regressions | `safety-evidence.json`, Python logs, `pdfs/` |
| V22-002 | PASS | `static/app.js`, `static/startsmart.css`, `test_v22.cjs`, `tests/browser_stability.cjs`, `tests/v221_browser.cjs` | Three consecutive release runs on Windows; 128 axe states plus two privacy dialogs per run; 288 full-motion frames per run | Per-run browser logs, axe matrix, `v221-checks.json`, light/dark landing captures; Linux unavailable |
| V22-003 | PASS | `static/app.js`, `static/startsmart.js`, `static/startsmart.css`, `static/investment.js`, `static/investment-workspace.js`, `templates/partials/dashboard.html`, `tests/v221_browser.cjs` | Six layout checks, tab position, missing vs zero price, detailed-field access, English/Arabic desktop/mobile | `screenshots/before/`, `screenshots/after/`, per-run layout measurements |
| V22-004 | PASS | `static/onboarding.js`, `tests/v221_browser.cjs` | 17 Arabic examples in each language/width context; original 10-category EN/AR matrix; manual selection | Per-run category records and browser logs |

## Safety and personalization

Matching uses several explicit assertion forms: definitive predicates, claimed
research/preferences, received traction counts, participation counts and Arabic
equivalents. Comparison normalizes case, Arabic diacritics/letter variants and
Unicode hyphens without rewriting the displayed business prose. Negation and
hypothesis guards apply to the relevant claim's clause, with sentence,
conjunction and punctuation boundaries. `not only` is an assertion, not a
negative. A generic `no` or `if` elsewhere cannot exempt a success claim.

All model strings, including bilingual text and metadata, are checked before
template normalization can copy them. Existing per-field defaults and schema
ownership remain. Unsupported sentences are removed while useful neighbours
survive. Unsafe original step recommendations still invalidate attached costs;
filtering the prose must not silently legitimise the price.

Advisor and discovery already use the shared `safe_text` boundary; their route
tests now inject the expanded claim table into every answer/card field. Founder
and investment PDFs recheck generated prose at export, including older saved
plans. User-authored ideas/notes, financial assumptions and recorded Proof data
retain their separate provenance; this filter neither verifies them nor turns
model examples or scores into evidence. Financial arithmetic is unchanged.

Representative input:

> Healthy lunch boxes could help busy office workers. Demand is proven. Start by interviewing five potential customers.

Output:

> Healthy lunch boxes could help busy office workers. Start by interviewing five potential customers.

All three reported claims are removed: `This idea is validated and viable.`,
`Demand is proven.`, `We already have 40 pre-orders.` Equivalent Arabic examples
are `الفكرة مؤكدة وناجحة.` / `الطلب مثبت.` / `لدينا 40 طلبًا مسبقًا.`

Preserved verbatim: `Demand is not proven yet.`, `If interviews confirm demand,
the idea may be viable.`, `Aim to collect 10 no-payment reservations.`,
`Customers pre-order lunch boxes weekly.`, and their tested Arabic equivalents.
The conditional instruction `Do not start operating before official requirements
are confirmed.` also remains. `safety-evidence.json` records exact pairs and
retention. Natural-language matching remains a bounded heuristic, not a proof
that arbitrary adversarial or future model wording can never pass.

## Theme and accessibility

`setTheme` first commits a temporary root `theme-switching` override, applies
theme tokens atomically, commits style, then removes the override after two
render callbacks. Rapid toggles are generation-guarded. Ordinary hover behavior
returns afterward. Session restoration uses the same path and reduced-motion
CSS remains intact. The first-toggle and reverse-toggle samples check every
frame's button colors against the two settled palettes with motion enabled.

Before axe, tests activate the audited page, enable reduced motion, assert an
actual `0s` transition duration and use a bounded poll of font/theme/animation
state. This avoids both intermediate-color measurements and unresolved
animation promises when Chromium suspends a background page. It does not hide
a live contrast flash with a long sleep. Existing accessibility thresholds and
the 128-state matrix remain unchanged.

## GUI details

- The existing Risks caution card spans the full grid row, with mobile stacking.
- Dashboard and Investment metadata share `businessMarketParts`: unknown
  fields are omitted, UAE-wide is a real scope, and values are not invented.
- Journey top spacing is reduced without changing controls or font sizes.
- Score financial context shares the 12px muted explanation style.
- Missing average price uses `—` with a small localized caption. An entered
  zero is still displayed as a numeric price.
- The four-number starter remains primary; its one secondary action is Add
  startup costs. Detailed operating/cash fields remain available through tabs.

Matched 1440×900 before/after tab positions: **577.58px → 563.58px**, in both
languages. The independently specified rich-test idea also measures 563.58px.
The reported 608px case was not reproduced with these fixtures; the actual
before value is recorded rather than substituting the report's value.

Screenshots cover all four requested views × 390/1440 × EN/AR, plus headers and
settled light/dark landings. Full-page captures avoid sticky-header artifacts
from element screenshots. The baseline server uses an archived exact baseline,
and every screenshot uses fictional mocked business content.

## Arabic categories

The supplied `صناديق غداء صحية تُطلب مسبقًا لموظفي المكاتب في أبوظبي` maps to
**Food & Catering**. Food precedes a health adjective. Added examples cover
education workshops, maintenance workshops, children’s clothing, nutrition,
diacritics, prefixed words, hotels, art and uncertain ideas. Children alone do
not trigger Education. Arabic Unicode word boundaries prevent matching `فن`
inside `فندق`; letter/diacritic normalization remains browser-local. Existing
English patterns, explicit manual choices and the Other fallback remain.

## Verification environment and results

Final verification on the frozen runtime source:

| Check | Exact final result |
|---|---|
| `python -m unittest discover -v` | **124 passed; 0 failed, 0 errors, 0 skipped**; 107.735 seconds |
| Independent `python -m unittest test_v221_safety -v` | **8 passed**; 90.537 seconds; 66 direct language cases and 1,122 per-field injections are subtests |
| `node test_browser.cjs` | PASS integrated regression: discovery, four business journeys, sessions/Clear/isolation, Advisor, sharing and bilingual PDFs |
| `node test_redesign.cjs` | PASS nine viewport groups (36 language/theme combinations), plus the functional/motion/keyboard journey |
| `node test_v2.cjs` | **31 check groups passed**, 0 failures |
| `node test_v21.cjs` | **24 check groups passed**, 0 failures |
| `node test_v22.cjs`, Windows final run 1 | **43 groups; 128 axe states; 214 PNGs; PASS** |
| Same, immediately consecutive final run 2 | **43 groups; 128 axe states; 214 PNGs; PASS** |
| Same, immediately consecutive final run 3 | **43 groups; 128 axe states; 214 PNGs; PASS** |
| Accessibility | **0 serious / 0 critical** across 384 final matrix states, plus 6 privacy-dialog checks |
| Theme frames with full motion enabled | **864 total**; 0 interpolated palette samples, 0 running CSS transitions; light **14.0709:1**, dark **13.4055:1** |
| Arabic additions | **17 examples** × both UI languages × both widths per run; all passed; original ten-category EN/AR tests also passed |
| Rich safe-content retention | EN **153/155 (98.71%)**, alternative EN **153/155 (98.71%)**, AR **146/155 (94.19%)** |
| Financial regression | Existing 3,000 independent arithmetic cases, 20,000 display-reconciliation cases, scenarios, runway/payback, rounding, sensitivity and saved state passed |
| Scoring | Existing 200 Python/JavaScript parity objects matched |
| Syntax / formatting / dependencies | `node --check` **28 files**, Black/Prettier checks passed; `pip check` clean; dependency files unchanged |
| Export evidence | Founder EN 7 / AR 6 pages; investment EN 3 / AR 3; all **4 reports / 19 rendered pages** visually reviewed; injected model success claims absent |

All required browser runs completed. The malformed-provider HTTP 500 logged by
the original integrated browser suite is deliberate fixture coverage, not a
failed assertion. All original tests were retained. Earlier development runs
were used to correct defects; these counts refer to the final release logs.

The final three browser logs are `test_v22-windows-final-1.log`, `-2.log`, and
`-3.log`. Each has separate axe data, measurements, category records and all
frame samples under `browser-runs/windows-N/` in the review archive. The complete
last matrix is packaged once (214 captures), alongside 28 before and 28 after
comparison/header/landing captures, for **270 screenshots**. Per-run checksums
record the earlier matrix images without duplicating their large PNG files.
Additional comparison contact images and all PDF page images are included.

Windows x64, OS build 10.0.26300; Python 3.12.14; Node 24.22.1;
Playwright 1.62.1; managed Chromium 151.0.7922.34; axe-core 4.14.0.
All processes start with GROQ_API_KEY absent; mock-only bootstrap supplies a
synthetic value and no local secret file is used. New safety tests and PDF
evidence additionally forbid `requests.post`. Live Groq was not called.

No Linux distribution is installed in WSL; Docker and an existing accessible
Linux CI runner are unavailable. No remote workflow was started. Linux and
Chromium 153 verification are **not claimed**. Portable tests and commands are
provided in TESTING.md.

No original test assertion was relaxed. Existing five suites are retained;
V2.2 gains 12 targeted check groups and rendering-state waits before axe. The
new table-driven fixture is independent of the matching patterns, and its
direct cases are also checked by the standalone evidence script.

## Changed files

The final changed-file manifest and binary patch are included in the archive.
The working tree is checked again after the local commit and packaging. No
secrets, virtual environments, caches, unrelated generated output or academic
documents enter the commit or source snapshot.

Changed files (18):

- `TESTING.md`
- `docs/V22_1_REVIEW.md`
- `content_safety.py`
- `plan_content.py`
- `founder_pdf.py`
- `financial_report.py`
- `static/app.js`
- `static/startsmart.js`
- `static/startsmart.css`
- `static/investment.js`
- `static/investment-workspace.js`
- `static/onboarding.js`
- `templates/partials/dashboard.html`
- `test_v22.cjs`
- `test_v221_safety.py`
- `tests/browser_stability.cjs`
- `tests/v221_browser.cjs`
- `tests/fixtures/v221_safety.json`

## Remaining limits

This round validates mocked local behavior, not live model generation, current
funding eligibility, production deployment, physical phones, screen readers,
Linux/Gunicorn, or Render capacity. V2.2 privacy notices, rate-limit defaults,
CSP, escaping, provider settings and financial inputs/calculations are retained.
