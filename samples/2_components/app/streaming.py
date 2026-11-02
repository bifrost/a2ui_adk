"""Live ADK SSE -> app SSE adapter. Text deltas and validated UI envelopes."""
import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any
from .a2ui import component_messages, validate_a2ui

LOG = logging.getLogger(__name__)

def sse(kind: str, data: Any) -> str:
    return f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def mock_selection(message: str) -> tuple[str, str, str] | None:
    """Only offline mode uses keyword rules; live ADK chooses the component."""
    t = message.casefold()
    if any(k in t for k in ("chart", "graf", "revenue", "omsætning", "trend")):
        return "chart", "revenue", "Monthly revenue"
    if any(k in t for k in ("card", "kort", "summary", "overblik", "kpi")):
        return "card", "invoices", "Invoice summary"
    if any(k in t for k in ("invoice", "faktura", "table", "tabel")):
        return "table", "invoices", "Recent invoices"
    return None

async def mock_stream(message: str) -> AsyncIterator[tuple[str, Any]]:
    selection = mock_selection(message)
    lead = "Her er et syntetisk eksempel. " if selection else "**Hej!** Jeg kan vise tabeller, kort og grafer. "
    for word in lead.split(' '):
        yield "text_delta", {"text": word + " "}
        await asyncio.sleep(.015)
    if selection:
        for envelope in component_messages(*selection):
            validate_a2ui(envelope)
            yield "a2ui", envelope
            await asyncio.sleep(.06)
    yield "text_delta", {"text": "\n\nDu kan bede om et andet format."}


class AdkStream:
    def __init__(self):
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from .agent import root_agent
        self.sessions = InMemorySessionService()
        self.runner = Runner(agent=root_agent, app_name="a2ui_components_demo", session_service=self.sessions)
        self._lock = asyncio.Lock()

    async def stream(self, message: str, session_id: str) -> AsyncIterator[tuple[str, Any]]:
        from google.adk.agents.run_config import RunConfig, StreamingMode
        from google.genai import types
        async with self._lock:
            if not await self.sessions.get_session(app_name="a2ui_components_demo", user_id="demo", session_id=session_id):
                await self.sessions.create_session(app_name="a2ui_components_demo", user_id="demo", session_id=session_id)
        streamed = False
        sent_text = False
        break_pending = False
        emitted_ui = set()
        async for event in self.runner.run_async(
            user_id="demo", session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=message)]),
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        ):
            # The ADK may emit a final aggregate after partial text chunks; skip it,
            # and separate text that resumes after a tool call with a paragraph break.
            if event.content and event.content.parts:
                texts = [p.text for p in event.content.parts if p.text and not p.thought and not p.function_call and not p.function_response]
                if texts:
                    text = "".join(texts)
                    if event.partial or not streamed:
                        if break_pending and sent_text:
                            text = "\n\n" + text
                        break_pending = False
                        sent_text = True
                        yield "text_delta", {"text": text}
                    streamed = bool(event.partial)
                if any(p.function_call or p.function_response for p in event.content.parts):
                    break_pending = True
            for response in event.get_function_responses() or []:
                if response.name != "show_ui": continue
                selection = response.response or {}
                if not selection.get("accepted"): continue
                key = (selection.get("kind"), selection.get("dataset"), selection.get("title"))
                if key in emitted_ui: continue
                emitted_ui.add(key)
                for envelope in component_messages(*key):
                    validate_a2ui(envelope)
                    yield "a2ui", envelope

_adk = None
async def stream_reply(message: str, session_id: str) -> AsyncIterator[str]:
    global _adk
    yield sse("start", {"session_id": session_id})
    try:
        if os.getenv("DEMO_MODE", "mock").lower() == "mock":
            stream = mock_stream(message)
        else:
            if _adk is None: _adk = AdkStream()
            stream = _adk.stream(message, session_id)
        async for kind, data in stream: yield sse(kind, data)
        yield sse("done", {})
    except Exception:
        LOG.exception("Agent streaming failed")
        yield sse("error", {"message": "Request failed. Check backend logs."})
        yield sse("done", {"failed": True})
