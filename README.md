# HOA Maintenance Resolution Agent

A stateful, code-heavy LangGraph project that demonstrates **agentic control flow** rather than a one-shot LLM call.

The agent receives an HOA maintenance request, decides what information or tool it needs next, updates shared case state, handles tool failures, and pauses for human approval before write/high-impact actions.

## Why this is agentic

The workflow is iterative:

`plan -> act/tool -> observe -> update state -> plan again`

The LLM does not produce the final answer in one call. It chooses the next action from the current state. Deterministic graph logic enforces boundaries around write actions and failure handling.

## Architecture

```text
Resident request
      |
      v
  initialize
      |
      v
   planner  <-----------------------------+
      |                                   |
      +--> lookup_policy -----------------+
      +--> check_history -----------------+
      +--> check_vendor ------------------+
      |         |                         |
      |         +-- tool error -> state --+
      +--> ask_human -- interrupt --------+
      |
      +--> create_ticket --> approval interrupt --> execute_write --> END
      |
      +--> escalate -----> approval interrupt --> execute_write --> END
      |
      +--> resolve -----------------------------------------------> END
```

## Tools

### Read tools
- `lookup_hoa_policy`
- `get_maintenance_history`
- `check_vendor_availability`

### Write tools
- `create_maintenance_ticket`
- `escalate_to_hoa_manager`

Write tools are never executed until the graph pauses and a human approves the action.

## State

The graph tracks:
- resident request and unit/common area
- issue classification and severity
- HOA responsibility assessment
- policy, maintenance history, and vendor observations
- selected next action and rationale
- tool retry count
- actions already taken
- human approval
- final case status

## Failure recovery

The vendor tool can intentionally simulate an outage. Failed attempts are written into state and the planner sees the retry count. After repeated failures, the prompt instructs the planner to escalate instead of inventing vendor availability.

## Human-in-the-loop

LangGraph `interrupt()` pauses execution for:
1. missing resident information
2. approval before creating a maintenance ticket
3. approval before escalation/write actions

The graph uses `InMemorySaver` with a `thread_id` so execution can resume from the saved state.

## Demo scenarios

### 1. Routine issue
"The hallway light outside my unit has been out for two days."

Expected path: classify -> policy/history/vendor reads -> propose ticket -> human approval -> ticket created.

### 2. Emergency
"Water is pouring from the hallway ceiling outside my unit."

Expected path: classify as emergency -> gather enough context -> propose escalation -> human approval -> escalated.

### 3. Tool failure
"The shared garage door is stuck and will not open."

Enable simulated vendor failure. Expected path: vendor lookup fails -> retry based on state -> eventually recover or escalate based on the planner decision.

## Setup

Python 3.12+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env`.

Run the UI:

```bash
streamlit run app.py
```

Or run a CLI scenario:

```bash
python demo_cli.py routine
python demo_cli.py emergency
python demo_cli.py failure
```

Run tests:

```bash
pytest -q
```

## One-liner

My agent helps HOA residents resolve maintenance issues through a web app, replacing manual back-and-forth with property managers. It autonomously classifies issues, assesses urgency, checks HOA responsibility and maintenance history, and decides the next action using five tools; it hands off write actions, emergencies, and ambiguous cases to a human, and succeeds when common requests are correctly resolved or escalated in under two minutes.

## Cohort concepts demonstrated

- stateful LangGraph workflow
- LLM-driven next-action planning
- tool calling
- conditional routing
- retry/error recovery
- human-in-the-loop interrupts
- explicit autonomy boundaries
- end-to-end task completion

## Scope note

This is an educational MVP. HOA policies, maintenance history, and vendors are mock data. A production implementation would use authenticated property-management APIs, persistent checkpointing, audit logs, role-based approvals, and property-specific governing documents.
