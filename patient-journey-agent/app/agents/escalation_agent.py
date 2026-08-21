import uuid
from typing import Any, Dict, List
from app.models.state import AgentState
from app.models.schemas import ActionTier, ReviewStatus

def escalation_node(state: AgentState) -> Dict[str, Any]:
    overdue: List[Dict[str, Any]] = []
    hitl_proposals: List[Dict[str, Any]] = []
    
    for evt in state.get("timeline", []):
        # Identify overdue follow-ups or critical referrals
        if evt["event_type"] in ["FollowUp", "Referral"] and evt["status"] in ["overdue", "unfulfilled"]:
            overdue.append(evt)
            
            # Clinical action requirement -> escalate to HITL queue
            hitl_proposals.append({
                "review_id": f"REV-{uuid.uuid4().hex[:6].upper()}",
                "patient_id": state["patient_id"],
                "action_type": "CRITICAL_FOLLOWUP_ESCALATION",
                "proposed_action": {
                    "action": "Urgent Re-booking & Alert to Cardiologist",
                    "target_service": evt["details"].get("specialty", "Cardiology Clinic"),
                    "associated_resource": evt["source_resource"]
                },
                "clinical_rationale": f"Action is overdue ({evt['event_type']}). Requires staff clearance before issuing alert.",
                "tier": ActionTier.TIER_2_CLINICAL.value,
                "status": ReviewStatus.PENDING.value
            })
            
    return {
        "overdue_followups": overdue,
        "hitl_proposals": hitl_proposals
    }
