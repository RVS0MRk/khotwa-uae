# Khotwa V2.2.6 correction review

Baseline: `9af1149ba679b8978d7a0b82e25ff128ac4a1d23` on
`codex/khotwa-v2-redesign`. Last independently reviewed baseline: `03a29b1`.
Implementation and measurements: 21 November 2026, Windows, Python 3.12.14,
Node 24.22.1, Playwright 1.62.1 / Chromium 151.0.7922.34 / axe 4.14.0.
All model transport in this correction's automated verification was mocked.
No push, merge, deployment, live Groq call or academic-report change was made.

## Changes and acceptance

| Ticket | Implementation | Measured acceptance |
| --- | --- | --- |
| V226-001, P0 | Material achievement/promise policy instead of a generic ban on finite descriptions. Preserve complete original sentences; no clause-tail reconstruction. Missing classifier verdicts still require deterministic safety. Reject the entire score dimension if any reason sentence is rejected. | Four required fixtures exceed 80% verbatim retention; all five dimensions, Problem and Solution retained. Complete instruction and parenthetical-profit regression tests pass. |
| V226-002, P0 | Whole-word qualifiers scoped to each predicate; future/absolute negatives separated from actual denials; Arabic clitic boundaries, nominal/participial predicates and English irregular predicates checked independently of verdict labels. Valid signed text is rechecked too. | 40 new unsafe examples per language, plus 17 supplied examples: zero survivors under each of five labels. 25/25 safe examples per language retained. All legacy safety assertions remain unchanged. |
| V226-003, P1 | Resolve the first strong base direction from the logical paragraph / hard-break segment and reuse it for every soft wrap. Per-line shaping and the pure-Latin path remain. | 76 paragraph/width combinations, 303 wrapped lines: 20 wrong directions before, zero after. A separate hard-break / pure-Latin test passes. Twenty new reports rendered into 114 pages. |
| V226-004, P2 | Share original allowed input choices; normalize export display aliases, risk enums and finite nonnegative budgets to those choices or neutral defaults. Founder input remains labelled input. | 12 injection fields x two routes x two languages = 48 actual PDF exports pass. Display-sink retentions fall from 11/12 to 0/12 in the paired probe. |
| V226-005, P2 | Whole-word Arabic intent matching; food/service activity precedes generic selling, preserving education/development intent. | All four supplied cases were Retail on the isolated baseline; now Food / Services / Food / Food. Eighteen JS detector cases and the existing browser category cases pass. |

### Paired content measurements

These are measurements of the same fixtures, classifier and counting method
against an isolated `git archive` of V2.2.5 and the current implementation. They
are not a reinterpretation of the independent review's different denominators.
Count an eligible original string as retained only if that entire exact string
occurs in the route's normalized prose. Exclusions are manually annotated actual
claim/promise paths in `tests/fixtures/v226_cases.json`, not policy-derived labels.
App-owned evidence wording and intentional translation normalization still count
as lost verbatim strings in this conservative measurement.

| Fixture | Before | After | Assessed dimensions before -> after | Total after |
| --- | ---: | ---: | ---: | ---: |
| Rich lunch with the requested ordinary reasons | 109/147 (74.15%) | 144/147 (97.96%) | 1 -> 5 | 18/25 |
| Original committed rich English, unchanged | 131/179 (73.18%) | 160/179 (89.39%) | 5 -> 5 | 15/25 |
| Captured live English lunch | 103/158 (65.19%) | 145/158 (91.77%) | 5 -> 5 | 19/25 |
| Captured live Arabic lunch | 91/159 (57.23%) | 146/159 (91.82%) | 4 -> 5 | 18/25 |
| Captured live packaging | 109/155 (70.32%) | 149/155 (96.13%) | 4 -> 5 | 19/25 |

The added rich lunch fixture derives from the committed rich English fixture,
adds the specification's ordinary 18-point reasons and complete long instruction,
and omits a stale duplicate bilingual copy. It does not replace or edit the
original rich fixture. Both versions are measured. Before/after fixture hashes
match and are recorded in the acceptance JSON. The three live captures are
unchanged; these are captured data, not new live-provider tests.

