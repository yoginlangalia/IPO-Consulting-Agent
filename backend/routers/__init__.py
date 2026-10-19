from routers.companies import router as companies_router
from routers.documents import router as documents_router
from routers.questionnaire import router as questionnaire_router
from routers.eligibility import router as eligibility_router
from routers.readiness import router as readiness_router
from routers.reports import router as reports_router

__all__ = [
    "companies_router",
    "documents_router",
    "questionnaire_router",
    "eligibility_router",
    "readiness_router",
    "reports_router",
]
