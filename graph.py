from __future__ import annotations

from typing import Literal
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from planner import decide_next_action
from state import HOAState
from tools import (
    check_vendor_availability,
    create_maintenance_ticket,
    escalate_to_hoa_manager,
    get_maintenance_history,
    lookup_hoa_policy,
)


def initialize_node(state: HOAState) -> HOAState:
    return {
        "case_id": state.get("case_id") or str(uuid4()),
        "maintenance_history": state.get("maintenance_history", []),
        "missing_information": state.get("missing_information", []),
        "retry_count": state.get("retry_count", 0),
        "actions_taken": state.get("actions_taken", []),
        "approval_required": False,
        "human_approval": None,
        "status": "investigating",
    }


def planner_node(state: HOAState) -> HOAState:
    decision = decide_next_action(state)
    return {
        "issue_type": decision.issue_type,
        "severity": decision.severity,
        "hoa_responsibility": decision.hoa_responsibility,
        "next_action": decision.next_action,
        "rationale": decision.rationale,
        "missing_information": decision.missing_information,
    }


def route_after_planner(state: HOAState) -> str:
    return state["next_action"]


def lookup_policy_node(state: HOAState) -> HOAState:
    result = lookup_hoa_policy.invoke({"issue_type": state["issue_type"]})
    return {
        "policy_result": result,
        "actions_taken": state.get("actions_taken", []) + ["lookup_policy"],
    }


def check_history_node(state: HOAState) -> HOAState:
    unit = state.get("unit_number") or "COMMON"
    result = get_maintenance_history.invoke({"unit_number": unit})
    return {
        "maintenance_history": [result],
        "actions_taken": state.get("actions_taken", []) + ["check_history"],
    }


def check_vendor_node(state: HOAState) -> HOAState:
    attempt = state.get("retry_count", 0)
    try:
        result = check_vendor_availability.invoke({
            "issue_type": state["issue_type"],
            "attempt": attempt,
            "simulate_failure": state.get("simulate_vendor_failure", False),
        })
        return {
            "vendor_result": result,
            "retry_count": 0,
            "actions_taken": state.get("actions_taken", []) + ["check_vendor"],
        }
    except Exception as exc:
        new_retry = attempt + 1
        return {
            "vendor_result": f"ERROR: {type(exc).__name__}: {exc}",
            "retry_count": new_retry,
            "actions_taken": state.get("actions_taken", []) + [
                f"check_vendor_failed_attempt_{new_retry}"
            ],
        }


def ask_human_node(state: HOAState):
    answer = interrupt({
        "type": "missing_information",
        "question": "The agent needs more information before continuing.",
        "missing_information": state.get("missing_information", []),
    })
    updated_message = (
        state["resident_message"]
        + "\nAdditional resident information: "
        + str(answer)
    )
    return {
        "resident_message": updated_message,
        "actions_taken": state.get("actions_taken", []) + ["asked_human_for_details"],
    }


def approval_node(state: HOAState) -> Command[Literal["execute_write", "rejected"]]:
    proposed = state["next_action"]
    decision = interrupt({
        "type": "approval",
        "question": f"Approve proposed write action: {proposed}?",
        "case_id": state["case_id"],
        "issue_type": state.get("issue_type"),
        "severity": state.get("severity"),
        "rationale": state.get("rationale"),
        "vendor_result": state.get("vendor_result"),
    })
    approved = bool(decision)
    return Command(
        update={
            "approval_required": True,
            "human_approval": approved,
            "actions_taken": state.get("actions_taken", []) + [
                "human_approved" if approved else "human_rejected"
            ],
        },
        goto="execute_write" if approved else "rejected",
    )


def execute_write_node(state: HOAState) -> HOAState:
    if state["next_action"] == "create_ticket":
        result = create_maintenance_ticket.invoke({
            "case_id": state["case_id"],
            "issue_type": state.get("issue_type", "other"),
            "severity": state.get("severity", "unknown"),
            "summary": state["resident_message"],
        })
        return {
            "status": "resolved",
            "final_message": result,
            "actions_taken": state.get("actions_taken", []) + ["create_ticket"],
        }

    result = escalate_to_hoa_manager.invoke({
        "case_id": state["case_id"],
        "reason": state.get("rationale", "Human escalation required."),
    })
    return {
        "status": "escalated",
        "final_message": result,
        "actions_taken": state.get("actions_taken", []) + ["escalate"],
    }


def rejected_node(state: HOAState) -> HOAState:
    return {
        "status": "stopped_by_human",
        "final_message": "The proposed action was rejected by the human reviewer.",
    }


def resolve_node(state: HOAState) -> HOAState:
    return {
        "status": "resolved",
        "final_message": (
            "No HOA write action is required. "
            + (state.get("rationale") or "Case can be resolved with guidance.")
        ),
    }


def build_graph():
    builder = StateGraph(HOAState)

    builder.add_node("initialize", initialize_node)
    builder.add_node("planner", planner_node)
    builder.add_node("lookup_policy", lookup_policy_node)
    builder.add_node("check_history", check_history_node)
    builder.add_node("check_vendor", check_vendor_node)
    builder.add_node("ask_human", ask_human_node)
    builder.add_node("approval", approval_node)
    builder.add_node("execute_write", execute_write_node)
    builder.add_node("rejected", rejected_node)
    builder.add_node("resolve", resolve_node)

    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "planner")

    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "lookup_policy": "lookup_policy",
            "check_history": "check_history",
            "check_vendor": "check_vendor",
            "ask_human": "ask_human",
            "create_ticket": "approval",
            "escalate": "approval",
            "resolve": "resolve",
        },
    )

    # Observations loop back to the planner.
    builder.add_edge("lookup_policy", "planner")
    builder.add_edge("check_history", "planner")
    builder.add_edge("check_vendor", "planner")
    builder.add_edge("ask_human", "planner")

    builder.add_edge("execute_write", END)
    builder.add_edge("rejected", END)
    builder.add_edge("resolve", END)

    return builder.compile(checkpointer=InMemorySaver())


graph = build_graph()
