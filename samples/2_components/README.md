# Python ADK + A2UI v1.0: agent-selected components

End-to-end demo with **one** Google ADK agent, FastAPI, SSE, and a browser renderer for a restricted A2UI v1.0 custom component catalog (`Table`, `Card`, `Chart`). Text streams as Markdown-style deltas; UI appears as progressive A2UI messages. Data is **synthetic**.

## Run offline (no model credentials)

```bash
uv sync   # installs from the repo-root pyproject.toml
DEMO_MODE=mock uv run uvicorn app.server:app --reload
```

Visit http://localhost:8000 and try:
- `Vis mine fakturaer` → Table
- `Vis faktura KPI overblik` → Card
- `Vis omsætning graf` → Chart
- `Hej` → streamed text only

## Run with Google ADK

Set up Google credentials for the model chosen and run:

```bash
export DEMO_MODE=adk
export GOOGLE_API_KEY=your-key
export ADK_MODEL=gemini-2.5-flash
uv run uvicorn app.server:app --reload
```

For Vertex AI, configure `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`, and appropriate ADC credentials instead of `GOOGLE_API_KEY`.

**Live behavior:** the LLM calls `get_finance_data(dataset)` and chooses `show_ui(kind, dataset, title)` itself. The server only transforms a *validated successful UI tool result* into restricted A2UI v1.0 `createSurface`, `updateComponents`, `updateDataModel` messages. Unlike offline mode, there is no keyword-based UI selection. Non-UI responses stream normally. ADK's SSE partial-event and final-event behavior can vary with model and release; check duplication and ordering for your pinned ADK release before production.

## Architecture

```
Browser (fetch POST /api/chat; SSE parser)
  <- text_delta (ordinary text) and a2ui (A2UI protocol envelope)
FastAPI / app.streaming (validation, streaming)
  <- ADK runner event stream
Single ADK agent with two tools:
  get_finance_data(dataset) -- synthetic, allowlisted data
  show_ui(kind, dataset, title) -- model-driven presentation selection
A2UI v1.0 custom catalog: Column, Text, Table, Card, Chart
```

`app/a2ui.py` generates v1.0 envelopes with stable per-surface component IDs and `@path` data bindings. The browser uses a small **custom catalog renderer**, not the official A2UI frontend SDK. Catalog URL is an identifier only. These `Card`/`Chart` component properties are **application-defined** and not claimed to be built-in standard A2UI catalog shapes. This is a constrained demonstration of the protocol envelope and custom components, not comprehensive protocol conformance or a production frontend.

### Extending with new components

1. Add component to `APPROVED` and emitter in `app/a2ui.py`.
2. Add a renderer for it to `client/client.js` (no `innerHTML` for untrusted values).
3. Add its choice/description to `show_ui` and the ADK instruction.
4. Add a test for both component creation and input validation.

In production use a maintained A2UI v1 renderer and formal JSON Schema catalog; validate **all** message properties, authenticate the user and scope data tools to their tenant, authorize UI actions, and persist ADK sessions. A tool-result-driven adapter deliberately minimizes invented UI shapes but does not demonstrate unconstrained LLM-authored A2UI JSON.

## Tests

```bash
uv run python -m pytest -q
```

## Security / limitations

- Fake data only. In-memory sessions; no auth, no tenant isolation, no rate limiting.
- Chart uses simple CSS bars, no external charting dependencies.
- Minimal Markdown renderer supports inline bold/code only; not full Markdown.
- A2UI v1.0 specification remains a Candidate at the time of preparation.
- This demo is an integration pattern, not a tested production ADK/Vertex deployment.

Protocol reference: https://github.com/a2ui-project/a2ui/blob/main/specification/v1_0/docs/a2ui_protocol.md
