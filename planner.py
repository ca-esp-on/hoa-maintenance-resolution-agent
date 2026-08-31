import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from state import HOAState


class AgentDecision(BaseModel):
    issue_type: Literal[
        "plumbing", "electrical", "garage", "elevator",
        "landscaping", "hvac", "other"
    ] = Field(description="Best current issue category.")
    severity: Literal["routine", "urgent", "emergency", "unknown"]
    hoa_responsibility: str = Field(
        description="Current best assessment: HOA, homeowner, shared/unclear, or unknown."
    )
    next_action: Literal[
        "lookup_policy",
        "check_history",
        "check_vendor",
        "ask_human",
        "create_ticket",
        "escalate",
        "resolve",
    ]
    rationale: str = Field(description="Short operational reason for the next action.")
    missing_information: list[str] = Field(default_factory=list)


SYSTEM_PROMPT = SYSTEM_PROMPT = """
You are the planner for an HOA Maintenance Resolution Agent.

Your job is to choose the NEXT useful action based on the current case state.

For garage, elevator, plumbing, electrical, HVAC, or other vendor-dependent maintenance,
do not choose create_ticket until vendor availability has been checked.

If vendor_result is missing and the issue requires a vendor, choose check_vendor first.

If vendor lookup fails:
- retry once
- if retry_count >= 2, choose escalate

Rules:

1. Do not ask for information that is already explicitly stated
   or clearly implied by the resident's message.

2. Treat phrases such as:
   - "water is pouring"
   - "active flooding"
   - "sparks"
   - "smoke"
   - "fire"
   - "person trapped in elevator"
   - "gas smell"

   as strong emergency signals.

3. When a strong emergency signal is already present,
   set severity="emergency" and prefer next_action="escalate".
   Do not ask unnecessary clarification questions before escalation.

4. Use ask_human only when genuinely necessary factual
   information is missing.

5. NEVER use ask_human for approval.

6. Approval is handled automatically by LangGraph after
   choosing create_ticket or escalate.

7. Use read tools before responsibility claims when needed,
   unless delaying for those reads would be inappropriate
   for an obvious emergency.

8. If a read tool fails twice, choose escalate.

9. Do not repeat a successful read tool.

10. Keep rationale short and operational.
"""


def get_planner():
    model_name = os.getenv("MODEL_NAME", "gpt-4.1-mini")
    model = ChatOpenAI(model=model_name, temperature=0)
    return model.with_structured_output(AgentDecision)


def decide_next_action(state: HOAState) -> AgentDecision:
    planner = get_planner()
    compact_state = {
        "resident_message": state.get("resident_message"),
        "unit_number": state.get("unit_number"),
        "issue_type": state.get("issue_type"),
        "severity": state.get("severity"),
        "hoa_responsibility": state.get("hoa_responsibility"),
        "policy_result": state.get("policy_result"),
        "maintenance_history": state.get("maintenance_history", []),
        "vendor_result": state.get("vendor_result"),
        "retry_count": state.get("retry_count", 0),
        "actions_taken": state.get("actions_taken", []),
    }
    return planner.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", f"Current case state:\n{compact_state}")
    ])
