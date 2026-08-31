import os
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from graph import graph

load_dotenv()

st.set_page_config(page_title="HOA Maintenance Resolution Agent", page_icon="🏢")
st.title("🏢 HOA Maintenance Resolution Agent")
st.caption("Stateful LangGraph demo: decisions, tools, retries, and human approval.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

with st.sidebar:
    st.subheader("Demo scenarios")
    scenario = st.radio(
        "Choose one",
        [
            "Custom",
            "Routine hallway light",
            "Emergency water leak",
            "Garage vendor failure",
        ],
    )

defaults = {
    "Custom": ("", "B204", False),
    "Routine hallway light": (
        "The hallway light outside my unit has been out for two days.",
        "B204",
        False,
    ),
    "Emergency water leak": (
        "Water is pouring from the hallway ceiling outside my unit.",
        "B204",
        False,
    ),
    "Garage vendor failure": (
        "The shared garage door is stuck and will not open.",
        "COMMON",
        True,
    ),
}

default_message, default_unit, default_failure = defaults[scenario]

message = st.text_area("Describe the maintenance issue", value=default_message, height=120)
unit = st.text_input("Unit / area", value=default_unit)
simulate_failure = st.checkbox(
    "Simulate vendor API failure (for error-handling demo)",
    value=default_failure,
)

def run_graph(input_value):
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    result = graph.invoke(input_value, config=config)
    st.session_state.last_result = result
    interrupts = result.get("__interrupt__", [])
    st.session_state.pending_interrupt = interrupts[0] if interrupts else None
    return result

if st.button("Start case", type="primary"):
    st.session_state.thread_id = str(uuid4())
    st.session_state.pending_interrupt = None
    st.session_state.last_result = None
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Add OPENAI_API_KEY to your .env file first.")
    elif not message.strip():
        st.warning("Enter a maintenance issue.")
    else:
        with st.spinner("Agent is working..."):
            run_graph({
                "resident_message": message,
                "unit_number": unit or None,
                "simulate_vendor_failure": simulate_failure,
            })

pending = st.session_state.pending_interrupt
if pending:
    payload = pending.value
    st.warning("Human input required")
    st.json(payload)

    if payload.get("type") == "approval":
        col1, col2 = st.columns(2)
        if col1.button("Approve"):
            with st.spinner("Resuming agent..."):
                run_graph(Command(resume=True))
            st.rerun()
        if col2.button("Reject"):
            with st.spinner("Resuming agent..."):
                run_graph(Command(resume=False))
            st.rerun()

    elif payload.get("type") == "missing_information":
        answer = st.text_input("Provide the missing information")
        if st.button("Submit information"):
            with st.spinner("Resuming agent..."):
                run_graph(Command(resume=answer))
            st.rerun()

result = st.session_state.last_result

if result:
    st.subheader("Case Summary")

    st.write(f"**Issue type:** {result.get('issue_type', 'Unknown')}")
    st.write(f"**Severity:** {result.get('severity', 'Unknown')}")
    st.write(f"**HOA responsibility:** {result.get('hoa_responsibility', 'Unknown')}")
    st.write(f"**Status:** {result.get('status', 'Unknown')}")

    if result.get("policy_result"):
        st.write("**Policy check:**")
        st.info(result["policy_result"])

    if result.get("vendor_result"):
        st.write("**Vendor check:**")
        st.info(result["vendor_result"])

    if result.get("final_message"):
        if result.get("status") == "resolved":
            st.success(result["final_message"])
        elif result.get("status") == "escalated":
            st.warning(result["final_message"])
        else:
            st.info(result["final_message"])

    with st.expander("Agent State / Debug Trace"):
        safe_state = {
            k: v
            for k, v in result.items()
            if k != "__interrupt__"
        }
        st.json(safe_state)

    if result.get("final_message"):
        if result.get("status") == "resolved":
            st.success(result["final_message"])
        elif result.get("status") == "escalated":
            st.info(result["final_message"])
        else:
            st.warning(result["final_message"])
