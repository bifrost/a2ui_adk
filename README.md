# a2ui_adk

Three small demos of Google ADK agents that answer with Markdown text plus A2UI v1.0 UI components. All data is synthetic. Run one at a time.

| Sample | Shows | Transport |
|---|---|---|
| [1_table](samples/1_table) | A2UI v1.0 with a single `Table` component | own SSE, plain HTML/JS |
| [2_components](samples/2_components) | Agent picks `Table`, `Card` or `Chart` | own SSE, plain HTML/JS |
| [3_agui_react](samples/3_agui_react) | Same components over AG-UI via `ag_ui_adk` | AG-UI, React frontend |

## Setup

```bash
uv sync   # one shared environment (pyproject.toml) for all three samples
cp .env.example .env   # DEMO_MODE=mock works without a key; set DEMO_MODE=adk + GOOGLE_API_KEY for Gemini
```

## Run

Samples 1 and 2 (open http://localhost:8000):
```bash
uv run uvicorn app.server:app --reload --app-dir samples/1_table
uv run uvicorn app.server:app --reload --app-dir samples/2_components
```

Sample 3 (backend on :8000, frontend on http://127.0.0.1:5173):
```bash
uv run uvicorn backend.app:app --reload --app-dir samples/3_agui_react
npm --prefix samples/3_agui_react/frontend install
npm --prefix samples/3_agui_react/frontend run dev   # in a second terminal
```

## Tests

```bash
for s in samples/*/; do (cd "$s" && uv run python -m pytest -q tests); done
```

The sample READMEs describe each demo in more detail; run their commands from inside the sample folder.
