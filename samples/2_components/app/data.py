"""Synthetic and allowlisted datasets. Real data should be pulled from authenticated tools."""
INVOICES = [
    {"number": "INV-1001", "customer": "Northwind Demo", "amount": 1250, "currency": "DKK", "status": "paid"},
    {"number": "INV-1002", "customer": "Contoso Demo", "amount": 850, "currency": "DKK", "status": "unpaid"},
    {"number": "INV-1003", "customer": "Fabrikam Demo", "amount": 2890, "currency": "DKK", "status": "paid"},
]
REVENUE = [
    {"month": "May", "revenue": 13500},
    {"month": "Jun", "revenue": 16300},
    {"month": "Jul", "revenue": 14950},
    {"month": "Aug", "revenue": 20200},
    {"month": "Sep", "revenue": 18900},
    {"month": "Oct", "revenue": 22600},
]
DATASETS = {"invoices": INVOICES, "revenue": REVENUE}


def get_finance_data(dataset: str) -> dict:
    """Get one synthetic dataset. dataset must be 'invoices' or 'revenue'."""
    if dataset not in DATASETS:
        return {"error": "Unknown dataset; allowed: invoices, revenue"}
    return {"dataset": dataset, "rows": DATASETS[dataset]}


def show_ui(kind: str, dataset: str, title: str) -> dict:
    """Display a UI component chosen by YOU. kind: table/card/chart; dataset: invoices/revenue. Use only for structured views, after get_finance_data. A card summarizes invoices; a chart plots revenue. For invoice detail use table; revenue trend use chart. The backend validates every choice."""
    if kind not in ("table", "card", "chart"):
        return {"error": "Unsupported component"}
    if dataset not in DATASETS:
        return {"error": "Unsupported dataset"}
    if kind == "chart" and dataset != "revenue":
        return {"error": "Chart supports revenue only"}
    if kind == "card" and dataset != "invoices":
        return {"error": "Card supports invoices only"}
    if not isinstance(title, str) or not (1 <= len(title) <= 100):
        return {"error": "Invalid title"}
    return {"kind": kind, "dataset": dataset, "title": title, "accepted": True}
