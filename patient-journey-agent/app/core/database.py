"""
MongoDB database connection, schema setup, and data access repositories.
Connects to mongodb://localhost:27017/ (patient_journey_db).
Includes fallback resilience and automatic initial dataset seeding.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "patient_journey_db")

# In-memory fallback stores (used if MongoDB service is unreachable)
_FALLBACK_PATIENTS: Dict[str, Dict[str, Any]] = {}
_FALLBACK_EVENTS: Dict[str, List[Dict[str, Any]]] = {}
_FALLBACK_REVIEWS: Dict[str, Dict[str, Any]] = {}
_FALLBACK_COORDINATION_LOGS: List[Dict[str, Any]] = []
MOCK_PATIENTS_DB = _FALLBACK_EVENTS

_mongo_client: Optional[MongoClient] = None
_db = None


def get_mongo_client() -> Optional[MongoClient]:
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            # Test connectivity
            _mongo_client.admin.command("ping")
            logger.info("Connected to MongoDB successfully at %s", MONGO_URI)
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as err:
            logger.warning("MongoDB not reachable at %s: %s. Using resilient in-memory store.", MONGO_URI, err)
            _mongo_client = None
    return _mongo_client


def get_db():
    client = get_mongo_client()
    if client is not None:
        return client[DB_NAME]
    return None


def is_mongodb_connected() -> bool:
    try:
        client = get_mongo_client()
        if client is not None:
            client.admin.command("ping")
            return True
    except Exception:
        pass
    return False


def seed_initial_data_if_needed():
    """Populates initial mock clinical dataset if collections are empty."""
    default_patients = [
        {
            "patient_id": "PATIENT_101",
            "name": "Eleanor Vance",
            "age": 58,
            "gender": "Female",
            "condition": "Suspected Angina / CAD",
            "primary_physician": "Dr. Sarah Chen (Cardiology)",
            "avatar_initials": "EV",
            "created_at": datetime.utcnow() - timedelta(days=15),
        },
        {
            "patient_id": "PATIENT_102",
            "name": "Marcus Aurelius Reed",
            "age": 46,
            "gender": "Male",
            "condition": "Post-Acute Bronchial Assessment",
            "primary_physician": "Dr. Alan Grant (Pulmonology)",
            "avatar_initials": "MR",
            "created_at": datetime.utcnow() - timedelta(days=7),
        },
        {
            "patient_id": "PATIENT_103",
            "name": "Sophia Lin",
            "age": 34,
            "gender": "Female",
            "condition": "Endocrine & Metabolic Monitoring",
            "primary_physician": "Dr. Emily Taylor (Endocrinology)",
            "avatar_initials": "SL",
            "created_at": datetime.utcnow() - timedelta(days=3),
        }
    ]

    default_events = [
        {
            "event_id": "EVT_01",
            "patient_id": "PATIENT_101",
            "event_type": "Consultation",
            "timestamp": datetime.utcnow() - timedelta(days=10),
            "status": "completed",
            "details": {"doctor": "Dr. Sarah Chen (Cardiology)", "diagnosis": "Suspected Angina"},
            "source_resource": "Encounter/ENC-901",
        },
        {
            "event_id": "EVT_02",
            "patient_id": "PATIENT_101",
            "event_type": "LabOrder",
            "timestamp": datetime.utcnow() - timedelta(days=10),
            "status": "pending",
            "details": {"test": "Lipid Panel & Troponin-I", "urgency": "High"},
            "source_resource": "ServiceRequest/SR-401",
        },
        {
            "event_id": "EVT_03",
            "patient_id": "PATIENT_101",
            "event_type": "Referral",
            "timestamp": datetime.utcnow() - timedelta(days=9),
            "status": "unfulfilled",
            "details": {"specialty": "Echocardiogram Imaging", "target_window_days": 5},
            "source_resource": "ServiceRequest/SR-402",
        },
        {
            "event_id": "EVT_04",
            "patient_id": "PATIENT_101",
            "event_type": "FollowUp",
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "status": "overdue",
            "details": {"plan": "Review echo results with Cardiologist"},
            "source_resource": "CarePlan/CP-105",
        },
        # Patient 102 events
        {
            "event_id": "EVT_102_01",
            "patient_id": "PATIENT_102",
            "event_type": "Consultation",
            "timestamp": datetime.utcnow() - timedelta(days=5),
            "status": "completed",
            "details": {"doctor": "Dr. Alan Grant", "diagnosis": "Persistent Cough & Dyspnea"},
            "source_resource": "Encounter/ENC-102-01",
        },
        {
            "event_id": "EVT_102_02",
            "patient_id": "PATIENT_102",
            "event_type": "LabOrder",
            "timestamp": datetime.utcnow() - timedelta(days=5),
            "status": "pending",
            "details": {"test": "High-Resolution Chest CT & Spirometry", "urgency": "Standard"},
            "source_resource": "ServiceRequest/SR-102-02",
        },
    ]

    db = get_db()
    if db is not None:
        try:
            if db.patients.count_documents({}) == 0:
                db.patients.insert_many(default_patients)
                logger.info("Seeded %d patients into MongoDB.", len(default_patients))
            if db.events.count_documents({}) == 0:
                db.events.insert_many(default_events)
                logger.info("Seeded %d events into MongoDB.", len(default_events))
        except Exception as e:
            logger.warning("Error seeding MongoDB: %s", e)

    # Also seed fallback in-memory store
    for p in default_patients:
        _FALLBACK_PATIENTS[p["patient_id"]] = p
    for e in default_events:
        pid = e["patient_id"]
        if pid not in _FALLBACK_EVENTS:
            _FALLBACK_EVENTS[pid] = []
        _FALLBACK_EVENTS[pid].append(e)


# Initialize seeds on import
seed_initial_data_if_needed()


# --- Data Access Methods ---

def db_list_patients() -> List[Dict[str, Any]]:
    db = get_db()
    if db is not None:
        try:
            patients = list(db.patients.find({}, {"_id": 0}))
            if patients:
                return patients
        except Exception:
            pass
    return list(_FALLBACK_PATIENTS.values())


def db_get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    if db is not None:
        try:
            doc = db.patients.find_one({"patient_id": patient_id}, {"_id": 0})
            if doc:
                return doc
        except Exception:
            pass
    return _FALLBACK_PATIENTS.get(patient_id)


def db_create_patient(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    pid = patient_dict["patient_id"]
    db = get_db()
    if db is not None:
        try:
            db.patients.update_one({"patient_id": pid}, {"$set": patient_dict}, upsert=True)
        except Exception as e:
            logger.warning("Failed saving patient to MongoDB: %s", e)
    _FALLBACK_PATIENTS[pid] = patient_dict
    return patient_dict


def db_get_patient_events(patient_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    if db is not None:
        try:
            docs = list(db.events.find({"patient_id": patient_id}, {"_id": 0}))
            if docs:
                return docs
        except Exception:
            pass
    return _FALLBACK_EVENTS.get(patient_id, [])


def db_add_patient_event(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    pid = event_dict["patient_id"]
    db = get_db()
    if db is not None:
        try:
            db.events.insert_one(event_dict.copy())
        except Exception as e:
            logger.warning("Failed adding event to MongoDB: %s", e)
    if pid not in _FALLBACK_EVENTS:
        _FALLBACK_EVENTS[pid] = []
    _FALLBACK_EVENTS[pid].append(event_dict)
    return event_dict


def db_save_review_item(item_dict: Dict[str, Any]) -> Dict[str, Any]:
    review_id = item_dict["review_id"]
    db = get_db()
    if db is not None:
        try:
            db.reviews.update_one({"review_id": review_id}, {"$set": item_dict}, upsert=True)
        except Exception as e:
            logger.warning("Failed saving review to MongoDB: %s", e)
    _FALLBACK_REVIEWS[review_id] = item_dict
    return item_dict


def db_get_pending_reviews(patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    if db is not None:
        try:
            query = {}
            if patient_id:
                query["patient_id"] = patient_id
            docs = list(db.reviews.find(query, {"_id": 0}))
            if docs:
                return docs
        except Exception:
            pass
    items = list(_FALLBACK_REVIEWS.values())
    if patient_id:
        items = [i for i in items if i.get("patient_id") == patient_id]
    return items


def db_update_review_item(review_id: str, status: str, reviewer: str, comments: str) -> Optional[Dict[str, Any]]:
    update_data = {
        "status": status,
        "reviewed_by": reviewer,
        "reviewed_at": datetime.utcnow().isoformat(),
        "review_comments": comments,
    }
    db = get_db()
    if db is not None:
        try:
            db.reviews.update_one({"review_id": review_id}, {"$set": update_data})
            doc = db.reviews.find_one({"review_id": review_id}, {"_id": 0})
            if doc:
                _FALLBACK_REVIEWS[review_id] = doc
                return doc
        except Exception as e:
            logger.warning("Failed updating review in MongoDB: %s", e)
    if review_id in _FALLBACK_REVIEWS:
        _FALLBACK_REVIEWS[review_id].update(update_data)
        return _FALLBACK_REVIEWS[review_id]
    return None
