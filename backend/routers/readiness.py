"""Readiness scoring endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Company, ReadinessScore
from services.readiness_scorer import run_readiness_scoring

router = APIRouter(prefix="/api/readiness", tags=["readiness"])


@router.post("/score/{company_id}")
async def run_scoring(company_id: int, db: Session = Depends(get_db)):
    """Run readiness scoring for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    results = await run_readiness_scoring(db, company_id)

    total_weight = sum(r.get("weight", 25) for r in results)
    overall_score = sum(r["score"] * r.get("weight", 25) for r in results) / total_weight if total_weight > 0 else 0
    overall_score = round(overall_score, 1)

    tier = "High Readiness (IPO Ready)" if overall_score >= 80 else "Moderate Readiness (6-12 Months)" if overall_score >= 60 else "Early Stage / Restructuring Required"

    dimensions = {}
    for r in results:
        dimensions[r["category"]] = {
            "name": r.get("category_label", r["category"]),
            "score": r["score"],
            "weight": r.get("weight", 25),
            "details": r.get("details", {})
        }

    # Generate actionable gap matrix
    gaps = []
    for r in results:
        if r["score"] < 80:
            gaps.append({
                "dimension": r.get("category_label", r["category"]),
                "priority": "HIGH" if r["score"] < 65 else "MEDIUM",
                "description": f"Score in {r.get('category_label')} is currently {r['score']}%. Additional formalization required.",
                "recommendation": f"Review statutory policies and strengthen documentation for {r.get('category_label')}."
            })

    return {
        "company_id": company_id,
        "company_name": company.name,
        "overall_score": overall_score,
        "average_score": overall_score,
        "readiness_tier": tier,
        "dimensions": dimensions,
        "categories": results,
        "gaps": gaps
    }


@router.get("/results/{company_id}")
def get_scores(company_id: int, db: Session = Depends(get_db)):
    """Get stored readiness scores for a company."""
    scores = db.query(ReadinessScore).filter(
        ReadinessScore.company_id == company_id
    ).all()

    if not scores:
        return {"company_id": company_id, "categories": [], "dimensions": {}, "overall_score": 0, "message": "No readiness scoring has been run yet"}

    category_labels = {
        "financial_health": "Financial Preparedness",
        "governance": "Corporate Governance & Board",
        "legal_compliance": "Regulatory & Legal Compliance",
        "business_fundamentals": "Capital Structure & Restatement"
    }

    results = [{
        "category": s.category,
        "category_label": category_labels.get(s.category, s.category),
        "score": s.score,
        "assessment_type": s.assessment_type,
        "evidence": s.evidence,
        "details": s.details,
        "scored_at": s.scored_at.isoformat()
    } for s in scores]

    avg_score = sum(s.score for s in scores) / len(scores) if scores else 0
    avg_score = round(avg_score, 1)

    dimensions = {}
    for r in results:
        dimensions[r["category"]] = {
            "name": r.get("category_label", r["category"]),
            "score": r["score"],
            "details": r.get("details", {})
        }

    tier = "High Readiness (IPO Ready)" if avg_score >= 80 else "Moderate Readiness (6-12 Months)" if avg_score >= 60 else "Early Stage / Restructuring Required"

    return {
        "company_id": company_id,
        "overall_score": avg_score,
        "average_score": avg_score,
        "readiness_tier": tier,
        "dimensions": dimensions,
        "categories": results,
        "gaps": []
    }