No newly manufactured lowercase/conjunction fragment occurs in any measured
plan. Original noun labels such as `office workers in Abu Dhabi` retain their
original casing; capitalization of every noun label is not asserted. Sentence
prose is kept whole or omitted, including the whole risky sentence with a safe
trailing clause. No new full stops are inserted to salvage tails.

### Safety measurements and interpretation

The independent fixture was written separately from the production grammar and
contains 40 English and 40 Arabic claims about a different fictional repair
business. It spans achieved results, named/verb-initial/nominal predicates,
irregular predicates, word-number amounts, negative performance guarantees,
savings, income, timing promises and unrelated qualifiers. Seven English and ten
Arabic specification examples supplement it. `user_attributed` is tested with
nonmatching input; a model label cannot manufacture a matching founder source.
Existing exact founder-input quotation tests still pass with an explicit
not-independently-verified attribution.

| Mock label | EN survivors before -> after (47) | AR survivors before -> after (50) |
| --- | ---: | ---: |
| planning | 6 -> 0 | 15 -> 0 |
| hypothesis | 6 -> 0 | 15 -> 0 |
| negation | 6 -> 0 | 15 -> 0 |
| user_attributed | 0 -> 0 | 0 -> 0 |
| noun_phrase | 6 -> 0 | 15 -> 0 |

Safe statements and denials: English 14/25 -> 25/25; Arabic 20/25 -> 25/25.
The independent 80 unsafe cases are additionally injected into generation,
Advisor and discovery, and checked at authenticated export. Each score
dimension is tested with a safe sentence plus a fabricated reason: the score
does not survive on the safe neighbor. Two legitimate personalized 18/25 reports and sixteen additional actual PDF exports
exercise deliberately valid receipts over rejected achievements, savings,
income and timing promises in both languages and both report types.

Receipt verification is still required. No signature is bypassed, forged for
production or refreshed by the export path. A rejected baseline reason is
removed only after receipt authentication, and its dimension becomes unassessed.
If that rejected reason also occurs inside receipt metadata, the renderable
clone omits the tainted receipt; the original submitted receipt is unchanged.
Untainted receipts retain their normal behavior. Existing tamper/restart/old
receipt tests and 28 independent receipt/consistency checks pass.

The classifier outage test retains safe descriptions and score reasons while
dropping unsupported material. A bounded, operation-local cache avoids repeated
grammar work on the same text and is reset in `finally`; no visitor text is
retained in a shared global cache or across requests.

This is a bounded linguistic safety policy, not independent fact verification
or a guarantee for every possible paraphrase. Measured targets pass on the
frozen English/Arabic corpora. Further independent unseen review remains useful.

## Verification results

Final execution results are recorded below before the local commit. Exact logs,
assertion evidence, dependency inventory and command transcripts are in QA.

| Verification | Exact final result |
| --- | --- |
| Complete Python suite, pinned environment | 189 tests, 785.965 s, OK; zero failures/errors |
| V226 module, existing environment | 14 tests, 217.459 s, OK |
| `test_browser.cjs` | PASS: state/session, discovery, Advisor, CSV, bilingual PDF and syntax journeys |
| `test_redesign.cjs` | PASS: nine viewport sizes in EN/AR and both themes, journey/keyboard/reduced-motion checks |
| `test_v2.cjs` | 31 check groups, zero failures |
| `test_v21.cjs` | 24 financial/localization/accessibility/responsive groups, zero failures |
| `test_v22.cjs`, three consecutive final-source runs (4, 5, 6) | 87 groups, 128 axe states, 214 primary screenshots each; zero serious/critical violations |
| Independent old safety runner | 252 mocked route cases, zero unsupported survivals |
| Independent financial oracle | 25,200 comparisons / 1,200 random cases, zero mismatches |
| Independent receipt / finance export checks | 28 receipt cases pass; 76 CSV values agree; all four Investment PDFs agree |
| Signed PDF publication probes | Two legitimate 18/25 reports and 16 unsafe signed cases pass, with Latin marker extraction checks |
| Source syntax | 33 JS/CJS and 57 Python files parse successfully |
| Dependencies | All 31 declared pins match in the full-suite environment; 27 runtime pins match; `pip check` passes |
| Protected source | Seven protected implementation/UI files unchanged; 13 frozen application hashes verified |

