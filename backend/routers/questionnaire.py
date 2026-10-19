"""Questionnaire endpoints — 30-question intake form based on SEBI ICDR requirements."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.session import get_db
from database.models import QuestionnaireResponse, Company

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])

# Questionnaire structure — used by both frontend and backend
QUESTIONNAIRE_SCHEMA = [
    {
        "section": "Company Background",
        "questions": [
            {"id": "q1_company_name", "label": "What is the full legal name of the company?", "type": "text", "required": True},
            {"id": "q2_incorporation_date", "label": "Date of incorporation?", "type": "date", "required": True},
            {"id": "q3_is_public_company", "label": "Is the company currently a Public Limited Company?", "type": "select", "options": ["Yes", "No", "Conversion planned"], "required": True},
            {"id": "q4_industry", "label": "What industry / sector does the company operate in?", "type": "text", "required": True},
            {"id": "q5_name_changed", "label": "Has the company changed its name in the last 1 year?", "type": "select", "options": ["No", "Yes"], "required": True},
            {"id": "q5b_name_change_revenue", "label": "If yes, what % of revenue comes from the new activity?", "type": "number", "required": False, "conditional": "q5_name_changed=Yes"},
        ]
    },
    {
        "section": "Financial Information",
        "questions": [
            {"id": "q6_proposed_issue_size", "label": "What is the proposed IPO issue size (₹ crore)?", "type": "number", "required": True},
            {"id": "q7_other_capital_raises", "label": "What other capital raises (₹ crore) have been made in the current financial year?", "type": "number", "required": False},
            {"id": "q8_current_net_worth", "label": "What is the current net worth of the company (₹ crore)?", "type": "number", "required": True},
            {"id": "q9_ofs_percentage", "label": "Is any portion of the IPO an Offer for Sale (OFS)? If yes, what percentage?", "type": "number", "required": False},
        ]
    },
    {
        "section": "Promoter & Shareholding",
        "questions": [
            {"id": "q10_promoter_names", "label": "Who are the identified promoters and promoter group members?", "type": "textarea", "required": True},
            {"id": "q11_current_promoter_holding", "label": "What is the current promoter holding percentage?", "type": "number", "required": True},
            {"id": "q12_post_issue_promoter_holding", "label": "What will be the post-issue promoter holding percentage (estimated)?", "type": "number", "required": True},
            {"id": "q13_convertible_securities", "label": "Are there any outstanding convertible securities, warrants, or ESOPs?", "type": "select", "options": ["None", "ESOPs only", "Convertible securities exist", "Both ESOPs and convertibles"], "required": True},
        ]
    },
    {
        "section": "Governance & Compliance",
        "questions": [
            {"id": "q14_total_directors", "label": "How many directors are on the board?", "type": "number", "required": True},
            {"id": "q14_independent_directors", "label": "How many of these are Independent Directors?", "type": "number", "required": True},
            {"id": "q15_chairman_type", "label": "Is the chairperson executive or non-executive?", "type": "select", "options": ["Executive", "Non-Executive", "Independent"], "required": True},
            {"id": "q16_woman_director", "label": "Is there a woman director on the board?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"id": "q17_audit_committee", "label": "Has the Audit Committee been constituted?", "type": "select", "options": ["Yes, fully compliant", "Yes, but composition may not meet requirements", "No"], "required": True},
            {"id": "q17b_audit_committee_details", "label": "If yes, provide Audit Committee composition details (total members, independent members, chair details)", "type": "textarea", "required": False, "conditional": "q17_audit_committee!=No"},
            {"id": "q18_nrc", "label": "Has the Nomination & Remuneration Committee been constituted?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"id": "q19_src", "label": "Has the Stakeholders Relationship Committee been constituted?", "type": "select", "options": ["Yes", "No"], "required": True},
            {"id": "q20_compliance_officer", "label": "Has a qualified Company Secretary been appointed as Compliance Officer?", "type": "select", "options": ["Yes", "No", "Appointment in progress"], "required": True},
        ]
    },
    {
        "section": "Legal & Regulatory",
        "questions": [
            {"id": "q21_sebi_debarment", "label": "Has the company, any promoter, or any director ever been debarred by SEBI?", "type": "select", "options": ["No", "Yes"], "required": True},
            {"id": "q22_wilful_defaulter", "label": "Has any promoter or director been declared a wilful defaulter by any bank/FI?", "type": "select", "options": ["No", "Yes"], "required": True},
            {"id": "q23_fugitive_offender", "label": "Is any promoter or director a fugitive economic offender?", "type": "select", "options": ["No", "Yes"], "required": True},
            {"id": "q24_pending_litigation", "label": "List any pending litigation involving the company, promoters, or directors.", "type": "textarea", "required": False},
            {"id": "q25_regulatory_investigations", "label": "Are there any ongoing investigations by regulatory bodies?", "type": "textarea", "required": False},
        ]
    },
    {
        "section": "IPO Intent",
        "questions": [
            {"id": "q26_ipo_purpose", "label": "What is the primary purpose of the IPO?", "type": "select", "options": ["Business expansion", "Debt repayment", "Offer for Sale (OFS)", "Working capital", "General corporate purposes", "Multiple purposes"], "required": True},
            {"id": "q27_target_timeline", "label": "What is the target timeline for listing?", "type": "text", "required": True},
            {"id": "q28_raise_amount", "label": "How much capital does the company aim to raise (₹ crore)?", "type": "number", "required": True},
            {"id": "q29_brlm_appointed", "label": "Has a merchant banker (BRLM) been appointed?", "type": "select", "options": ["Yes", "No", "In discussions"], "required": True},
            {"id": "q30_restated_financials", "label": "Have restated financial statements been prepared under Ind AS?", "type": "select", "options": ["Yes, completed", "In progress", "No, not started"], "required": True},
        ]
    }
]


@router.get("/schema")
def get_questionnaire_schema():
    """Return the questionnaire structure for the frontend to render."""
    return QUESTIONNAIRE_SCHEMA


@router.get("/{company_id}")
def get_responses(company_id: int, db: Session = Depends(get_db)):
    """Get saved questionnaire responses for a company."""
    qr = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.company_id == company_id
    ).first()

    if not qr:
        return {"company_id": company_id, "responses": {}, "completed": False}

    return {
        "id": qr.id,
        "company_id": company_id,
        "responses": qr.responses,
        "completed": bool(qr.completed),
        "updated_at": qr.updated_at.isoformat() if qr.updated_at else None
    }


class SaveResponses(BaseModel):
    responses: dict
    completed: Optional[bool] = False


@router.post("/{company_id}")
def save_responses(company_id: int, data: SaveResponses, db: Session = Depends(get_db)):
    """Save or update questionnaire responses."""
    # Verify company exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    qr = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.company_id == company_id
    ).first()

    if qr:
        qr.responses = data.responses
        qr.completed = 1 if data.completed else 0
        qr.updated_at = datetime.utcnow()
        if data.completed:
            qr.completed_at = datetime.utcnow()
    else:
        qr = QuestionnaireResponse(
            company_id=company_id,
            responses=data.responses,
            completed=1 if data.completed else 0,
            completed_at=datetime.utcnow() if data.completed else None
        )
        db.add(qr)

    # Update company status
    if company.status == "draft":
        company.status = "in_progress"

    db.commit()
    db.refresh(qr)
    return {
        "id": qr.id,
        "company_id": company_id,
        "completed": bool(qr.completed),
        "message": "Responses saved successfully"
    }
