# Khotwa V2.2.4 — live AI reliability and QA corrections

Baseline: `03a29b1be811b7b9767acd6391c66d6e4c62b871` on
`codex/khotwa-v2-redesign`. HEAD, branch and a clean tree were checked before
editing. The final local commit SHA is recorded in the review archive's Git
metadata. This file intentionally does not embed its own commit hash.

The complete V2.2.3 live QA report, bug register and stored reproductions were
read before implementation. No academic report, secret.txt, production site or
earlier review archive was changed. No push, merge, PR or deployment occurred.

## Seven-ticket requirements matrix

PASS means the specified offline/browser/export checks passed in their recorded
scope. PARTIAL means implemented and passing those checks, with live semantic
quality still NOT VERIFIED; it does not imply an observed remaining bypass in
the supplied challenge fixtures.

| ID | Severity | Implemented correction | Changed files | Evidence | Outcome | Remaining limits |
|---|---|---|---|---|---|---|
| H01 | High/P0 | Independent bounded semantic classification, positive publication policy, source ledger, source-bound attribution, personalized fallback and authenticated export text | material_claims.py, provenance.py, app.py, advisor.py, prompts.py, content_safety.py, groq_client.py, provider_budget.py | test_v224.py; retained V2.2.1–V2.2.3 safety tests; stored pre-seed/Arabic revenue replays; both PDF paths; browser adverse pitch | PARTIAL | Live classifier accuracy and unrestricted generalization not established. No route accepts independently verified commercial-achievement evidence. |
| H02 | High/P0 | Numerical advertising benefits and unrequested offers cannot acquire authority from a model verdict; keep explicit user statements attributed, retain genuine research questions | same publication/export modules | EN/AR savings/free/refund/delivery cases; stored sustainable-packaging plan; generated Founder/Investment PDFs | PARTIAL | Arbitrary paraphrases and mixed clauses may be misclassified. A user statement is not proof that an offer is deliverable. |
| M03 | Medium/P1 | Primary educational/selling/development intent before topic keywords; retail word boundaries; manual override retained | static/onboarding.js | 9 category examples plus manual override in each repeated V2.2 run; existing category tests | PASS | This is a heuristic suggestion, not a complete business-activity classifier. Ambiguous ideas remain manually selectable. |
| M04 | Medium/P1 | Visible quick/full controls synchronize; inline live error, aria-invalid/errormessage and explicit-submit focus; scenario edits stay independent | static/investment.js | EN light/AR dark error-state axe and keyboard checks; missing/zero/corrected values; V2.1 scenario regression | PASS | Browser DOM/axe verifies announcements are wired; physical screen-reader speech was not tested. |
| M05 | Medium/P1 | Human-readable Advisor context labels, localized Proof Mode term, removed internal markers, coherent partial answer, distinct errors and retries | advisor.py, app.py, material_claims.py | exact `proofmoderecordedevidenceonly` and underscored reproduction; Arabic reply/error/retry browser group | PASS | Free-form language quality requires bounded live review. Deterministic budget recall is source-composed, not a live AI result. |
| M06 | Medium/P1 | One canonical normalized assessment; presentation overlays only; no second generic normalization; preserve score, evidence, finance and original content if translation unavailable | app.py, plan_normalize.py, static/app.js, founder_pdf.py, financial_report.py, disclosures.py | stored 19/25 EN→AR→EN; AR→EN→AR; Proof values/notes and finance; identity/reload; translation notice | PASS | Untranslated original prose remains visible with an honest notice. The fix does not manufacture a fluent translation. |
| L07 | Low/P2 | Keep section headings with following content; established report styling retained | founder_pdf.py | eight rendered EN/AR short/long Founder/Investment PDFs; coordinate checks and visual contact-sheet review | PASS | Very different future content still needs pagination review. Automated coordinates are a heuristic, not a glyph/layout certification. |

## Publication and provenance contract

The generation/Advisor/discovery response is parsed as JSON before publication.
The independent verifier receives untrusted strings as data, not execution
instructions, and returns only sentence IDs and speech-act classifications. A
classification cannot authenticate a business outcome or promote an AI sentence
to verified evidence. The application additionally applies its existing safety
filters, a positive speech-act/source policy, field constraints and app-owned
fallbacks. No new list of achievement synonyms was added to the locked legacy
patterns. Existing safety challenge suites remain in place.

The structured ledger distinguishes user assumptions, AI suggestions,
self-reported observations, financial projections, externally verified sources
and unsupported/unknown claims. In this version external-achievement sources
are always empty: model flags and funding-directory entries cannot populate
them. Proof counts remain self-reports. Financial numbers are recalculated
using the unchanged Decimal engine and remain projections, not achieved revenue.
Explicit user statements retained in generated prose are labelled as not
independently verified. Raw user business descriptions remain user input.

The verifier is at most one additional provider request per AI route, with up to
160 unique sentences/26,000 characters, a 2,400-completion-token ceiling and a
12-second timeout. Missing IDs, unknown categories, overflow, invalid responses
and transport failure drop unverified sentences. Useful approved neighbours
survive. Failures produce planning templates and a visible generation notice;
they do not silently declare AI verification successful. Structured Advisor
responses expose a `X-Khotwa-Content-Verification` status header. The normal
GPT-OSS low-reasoning/hidden-reasoning JSON settings are retained.

