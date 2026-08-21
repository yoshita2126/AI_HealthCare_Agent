from typing import Any, Dict
from app.models.state import AgentState

def summarizer_node(state: AgentState) -> Dict[str, Any]:
    lines = [f"### Patient Summary for {state['patient_id']}"]
    lines.append(f"**Phase:** {state.get('current_phase', 'Active Coordination')}\n")
    lines.append("**Key Events & Citations:**")
    
    for evt in state.get("timeline", []):
        ts = evt["timestamp"].strftime("%Y-%m-%d") if hasattr(evt["timestamp"], "strftime") else str(evt["timestamp"])
        lines.append(f"- [{ts}] **{evt['event_type']}** ({evt['status']}) - {evt['details']} | *Ref: {evt['source_resource']}*")
        
    if state.get("missing_actions"):
        lines.append("\n**Open Investigation Gaps:**")
        for m in state["missing_actions"]:
            lines.append(f"- ⚠️ {m['issue']} (Source: {m['resource']})")
            
    if state.get("hitl_proposals"):
        lines.append(f"\n**Human Review Items Pending:** {len(state['hitl_proposals'])} action(s) gated for clinical sign-off.")
        
    return {"summary_text": "\n".join(lines)}
