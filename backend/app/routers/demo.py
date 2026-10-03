from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.privacy import PRIVACY_STATEMENT
from app.models import Recommendation, Approval, QueryEvent, AuditLog
from app.seed_data import seed_database_force

router = APIRouter(prefix="/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demo_state(db: Session = Depends(get_db)):
    """
    Resets the demo benchmark database back to its pristine seed values.
    Enforces that zero production changes are touched.
    """
    seed_database_force(db)
    return {
        "success": True,
        "message": "Demo benchmark and virtual database state restored to initial seeded state.",
        "privacy_status": PRIVACY_STATEMENT,
    }
