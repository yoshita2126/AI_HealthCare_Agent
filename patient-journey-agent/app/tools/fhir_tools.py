from datetime import datetime, timedelta
from typing import Any, Dict, List
from app.core.database import db_get_patient_events, db_add_patient_event, MOCK_PATIENTS_DB


def fetch_patient_events(patient_id: str) -> List[Dict[str, Any]]:
    """Fetches patient events from MongoDB repository with fallback."""
    events = db_get_patient_events(patient_id)
    if not events:
        # Fallback to in-memory MOCK_PATIENTS_DB if present
        events = MOCK_PATIENTS_DB.get(patient_id, [])
    return events


def record_patient_event(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Records a new clinical or intake event in the database."""
    return db_add_patient_event(event_dict)
