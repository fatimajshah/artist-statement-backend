# Verification record

Verified locally on September 26, 2026. Nothing was deployed or pushed.

## Initial build checks

- All 10 `unittest` backend tests on Python 3.12: success with a mocked OpenAI
  response; input validation; 5,000/5,001-character limits; malformed JSON and body
  limits; missing credentials; provider timeout/connection/HTTP failures; invalid
  output; refusal/incomplete output; allowed/disallowed browser origins.
- JavaScript syntax check with `node --check`.
- Browser interaction with the actual portfolio page served on localhost: empty
  and oversized validation; disabled button and loading message; three labeled
  suggestions; button recovery; unreachable-backend error; real backend HTTP 503
  configuration error displayed clearly.
- Browser success used the real Flask handler with only the outbound provider
  call mocked by a temporary harness outside the deliverables. A literal `<b>`
  string in mocked feedback remained visible text rather than HTML formatting.
  The mock server was stopped after testing; no demo mode was added to the app.
- Gunicorn starts the delivered app; HTTP GET `/` returns the expected JSON.
- Homepage compared to a pre-edit copy: exactly one card added, all other content
  unchanged. The delivered frontend copy matches the integrated page.
- Existing staged portfolio edits were preserved. No Git initialization, staging,
  commits, pushes, or repository creation was performed.

## Still required

- Real OpenAI success/feedback-quality testing with your locally configured key.
  At initial verification, no successful real feedback request had been verified. Mock tests cannot verify account billing,
  model access, generated suggestion quality, or resistance to prompt injection.
- Public repository creation, Render deployment, and live GitHub Pages/CORS tests.
- Video, view permissions, and assignment form submission.

The system Python 3.9 produced a LibreSSL compatibility warning from urllib3, so
verification was repeated successfully with the installed Python 3.12 runtime.
The README uses Python 3.12 for this reason.

## Subsequent live diagnostic

Real requests were made after local key entry. The original inherited key failed
with 401 `invalid_api_key`. Explicit local `.env` precedence fixed key selection
(verified with a boolean equality check only). The local key then received 429
`credit_balance_exhausted` / `insufficient_quota`. At that diagnostic, live successful suggestions
were blocked by API credits (subsequently resolved, as recorded below). All 11 offline tests pass after error handling
updates. Model remains `gpt-4o-mini`; no request-format change was needed based
on the observed errors. Secrets, headers, and statement text were not logged.

## Backend publication preparation

The intended publication set is the ten files listed in README.md. A temporary
Git metadata directory was used to evaluate the actual backend ignore rules;
no backend repository was initialized or staged. `.env`, `.venv/`, caches, and
other ignored files are excluded; `.env.example` contains placeholders only.
Only intended files were scanned for common credential patterns; no matches
were found. This scan is a check, not a guarantee about future edits.
No portfolio files were changed, and no commit, push, or deployment was made.

## Real feedback specificity checks

Subsequent real requests succeeded for two synthetic examples: ceramic sculptures
about family memory and interactive installations using motion sensors. No
private artist statements or credentials were recorded. A temporary diagnostic
asserted the outbound OpenAI user input exactly matched each submitted example;
both provider responses were HTTP 200. Baseline feedback differed in content but
repeated generic requests for examples and introductory structure.

The prompt was revised to require evidence in every category, acknowledge
strengths, and respect existing sequencing. An intermediate real response
suggested moving a question to its existing final position, so the prompt was
further clarified to check first/last sentences. Final browser submissions for
both examples returned three real suggestions: ceramics feedback referenced
lace, gaps, and the process-to-emotion transition; sensor feedback referenced
shifting light, types of movement, and the transition to the shared-space question.
Sequential browser submissions replaced previous results and re-enabled the
button. No fallback/mock was used. Frontend source was unchanged. All 11 existing
backend tests passed during this investigation. The backend was restarted with
the revised prompt; nothing was committed, pushed, or deployed.

## Insufficient-input fix and real API verification

Reproduced exact input `hi` with the old prompt. An assertion verified the outbound
user input was exactly `hi`; the real provider returned invented references to
internal struggles and personal experiences. No stale/sample input, mock, cache,
or fallback was involved. The old schema forced three suggestions even for text
that did not describe artwork.

After adding the internal relevance flag and nullable category fields, all five
real provider calls returned HTTP 200; the backend mapped them as follows:

| Synthetic case | Backend outcome |
| --- | --- |
| `hi` | 422 insufficient_input, no suggestions |
| Grocery-store closing-time question | 422 insufficient_input, no suggestions |
| `I draw trees.` | 200, three suggestions asking for missing details |
| Ceramic sculptures / family memory | 200, three suggestions grounded in lace, traces, and process/emotion |
| Motion-sensor installations | 200, three suggestions grounded in movement, light, participation, and sequence |

Exact forwarding was asserted for each case without printing request text or
secrets. Browser testing then submitted a short valid statement followed by `hi`:
three results were replaced by the clear insufficient-input message; old content
was cleared and hidden, and the submit button recovered. All 14 offline tests
passed; JavaScript syntax passed. Servers were restarted. No commit, push, or
deployment was performed. These finite tests do not guarantee all model outputs.
