from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import HumanReviewItem, ReviewStatus
from app.core.database import (
    db_save_review_item,
    db_get_pending_reviews,
    db_update_review_item,
    _FALLBACK_REVIEWS,
)

REVIEW_STORE: Dict[str, HumanReviewItem] = {}


def add_to_queue(item_dict: dict) -> HumanReviewItem:
    item = HumanReviewItem(**item_dict)
    REVIEW_STORE[item.review_id] = item
    db_save_review_item(item.model_dump())
    return item


def get_pending_reviews(patient_id: Optional[str] = None) -> List[HumanReviewItem]:
    raw_items = db_get_pending_reviews(patient_id)
    items: List[HumanReviewItem] = []
    for r in raw_items:
        try:
            items.append(HumanReviewItem(**r))
        except Exception:
            pass
    if not items:
        items = list(REVIEW_STORE.values())
        if patient_id:
            items = [i for i in items if i.patient_id == patient_id]
    return items


def update_review(review_id: str, status: ReviewStatus, reviewer: str, comments: str) -> Optional[HumanReviewItem]:
    status_str = status.value if hasattr(status, "value") else str(status)
    updated_dict = db_update_review_item(review_id, status_str, reviewer, comments)
    if updated_dict:
        item = HumanReviewItem(**updated_dict)
        REVIEW_STORE[review_id] = item
        return item
    if review_id in REVIEW_STORE:
        item = REVIEW_STORE[review_id]
        item.status = status
        item.reviewed_by = reviewer
        item.reviewed_at = datetime.utcnow().isoformat()
        item.review_comments = comments
        return item
    return None
