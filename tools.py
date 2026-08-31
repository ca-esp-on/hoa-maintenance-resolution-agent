import json
from pathlib import Path
from langchain_core.tools import tool

DATA_DIR = Path(__file__).parent / "data"


def _load(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def lookup_hoa_policy(issue_type: str) -> str:
    """Read HOA maintenance responsibility and escalation guidance for an issue type."""
    policies = _load("hoa_policies.json")
    result = policies.get(issue_type, policies["other"])
    return (
        f"Responsibility: {result['responsibility']}. "
        f"Guidance: {result['guidance']} "
        f"Approval rule: {result['approval_rule']}"
    )


@tool
def get_maintenance_history(unit_number: str) -> str:
    """Read prior maintenance incidents for a unit or shared/common area."""
    history = _load("maintenance_history.json")
    items = history.get(unit_number, [])
    if not items:
        return f"No prior maintenance incidents found for {unit_number}."
    return " | ".join(items)


@tool
def check_vendor_availability(issue_type: str, attempt: int = 0, simulate_failure: bool = False) -> str:
    """Read vendor availability for a maintenance category. May simulate an API outage for demo purposes."""
    if simulate_failure and attempt < 2:
        raise ConnectionError("Vendor service temporarily unavailable")
    vendors = _load("vendors.json")
    options = vendors.get(issue_type, vendors["other"])
    if not options:
        return "No matching vendor is currently available."
    best = options[0]
    return f"{best['name']} is available {best['availability']} (priority: {best['priority']})."


@tool
def create_maintenance_ticket(case_id: str, issue_type: str, severity: str, summary: str) -> str:
    """WRITE ACTION: Create a mock maintenance work order after human approval."""
    return (
        f"Ticket HOA-{case_id[-6:].upper()} created for {issue_type} "
        f"with severity={severity}. Summary: {summary}"
    )


@tool
def escalate_to_hoa_manager(case_id: str, reason: str) -> str:
    """WRITE ACTION: Create a mock escalation for an HOA/property manager after human approval."""
    return f"Case {case_id} escalated to HOA manager. Reason: {reason}"
