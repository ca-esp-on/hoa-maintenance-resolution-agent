from typing import Literal, Optional, TypedDict

IssueType = Literal[
    "plumbing",
    "electrical",
    "garage",
    "elevator",
    "landscaping",
    "hvac",
    "other",
]

Severity = Literal["routine", "urgent", "emergency", "unknown"]

NextAction = Literal[
    "lookup_policy",
    "check_history",
    "check_vendor",
    "ask_human",
    "create_ticket",
    "escalate",
    "resolve",
]


class HOAState(TypedDict, total=False):
    # Intake
    case_id: str
    resident_message: str
    unit_number: Optional[str]

    # Agent understanding
    issue_type: Optional[IssueType]
    severity: Optional[Severity]
    hoa_responsibility: Optional[str]
    missing_information: list[str]

    # Tool observations
    policy_result: Optional[str]
    maintenance_history: list[str]
    vendor_result: Optional[str]

    # Control flow
    next_action: Optional[NextAction]
    rationale: Optional[str]
    retry_count: int
    actions_taken: list[str]
    simulate_vendor_failure: bool

    # Human-in-the-loop / outcome
    approval_required: bool
    human_approval: Optional[bool]
    status: str
    final_message: Optional[str]
