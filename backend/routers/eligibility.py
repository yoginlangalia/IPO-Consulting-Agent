"""Eligibility check endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Company, EligibilityResult, SebiRule
from services.eligibility_engine import run_eligibility_checks

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    """List all SEBI ICDR rules stored in the database."""
    rules = db.query(SebiRule).all()
    return [{
        "id": r.id,
        "rule_code": r.rule_code,
        "regulation": r.regulation,
        "regulation_ref": r.regulation,
        "category": r.category,
        "title": r.title,
        "description": r.description,
        "threshold_value": r.threshold_value,
        "threshold_criteria": r.threshold_value,
        "check_type": r.check_type,
        "rule_type": "QUANTITATIVE" if r.check_type == "code" else "QUALITATIVE",
        "route": r.route,
        "applicable_track": r.route or "BOTH",
        "is_mandatory": True,
    } for r in rules]


@router.post("/check/{company_id}")
async def run_checks(company_id: int, db: Session = Depends(get_db)):
    """Run all eligibility checks for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    results = await run_eligibility_checks(db, company_id)

    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    insufficient_count = sum(1 for r in results if r["status"] in ["CONDITIONAL", "INSUFFICIENT_DATA"])

    reg_6_1_ok = not any(r["status"] == "FAIL" for r in results if "6_1" in r.get("rule_code", ""))
    reg_6_2_ok = True

    overall_status = "PASS" if reg_6_1_ok else "CONDITIONAL"

    return {
        "company_id": company_id,
        "company_name": company.name,
        "overall_status": overall_status,
        "total_rules": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "insufficient_data": insufficient_count,
        "route_summary": {
            "reg_6_1_eligible": reg_6_1_ok,
            "reg_6_2_eligible": reg_6_2_ok,
            "recommended_route": "REG_6_1" if reg_6_1_ok else "REG_6_2"
        },
        "results": results
    }


@router.get("/results/{company_id}")
def get_results(company_id: int, db: Session = Depends(get_db)):
    """Get stored eligibility results for a company."""
    results = db.query(EligibilityResult, SebiRule).join(
        SebiRule, EligibilityResult.rule_id == SebiRule.id
    ).filter(
        EligibilityResult.company_id == company_id
    ).all()

    if not results:
        return {"company_id": company_id, "results": [], "route_summary": None, "message": "No eligibility checks have been run yet"}

    formatted_results = [{
        "rule_code": rule.rule_code,
        "rule_title": rule.title,
        "regulation": rule.regulation,
        "regulation_ref": rule.regulation,
        "category": rule.category,
        "check_type": rule.check_type,
        "threshold": rule.threshold_value,
        "status": result.status.upper(),
        "actual_value": result.actual_value,
        "evidence": result.evidence,
        "checked_at": result.checked_at.isoformat()
    } for result, rule in results]

    passed_count = sum(1 for r in formatted_results if r["status"] == "PASS")
    failed_count = sum(1 for r in formatted_results if r["status"] == "FAIL")
    insufficient_count = sum(1 for r in formatted_results if r["status"] in ["CONDITIONAL", "INSUFFICIENT_DATA"])
    reg_6_1_ok = not any(r["status"] == "FAIL" for r in formatted_results if "6_1" in r["rule_code"])

    return {
        "company_id": company_id,
        "overall_status": "PASS" if reg_6_1_ok else "CONDITIONAL",
        "total_rules": len(formatted_results),
        "passed": passed_count,
        "failed": failed_count,
        "insufficient_data": insufficient_count,
        "route_summary": {
            "reg_6_1_eligible": reg_6_1_ok,
            "reg_6_2_eligible": True,
            "recommended_route": "REG_6_1" if reg_6_1_ok else "REG_6_2"
        },
        "results": formatted_results
    }
