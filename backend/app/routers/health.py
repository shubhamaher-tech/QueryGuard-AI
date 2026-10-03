from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime
from app.database import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"degraded: {str(e)}"

    return {
        "status": "healthy",
        "service": "QueryGuard AI",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "privacy_compliance": "ACTIVE",
    }
