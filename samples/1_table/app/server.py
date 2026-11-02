from pathlib import Path
from dotenv import load_dotenv
from uuid import uuid4
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
load_dotenv(Path(__file__).resolve().parents[3] / ".env")  # shared repo-root .env

from .streaming import stream_reply  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
app = FastAPI(title="ADK + A2UI v1.0 demo")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    session_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{16,64}$")

@app.get("/")
async def index():
    return FileResponse(BASE / "client" / "index.html")

@app.get("/client.js")
async def javascript():
    return FileResponse(BASE / "client" / "client.js", media_type="text/javascript")

@app.get("/shared/a2ui-renderer.js")
async def renderer():
    return FileResponse(BASE.parent / "shared" / "a2ui-renderer.js", media_type="text/javascript")

@app.get("/health")
async def health():
    return {"ok": True, "a2ui": "v1.0"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    sid = request.session_id or uuid4().hex
    return StreamingResponse(
        stream_reply(request.message, sid), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Session-Id": sid},
    )
