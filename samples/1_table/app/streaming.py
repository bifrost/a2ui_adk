"""Transport mapping from ADK events to app-level SSE frames."""
import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from .a2ui import table_messages, validate_a2ui
from .data import INVOICES


def sse(kind: str, data: Any) -> str:
    return f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def mock_stream(message: str) -> AsyncIterator[tuple[str, Any]]:
    """Fully offline deterministic mode, useful for seeing actual streaming."""
    show_table = any(word in message.casefold() for word in ("invoice", "faktura", "table", "tabel"))
    content = ("Her er de seneste fakturaer. " if show_table else
               "Dette er en **streamet Markdown-besked** fra demoagenten. ")
    content += "Teksten sendes i mindre dele, uden at vente på A2UI."
    for chunk in content.split(" "):
        yield "text_delta", {"text": chunk + " "}
        await asyncio.sleep(0.045)
    if show_table:
        for item in table_messages(INVOICES):
            validate_a2ui(item)
            yield "a2ui", item
            await asyncio.sleep(0.06)


class AdkStream:
    """ADK Runner with per-session history and streamed text chunks.

    Final aggregated ADK responses are skipped after partial chunks to avoid
    duplicate text. Tool responses are taken from the SDK's function events.
    """
    def __init__(self) -> None:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from .agent import root_agent
        self.sessions = InMemorySessionService()
        self.runner = Runner(agent=root_agent, app_name="a2ui_demo", session_service=self.sessions)
        self.lock = asyncio.Lock()

    async def stream(self, message: str, session_id: str) -> AsyncIterator[tuple[str, Any]]:
        from google.adk.agents.run_config import RunConfig, StreamingMode
        from google.genai import types

        async with self.lock:
            if not await self.sessions.get_session(app_name="a2ui_demo", user_id="demo", session_id=session_id):
                await self.sessions.create_session(app_name="a2ui_demo", user_id="demo", session_id=session_id)

        streamed = False
        sent_text = False
        break_pending = False
        surfaces: list[dict[str, Any]] = []
        seen_tables: set[str] = set()
        try:
            async for event in self.runner.run_async(
                user_id="demo", session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text=message)]),
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            ):
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

                # Use authoritative structured tool response instead of trying to
                # deserialize a potentially partial model-generated UI payload.
                for tool_response in event.get_function_responses() or []:
                    if tool_response.name == "get_invoices":
                        invoices = (tool_response.response or {}).get("invoices")
                        key = json.dumps(invoices, sort_keys=True, default=str)
                        if isinstance(invoices, list) and key not in seen_tables:
                            seen_tables.add(key)
                            for item in table_messages(invoices):
                                validate_a2ui(item)
                                surfaces.append(item)
        except Exception:
            # Keep the surfaces already built; the caller still reports the failure.
            for item in surfaces:
                yield "a2ui", item
            raise

        # Surfaces are flushed after the text so the reply streams first.
        for item in surfaces:
            yield "a2ui", item


_adk: AdkStream | None = None


async def stream_reply(message: str, session_id: str) -> AsyncIterator[str]:
    global _adk
    yield sse("start", {"session_id": session_id})
    try:
        if os.getenv("DEMO_MODE", "mock").casefold() == "mock":
            stream = mock_stream(message)
        else:
            if _adk is None:
                _adk = AdkStream()
            stream = _adk.stream(message, session_id)
        async for kind, payload in stream:
            yield sse(kind, payload)
        yield sse("done", {})
    except Exception as exc:
        logging.getLogger(__name__).exception("Streaming failure: %s", type(exc).__name__)
        # Avoid leaking tracebacks or internal credentials to the browser.
        yield sse("error", {"message": "Agent request failed. Check server logs/configuration."})
        yield sse("done", {"failed": True})
