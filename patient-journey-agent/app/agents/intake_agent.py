from typing import Any, Dict
from app.models.state import AgentState
from app.tools.fhir_tools import fetch_patient_events

def intake_node(state: AgentState) -> Dict[str, Any]:
    events = fetch_patient_events(state["patient_id"])
    return {
        "timeline": events,
        "current_phase": "Assessment & Diagnostics"
    }
