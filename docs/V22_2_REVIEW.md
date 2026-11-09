# Khotwa V2.2.2 correction review

Baseline: `a895004cb711b800842a1d4de05c8df6622e94c5`.
Branch: `codex/khotwa-v2-redesign`. HEAD, branch and clean working tree were
verified before edits. The final local commit is recorded in the archive
manifest and appended to the packaged copy of this review after commit, avoiding
a self-referential SHA in the committed file.

No push, merge, PR or deployment was performed. No academic report or secret
file was opened or edited. No runtime dependency, framework, ML model or remote
moderation API was added. The existing local preview process was not restarted;
all browser checks use isolated mock servers.

## Ticket matrix

| Ticket | Result | Implementation | Verification / evidence |
|---|---|---|---|
| V221-001 | PASS | `content_safety.py`; expanded `tests/fixtures/v221_safety.json`; `tests/fixtures/v222_review.json`; `tests/fixtures/v222_heldout.json`; `test_v222_safety.py`; `test_v222_heldout.py`; `scripts/evaluate_v222_safety.py` | Development table, five plan fields, Advisor/discovery routes, EN/AR PDF extraction, unchanged V2.2.1 tests, held-out JSON and retention |
| V221-002 | PASS | `static/startsmart.css`, `tests/v222_browser.cjs`, `test_v22.cjs` | Eight EN/AR light/dark footer screenshots at 390/1440; 20px horizontal gap; all targets at least 24px; axe matrix |
| V221-003 | PASS | `static/onboarding.js`, `tests/v222_browser.cjs` | Liwa safari, two tourism variants and school-trip Education precedence, both UI languages and widths; all old category tests retained |

## Outcome detector and scope

The filter now combines an achieved-outcome predicate/state with a business
subject/object. Categories cover purchases, sign-ups, contracts, revenue,
investors/funding, certainty, trust and evidence sources in both languages.
Quantified people plus a present/past verb and unconditional market-certainty
patterns supplement the ordinary verb/object pairing. Matching normalizes
comparison text without changing displayed spelling. It remains deterministic
and entirely local.

Clause boundaries prevent an unrelated conditional or negative from qualifying
a separate assertion. Guards distinguish hypotheses, future/modal statements,
questions, imperatives and negation. Ordinary descriptions such as weekly lunch
pre-orders remain. A heading followed by a new assertion cannot borrow the
heading's imperative exemption. Existing Arabic instructions without payment
also remain, rather than treating the noun دفع as an achieved payment.

Sentence-level removal remains: useful neighbours are preserved. The same
filter is used before plan/bilingual normalization, by Advisor/discovery, and
again at both PDF boundaries. No separate UI regex or output channel bypass was
introduced. User financial assumptions, Proof records and their provenance are
unchanged. No generated traction is turned into recorded customer evidence.

## Pre-authored held-out protocol and honest results

The held-out file was written **before any detector edit** with 15 further
English unsafe statements, 10 Arabic unsafe statements, and 15 safe statements
(8 EN / 7 AR). Its immutable LF-text SHA-256 is:

`3265763ad3e6ae7efd4a23e265ff0cd5b1d0cf4ed52331b9b4c015f6ebe7525f`

`heldout-lock.json` and `detector-freeze.json` record the initial fixture lock and
the first frozen detector. The first evaluation removed **24/25 unsafe (96%)**
and preserved **15/15 safe (100%)**. The fixture was not changed afterward.

Subsequent detector edits addressed failures from the **unchanged existing
V2.2.1 test** (an imperative heading concatenated with a claim) and the existing
rich Arabic fixture (no-payment instructions). They did not address the held-out
miss. Both first and final reports are packaged, with their actual detector
hashes; the final result remains **96% unsafe removal / 100% safe survival**.
This is a locally pre-authored evaluation, not a claim of independent external
validation or perfect generalization.

The remaining missed statement is:

> خدمتنا مربحة منذ الشهر الأول.

The possessive Arabic service form is not recognized as a business object by
the current bounded vocabulary. It **still survives the filter**. This is a
known limitation, recorded instead of silently tuning the held-out set. The
specified ≥90% / 100% targets pass; this is not a claim that all fabricated
success wording is blocked. Further unseen review is still useful.

## Safety table and channel evidence

The expanded development table has **53 unsafe** and **43 safe** statements,
including all 18 new reviewer claims and all 12 reviewer safe statements.
`safety-table.log` and `table-results.json` record every input/output.
`test_v222_safety.py` tests the reviewer set in summary, 30-second pitch,
first action, market rationale and a score reason, plus Advisor summary/point/
next-action and discovery fit/first-test/assumption. All other model leaves
continue to be tested by the unchanged V2.2.1 test file.

PDF checks inject a unique Latin marker inside each safe/unsafe sentence before
export, then extract the **actual founder and investment PDFs** in EN and AR.
Safe markers must appear and unsafe markers must be absent. This makes the
Arabic assertion meaningful despite RTL presentation forms in PDF text, where
searching the original logical Arabic alone could give a false pass. No PDF
layout or financial engine was changed.

