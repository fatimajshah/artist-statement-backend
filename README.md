# Artist Statement Feedback

A small Flask backend for a CMU Effective Coding with AI assignment. It sends one
artist statement to OpenAI and returns three suggestions: **clarity, specificity,
and structure**. Greetings or unrelated text receive an insufficient-input message.
No accounts, database, uploads, conversation history, or statement storage.

## Frontend → backend → OpenAI

The separate plain HTML/CSS/JavaScript portfolio page reads the current textarea
and uses `fetch()` to POST JSON to this backend. Only Flask uses the private API
key. The page displays the latest suggestions with `textContent`, never untrusted
HTML, and clears previous results when a new request starts.

The prompt requires observations grounded in submitted text, preserves voice,
asks about missing information, and treats the statement as content rather than
instructions. A single structured response assesses whether it describes artwork
and supplies feedback only when appropriate. There is no minimum word count;
short meaningful statements work. Model judgments still need human review.

## API

**GET `/`** — HTTP 200 liveness check (does not verify credentials):

```json
{"status":"ok","service":"Artist Statement Feedback"}
```

**POST `/feedback`** — requires `Content-Type: application/json` and a `statement`
string, nonblank and at most 5,000 characters. Request bodies are limited to 64 KiB.

Request:

```json
{"statement":"I draw trees."}
```

HTTP 200 response (illustrative):

```json
{"feedback":{"clarity":"Consider explaining what draws you to trees.","specificity":"Could you describe one detail you notice when drawing a tree?","structure":"Your short opening is direct; optionally follow it with why this subject matters to you."}}
```

Insufficient artistic content returns HTTP 422, without a feedback object:

```json
{"code":"insufficient_input","error":"Please enter an artist statement describing your work so I can give meaningful feedback."}
```

Other errors use `{"error":"Helpful message"}`:

| HTTP status | Meaning |
| --- | --- |
| 400 | Missing/non-string/blank/oversized statement or malformed JSON |
| 413 | Body exceeds 64 KiB |
| 415 | Content type is not JSON |
| 422 | Insufficient artistic content or model refusal |
| 502 | Provider failure or invalid/incomplete response |
| 503 | Missing/rejected credentials or provider quota/billing action needed |
| 504 | Provider timeout |

The provider connection/read timeouts are 5/30 seconds, with no automatic retries.
Responses have `Cache-Control: no-store`. Errors never include raw provider details.

## Local setup

Use Python 3.12. From this backend folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

Edit `.env` privately: set your API key, `OPENAI_MODEL=gpt-4o-mini`, and
`ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,https://fatimajshah.github.io`.
Then run:

```sh
python app.py
```

Backend: `http://127.0.0.1:5001`. In another Terminal, from the **separate portfolio
root**, run `python3 -m http.server 8000 --bind 127.0.0.1`. Open
`http://localhost:8000/statement-feedback/`. Set the portfolio's
`statement-feedback/config.js` to `window.FEEDBACK_API_URL = "http://127.0.0.1:5001";`.
Use HTTP, not a `file://` page. Restart Flask after changing environment settings.

## Configuration and secrets

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Required; private backend credential |
| `OPENAI_MODEL` | Defaults to `gpt-4o-mini`; must support Responses structured outputs |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins; defaults to local port 8000 and `https://fatimajshah.github.io` |
| `PORT` | Supplied by Render for Gunicorn |

Local `.env` beside `app.py` overrides inherited shell variables. Do not deploy
that file: Render should use its Environment settings. `.env.example` contains
placeholders only; `.gitignore` excludes secrets, virtual environments, and caches.
Never commit credentials or place them in frontend code, recordings, or chat.

Statements are not saved or logged by the app. They are sent to OpenAI with
`store: false`; provider retention policies still apply. CORS restricts browser
origins, not all clients or API spending. Monitor account usage for this public API.

## Testing and troubleshooting

```sh
python -m unittest -v test_app.py
curl -i http://127.0.0.1:5001/
curl -i http://127.0.0.1:5001/feedback -H 'Content-Type: application/json' -d '{"statement":"I draw trees."}'
curl -i http://127.0.0.1:5001/feedback -H 'Content-Type: application/json' -d '{"statement":" "}'
python -c 'import json; print(json.dumps({"statement":"x"*5001}))' | curl -i http://127.0.0.1:5001/feedback -H 'Content-Type: application/json' --data-binary @-
```

Expect 200 for status and valid feedback, and 400 for blank/oversized input.
The 14 offline tests mock OpenAI and cover validation, provider failures/timeouts,
quota errors, malformed responses, short statements, insufficient input, and CORS.
Real tests verified `hi` and unrelated text return 422, while `I draw trees.` and
two different full statements return three suggestions. Browser checks verified
latest-result replacement and clearing results after insufficient input.
See [VERIFICATION.md](VERIFICATION.md) for the detailed record.

An inherited invalid key originally caused HTTP 401; explicit local `.env`
precedence fixed it. A subsequent `credit_balance_exhausted` error required account
credits. Later real tests succeeded. Repetitive/fabricated feedback prompted
stronger grounding instructions and an insufficient-input response path. These
checks do not guarantee every future model judgment.

## Publication and hosting (not performed)

Keep this backend in its own **public GitHub repository**, separate from
`fatimajshah/113-Portfolio-`. Publish only these ten files:

```text
.env.example       .gitignore          .python-version
app.py             requirements.txt    test_app.py
README.md          prompt_log.md       VERIFICATION.md
SUBMISSION_CHECKLIST.md
```

Connect the new repository to a Render **Web Service**:

| Setting | Value |
| --- | --- |
| Runtime / branch | Python 3 / `main` |
| Root directory | Blank (backend files at repo root) |
| Build | `pip install -r requirements.txt` |
| Start | `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 60` |
| Health check | `/` |

`.python-version` selects Python 3.12; leave `PYTHON_VERSION` unset. Set
`OPENAI_API_KEY` privately, `OPENAI_MODEL=gpt-4o-mini`, and `ALLOWED_ORIGINS` to
`https://fatimajshah.github.io,http://localhost:8000,http://127.0.0.1:8000`.
Do not upload `.env`.

Later, set the portfolio's `config.js` to the actual Render HTTPS base URL without
`/feedback`. Publish through the portfolio's existing GitHub Pages setup. CORS
uses the origin only (no repository path or trailing slash); add any custom-domain
origin if applicable. Restore the localhost URL for local development. Verify
live POST requests as well as the health check before submitting.

See [prompt_log.md](prompt_log.md) for the actual development history and
[SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for required URLs, public
repositories, video/view permissions, and the assignment form.

References: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[Render Flask](https://render.com/docs/deploy-flask),
[Render Python versions](https://render.com/docs/python-version).
