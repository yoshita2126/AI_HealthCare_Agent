from typing import Annotated, Any, Dict, List
from typing_extensions import TypedDict
import operator

class AgentState(TypedDict):
    patient_id: str
    timeline: Annotated[List[Dict[str, Any]], operator.add]
    missing_actions: Annotated[List[Dict[str, Any]], operator.add]
    overdue_followups: Annotated[List[Dict[str, Any]], operator.add]
    hitl_proposals: Annotated[List[Dict[str, Any]], operator.add]
    current_phase: str
    summary_text: str
