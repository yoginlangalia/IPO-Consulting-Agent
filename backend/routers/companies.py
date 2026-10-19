"""Company management endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from database.session import get_db
from database.models import Company, Document, QuestionnaireResponse, EligibilityResult, ReadinessScore, Report

router = APIRouter(prefix="/api/companies", tags=["companies"])


class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    incorporation_date: Optional[str] = None
    incorporation_year: Optional[int] = None
    entity_type: Optional[str] = None
    target_track: Optional[str] = "REG_6_1"
    target_ipo_date: Optional[str] = None
    description: Optional[str] = None
    financial_data: Optional[dict] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    incorporation_date: Optional[str] = None
    incorporation_year: Optional[int] = None
    entity_type: Optional[str] = None
    target_track: Optional[str] = None
    target_ipo_date: Optional[str] = None
    description: Optional[str] = None
    financial_data: Optional[dict] = None
    readiness_score: Optional[float] = None
    eligibility_status: Optional[str] = None


@router.get("")
def list_companies(db: Session = Depends(get_db)):
    """List all companies with assessment progress and status."""
    companies = db.query(Company).order_by(Company.created_at.desc()).all()
    result = []
    for c in companies:
        doc_count = db.query(Document).filter(Document.company_id == c.id).count()
        questionnaire = db.query(QuestionnaireResponse).filter(
            QuestionnaireResponse.company_id == c.id
        ).first()
        q_completed = questionnaire.completed if questionnaire else 0

        elig_count = db.query(EligibilityResult).filter(
            EligibilityResult.company_id == c.id
        ).count()

        readiness_count = db.query(ReadinessScore).filter(
            ReadinessScore.company_id == c.id
        ).count()

        report_count = db.query(Report).filter(Report.company_id == c.id).count()

        sec = c.sector or c.industry or "General Sector"

        result.append({
            "id": c.id,
            "name": c.name,
            "industry": c.industry or sec,
            "sector": sec,
            "incorporation_date": c.incorporation_date.isoformat() if c.incorporation_date else None,
            "incorporation_year": c.incorporation_year,
            "entity_type": c.entity_type,
            "target_track": c.target_track or "REG_6_1",
            "target_ipo_date": c.target_ipo_date,
            "description": c.description,
            "financial_data": c.financial_data or {},
            "readiness_score": c.readiness_score,
            "eligibility_status": c.eligibility_status or "PENDING",
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else c.created_at.isoformat(),
            "documents_count": doc_count,
            "questionnaire_completed": bool(q_completed),
            "eligibility_checked": elig_count > 0,
            "readiness_scored": readiness_count > 0,
            "reports_count": report_count,
        })
    return result


@router.post("")
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company assessment."""
    inc_date = None
    if data.incorporation_date:
        try:
            inc_date = datetime.strptime(data.incorporation_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    sec = data.sector or data.industry or "Technology & SaaS"

    company = Company(
        name=data.name,
        industry=data.industry or sec,
        sector=sec,
        incorporation_date=inc_date,
        incorporation_year=data.incorporation_year,
        entity_type=data.entity_type or "Public Limited Company",
        target_track=data.target_track or "REG_6_1",
        target_ipo_date=data.target_ipo_date,
        description=data.description,
        financial_data=data.financial_data or {},
        eligibility_status="PENDING",
        status="draft"
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    return {
        "id": company.id,
        "name": company.name,
        "sector": company.sector,
        "industry": company.industry,
        "target_track": company.target_track,
        "target_ipo_date": company.target_ipo_date,
        "incorporation_year": company.incorporation_year,
        "financial_data": company.financial_data,
        "status": company.status,
        "created_at": company.created_at.isoformat()
    }


@router.get("/{company_id}")
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get a company's full details."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    doc_count = db.query(Document).filter(Document.company_id == company_id).count()
    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.company_id == company_id
    ).first()
    elig_count = db.query(EligibilityResult).filter(
        EligibilityResult.company_id == company_id
    ).count()
    readiness_count = db.query(ReadinessScore).filter(
        ReadinessScore.company_id == company_id
    ).count()
    report_count = db.query(Report).filter(Report.company_id == company_id).count()

    sec = company.sector or company.industry or "General Sector"

    return {
        "id": company.id,
        "name": company.name,
        "industry": company.industry or sec,
        "sector": sec,
        "incorporation_date": company.incorporation_date.isoformat() if company.incorporation_date else None,
        "incorporation_year": company.incorporation_year,
        "entity_type": company.entity_type,
        "target_track": company.target_track or "REG_6_1",
        "target_ipo_date": company.target_ipo_date,
        "description": company.description,
        "financial_data": company.financial_data or {},
        "readiness_score": company.readiness_score,
        "eligibility_status": company.eligibility_status or "PENDING",
        "status": company.status,
        "created_at": company.created_at.isoformat(),
        "updated_at": company.updated_at.isoformat() if company.updated_at else company.created_at.isoformat(),
        "documents_count": doc_count,
        "questionnaire_completed": bool(questionnaire.completed) if questionnaire else False,
        "eligibility_checked": elig_count > 0,
        "readiness_scored": readiness_count > 0,
        "reports_count": report_count,
    }


@router.put("/{company_id}")
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db)):
    """Update a company's details."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if data.name is not None: company.name = data.name
    if data.industry is not None: company.industry = data.industry
    if data.sector is not None: company.sector = data.sector
    if data.incorporation_year is not None: company.incorporation_year = data.incorporation_year
    if data.target_track is not None: company.target_track = data.target_track
    if data.target_ipo_date is not None: company.target_ipo_date = data.target_ipo_date
    if data.description is not None: company.description = data.description
    if data.financial_data is not None: company.financial_data = data.financial_data
    if data.readiness_score is not None: company.readiness_score = data.readiness_score
    if data.eligibility_status is not None: company.eligibility_status = data.eligibility_status
    if data.entity_type is not None: company.entity_type = data.entity_type

    db.commit()
    db.refresh(company)
    return {"message": "Company updated", "id": company.id}


@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    """Delete a company and all its related data."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted"}
