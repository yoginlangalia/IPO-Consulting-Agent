"""IPO Readiness Agent — FastAPI Backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import init_db
from database.seed_rules import seed_rules
from routers.companies import router as companies_router
from routers.documents import router as documents_router
from routers.questionnaire import router as questionnaire_router
from routers.eligibility import router as eligibility_router
from routers.readiness import router as readiness_router
from routers.reports import router as reports_router

app = FastAPI(
    title="IPO Readiness Agent",
    description="AI-powered IPO readiness assessment tool based on SEBI ICDR regulations",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(companies_router)
app.include_router(documents_router)
app.include_router(questionnaire_router)
app.include_router(eligibility_router)
app.include_router(readiness_router)
app.include_router(reports_router)


@app.on_event("startup")
def on_startup():
    """Initialize database and seed rules on startup."""
    init_db()
    seed_rules()


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "IPO Readiness Agent"}
