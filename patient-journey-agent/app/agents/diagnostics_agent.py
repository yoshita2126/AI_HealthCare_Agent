from datetime import datetime
from typing import Any, Dict, List
from app.models.state import AgentState

def diagnostics_node(state: AgentState) -> Dict[str, Any]:
    missing: List[Dict[str, Any]] = []
    
    for evt in state.get("timeline", []):
        if evt["event_type"] == "LabOrder" and evt["status"] == "pending":
            missing.append({
                "source_event": evt["event_id"],
                "issue": f"Pending investigation: {evt['details'].get('test')}",
                "resource": evt["source_resource"]
            })
            
    return {"missing_actions": missing}