The 160-sentence/2,400-token limits can truncate a verbose verifier response;
fail-closed fallback is deliberate. False positives can remove useful text.
False negatives remain possible with adversarial grammar, euphemisms, mixed
clauses and model classification errors. Named market/legal statements are not
independently checked against official sources by this pipeline. Negations and
conditional questions are tested, but those tests cannot establish universal
truth verification. Additional live and independent held-out review is required.

## Export boundary and recovery

Published application/model narrative is sealed with an HMAC receipt. Export
accepts authenticated full fields or unchanged authenticated fragments; an
unsigned appended achievement cannot borrow a placeholder's negation or an
earlier planning verb. State display aliases are rebuilt from protected prose.
Both PDF builders use the same boundary. User-entered business assumptions,
Proof counts, investor notes and financial inputs stay separate, and financial
results are recomputed rather than trusted from the client.

Unsigned, forged, older or edited narrative is omitted conservatively from
exports; it is not silently re-certified by a lightweight offline grammar rule.
The optional **secret environment variable** `KHOTWA_CONTENT_SIGNING_KEY` should
contain a private random value of at least 32 bytes for stable receipts across
restarts. Never commit or log it. Without it, a random process key is used and
old receipts cease authenticating after a restart. A changed key similarly
requires regenerating model narrative for a complete export. One-worker
deployment remains necessary for the existing process-local quotas; a shared
key alone does not create a distributed limiter. Receipts are not external
verification or an assertion that user-entered Proof records are true.

Session privacy checks still inspect user/content fields, including the ledger.
Only opaque receipts and canonical identity hashes are excluded from the
contact/credential pattern scan: random digits in those hashes previously
caused intermittent recovery loss. An explicit browser regression now covers
that failure. Existing Clear, New idea and separate-session tests remain.

## Quotas, timeouts and the historical 429

The V2.2.3 report's first 429 came from the direct Groq smoke request, outside
Flask's limiter. Its origin is therefore Groq, not Khotwa. That historical
observation is not a new V2.2.4 live test.

Primary upstream 429 responses now produce `provider_rate_limited` and bounded
`Retry-After`; local exhaustion remains `rate_limited`. No automatic retry loop
was added. An unavailable verification request instead fails closed and is
logged with safe diagnostics. Primary calls retain their 40-second timeout;
frontend AI requests allow 65 seconds for the sequential primary + verification
work. Exports do not call Groq.

Actual provider attempts, including the verification request, consume the same
configured production allowance (`RENDER=true`):
`KHOTWA_AI_GLOBAL_PER_10MIN` and `KHOTWA_AI_CLIENT_PER_10MIN`. Existing logical
route limiting also remains, and PDF quotas remain separate. Defaults were not
raised. At the defaults, two-call routes can exhaust an allowance in roughly
half as many successful user actions as before. These are request-count limits,
not token or currency budgets. Provider tokens, cost, bursts, shared IPs and
multiple workers need separate operational judgment. Failed attempts count;
in-memory counters reset on restart and are not shared across instances.

## Verification record

Final exact commands, counts and artifact paths are recorded below and in the
archive's `logs/`, `git/` and evidence manifests. Development failures and the
fixes they prompted are retained separately; they are not presented as passing
final runs.

The original 134 unittest methods are retained; 16 new V2.2.4 methods bring
discovery to 150. Existing fixture assertions were adapted where the contract
changed: hypothetical founder skills are explicit assumptions; untranslated
content remains original instead of generic; trusted export fixture text is
sealed **before** malicious additions. Unsafe strings are never sealed merely
to make a test pass. `test_support.py` mocks only the new external semantic
classification boundary; production has no environment bypass for that gate.
New challenges supply explicit semantic fixtures and separately test bad,
missing, naive and failing classifications. These are mocked tests, not real
model judgments.

The full existing financial coverage includes 3,000 seeded independent
arithmetic cases, 20,000 display-consistency cases and 200 Python/JavaScript
score-parity objects inside the unittest methods. Neither `finance.py` nor
`scoring.py` was edited. The independent PDF/browser example retains startup
capital 7,220.00 AED, funding gap 720.00 AED, monthly revenue 6,800.00 AED,
operating profit 2,140.00 AED, break-even 40 units and runway 1.30 months.
Missing assumptions remain unknown, and explicit zero remains zero.

Eight PDFs cover both report types × both languages × short/long plans. Their
page renders, extracted text and `pdf-verification.json` are packaged. They
contain explicit AI-assumption and self-reported Proof disclosures; injected
pre-seed/revenue/savings claims are absent. Automated checks include numeric
agreement, heading candidates and text coordinates; rendered pages were also
visually inspected. English/Arabic fonts and established layouts are retained.

