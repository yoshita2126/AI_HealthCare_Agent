"""
Audit logging service for compliance and traceability in patient interactions.
"""

import datetime
from typing import Dict, Any


def log_audit_event(event_type: str, patient_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": event_type,
        "patient_id": patient_id,
        "details": details,
    }
    # In production, persist record to a secure audit store
    return record
