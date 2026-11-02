import os
from google.adk.agents import Agent

# The agent only selects which of three predefined UI components to show.
# The frontend builds the A2UI surface from its own synthetic demo data; the tool carries no data.
def show_ui(kind: str) -> dict:
    """Display one structured component. kind must be table, card, or chart."""
    if kind not in ('table', 'card', 'chart'):
        return {'error': 'unsupported component'}
    return {'kind': kind, 'status': 'ready'}

root_agent = Agent(
    name='accounting_demo',
    model=os.getenv('MODEL') or 'gemini-2.5-flash',
    instruction=(
        'You are a Danish accounting assistant. Answer briefly in Markdown. '
        'For invoice lists call show_ui(kind="table"). For KPI summaries use "card". '
        'For revenue trends use "chart". Do not write Markdown tables. '
        'Do not invent amounts; the UI tool uses explicitly synthetic demo data. '
        'Say that data is synthetic. Never include JSON/A2UI in conversational text.'
    ),
    tools=[show_ui],
)