The five browser suites are integrated, redesign, V2, V2.1 and V2.2. V2.2 also
executes eight new V2.2.4 groups. Its three consecutive final runs use fresh
mock servers, separate evidence directories and the same final source. Tests
cover English/Arabic, light/dark, responsive layouts, exports, Clear/recovery,
session isolation, finance and accessibility. Linux, Render, physical phones,
hardware screen readers and public load remain NOT VERIFIED this round.

## Opt-in live validation — NOT RUN for V2.2.4

No new real Groq request was made. Stored V2.2.3 responses were replayed through
the actual V2.2.4 pipeline with mocked verification; that does not establish
live retention, semantic quality, provider quota or latency.

The owner may deliberately run:

```powershell
.\.venv\Scripts\python.exe scripts/live_v224.py --confirm-live
```

Without the flag this exits before app import or any request. With the flag it
uses the application's existing configured key privately. It exercises five
English and five Arabic fictional business ideas and a relevant Advisor
question for each. Maximum: **40 actual provider attempts**, including semantic
checks. Requests are paced 65 seconds apart; the script stops on a primary
failure, quota response or unavailable verifier, without automatic retries.
It is not a guarantee that 40 requests fit a provider plan or spend budget.

Ignored `outputs/v224-live/results.json` records statuses, timings, actual
attempt count and fictional structured outputs. After any executed run, review
every pitch/summary/action/Advisor point against actual supplied assumptions;
record sentence-level findings for achievements, offers, Arabic fluency,
personalization and consistency. A `checked` status means the pipeline ran,
not that a human verified the content. Check provider usage separately. Do not
attach private inputs, headers, credentials or raw reasoning to review reports.

## Release conclusion

### Final executed results — 14 November 2026

| Verification | Exact result | Final evidence |
|---|---|---|
| `python -m unittest discover -v`, shell key unset | **150 passed, 0 failed**, 188.698 seconds; all 134 baseline methods retained + 16 new methods | `logs/final/python-final-complete.log`, source-audit.json |
| `node test_browser.cjs` | PASS, exit 0; integrated assertions are unnumbered | `logs/final/verified-browser-1.log` |
| `node test_redesign.cjs` | PASS, exit 0; eight-width EN/AR light/dark matrix and interaction checks | `logs/final/verified-browser-2.log` |
| `node test_v2.cjs` | **31 groups**, 0 failures | `logs/final/verified-browser-3.log` |
| `node test_v21.cjs` | **24 groups**, 0 failures | `logs/final/verified-browser-4.log` |
| `node test_v22.cjs`, three consecutive final repeats | **59 + 59 + 59 groups**, all exit 0; 214 screenshots per repeat | `logs/final/verified-browser-6.log`, -7.log, -8.log; browser-v22-run-1/2/3 |
| Accessibility in those repeats | **462 axe audits**: 384 main + 72 disclosure + 6 visible-error checks; 0 serious/critical violations | three axe-matrix.json, v223-checks.json and v224-checks.json files |
| Theme contrast samples | **864 frames**, all at least 4.5:1 under the suite's measurement | three v221-checks.json files |
| Frontend syntax | **24 JS/CJS files**, 0 failures | logs/final/frontend-syntax.log |
| Dependencies | `pip check`: no broken requirements | logs/final/dependencies.log |
| Founder/Investment reports | **8 PDFs, 44 rendered pages**, matching checked numbers, disclosures, no detected heading orphan/coordinate candidates; injected H01/H02 claims removed | evidence/pdfs/, pdf-renders/, screenshots/, pdf-verification.json |
| Live V2.2.4 Groq | **NOT VERIFIED; 0 real calls** | bounded opt-in procedure above |

The numbered browser total is 232 groups (31 + 24 + 177), plus the two
unnumbered legacy suites; this is not 232 individual unit tests. Invocation 5
also passed but preceded the corrected packaging replay input, so it is kept as
development evidence. Final consecutive V2.2 repetitions are invocation IDs
6, 7 and 8, against the final application and fixture code. The first four
suites' source did not change during that fixture correction. The final full
Python discovery ran after it.

Stored English lunch scoring remains 19/25 through both switches. The stored
Arabic sample retains its canonical incomplete assessment after unsupported
score reasons are removed; switching does not manufacture missing points or
change that status. Both round trips retain identity, idea, segments, first
action, Proof values and financial inputs. No further generation request occurs
on switching. Free-text Proof notes remain in memory across language changes
but stay excluded from refresh recovery under the existing privacy contract.

All 35 staged files were reviewed and scanned for key patterns; no matching
credential patterns or private/academic paths were found. The complete tracked
source index was separately scanned without printing values. The previous
V2.2.3 Claude review ZIP retains SHA-256
`52eac9547164f599df7af3d1e60c5043b395c54469a673e35a01dce6a6849633`.
Source scans are bounded checks, not a complete secret-history or security audit.

This is an implementation ready for independent review, not an unrestricted
public-release safety certification. The supplied reproductions and regression
scope are addressed; real verifier quality/cost, independent unseen challenges
and deployment behaviour remain release checks. Claude remains the independent
reviewer. The complete archive is `outputs/Khotwa_V2.2.4_Claude_review.zip`.