## Final verification

| Check | Final result |
|---|---|
| `python -m unittest discover -v` | **129 passed; 0 failures, errors or skips**, 163.840 seconds |
| Independent new safety/held-out unit run | **5 passed**, 19.830 seconds |
| Expanded development table | **53/53 unsafe removed, 43/43 safe retained** |
| First and final held-out evaluations | **24/25 unsafe removed (96%); 15/15 safe retained (100%)**; known miss above |
| Rich safe-content retention | EN **153/155 (98.71%)**, alternative EN **153/155 (98.71%)**, AR **146/155 (94.19%)** |
| `node test_browser.cjs` | PASS integrated discovery, four business journeys, sharing, sessions/Clear/isolation, Advisor, CSV and bilingual PDF checks |
| `node test_redesign.cjs` | PASS nine viewport groups / 36 EN/AR theme combinations plus the functional/motion/keyboard group |
| `node test_v2.cjs` | **31 check groups passed**, 0 failures |
| `node test_v21.cjs` | **24 check groups passed**, 0 failures |
| `node test_v22.cjs`, Windows release run 1 | **47 groups; 128 axe states; 214 matrix PNGs + 8 footer PNGs; PASS** |
| Immediately consecutive run 2 | **47 groups; 128 axe states; 214 + 8 captures; PASS** |
| Immediately consecutive run 3 | **47 groups; 128 axe states; 214 + 8 captures; PASS** |
| Accessibility | **0 serious / 0 critical** over 384 matrix states, plus 6 privacy-dialog checks |
| Theme switch | **864 full-motion frames** passed; minimum contrast **13.4055:1**; no running/interpolated CSS color transitions |
| Footer geometry | Eight combinations per run; **20px horizontal gap**, smallest target **53.20 × 24px**; no page overflow |
| Prior layout target | Desktop tab top **563.58px** in EN and AR, below 600px |
| Categories | Original 17 Arabic examples and ten-category EN/AR checks retained; safari + two tourism variants + school-trip Education precedence all passed in both languages/widths |
| Financial / scoring regressions | Existing 3,000 independent arithmetic cases + 20,000 display consistency cases, scenarios/cash/rounding/sensitivity/saved state and 200 Python/JS scoring-parity objects passed |
| Engineering | `node --check`: **29 files**, zero failures; Black/Prettier checks and `pip check` passed; dependencies unchanged |

All three requested final browser invocations completed in sequence against the
final runtime code. Per-run logs, axe JSON, footer geometry, category fixtures,
frame samples and measurements are included. The last 214-image matrix and 8
footer captures are packaged once (**222 PNGs**); per-run hashes record earlier
images without duplicating the matrix three times. All eight footer language/
theme/width combinations were visually inspected.


The workstation environment is Windows x64 build 10.0.26300, Python 3.12.14,
Node 24.22.1, Playwright 1.62.1, managed Chromium 151.0.7922.34 and axe 4.14.0.
Linux/Chromium 153 was independently reported by the owner for V2.2.1; it was
**not run by this implementing session for V2.2.2**. WSL/Docker/accessible Linux
CI are unavailable here. No remote CI or deployment was started.

All automated processes start with GROQ_API_KEY unset. Mock bootstrap supplies
only its synthetic key, and new channel tests explicitly forbid requests.post.
The held-out evaluator imports neither config nor Flask. No live Groq request
was made. The malformed-provider HTTP 500 in the original browser suite is
expected fixture coverage, not a failed assertion.

No original assertion was weakened, and `test_v221_safety.py` is byte-equivalent
to baseline after line-ending normalization. The separate held-out threshold
test accepts ≥90% unsafe removal and exactly 100% safe survival; it deliberately
does not disguise the remaining unsafe miss as a pass for that individual case.

## Changed files

- `content_safety.py`
- `static/startsmart.css`
- `static/onboarding.js`
- `test_v22.cjs`
- `tests/v222_browser.cjs`
- `tests/fixtures/v221_safety.json`
- `tests/fixtures/v222_review.json`
- `tests/fixtures/v222_heldout.json`
- `test_v222_safety.py`
- `test_v222_heldout.py`
- `scripts/evaluate_v222_safety.py`
- `TESTING.md`
- `docs/V22_2_REVIEW.md`

## Archive and remaining limits

The review archive contains an exact committed source snapshot, verified binary
baseline patch, changed-file list, commit metadata, full final logs, all three
browser-run axe/geometry/frame measurements, the complete last screenshot
matrix and eight footer captures, training/held-out results, fixture lock and
retention evidence. No private credentials, academic files, environments or
unrelated generated output are included. Existing V2.2.1 archives are untouched.

The known Arabic held-out miss remains. Live Groq, Linux/Chromium 153,
physical phones, screen readers, Render capacity and production operation were
not verified by these local mocked checks. This correction does not establish
current funding eligibility or independent verification of user-entered Proof.
