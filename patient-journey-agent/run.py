"""
Patient Journey Agent - Interactive Terminal Runner & Demo
"""

import sys
import json

# Ensure UTF-8 output across all terminal environments
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import is_mongodb_connected, db_list_patients
from app.agents.graph import coordinator_app
from app.hitl.review_queue import add_to_queue, get_pending_reviews, update_review
from app.models.schemas import ReviewStatus


def main():
    print("=" * 75)
    print("🏥  AEGISCARE - PATIENT JOURNEY COORDINATION & CLINICIAN HITL AGENT")
    print("=" * 75)

    # 1. Check MongoDB Status
    mongo_ok = is_mongodb_connected()
    db_status = "CONNECTED (mongodb://localhost:27017/)" if mongo_ok else "IN-MEMORY FALLBACK (Local DB Offline)"
    print(f"\n[DATABASE STATUS] MongoDB: {db_status}")

    # 2. List Available Patients
    patients = db_list_patients()
    print(f"[REGISTERED PATIENTS] Found {len(patients)} patient(s) in database:")
    for p in patients:
        print(f"   • {p.get('patient_id')}: {p.get('name')} (Age: {p.get('age')}, {p.get('condition')})")

    # 3. Coordinate Active Patient
    patient_id = "PATIENT_101"
    print(f"\n[AGENT COORDINATION] Executing multi-agent pipeline for: {patient_id}...")
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

    # Stage proposals in HITL review queue
    for proposal in result.get("hitl_proposals", []):
        add_to_queue(proposal)

    # 4. Print Grounded Summary
    print("\n" + "-" * 55)
    print("📋 EVIDENCE-GROUNDED CLINICAL SUMMARY:")
    print("-" * 55)
    print(result.get("summary_text"))
    print("-" * 55)

    # 5. Display Pending Clinician Reviews
    pending_items = get_pending_reviews(patient_id)
    print(f"\n🚨 CLINICIAN HITL REVIEW QUEUE ({len(pending_items)} item(s) pending):")
    for i, item in enumerate(pending_items, start=1):
        print(f"\n  [{i}] Review ID: {item.review_id}")
        print(f"      Action Type : {item.action_type}")
        print(f"      Rationale   : {item.clinical_rationale}")
        print(f"      Proposed    : {json.dumps(item.proposed_action, indent=8)}")
        print(f"      Status      : {item.status}")

    # 6. Simulate Clinician Approval on First Item
    if pending_items:
        first_id = pending_items[0].review_id
        print(f"\n👩‍⚕️ [CLINICIAN DECISION] Approving review item {first_id}...")
        resolved = update_review(
            review_id=first_id,
            status=ReviewStatus.APPROVED,
            reviewer="Dr. Sarah Chen (Lead Cardiologist)",
            comments="Approved expedited cardiology echocardiogram and alert.",
        )
        print(f"   Updated Status  : {resolved.status}")
        print(f"   Reviewed By     : {resolved.reviewed_by}")
        print(f"   Comments        : {resolved.review_comments}")

    print("\n" + "=" * 75)
    print("✨ Execution Complete!")
    print("🌐 Web Application is live at : http://localhost:8000")
    print("📖 API Documentation & Swagger: http://localhost:8000/docs")
    print("=" * 75)


if __name__ == "__main__":
    main()
