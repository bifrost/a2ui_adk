"""A2UI v1.0 envelopes and a versioned application-specific Table catalog.

A2UI v1.0 is Candidate. This demo uses its protocol envelopes and a custom
Table component, not a claimed implementation of the official full renderer SDK.
"""
from uuid import uuid4
from typing import Any

VERSION = "v1.0"
CATALOG_ID = "https://example.org/catalogs/accounting/v1.json"


def table_messages(invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    surface_id = f"invoices_{uuid4().hex}"
    return [
        {"version": VERSION, "createSurface": {
            "surfaceId": surface_id, "catalogId": CATALOG_ID,
        }},
        {"version": VERSION, "updateComponents": {
            "surfaceId": surface_id,
            "components": [
                {"id": "root", "component": "Column", "children": ["heading", "invoice_table"]},
                {"id": "heading", "component": "Text", "text": "Invoice overview"},
                {"id": "invoice_table", "component": "Table",
                 "columns": [
                     {"key": "number", "label": "Invoice"},
                     {"key": "customer", "label": "Customer"},
                     {"key": "amount", "label": "Amount"},
                     {"key": "currency", "label": "Currency"},
                     {"key": "status", "label": "Status"},
                 ], "rows": {"path": "/invoices"}},
            ],
        }},
        {"version": VERSION, "updateDataModel": {
            "surfaceId": surface_id, "path": "/invoices", "value": invoices,
        }},
    ]


def _validate_component(c: dict[str, Any], ids: set[str]) -> None:
    kind = c["component"]
    allowed = {"Column": {"children"}, "Text": {"text"}, "Table": {"columns", "rows"}}[kind]
    if set(c) - allowed - {"id", "component"}:
        raise ValueError("Unexpected component property")
    if kind == "Column":
        children = c.get("children", [])
        if not isinstance(children, list) or any(ch not in ids for ch in children):
            raise ValueError("Invalid children")
    elif kind == "Text":
        if not isinstance(c.get("text"), str):
            raise ValueError("Invalid text property")
    else:
        columns = c.get("columns")
        if not isinstance(columns, list) or len(columns) > 20 or not all(
                isinstance(col, dict) and isinstance(col.get("key"), str) and isinstance(col.get("label"), str)
                for col in columns):
            raise ValueError("Invalid columns")
        rows = c.get("rows")
        if not isinstance(rows, dict) or set(rows) != {"path"} or not str(rows["path"]).startswith("/"):
            raise ValueError("Invalid data binding")


def validate_a2ui(message: dict[str, Any]) -> None:
    """Small fail-closed validation for our narrow demo catalog, not full spec validation."""
    if message.get("version") != VERSION:
        raise ValueError("Only A2UI v1.0 is supported")
    keys = set(message) - {"version"}
    if len(keys) != 1 or next(iter(keys)) not in {"createSurface", "updateComponents", "updateDataModel", "deleteSurface"}:
        raise ValueError("Invalid A2UI message envelope")
    kind = next(iter(keys))
    payload = message[kind]
    if not isinstance(payload, dict) or not isinstance(payload.get("surfaceId"), str):
        raise ValueError("Missing surfaceId")
    if kind == "createSurface" and payload.get("catalogId") != CATALOG_ID:
        raise ValueError("Unknown UI catalog")
    if kind == "updateComponents":
        components = payload.get("components", [])
        if not isinstance(components, list):
            raise ValueError("Invalid component list")
        if len(components) > 20:
            raise ValueError("Invalid component list")
        for component in components:
            if not isinstance(component, dict) or not isinstance(component.get("id"), str):
                raise ValueError("Invalid component")
            if component.get("component") not in {"Column", "Text", "Table"}:
                raise ValueError("Unapproved component")
        ids = [c["id"] for c in components]
        if "root" not in ids or len(ids) != len(set(ids)):
            raise ValueError("Invalid IDs")
        for c in components:
            _validate_component(c, set(ids))
    if kind == "updateDataModel":
        path = payload.get("path", "/")
        if not isinstance(path, str) or (path and not path.startswith("/")) or "value" not in payload:
            raise ValueError("Invalid data model update")
        if any(t in {"__proto__", "constructor", "prototype"} for t in path.split("/")):
            raise ValueError("Unsafe data path")
