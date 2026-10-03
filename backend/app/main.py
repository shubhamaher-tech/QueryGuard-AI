import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.seed_data import seed_database
from app.routers import health, dashboard, queries, recommendations, audit, telemetry, users, demo
from app.llm import router as llm_router
from app.ml import router as ml_router
from app.analysis import router as analysis_router
from app.benchmarks import router as benchmarks_router
from app.realtime import router as realtime_router

# Set up privacy-compliant logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [QueryGuardPrivacySafe] %(message)s",
)
logger = logging.getLogger("queryguard.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed realistic mock records
    logger.info("Initializing QueryGuard database schema...")
    init_db()
    db = SessionLocal()
    try:
        logger.info("Seeding anonymized PostgreSQL workload metadata...")
        seed_database(db)
        logger.info("Seed data ready. Privacy compliance: ACTIVE.")
    finally:
        db.close()
    yield
    logger.info("QueryGuard AI shutting down.")


app = FastAPI(
    title="QueryGuard AI API",
    description=(
        "Privacy-first PostgreSQL performance-tuning copilot. "
        "Analyzes strictly anonymized SQL/query-plan metadata, detects slow-query bottlenecks, "
        "recommends safe database optimizations, simulates potential impact, explains recommendations with evidence, "
        "and enforces DBA approval before any production change."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(queries.router, prefix=settings.API_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(telemetry.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(demo.router, prefix=settings.API_PREFIX)
app.include_router(llm_router.router, prefix=settings.API_PREFIX)
app.include_router(ml_router.router, prefix=settings.API_PREFIX)
app.include_router(analysis_router, prefix=settings.API_PREFIX)
app.include_router(benchmarks_router.router, prefix=settings.API_PREFIX)
app.include_router(realtime_router.router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "service": "QueryGuard AI",
        "description": "Privacy-First PostgreSQL Performance Tuning Copilot",
        "docs": "/docs",
        "privacy": "Active. Zero raw customer data ingestion.",
        "status": "online",
    }