The first three V2.2 runs also passed, but are retained as development evidence;
the three counted final runs were started after the last application change.
Expected mocked 429, malformed-response and opt-in denial messages in test logs
are exercised error paths, not live provider errors.

The previous local virtual environment has nine runtime-pin deviations; its
new V226 regression module passes. The final full run uses the isolated pinned
environment. All 31 declared runtime/development pins match there, and the
vendored fonts/assets match committed versions. No dependencies were changed.

The original tests were not weakened. Development failure logs are retained
separately: they caught dropped Arabic intentions, service modifiers and a
conjoined question losing its original wording. The final run is identified
explicitly rather than presenting a failed development run as a pass.

## PDF and visual evidence

`review/generate_mock_pdfs.py` creates 16 Founder reports across native EN/AR,
export-label EN/AR and none/five/payment/clear Proof stages, plus four Investment
reports. They include the mixed paragraphs on summary/cover, detailed-plan and
Investment pages. The actual browser matrix separately exports 16 Founder,
four Investment and four CSV files, exercising refresh, Clear, language switches
and signed state. Its score path remains 15 -> 18 -> 15 under unchanged rules.
Five interests alone do not manufacture sales or independently verified evidence.

All 20 helper reports / 114 rendered pages were visually inspected through
contact sheets. Affected mixed-script covers and table pages were also viewed at
page resolution. There are no extracted black-square or replacement glyphs in
the matrix, and Amiri is embedded. Poppler's display-font warnings for Symbol
and ArialUnicode are recorded; they did not produce visible missing glyphs in
these renders. Long tables retain repeated headers and may continue to another
page. This is assistant visual inspection, not native-reader certification.

QA includes paired actual mobile dashboards from the isolated V225 baseline
and current V226, plus EN/AR, light/dark finance and Proof screenshots. CSS,
templates, animations, dashboard layout and Proof rules were not changed.

## Inventory and reproduction

- Policy/content: `publication_policy.py`, `material_claims.py`,
  `content_safety.py`, the scoped wrapper in `plan_normalize.py`.
- Export enums: new `input_options.py`, original option sets imported in `app.py`.
- PDF direction: `pdf_text.py`; category intent: `static/onboarding.js`.
- Regression tests/fixtures: `test_v226.py`, `tests/v226_category.cjs`,
  `tests/v226_browser.cjs`, `tests/fixtures/v226_cases.json`,
  `tests/fixtures/v226_rich_lunch.json`; existing browser runner/server extended.
- Portable reproduction: `review/README.md`, `review/reproduce_independent_probes.py`,
  `review/reproduce_v226_acceptance.py`, `review/check_v226_signed_pdfs.py`,
  `review/generate_mock_pdfs.py`; this review document.

`finance.py`, `scoring.py`, `provenance.py`, `disclosures.py`, `static/proof.js`,
`templates/index.html` and `static/startsmart.css` match the starting commit
after line-ending normalization. Hash evidence is included. Academic files
were neither opened nor modified. CORE contains the complete final committed
source, all test fixtures/scripts/fonts/pins, a full binary patch and intermediate
commit history from V2.2.3, plus the targeted V225-to-V226 patch. Archives exclude
credentials, virtual environments, caches, node_modules and academic reports.

See `review/README.md` for exact isolated Linux setup, mocked preview, suite and
PDF commands. Automated verification here ran on Windows; no new Linux or live
Groq/Render validation is claimed. Configure a stable production signing key of
at least 32 bytes, retain one worker, and check actual provider quota/cost before
the demo. Those owner operations were not performed or silently assumed safe.
