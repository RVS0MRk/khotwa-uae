# V2.2 security, privacy and operating limits

Baseline: `802149433729d58ebb191cb631c242a28dca914d`. This round is local only. No production settings, accounts, secrets or academic deliverables were changed.

## Independent request windows

In Render mode (`RENDER=true`), `protect_public_requests` applies these ten-minute rolling windows:

| Variable | Default | Scope |
|---|---:|---|
| `KHOTWA_AI_GLOBAL_PER_10MIN` | 400 | `/generate`, `/discover`, `/ask` combined across this process |
| `KHOTWA_AI_CLIENT_PER_10MIN` | 30 | The same AI routes, per validated client address |
| `KHOTWA_PDF_CLIENT_PER_10MIN` | 20 | `/pdf`, `/investment/pdf` combined per client, independently of AI |

`/finance` does not spend AI/PDF quota. All public POST routes retain the 256 KiB body limit and their existing field/collection checks. Invalid, nonpositive or over-100,000 configuration values use the defaults. HTTP 429 returns the stable JSON error code and an actual `Retry-After` delay; UI callers display a localized wait time.

These defaults accommodate a classroom demonstration; they are **not a provider spending budget or a production capacity guarantee**. An owner should choose lower limits where appropriate for the Groq account, shared classroom IPs, concurrent PDF memory and public exposure. Do not increase limits merely because they are configurable. Counters and the PDF lock are per process, reset on restart, and are not shared between workers/replicas. Keep the supported one-worker configuration; use a shared limiter before scaling. Existing spoofed-IP and multi-worker limitation tests are retained.

## Actual data flow and disclosures

- There are no accounts or a visitor database. Flask holds request plans and generated PDF bytes in memory, then returns them; it does not save reports or business plans to disk. Matplotlib may cache font metadata in the system temporary directory; this is not plan storage.
- Groq receives the business idea and founder answers for generation/discovery. Advisor requests include a bounded allowlist of relevant plan context, financial assumptions and numeric user-recorded evidence, the question and recent chat. Customer frequency, concerns and respondent notes are excluded from Advisor context. Groq's own retention/processing policies apply; Khotwa makes no compliance or provider-retention claim.
- Tab recovery uses `sessionStorage`: business/form state, bilingual plan variants, selected panels, numeric/category Proof progress, finance/scenarios/allocations/checklists and the three optional investor notes. It excludes Advisor chat and free-text respondent frequency, concern and Note fields. Clear removes saved validation entries and investor notes; New idea resets the old business. A heuristic rejects recovery snapshots containing recognizable email/phone/credential patterns; this cannot identify every kind of personal or confidential text. Visitors are told not to enter it.
- Closing a tab normally ends session storage, but browsers can restore sessions. The UI explicitly says this and offers New idea; it does not promise guaranteed deletion upon browser closure. Different browser contexts/tabs with no opener are tested independently; browser tab duplication can copy a session according to browser behavior.
- An anonymous HttpOnly, SameSite=Lax session cookie binds server-issued Advisor HMAC signatures. It is Secure over HTTPS and in Render mode. It contains no business text. A random process key signs the canonical response. Unsigned, changed and other-session assistant turns are discarded; valid history is capped at eight turns/1,200 characters. A restart invalidates old signatures. User turns remain untrusted data, not instructions or evidence.
- Access/error logs and temporary rate counters remain. Application code does not log POST bodies, plans, chat, reasoning or keys. Groq errors are redacted and bounded, with status/finish reason/empty-content diagnostics. Hosting infrastructure may have its own access logs. Sharing opens an encoded message on WhatsApp only at the user's request.

The bilingual notices under the submit buttons/Advisor and the footer Privacy & data dialog describe these boundaries. Do not infer anonymity, sensitive-data suitability or a legal privacy certification from the absence of accounts.

## Rendering and content trust

Model final `message.content` is JSON parsed server-side; reasoning is neither requested nor used. GPT-OSS settings remain low reasoning effort, `include_reasoning=false`, JSON mode and 1,200/2,500/5,000 completion tokens for Advisor/discovery/generation. Rich mocked fixtures do not justify reducing the full-plan token budget.

Sentence-level sanitization preserves useful neighboring content while removing unsupported evidence, asserted legal fees/requirements, unguarded payment/operation instructions and medical/return promises. Missing fields and unassessed scores remain explicit. These deterministic checks reduce specific known failure modes; they are not a semantic guarantee against every possible fabricated assertion. The model prompt and evidence provenance rules remain necessary.

Touched output templates now use DOM text nodes. The one untouched persona template receives only recursively escaped `p` data and fixed translations; `test_v22_engineering` guards that boundary. PDF text remains escaped, finance is recalculated, CSV cells are quoted/formula guarded, and the QR fallback uses a fixed WhatsApp origin. CSP, HSTS, input constraints and secret redaction were not weakened.

## Assets, dependency and release boundaries

Runtime pins were frozen from a new Python 3.12 virtual environment containing only the seven existing direct server requirements and their resolved dependencies. No new runtime package was introduced. The exact pinned set was checked with pip-audit; the review package records the result and tool version. Node/Playwright/axe, font subsetting, formatting, PDF inspection and pip-audit are development tools.

WOFF2 subsets are below 60 KB each; the original full TTF remains for server PDFs only. Static Jinja URLs carry content hashes; matching assets receive one-year immutable cache headers, while unversioned assets require revalidation. Charts load on first Plan use; QR and funding data wait until a business exists. No script/CSP bypass or third-party font/CDN was introduced.

[Render documents Brotli support](https://render.com/docs/web-services#additional-features) (checked 8 November 2026). This does not verify compression headers on this project's live service. No WSGI compression dependency was added: the measured cold local landing meets the transfer budget without compression, and adding another application buffering layer is unnecessary. Check `Content-Encoding`, cache headers, HTTPS, cold-start latency and PDF memory on the approved deployment later.

No live Groq, Linux Gunicorn/Render load test, physical-phone or screen-reader validation was performed in this round. Matplotlib/report generation can still be expensive on a free instance. PDF serialization and existing timeouts remain. See the V2.2 review matrix for precise executed evidence and unresolved verification limits.
