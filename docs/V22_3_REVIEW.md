# Khotwa V2.2.3 release hardening

Baseline: `22d31b49abdce9ff7161fb7d06e0924a2d68905a`.
Branch: `codex/khotwa-v2-redesign`. HEAD, branch and a clean tree were confirmed
before editing. The final local SHA is in the review archive manifest and is
appended to its packaged copy of this document after commit, avoiding a
self-referential commit hash in the committed source.

No push, merge, PR, deployment, framework migration, runtime dependency,
moderation API or ML model was added. No academic report or secret file was
opened or edited. Existing local preview processes were not restarted. All
automated tests start with GROQ_API_KEY unset and use mocked transport; no live
Groq test or owner-only live-smoke action was performed.

## Ticket matrix

| Ticket | Result | Files / implementation | Evidence |
|---|---|---|---|
| V222-001 | PASS | `disclosures.py`, Jinja globals in `app.py`, reusable note partial, Pitch/Advisor/Investment templates, one Investment workspace insertion, muted CSS, both PDF builders | Fixed EN/AR AI line plus explicit self-reported/not-independently-verified qualification; page-1 extraction/renders; browser note locations and axe |
| V222-002 | PASS | `content_safety.py`, expanded safe table, `test_v223.py` | Attributive participles distinguished from finite-result clauses; scoped English negation; five fields, Advisor and PDFs; rich-retention JSON |
| V222-003 | PASS | Matching-copy morphology in `content_safety.py`, `test_v223.py` | Possessive suffixes, ة/ت and accusative alef handling; original displayed text retained; existing Arabic safe tables; unchanged held-out evaluator |

## Disclosure, not a verification claim

The supplied AI-text line is retained verbatim in English and Arabic. It is
immediately paired with this explicit qualification:

> Proof Mode entries are self-reported observations, not independently verified evidence. Recording them does not automatically confirm customers, payments or other business outcomes.

> إدخالات وضع الإثبات ملاحظات تُبلّغ عنها بنفسك، وليست أدلة متحققًا منها بشكل مستقل. تسجيلها لا يؤكد تلقائيًا وجود عملاء أو مدفوعات أو نتائج أعمال أخرى.

This avoids treating user-entered observations as automatically confirmed facts.
It distinguishes model assumptions, user observations and independent
verification; the application does not perform the latter. These notes are
application constants, rendered outside the model normalization/export filter.
Model or client JSON cannot override them.

Locations: directly below the founder PDF's branded page-1 title, directly below
the investment PDF title, first in Readiness & Investor brief, under the Pitch
generator heading, and once in the Advisor footer beside its privacy note. The
Advisor presents the self-reporting qualification first, with keyboard-scrollable
note content so the composer/conversation remain usable. Language switching,
RTL and dark-mode colors use the existing mechanisms.

The founder Executive summary now explicitly labels Summary, Problem, Solution
and Why this market as AI ASSUMPTION (localized in Arabic). User idea/input
labels and financial assumptions remain distinct. No financial formula or
Proof counter was changed. The new Arabic investment-PDF notice alone is
wrapped in logical order before bidi shaping; other report layout is retained.

## Precision and morphology

No detection vocabulary was expanded. All **nine compiled patterns** are locked
by SHA-256 to the baseline in `v223_pattern_lock.json`; tests assert equality.
The additions are grammatical/morphological guards, not new success-claim lists.

The participle handling preserves product descriptions without finite completed
results, while retaining checks for auxiliaries, quantities, result timing and
direct-object finite clauses. English `none of`, `not one of`, `no one`,
`nobody` and negated perfect constructions qualify the relevant clause only.

Both reported English sentences survive verbatim in all five plan fields,
Advisor text and actual PDF extraction. Five further English and five Arabic
business-model descriptions were added to the safe table, plus the Arabic
negation equivalent. All pre-existing unsafe tests remain.

Arabic noun suffixes نا / ها / هم / ك and ت→ة restoration use an internal
matching copy and the existing noun patterns. A possessive noun immediately
before an existing outcome state also supplies its grammatical subject without
adding a noun inventory; accusative alef is normalized for existing outcome
states. Original displayed text is unchanged. Negated/conditional Arabic
remains, while `خدمتنا مربحة منذ الشهر الأول.` and `صار مطعمنا مربحًا.` are removed.

## Evaluation and limits

The V2.2.2 held-out fixture and its lock have not changed. LF-text SHA-256:

`3265763ad3e6ae7efd4a23e265ff0cd5b1d0cf4ed52331b9b4c015f6ebe7525f`

Original V2.2.2 result: **24/25 unsafe removed (96%), 15/15 safe retained (100%)**.
V2.2.3 result: **25/25 unsafe removed (100%), 15/15 safe retained (100%)**.
This is an evaluation of the same known fixture after an explicitly requested
morphology fix, not a fresh independent generalization estimate. It does not
invalidate the owner's unseen 4/29 result. The filter remains a backstop;
the disclosure is the release safeguard, not a claim of perfect filtering.

