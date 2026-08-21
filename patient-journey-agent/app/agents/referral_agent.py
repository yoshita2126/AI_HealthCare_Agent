"""
Referral Agent: Determines appropriate clinical department or specialist referral.
"""

from typing import Dict, Any
from ..models.state import AgentGraphState


def run_referral_agent(state: AgentGraphState) -> Dict[str, Any]:
    """
    Assesses patient case for specialist routing and scheduling.
    """
    suggestions = state.get("diagnostic_suggestions", [])
    specialty = "General Practice"
    if any("Chest" in s for s in suggestions):
        specialty = "Pulmonology"
    return {
        "referral_recommendation": {
            "specialty": specialty,
            "priority": "standard",
        }
    }
