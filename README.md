# HOA Maintenance Resolution Agent

A stateful AI agent built with **LangGraph, LangChain, OpenAI, and Streamlit** that helps HOA residents report and resolve maintenance issues.

Unlike a one-shot LLM call, the agent decides what to do next, calls tools, maintains state, handles tool failures, and pauses for human approval when required.

## How It Works

```text
Resident Request
      ↓
LLM Planner
"What should I do next?"
      ↓
 ┌────────┬─────────┬────────┐
 Policy   History   Vendor
 Lookup   Lookup    Lookup
 └────────┴─────────┴────────┘
      ↓
Update State
      ↓
Planner Decides Again
      ↓
Resolve / Create Ticket / Escalate
                    ↓
              Human Approval
                    ↓
               Final Action
```

The exact path is dynamic. After each tool call, the result is stored in LangGraph state and the planner decides the next action.

## Tools

**Read**

* `lookup_hoa_policy`
* `get_maintenance_history`
* `check_vendor_availability`

**Write**

* `create_maintenance_ticket`
* `escalate_to_hoa_manager`

Write actions require human approval.

## State

The agent tracks information such as:

* Issue type and severity
* HOA responsibility
* Policy and maintenance history
* Vendor availability
* Actions already attempted
* Retry count
* Human approval
* Case status

## Human-in-the-Loop

LangGraph `interrupt()` pauses the workflow before write/escalation actions.

```text
Agent recommends action
        ↓
Human Approval
   /          \
Approve      Reject
   ↓            ↓
Execute        Stop
```

The agent can also ask the resident for missing information before continuing.

## Failure Recovery

Vendor failure is simulated to demonstrate error handling.

```text
Vendor API
   ↓
❌ Failure
   ↓
retry_count = 1
   ↓
Retry
   ↓
❌ Failure
   ↓
retry_count = 2
   ↓
Escalate
   ↓
Human Approval
```

The failure is stored in state instead of crashing the workflow.

## Demo Scenarios

### Routine Hallway Light

> "The hallway light outside my unit has been out for two days."

Demonstrates classification, policy/history lookup, and ticket approval.

### Emergency Water Leak

> "Water is pouring from the hallway ceiling outside my unit."

The agent identifies an emergency and prioritizes escalation.

### Garage Vendor Failure

> "The shared garage door is stuck and will not open."

Demonstrates vendor tool failure, retries, and escalation.

## Project Structure

```text
├── app.py
├── graph.py
├── planner.py
├── state.py
├── tools.py
├── data/
│   ├── hoa_policies.json
│   ├── maintenance_history.json
│   └── vendors.json
├── requirements.txt
├── .env.example
└── README.md
```

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
```

Add your API key to `.env`, then:

```bash
streamlit run app.py
```

## Key Concepts Demonstrated

* Stateful LangGraph workflow
* LLM next-action planning
* Structured LLM output
* Tool calling
* Conditional routing
* Error recovery and retries
* Human-in-the-loop
* Explicit autonomy boundaries

## Scope

This is an educational MVP using mock HOA policies, maintenance history, and vendor data. A production version would integrate real property-management systems, persistent storage, authentication, audit logs, and deterministic safety rules for emergency conditions.
