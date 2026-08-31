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


SYSTEM_PROMPT = """You are the planner for an HOA Maintenance Resolution Agent.

Your job is not to answer in one shot. Decide the NEXT useful action using the current
case state and tool observations.

Rules:
1. Use read tools before making responsibility claims when policy/history is not known.
2. For emergency signals (active flooding, fire/electrical danger, trapped elevator,
   major safety risk), prefer escalation once enough context exists.
3. `create_ticket` and `escalate` are write actions and will require human approval.
4. If a read tool failed twice, choose `escalate`.
5. Do not repeat a successful read tool unless there is a clear reason.
6. Use `resolve` only when no write action is required and the user can safely handle
   the next step themselves.
7. Use `ask_human` only when factual information is genuinely missing
   from the resident, such as the exact location of the issue, whether
   water is actively flowing, or which asset is affected.

   NEVER use `ask_human` to request approval.

   Approval is handled automatically by the graph after you choose
   `create_ticket` or `escalate`.

8. If policy and history provide enough evidence for a routine
   HOA-maintained issue and a work order is appropriate,
   choose `create_ticket`.
   9. If an emergency or repeated tool failure requires manager
   involvement, choose `escalate`.

10. Never put "approval" in `missing_information`.

11. Keep the rationale operational and short.
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
