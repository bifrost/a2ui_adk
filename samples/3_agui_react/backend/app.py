"""Official AG-UI ADK adapter for the live agent; mock endpoint for no-key testing."""
import asyncio
import json
import os
import re
import unicodedata
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

load_dotenv()
DEMO_MODE = os.getenv('DEMO_MODE', 'mock').strip().lower()
# Checked in order; keywords match at word starts so compounds like 'fakturaoverblik' still hit.
MOCK_KEYWORDS = (('table', ('faktura','invoice','tabel','table')), ('chart', ('chart','graf','omsætning','trend')), ('card', ('kpi','kort','overblik','card')))

app = FastAPI(title='AG-UI + A2UI v1 demo')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_methods=['*'], allow_headers=['*'])

if DEMO_MODE == 'adk':
    from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
    try:
        from .agent import root_agent  # uvicorn backend.app:app, from the sample folder
    except ImportError:
        from agent import root_agent  # uvicorn app:app, from backend/
    adapter = ADKAgent(adk_agent=root_agent, app_name='accounting_demo', user_id='demo_user', use_in_memory_services=True)
    add_adk_fastapi_endpoint(app, adapter, path='/agent')
else:
    @app.post('/agent')
    def agent_disabled():
        return JSONResponse({'detail': 'Gemini ADK is disabled. Start the server with DEMO_MODE=adk and GOOGLE_API_KEY set.'}, status_code=503)

class RunInput(BaseModel):
    threadId: str = 'demo'
    runId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[dict] = Field(default_factory=list)
    state: dict = Field(default_factory=dict)
    tools: list = Field(default_factory=list)
    context: list = Field(default_factory=list)
    forwardedProps: dict = Field(default_factory=dict)

def sse(event):
    return 'data: ' + json.dumps(event, ensure_ascii=False) + '\n\n'

@app.get('/health')
def health():
    return {'mode': DEMO_MODE, 'status': 'ok'}

@app.post('/mock-agent')
async def mock_agent(req: RunInput):
    content = req.messages[-1].get('content') if req.messages else ''
    if isinstance(content, list):
        content = ' '.join(p.get('text', '') for p in content if isinstance(p, dict))
    q = unicodedata.normalize('NFC', str(content or '')).lower()
    kind = next((k for k, words in MOCK_KEYWORDS if any(re.search(r'\b' + re.escape(w), q) for w in words)), None)
    mid = str(uuid.uuid4())
    async def events():
        try:
            yield sse({'type':'RUN_STARTED','threadId':req.threadId,'runId':req.runId})
            yield sse({'type':'TEXT_MESSAGE_START','messageId':mid,'role':'assistant'})
            sentence = ('Her er **syntetiske eksempeldata**. ' if kind else 'Hej! Jeg kan vise fakturaer, KPI-kort eller en omsætningsgraf. ')
            for fragment in sentence.split():
                yield sse({'type':'TEXT_MESSAGE_CONTENT','messageId':mid,'delta':fragment+' '})
                await asyncio.sleep(0.015)
            yield sse({'type':'TEXT_MESSAGE_END','messageId':mid})
            if kind:
                tid = str(uuid.uuid4())
                yield sse({'type':'TOOL_CALL_START','toolCallId':tid,'toolCallName':'show_ui','parentMessageId':mid})
                yield sse({'type':'TOOL_CALL_ARGS','toolCallId':tid,'delta':json.dumps({'kind':kind})})
                yield sse({'type':'TOOL_CALL_END','toolCallId':tid})
                yield sse({'type':'TOOL_CALL_RESULT','toolCallId':tid,'messageId':str(uuid.uuid4()),'content':json.dumps({'kind':kind,'status':'ready'})})
            yield sse({'type':'RUN_FINISHED','threadId':req.threadId,'runId':req.runId})
        except Exception as e:
            yield sse({'type':'RUN_ERROR','message':str(e) or 'Mock agent failed'})
    return StreamingResponse(events(), media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