Repository rich retention: EN **153/155 (98.71%)**, alternative EN **153/155
(98.71%)**, AR **146/155 (94.19%)**. Substituting the reviewer's supplied lunch-box
summary into the repository rich fixture gives **152/155 (98.06%)**, with the
summary preserved verbatim. The reviewer's complete external rich fixture was
not supplied here, so its exact independently measured ratio is not claimed.

## Final verification

| Check | Final result |
|---|---|
| `python -m unittest discover -v` | **134 passed; 0 failures, errors or skips**, 176.955 seconds |
| Focused release checks | **5 tests passed** in 4.946 seconds; precision/morphology plus existing V2.2 safety checks: **9 passed** |
| Existing unsafe/safe table | **53/53 unsafe removed; 56/56 safe preserved** |
| Unchanged known held-out fixture | **25/25 unsafe removed; 15/15 safe preserved**, compared with original **24/25** unsafe |
| Original browser suite | PASS integrated journeys, Advisor, sharing, Proof/Clear/recovery/isolation, CSV and bilingual PDF checks |
| Redesign suite | PASS nine viewport groups / 36 language-theme cases plus functional/motion/keyboard checks |
| V2 browser suite | **31 check groups passed** |
| V2.1 browser suite | **24 check groups passed** |
| V2.2 browser suite, consecutive final Windows runs 1 / 2 / 3 | **51 groups; 128 matrix axe states; 24 additional disclosure states; PASS each run** |
| Accessibility | **0 serious / 0 critical** across 384 matrix + 72 disclosure audits, plus 6 privacy-dialog audits |
| Theme/layout preservation | 864 full-motion transition frames passed; desktop tabs remain 563.58px from the top; no new horizontal overflow |
| Browser evidence | Per run: 214 matrix + 8 footer + 24 disclosure PNGs; the complete last **246-image** set is packaged with all three run records |
| PDFs | **4 reports**, **4 page-1 PNGs/text files** with both fixed notices; all **17 report pages** also rendered and visually checked via QA contact sheets |
| Financial/scoring regression | Existing 3,000 independent arithmetic + 20,000 display cases, scenario/runway/payback/rounding/sensitivity/saved-state cases and 200 Python/JS parity objects passed |
| Engineering | Syntax: **30 JS/browser/helper files**; Black/Prettier and pip check passed; all 9 vocabulary patterns match baseline; no dependency changes |

The final three browser logs are test_v22-windows-final-1.log, -2.log and -3.log.
The archive includes each run's axe, disclosure, layout/frame/category records
and screenshot checksums; it avoids triplicating the same screenshot matrix.
All eight disclosure width/language/theme combinations were checked for each
of the three locations. The Advisor qualification remains readable first and
the longer note remains keyboard-scrollable.


Environment: Windows x64 build 10.0.26300, Python 3.12.14, Node 24.22.1,
Playwright 1.62.1, managed Chromium 151.0.7922.34, axe 4.14.0. Linux/Chromium 153
was not available in this session; no Linux result is claimed. No remote CI was
started. The owner-reported independent Linux baseline result is context only.

Arabic PDF extraction is normalized from presentation forms and checked for
the full fixed wording on page 1. The five-field precision cases are also
checked in actual exported PDF text. Fixed notices are not inferred from a
successful model call. The deliberate malformed-provider 500 in the original
browser suite is expected test coverage, not a failed assertion.

No existing assertion or safety test was removed or relaxed. Grammar regressions
found during development were corrected before final runs; final release logs
are identified explicitly. No fixture was adjusted to conceal an unsafe miss.

## Changed files

Changed files (18): `app.py`, `content_safety.py`, `disclosures.py`,
`financial_report.py`, `founder_pdf.py`, `static/investment-workspace.js`,
`static/startsmart.css`, `templates/partials/advisor.html`,
`templates/partials/ai-disclosure.html`, `templates/partials/dashboard.html`,
`templates/partials/investment.html`, `test_v22.cjs`, `test_v223.py`,
`tests/fixtures/v221_safety.json`, `tests/fixtures/v223_pattern_lock.json`,
`tests/v223_browser.cjs`, `TESTING.md`, and this review document.

The archive includes the exact changed-file manifest, source snapshot, verified
baseline patch and commit metadata. Changes are confined to disclosure
constants/templates/PDF labels, precision/morphology, targeted tests and their
documentation. Financial engine, provider settings, rate limits, deployment
configuration, privacy disclosures and academic report are unchanged.

## Remaining release actions

Live provider fluency and fabrication rates, Linux/Chromium 153, physical phones,
screen readers and Render capacity were not verified here. As specified, the
owner must run the opt-in two-request smoke and varied live ideas/Advisor review
before going live. This patch does not perform those billable actions or
independently verify Proof observations, funding eligibility or business outcomes.
