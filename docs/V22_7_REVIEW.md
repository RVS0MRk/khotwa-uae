# Khotwa V2.2.7 independent review

Starting commit: `4ca92c27e4201be950371a698a2c84b93d896747` (V2.2.6).
Branch: `codex/khotwa-v2-redesign`. Verification date: 22 November 2026 (Dubai).
Only the publication gate changes. No scoring, finance, PDF, receipt/HMAC,
UI, prompts, disclosures or existing test files were edited. No live Groq,
push, merge or deployment was performed.

## Important acceptance conflict / freeze blocker

The strict V227 outage rule and one existing V226 assertion contradict each
other. `test_v226.V226Tests.test_timeout_keeps_nonclaim_plan_but_never_claims_or_garbage`
requires the unhedged summary `A weekly pre-order lunch box service with rotating
menus.` to survive an outage verbatim. V227 permits only planning, hedged or
denial forms in summary during an outage; a noun-only summary is not one of the
allowlisted short-label fields. The strict new rule is implemented. That old
assertion was not changed or bypassed. The application uses its existing field
fallback and remains usable. This is reported as a test/acceptance conflict,
not an all-green release. A clarification was requested; no answer was assumed.

The independent reviewer should resolve this contract before a baseline freeze.
Allowing arbitrary unhedged summaries merely to satisfy that assertion would
silently weaken the new failure-mode policy.

## V227-001: label and form agreement

- `planning`: every independent clause must match an action/question form.
- `hypothesis`: every asserting clause must carry its own uncertainty before
  its predicate. Coordinated noun arguments are not independent assertions.
- `negation`: each clause must be an actual current/past denial; future/absolute
  promises and comparative bounds are not treated as denials.
- `user_attributed`: existing exact input binding and disclosure are unchanged.
- `noun_phrase`: the V226 material backstop remains; it is **not a factual
  verifier**. Its significant measured residual is reported below.
- Unknown, missing, malformed or unavailable classifications: only safe forms
  and bounded non-finite short labels are permitted. The existing
  `verification.status` reports `fallback` for incomplete/unusable verdicts.

The short-label paths are title, name, business_name_suggestion, target_customer,
location and focus, limited to 12 words. Ambiguous finite forms fall back during
an outage. Form checks use grammar, functional words, morphology and generic
irregular English inflection, without adding studio/pet/bike/business-specific
commercial terms or sentence-specific exceptions. The semantic verifier prompt
is byte/AST unchanged. Export/receipt functions are unchanged. The policy marker
is `v227-1`; this changes the publication policy identifier, not the HMAC design.

## Fresh-domain before/after

The new frozen fixture contains 30 English and 30 Arabic fabricated statements
about a fictional rehearsal/recording studio. It was created before gate edits.
It is neither the reviewer's unavailable pet-grooming corpus nor the old lunch,
delivery or bicycle set. Every case is injected into ten sinks: the eight core
plan/score/pitch fields plus title and business-name fields. The same fixture and
independent mixed classifier are used against an isolated archive of V226 and
current source. Counts are cases with any full-string survivor, not multiplied
by field count. Full per-field evidence and fixture hashes are in QA.

| Verdict / failure mode | V226 EN / AR | V227 EN / AR |
| --- | ---: | ---: |
| achievement | 0 / 0 | 0 / 0 |
| promise | 0 / 0 | 0 / 0 |
| planning (wrong) | 16 / 16 | 0 / 0 |
| hypothesis (wrong) | 16 / 16 | 0 / 0 |
| negation (wrong) | 16 / 16 | 0 / 0 |
| unknown | 16 / 16 | 0 / 0 |
| missing verdicts | 16 / 16 | 0 / 0 |
| invalid verdict values | 16 / 16 | 0 / 0 |
| classifier timeout | 16 / 16 | 0 / 0 |
| classifier error | 16 / 16 | 0 / 0 |
| noun_phrase (wrong) | **16 / 16** | **16 / 16** |

The noun-phrase residual is **16/30 (53.33%) in each language**. It is intentionally
visible, and the new policy does not claim universal semantic safety. A provider
that labels an unrecognized achieved result `noun_phrase` can still publish it.
This remains a material deployment risk and is appropriate for further independent
review rather than an unsupported readiness score.

The supplied review reports 21/30 EN and 20/30 AR survivors on its separate pet
corpus, and 11/38 EN and 10/33 AR route leaks on its earlier corpus. The raw corpora
were not attached, so those exact denominators were not independently rerun or
presented as our fresh measurements. The two quoted outage leak sentences are
included in the fixture for inspection. Automated cases use no credentials.

During outage, safe retention improves from 9/10 to 10/10 English and stays 10/10 Arabic. All ten new safe examples per language (actions, questions,
hedges and denials) survive intact; all 60 new unsupported sentences are blocked
under the required failure modes. The generation-route outage test returns a
nonblank plan, retains an explicitly safe summary/action and reports fallback.
Raw scores without publishable reasons become unassessed by existing scoring. The additional 30 actual API/export probes reject all strict-mode markers; the noun-label cases still publish the marker in generation, Advisor, discovery and Founder PDF (eight of ten noun-labelled route cases). Investment PDF did not render those injected fields, so its absent marker is not treated as independent proof that this residual is fixed.

