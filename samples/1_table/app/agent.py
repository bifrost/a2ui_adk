"""Real Google ADK agent. The agent calls the tool; the adapter emits A2UI.

This deliberately avoids assuming an unverified A2UI v1.0 Python SDK API.
The same table catalog can later be supplied to an A2UI-aware model agent.
"""
import os
from google.adk.agents import Agent
from .data import get_invoices

SYSTEM_PROMPT = """You are a concise accounting assistant.
Reply in short conversational Markdown, in the user's language.
For invoice lists, tables, and overviews, first write one short sentence saying what you are fetching, then call get_invoices to obtain authoritative data.
Never reproduce tabular data as a Markdown table or JSON in conversational text.
Instead, explain briefly what the data contains; the presentation layer will
render the tool's structured result as an A2UI v1.0 Table surface.
For ordinary queries, answer in Markdown without calling tools.
Never invent invoice data or amounts.
"""

root_agent = Agent(
    name="accounting_assistant",
    model=os.environ.get("ADK_MODEL", "gemini-2.5-flash"),
    instruction=SYSTEM_PROMPT,
    tools=[get_invoices],
)
