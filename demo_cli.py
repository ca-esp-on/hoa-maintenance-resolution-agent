import argparse
from uuid import uuid4

from dotenv import load_dotenv
from langgraph.types import Command

from graph import graph

load_dotenv()

SCENARIOS = {
    "routine": {
        "resident_message": "The hallway light outside my unit has been out for two days.",
        "unit_number": "B204",
        "simulate_vendor_failure": False,
    },
    "emergency": {
        "resident_message": "Water is pouring from the hallway ceiling outside my unit.",
        "unit_number": "B204",
        "simulate_vendor_failure": False,
    },
    "failure": {
        "resident_message": "The shared garage door is stuck and will not open.",
        "unit_number": "COMMON",
        "simulate_vendor_failure": True,
    },
}

parser = argparse.ArgumentParser()
parser.add_argument("scenario", choices=SCENARIOS.keys())
args = parser.parse_args()

config = {"configurable": {"thread_id": str(uuid4())}}
result = graph.invoke(SCENARIOS[args.scenario], config=config)

while "__interrupt__" in result:
    payload = result["__interrupt__"][0].value
    print("\nHUMAN INPUT REQUIRED")
    print(payload)
    if payload.get("type") == "approval":
        raw = input("Approve? [y/N]: ").strip().lower()
        result = graph.invoke(Command(resume=(raw == "y")), config=config)
    else:
        raw = input("Additional information: ")
        result = graph.invoke(Command(resume=raw), config=config)

print("\nFINAL STATE")
for key, value in result.items():
    print(f"{key}: {value}")
