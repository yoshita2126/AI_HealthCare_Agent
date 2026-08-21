from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ActionTier(str, Enum):
    TIER_1_AUTO = "TIER_1_AUTO"          # Automated administrative actions
    TIER_2_CLINICAL = "TIER_2_CLINICAL"  # Requires clinician review

class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"

class TimelineEvent(BaseModel):
    event_id: str
    patient_id: str
    event_type: str  # Consultation, LabOrder, LabResult, Referral, FollowUp
    timestamp: datetime
    status: str      # scheduled, pending, completed, overdue
    details: Dict[str, Any]
    source_resource: str  # e.g., "ServiceRequest/SR101", "Appointment/A502"

class HumanReviewItem(BaseModel):
    review_id: str
    patient_id: str
    action_type: str
    proposed_action: Dict[str, Any]
    clinical_rationale: str
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_comments: Optional[str] = None

class PatientSummary(BaseModel):
    patient_id: str
    current_phase: str
    active_concerns: List[str]
    timeline: List[TimelineEvent]
    pending_clinical_reviews: List[HumanReviewItem]
    grounded_summary_text: str