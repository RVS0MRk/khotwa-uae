# V2.1 security and rendering review

## Browser trust boundaries

The Round 2 review covered the remaining legacy template sinks, not just the new Investment UI. Empty `innerHTML` assignments became `replaceChildren`. The opportunity-map sink accepted selected market/context from restored state; it now uses DOM text nodes throughout. The WhatsApp QR fallback is also a DOM-created link using a fixed HTTPS origin and encoded text.

Retained legacy markup templates in `static/app.js` are grouped below. In `showPlan`, the rendering object `p` is the recursively escaped copy from `escapePlan(rawPlan)`. It must never be replaced with raw model or stored content in these templates.

| Sink group | Input boundary |
|---|---|
| Overview rows, test/check/question lists, seven-day cards | Escaped `p` fields and application-owned translations; raw founder identity rows use textContent |
| Readiness/report rows, passport | Escaped `p`, explicitly escaped idea/evidence, fixed labels, numeric formatting and computed score |
| Steps, tip, decision, avoid/instead lists | Escaped `p`; risk CSS classes selected from a fixed enum |
| Personas, risk cards, pitches | Escaped `p`; pitch IDs/labels selected from fixed definitions; no model-controlled URL or event attribute |
| Proof table | Fixed translations, fixed row numbers and constant input markup; edited notes never enter these templates |
| Proof statistics | Counts and average derived from validated numeric controls; fixed translations |

New financial, funding, scoring, readiness, Advisor and restored input controls render with textContent/DOM APIs. Advisor context allowlists numeric evidence, excluding customer free-text concerns and frequency notes. Recovery stores browser-tab business state and safe numeric/category progress; customer notes, Advisor chat and optional investor draft notes remain excluded. New Idea resets prior investment/validation state; Clear removes saved validation entries. There is no shared visitor database.

PDF text is escaped and reshaped; financial output is recomputed server-side. CSV quotes fields and prefixes possible formula cells. Currency-direction controls are removed from financial CSV display cells. The tests exercise harmless HTML payloads, malformed state, tampered export results and hostile CSV input. This is a focused application review, not a guarantee against every possible XSS or supply-chain issue.

## CSP and HTTPS

CSP now separates `style-src-elem 'self'` from `style-src-attr 'unsafe-inline'`. Stylesheets and scripts must be same-origin; arbitrary inline style elements remain blocked. All static inline template styles were moved to named CSS classes. Style attributes remain necessary for computed chart widths, Chart.js canvas sizing, QRCode, progress indicators and existing scripted visibility. No script-inline allowance was introduced. Browser suites record CSP violations and require none on tested paths.

Render's [web-service documentation](https://render.com/docs/web-services) says TLS terminates at its load balancer and requests are forwarded to the application over HTTP, with inbound HTTP redirected to HTTPS. That does not establish whether the live service currently emits HSTS. The application now emits HSTS on secure requests and when the configured `RENDER=true` environment is present, so the header can reach the HTTPS visitor through that edge. It does not trust arbitrary client `X-Forwarded-Proto`. Browsers ignore HSTS over localhost HTTP. No includeSubDomains/preload commitment is added. Actual public edge headers still require a release check; Render was not modified or tested live.

## Rate limiter and memory

Supported Gunicorn configuration remains one worker, two threads. The in-memory window is shared between threads under a lock: 30 requests per client and 150 globally per 10 minutes for guarded generation/export endpoints in Render mode, excluding the cheap `/finance` arithmetic route. Retry-After is returned. Forwarded client selection uses the rightmost validated address, not a spoofable leading entry. Windows/local fixture mode does not throttle normal browser tests.

Each worker/process or replica has its own store and PDF lock. Two workers can therefore allow up to twice those aggregate limits, without a hard globally shared cap; process restarts reset counters. `test_v21_security.py` tests independent stores explicitly, alongside existing same-worker, spoofed-IP and request-boundary tests. Add a shared limiter before increasing workers/replicas. The current bounded limiter is an essential guard, not comprehensive abuse protection.

PDF generation remains serialized within the supported worker. Matplotlib/font/report generation may use substantial memory and latency on a free service. No Linux Gunicorn memory profile, cold-start test or real Render load test was performed. Public release still needs a controlled HTTPS/phone/PDF smoke check. No customer records or live model requests were used. Corrected mock suites inject a synthetic key before application import and guard against local credential-file fallback.
