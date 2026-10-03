import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, QueryEvent, Recommendation, AuditLog, Approval
from app.routers.recommendations import approve_recommendation, reject_recommendation
from app.schemas import ApprovalRequest, RejectionRequest


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    # Seed one test query and recommendation
    query = QueryEvent(
        id="QE-APP-01",
        fingerprint="fp_app_01",
        anonymized_sql="SELECT * FROM TBL_A12 WHERE COL_R01 = :INT",
        table_token="TBL_A12",
        avg_latency_ms=1200.0,
        primary_bottleneck="Sequential Scan",
        plan_json={},
    )
    rec = Recommendation(
        id="REC-APP-01",
        query_id="QE-APP-01",
        title="Test Index",
        type="INDEX_COMPOSITE",
        recommended_action="CREATE INDEX CONCURRENTLY idx_test ON TBL_A12 (COL_R01);",
        rationale="Test rationale",
        status="PENDING",
        xai_evidence={},
    )
    db.add(query)
    db.add(rec)
    db.commit()

    yield db
    db.close()


def test_approval_workflow_and_audit_logging(db_session):
    payload = ApprovalRequest(
        actor_id="DBA_TEST_01",
        comment="Approved for next maintenance window",
    )
    resp = approve_recommendation("REC-APP-01", payload, db_session)

    assert resp.action == "APPROVED"
    assert resp.actor_id == "DBA_TEST_01"

    # Verify recommendation status is updated
    rec = db_session.query(Recommendation).filter(Recommendation.id == "REC-APP-01").first()
    assert rec.status == "APPROVED"

    # Verify audit log entry is created
    audit = db_session.query(AuditLog).filter(AuditLog.recommendation_id == "REC-APP-01").first()
    assert audit is not None
    assert audit.action_type == "RECOMMENDATION_APPROVED"
    assert audit.actor_id == "DBA_TEST_01"
    assert "TBL_A12" in audit.anonymized_target


def test_rejection_workflow_and_audit_logging(db_session):
    payload = RejectionRequest(
        actor_id="DBA_TEST_02",
        comment="Rejected due to index storage overhead limits",
    )
    resp = reject_recommendation("REC-APP-01", payload, db_session)

    assert resp.action == "REJECTED"
    rec = db_session.query(Recommendation).filter(Recommendation.id == "REC-APP-01").first()
    assert rec.status == "REJECTED"

    audit = db_session.query(AuditLog).filter(
        AuditLog.recommendation_id == "REC-APP-01",
        AuditLog.action_type == "RECOMMENDATION_REJECTED"
    ).first()
    assert audit is not None
    assert audit.actor_id == "DBA_TEST_02"