## Retention and V227-002

The independent realistic mock labels imperatives/questions as planning,
explicit modal/assumption markers as hypothesis and other text as noun_phrase.
Its code is separate from production checks. It includes `can` and `يمكن`.
The unchanged V226 acceptance script was also run separately with its original
mock; no assertions or old fixture strings were edited.

| Fixture | V226 retention | V227 retention | V227 dimensions |
| --- | ---: | ---: | ---: |
| V226 rich lunch | 97.96% | 93.20% | 5/5 |
| Original rich_plan_en | 89.39% | 85.47% | 5/5 |
| Captured English lunch | 91.77% | 89.24% | 5/5 |
| Captured Arabic lunch | 91.82% | 89.31% | 5/5 |
| Captured packaging | 96.13% | 90.32% | 5/5 |

All five meet the requested 85% threshold. The V226 annotations of genuinely
risky fields are unchanged. Retention uses complete exact original strings and
therefore counts existing app-owned evidence wording/fallbacks as lost strings.

The three false-positive classes (four bilingual strings) improve from **0/4
to 4/4 retained**: the waitlist message with `can`, municipal permits adding time
and cost in English/Arabic, and the comma-listed denial. The rich fixture with
the reviewer's exact waitlist-message reason improves from **4/5 / Incomplete**
to **5/5 / 18/25**. The complete original review plan was not supplied; this is
the committed rich fixture with that exact reason, not a claim of access to the
reviewer's full private fixture.

Coordinated noun/argument lists keep their shared predicate or negation.
New subject/predicate clauses remain separate. Passive participle lists and
relative modifiers stay attached to their noun. Whole original sentences are
published or dropped; clause tails are never manufactured. `can`/`يمكن` are
whole-word, clause-local modals. Arabic regular person/conjunction morphology is
handled without adding new business-specific vocabularies.

## Actual verification

| Verification | Actual result |
| --- | --- |
| Full Python suite | **199 run, 198 passed, 1 failed, 0 errors; 791.741 seconds** |
| Unchanged legacy V226 assertions | 188/189 pass; the outage-summary contract assertion fails as documented above |
| New V227 module | 10/10 pass |
| First four browser suites | All pass; V2 has 31 groups, V2.1 has 24 groups |
| V2.2 final-source repeats 2, 3, 4 | Each passes 87 groups, 128 axe states, 214 screenshots; no serious/critical violations |
| Unchanged V226 acceptance script | All five fixtures retain at least 85%; 5/5 dimensions; its 40+40 safety set has zero survivors |
| Independent legacy probes | 252 mocked route cases, no unsupported survivals; 25,200 finance comparisons, zero mismatches |
| New-domain failure-mode probe | 30 EN + 30 AR, ten sinks each; zero survivors in strict modes; noun residual 16/30 each |
| False positives / reconstructed review reason | 4/4 strings retained; score 18/25, five dimensions |
| PDF matrix | 20 fresh reports, 114 page renders, zero replacement/box glyphs; all renders pixel-identical to V226 |
| Additional route/PDF probes | 30 cases; strict modes block markers; eight of ten noun-labelled cases still publish them |

**The complete suite is not all green and the all-V226-tests target is not met.**
No existing assertion was edited, skipped or conditionally bypassed. This local
commit is for independent review, not a claim that the project is freeze-ready.

Runtime: Windows, Python 3.12.14 with the existing isolated pinned environment;
Node 24.22.1, Playwright 1.62.1, axe 4.14.0. No new Linux execution or live Groq
verification is claimed. Existing/new automated transports are mocked.

## PDFs, protected code and review packages

The unchanged `review/generate_mock_pdfs.py` regenerates the 16 Founder + four
Investment matrix. All 114 rendered pages have identical PNG hashes to the
previously visually reviewed V226 matrix. Representative current native and
mixed-language Founder/Investment contact sheets were inspected again; extraction
reports no black-square or replacement glyphs. PDF code, fonts, finance and
receipt code are unchanged. The normal Proof progression and signed export tests
are included in the existing suites, not replaced by screenshots alone.

CORE contains the complete committed source, all original/new tests and fixtures,
pins/fonts/assets, the targeted V226 patch and full patch history from V223.
PDFS contains the fresh originals, 114 page renders/text checks and contact sheets.
QA contains exact logs (including failures), full survivor tables, retention,
outage/false-positive evidence, protected-code hashes and selected screenshots.
All paths inside ZIPs are relative, text is LF, and each archive has a member
manifest, CRC check and external SHA-256. No secret/environment, node_modules,
private output or academic report is included.

To reproduce from extracted CORE, work in `source/`, follow `review/README.md`
for dependency setup, then run:

```bash
unset GROQ_API_KEY
python -m unittest discover -v
python -m unittest test_v227 -v
python review/reproduce_v227_acceptance.py
python review/reproduce_v226_acceptance.py
npm run test:browser
python review/generate_mock_pdfs.py --output outputs/v227-pdf-matrix
```

The full Python suite is expected to expose the unchanged legacy outage-contract
conflict described above. Do not silently edit that test or describe the run as
all green. Resolve the intended safe noun-summary behavior before freeze.
