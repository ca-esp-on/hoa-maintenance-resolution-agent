# Project Documentation Notes

## Project overview
The HOA Maintenance Resolution Agent helps residents report maintenance issues and moves each case through investigation, routing, approval, and resolution. The project focuses on control flow, state, tool failure, and human handoff.

## Dataset / mock sources
- `data/hoa_policies.json`: synthetic HOA responsibility and escalation rules
- `data/maintenance_history.json`: synthetic historical maintenance incidents
- `data/vendors.json`: synthetic vendor availability

No real resident or HOA data is used.

## Key implementation decisions
- Single stateful agent rather than multi-agent architecture
- Explicit LangGraph StateGraph to make control flow visible
- Structured-output LLM planner chooses only the next action
- Read tools can run autonomously
- Write tools require `interrupt()` + human approval
- Vendor API failure is intentionally simulated to demonstrate recovery
- In-memory checkpointing is sufficient for the cohort demo

## Iterations to mention in submission
1. Initial idea: direct classifier -> create maintenance ticket.
2. Changed to iterative planner/tool loop so the agent decides what to do after each observation.
3. Added explicit state fields for actions and retries.
4. Added human approval before all write actions.
5. Added simulated vendor failure to prove the workflow does not only support the happy path.

## Learning / observations
- Tool calling alone does not make a system agentic; the key behavior is deciding the next step from state.
- Deterministic guardrails are useful around risky actions instead of leaving every decision to the LLM.
- Human-in-the-loop requires checkpointing so the graph can pause and resume safely.
- Failure information needs to be written back into state or the planner cannot adapt.
