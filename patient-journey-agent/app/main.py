import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.agents.graph import coordinator_app
from app.hitl.review_queue import add_to_queue, get_pending_reviews, update_review
from app.models.schemas import HumanReviewItem, ReviewStatus, TimelineEvent
from app.core.database import (
    is_mongodb_connected,
    db_list_patients,
    db_get_patient,
    db_create_patient,
    db_get_patient_events,
    db_add_patient_event,
)

app = FastAPI(
    title="Healthcare Patient Journey Coordination Agent",
    description="Multi-agent orchestration platform connecting patients and clinicians with FHIR alignment and MongoDB persistence.",
    version="1.0.0",
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ReviewDecisionRequest(BaseModel):
    decision: ReviewStatus
    reviewer_id: str
    comments: str


class PatientCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    name: str
    age: int
    gender: str
    condition: str
    primary_physician: Optional[str] = "Dr. General Practice"


class TimelineEventCreateRequest(BaseModel):
    event_type: str
    status: str = "completed"
    details: Dict[str, Any] = Field(default_factory=dict)
    source_resource: Optional[str] = None


class PatientIntakeChatRequest(BaseModel):
    message: str
    symptoms: List[str] = Field(default_factory=list)


# --- Web Page Route ---

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Patient Journey Agent API is active. Web UI initializing."}


# --- System & DB Health ---

@app.get("/api/db/status")
def get_db_status():
    connected = is_mongodb_connected()
    return {
        "mongodb_connected": connected,
        "uri": "mongodb://localhost:27017/",
        "database": "patient_journey_db",
        "mode": "MongoDB Cluster / Local Daemon" if connected else "Resilient In-Memory Mode (Auto-syncs on DB connect)",
    }


# --- Patient Management ---

@app.get("/api/patients")
def list_patients():
    return db_list_patients()


@app.post("/api/patients")
def create_patient(payload: PatientCreateRequest):
    pid = payload.patient_id or f"PATIENT_{uuid.uuid4().hex[:4].upper()}"
    names = payload.name.strip().split()
    initials = f"{names[0][0]}{names[-1][0]}".upper() if len(names) > 1 else payload.name[:2].upper()
    patient_record = {
        "patient_id": pid,
        "name": payload.name,
        "age": payload.age,
        "gender": payload.gender,
        "condition": payload.condition,
        "primary_physician": payload.primary_physician,
        "avatar_initials": initials,
        "created_at": datetime.utcnow(),
    }
    db_create_patient(patient_record)
    return patient_record


@app.get("/api/patients/{patient_id}")
def get_patient_details(patient_id: str):
    patient = db_get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    events = db_get_patient_events(patient_id)
    reviews = get_pending_reviews(patient_id)
    return {
        "patient": patient,
        "timeline": events,
        "pending_reviews": reviews,
    }


@app.post("/api/patients/{patient_id}/events")
def add_patient_event(patient_id: str, payload: TimelineEventCreateRequest):
    patient = db_get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    event_id = f"EVT_{uuid.uuid4().hex[:6].upper()}"
    event_record = {
        "event_id": event_id,
        "patient_id": patient_id,
        "event_type": payload.event_type,
        "timestamp": datetime.utcnow(),
        "status": payload.status,
        "details": payload.details,
        "source_resource": payload.source_resource or f"CarePlan/{event_id}",
    }
    db_add_patient_event(event_record)
    return {"status": "success", "event": event_record}


# --- Interactive Patient Chat & Intake ---

@app.post("/api/patients/{patient_id}/intake")
def patient_intake_interaction(patient_id: str, payload: PatientIntakeChatRequest):
    """
    Handles conversational symptom check-in by patient.
    Logs patient event, runs multi-agent coordination, and returns natural language guidance.
    """
    patient = db_get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Record intake consultation message
    event_id = f"EVT_CHAT_{uuid.uuid4().hex[:5].upper()}"
    intake_event = {
        "event_id": event_id,
        "patient_id": patient_id,
        "event_type": "Consultation",
        "timestamp": datetime.utcnow(),
        "status": "completed",
        "details": {
            "channel": "Patient Web Portal",
            "patient_message": payload.message,
            "reported_symptoms": payload.symptoms,
        },
        "source_resource": f"Encounter/{event_id}",
    }
    db_add_patient_event(intake_event)

    # Execute coordination graph
    initial_state = {
        "patient_id": patient_id,
        "timeline": [],
        "missing_actions": [],
        "overdue_followups": [],
        "hitl_proposals": [],
        "current_phase": "Assessment & Diagnostics",
        "summary_text": "",
    }
    result = coordinator_app.invoke(initial_state)

    # Store any proposals in HITL queue
    new_proposals = []
    for proposal in result.get("hitl_proposals", []):
        add_to_queue(proposal)
        new_proposals.append(proposal)

    # Formulate friendly, reassuring patient response
    missing = result.get("missing_actions", [])
    overdue = result.get("overdue_followups", [])

    patient_response_lines = [
        f"Thank you for checking in, {patient.get('name', 'Patient')}. We have updated your care record with your message."
    ]

    if payload.symptoms:
        patient_response_lines.append(f"Noted symptoms: {', '.join(payload.symptoms)}.")

    if new_proposals:
        patient_response_lines.append(
            f"⚡ Our clinical coordination system flagged {len(new_proposals)} item(s) for physician priority review to ensure you receive timely care."
        )

    if missing:
        patient_response_lines.append("📌 You have pending diagnostic tests scheduled. Please review your active care plan below.")

    patient_response_lines.append("Your care team is monitoring your journey closely.")

    return {
        "agent_response": " ".join(patient_response_lines),
        "coordination_result": {
            "phase": result.get("current_phase"),
            "summary": result.get("summary_text"),
            "hitl_items_created": len(new_proposals),
            "overdue_count": len(overdue),
        },
    }


# --- Journey Coordination ---

@app.post("/journey/coordinate/{patient_id}")
def coordinate_patient_journey(patient_id: str):
    """Executes the multi-agent pipeline and stages any clinical actions for review."""
    initial_state = {
        "patient_id": patient_id,
        "timeline": [],
        "missing_actions": [],
        "overdue_followups": [],
        "hitl_proposals": [],
        "current_phase": "Intake",
        "summary_text": "",
    }

    result = coordinator_app.invoke(initial_state)

    # Store proposals in the HITL review queue
    for proposal in result.get("hitl_proposals", []):
        add_to_queue(proposal)

    return {
        "patient_id": patient_id,
        "phase": result.get("current_phase"),
        "summary": result.get("summary_text"),
        "overdue_count": len(result.get("overdue_followups", [])),
        "hitl_items_created": len(result.get("hitl_proposals", []))
    }


# --- HITL Reviews ---

@app.get("/hitl/reviews", response_model=List[HumanReviewItem])
def list_reviews(patient_id: Optional[str] = None):
    """Retrieves all gated clinical actions awaiting human review."""
    return get_pending_reviews(patient_id)


@app.post("/hitl/reviews/{review_id}/action")
def resolve_review(review_id: str, payload: ReviewDecisionRequest):
    """Allows authorized staff to Approve, Reject, or Modify proposed actions."""
    updated = update_review(
        review_id=review_id,
        status=payload.decision,
        reviewer=payload.reviewer_id,
        comments=payload.comments,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Review item not found")
    return {"status": "success", "item": updated}
