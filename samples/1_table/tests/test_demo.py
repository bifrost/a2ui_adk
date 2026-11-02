import asyncio
import json
from app.a2ui import table_messages, validate_a2ui
from app.data import INVOICES
from app.streaming import mock_stream, sse


def test_envelopes():
    items = table_messages(INVOICES)
    assert len(items) == 3
    assert [next(k for k in x if k != 'version') for x in items] == ['createSurface','updateComponents','updateDataModel']
    for item in items: validate_a2ui(item)
    assert items[1]['updateComponents']['components'][2]['component'] == 'Table'


def test_mock_text_before_table():
    async def collect():
        return [x async for x in mock_stream('vis fakturaer')]
    events = asyncio.run(collect())
    assert events[0][0] == 'text_delta'
    assert len([v for k,v in events if k == 'a2ui']) == 3
    assert any(k == 'text_delta' for k,_ in events)


def test_no_table_for_regular_text():
    async def collect(): return [x async for x in mock_stream('hej')]
    assert not any(k == 'a2ui' for k,_ in asyncio.run(collect()))


def test_sse():
    frame=sse('text_delta',{'text':'æøå'})
    assert frame.startswith('event: text_delta\n')
    assert json.loads(frame.split('data: ',1)[1])['text']=='æøå'
