import json
from fastapi.testclient import TestClient
from backend.app import app, sse

client = TestClient(app)

def run(text):
    body = {'threadId': 't', 'runId': 'r', 'messages': [{'id': '1', 'role': 'user', 'content': text}]}
    r = client.post('/mock-agent', json=body)
    return [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith('data: ')]

def test_mock_sse():
    assert '"RUN_STARTED"' in sse({'type': 'RUN_STARTED'})

def test_event_order_and_tool_call():
    types = [e['type'] for e in run('Vis mine fakturaer')]
    assert types[0] == 'RUN_STARTED' and types[-1] == 'RUN_FINISHED'
    assert types.index('TEXT_MESSAGE_END') < types.index('TOOL_CALL_START') < types.index('TOOL_CALL_END')
    args = next(e for e in run('Vis mine fakturaer') if e['type'] == 'TOOL_CALL_ARGS')
    assert json.loads(args['delta']) == {'kind': 'table'}

def test_keyword_routing():
    kinds = {q: [json.loads(e['delta']) for e in run(q) if e['type'] == 'TOOL_CALL_ARGS'] for q in ('Vis faktura trend', 'Fakturaoverblik', 'Vis omsætning som graf', 'Vis mit KPI-overblik', 'Hej')}
    assert kinds['Vis faktura trend'] == [{'kind': 'table'}]
    assert kinds['Fakturaoverblik'] == [{'kind': 'table'}]
    assert kinds['Vis omsætning som graf'] == [{'kind': 'chart'}]
    assert kinds['Vis mit KPI-overblik'] == [{'kind': 'card'}]
    assert kinds['Hej'] == []

def test_agent_disabled_in_mock_mode():
    assert client.post('/agent', json={}).status_code == 503

def test_keywords_match_word_starts_only():
    assert [e for e in run('discard it') if e['type'] == 'TOOL_CALL_ARGS'] == []
    assert [e for e in run('comfortable') if e['type'] == 'TOOL_CALL_ARGS'] == []
