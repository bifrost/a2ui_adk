# Python ADK + A2UI v1.0 (Candidate) — full-stack demo

A runnable FastAPI + Server-Sent Events + browser demo. It streams **Markdown text** and sends **A2UI v1.0 protocol envelopes** containing a custom `Table` component. The browser renders A2UI messages progressively.

## Run (Python 3.11+)

```bash
uv sync   # installs from the repo-root pyproject.toml
cp .env.example .env               # Optional; default is offline/mock
uv run uvicorn app.server:app --reload
```

Visit **http://localhost:8000** and type `Vis mine seneste fakturaer`. Try `Hej` for text-only mode.

Run tests:

```bash
uv run python -m pytest -q
```

## Real ADK mode

By default `DEMO_MODE=mock` requires no Google credentials. To run the real Google ADK agent:

```bash
export DEMO_MODE=adk
export GOOGLE_API_KEY='your-api-key'
export ADK_MODEL='gemini-2.5-flash'
uv run uvicorn app.server:app --reload
```

Or configure `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and application-default credentials. No credentials are committed to the archive.

**ADK works as follows:** `get_invoices` returns structured synthetic data, ADK event text chunks are forwarded as `text_delta`, and the backend converts the tool response into ordered A2UI messages. This is an explicit **deterministic A2UI adapter**, not an LLM generating arbitrary A2UI schema. It is more reliable for accounting data. The agent decides when to call the tool.

## Example SSE transport

```
event: start
data: {"session_id":"..."}

event: text_delta
data: {"text":"Her er "}

event: a2ui
data: {"version":"v1.0","createSurface":{...}}

event: a2ui
data: {"version":"v1.0","updateComponents":{...}}

event: a2ui
data: {"version":"v1.0","updateDataModel":{...}}

event: done
data: {}
```

`text_delta` / `start` / `done` are **application SSE events**, not A2UI messages. The contents of `a2ui` frames are A2UI v1.0 envelopes. The protocol itself is transport-neutral.

## Files

- `app/agent.py` — real Python ADK agent and UI-related prompt
- `app/data.py` — synthetic invoice tool/data
- `app/a2ui.py` — A2UI v1.0 envelopes and limited validation for versioned custom Table catalog
- `app/streaming.py` — mock and real ADK event adapter, SSE
- `app/server.py` — FastAPI service
- `client/index.html`, `client/client.js` — zero-build UI, A2UI subset renderer and Markdown streaming
- `tests/` — protocol and stream tests

## Scope / limitations

- **A2UI v1.0 is Candidate.** This demo intentionally implements the documented v1.0 message envelopes and a simple custom component contract; it does **not** claim to embed the official complete Python A2UI SDK or official frontend renderer. Its browser renderer is a narrow reference implementation for `Column`, `Text`, and custom `Table` only. The catalog URI `https://example.org/catalogs/accounting/v1.json` is an identifier, **not a hosted real catalog**, and the contract in this example is shared by the server and browser. For production, publish a JSON Schema catalog and integrate a compatible official renderer, with negotiated version/catalog IDs.
- Markdown support is intentionally a safe, tiny subset (`**bold**`, inline code, linebreaks). Use a hardened Markdown library for production.
- ADK real-mode partial-event behavior is SDK/model dependent; run the integration against your pinned ADK version. This demo avoids duplicate text by preferring partial events; more complex multi-turn tool chains need additional deduplication tests.
- No auth, persistence, rate limiting, human approval, action handler, CSP, or production GDPR/PII controls. Mock data is wholly synthetic. Sessions are in-memory.
- All UI data uses DOM `textContent`, never `innerHTML`. In production restrict components and validate values against the **published** catalog schema.
- Streaming table is delivered as three complete v1.0 messages; a full model-output streaming parser is not implemented.

## Reference documentation

- https://github.com/a2ui-project/a2ui/blob/main/specification/v1_0/docs/a2ui_protocol.md
- https://github.com/google/adk-python
