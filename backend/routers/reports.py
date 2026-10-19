"""Report generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Company, Report
from services.report_generator import generate_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate/{company_id}")
async def create_report(company_id: int, db: Session = Depends(get_db)):
    """Generate a comprehensive IPO readiness report for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        report = await generate_report(db, company_id)
        # Ensure both content and report_content are present
        if "content" not in report and "report_content" in report:
            report["content"] = report["report_content"]
        if "title" not in report:
            report["title"] = f"IPO Readiness Advisory Report — {company.name}"
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/company/{company_id}")
def list_reports(company_id: int, db: Session = Depends(get_db)):
    """List all reports for a company."""
    reports = db.query(Report).filter(
        Report.company_id == company_id
    ).order_by(Report.generated_at.desc()).all()

    return [{
        "id": r.id,
        "company_id": r.company_id,
        "title": f"Report #{r.id}",
        "summary": r.summary,
        "report_type": r.report_type,
        "generated_at": r.generated_at.isoformat(),
        "created_at": r.generated_at.isoformat(),
    } for r in reports]


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    company = db.query(Company).filter(Company.id == report.company_id).first()

    return {
        "id": report.id,
        "company_id": report.company_id,
        "company_name": company.name if company else "Unknown",
        "title": f"IPO Readiness Report — {company.name if company else 'Entity'}",
        "report_content": report.report_content,
        "content": report.report_content,
        "summary": report.summary,
        "report_type": report.report_type,
        "generated_at": report.generated_at.isoformat(),
        "created_at": report.generated_at.isoformat(),
    }


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"message": "Report deleted"}
