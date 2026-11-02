import asyncio
import json
import pytest
from app.a2ui import component_messages, validate_a2ui
from app.data import get_finance_data, show_ui
from app.streaming import mock_stream, mock_selection, sse

@pytest.mark.parametrize('kind,dataset', [('table','invoices'),('table','revenue'),('card','invoices'),('chart','revenue')])
def test_all_components(kind,dataset):
    events=component_messages(kind,dataset,'Demo')
    assert len(events)==3
    for event in events: validate_a2ui(event)
    assert events[1]['updateComponents']['components'][2]['component'].lower()==kind
    assert events[2]['updateDataModel']['value']

def test_selection_is_not_backend_rule_in_real_mode():
    assert mock_selection('vis omsætning graf')[0]=='chart'
    assert mock_selection('faktura overblik')[0]=='card'
    assert mock_selection('faktura tabel')[0]=='table'
    assert mock_selection('hej') is None

def test_tool_allowlist():
    assert show_ui('chart','invoices','No')['error']
    assert show_ui('card','invoices','Summary')['accepted']
    assert get_finance_data('unknown')['error']

def test_stream_text_and_a2ui():
    async def collect(): return [v async for v in mock_stream('vis omsætning graf')]
    events=asyncio.run(collect())
    assert events[0][0]=='text_delta'
    assert [kind for kind, _ in events].count('a2ui')==3
    assert events[-1][0]=='text_delta'

def test_envelope_fails_closed():
    messages=component_messages('table','invoices','Demo')
    messages[1]['updateComponents']['components'][2]['component']='ArbitraryHTML'
    with pytest.raises(ValueError):validate_a2ui(messages[1])

def test_sse():
    assert json.loads(sse('text_delta',{'text':'æøå'}).split('data: ',1)[1])['text']=='æøå'
