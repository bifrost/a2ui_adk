"""Synthetic invoice data only: no real customer information."""

INVOICES = [
    {"number": "INV-1001", "customer": "Northwind Demo", "amount": 1250.0, "currency": "DKK", "status": "paid"},
    {"number": "INV-1002", "customer": "Contoso Demo", "amount": 850.0, "currency": "DKK", "status": "unpaid"},
    {"number": "INV-1003", "customer": "Fabrikam Demo", "amount": 2890.0, "currency": "DKK", "status": "paid"},
]


def get_invoices() -> dict:
    """Get synthetic invoices for a UI table. Call when a user asks for invoices or an invoice table."""
    return {"invoices": INVOICES}
