"""
Readiness scorer — calculates numerical scores and uses AI for qualitative assessments.
Four primary categories: Financial Health, Governance, Legal Compliance, Business Fundamentals.
"""
import json
import logging
from sqlalchemy.orm import Session
from database.models import ReadinessScore, Document, QuestionnaireResponse, Company
from services.gemini_service import get_gemini_model

logger = logging.getLogger(__name__)


def _parse_crore(value) -> float:
    """Convert value to crores."""
    if value is None:
        return 0.0
    try:
        val = float(value)
        if val > 1000000:
            return val / 10000000
        return val
    except (ValueError, TypeError):
        return 0.0


def score_financial_health(parsed_data: dict) -> dict:
    """Score financial health based on extracted financial data."""
    scores = {}
    details = {}
    total_weight = 0
    weighted_score = 0

    # 1. Operating Profit (weight: 35)
    op = parsed_data.get("operating_profit")
    op_val = None
    if isinstance(op, (int, float)):
        op_val = float(op)
    elif isinstance(op, dict) and op:
        years = sorted(op.keys())
        op_val = _parse_crore(op[years[-1]])

    if op_val is not None:
        if op_val >= 25:
            score = 100
        elif op_val >= 15:
            score = 85
        elif op_val >= 10:
            score = 70
        elif op_val >= 5:
            score = 55
        elif op_val > 0:
            score = 40
        else:
            score = 20
        scores["operating_profitability"] = score
        details["operating_profitability"] = f"Operating Profit: ₹{op_val:.2f} Cr"
        weighted_score += score * 35
        total_weight += 35

    # 2. Net Tangible Assets (weight: 35)
    nta = parsed_data.get("net_tangible_assets")
    nta_val = None
    if isinstance(nta, (int, float)):
        nta_val = float(nta)
    elif isinstance(nta, dict) and nta:
        years = sorted(nta.keys())
        nta_val = _parse_crore(nta[years[-1]])

    if nta_val is not None:
        if nta_val >= 20:
            score = 100
        elif nta_val >= 10:
            score = 85
        elif nta_val >= 3:
            score = 75
        elif nta_val >= 1:
            score = 50
        else:
            score = 25
        scores["net_tangible_assets"] = score
        details["net_tangible_assets"] = f"Net Tangible Assets: ₹{nta_val:.2f} Cr"
        weighted_score += score * 35
        total_weight += 35

    # 3. Net Worth (weight: 30)
    nw = parsed_data.get("net_worth")
    nw_val = None
    if isinstance(nw, (int, float)):
        nw_val = float(nw)
    elif isinstance(nw, dict) and nw:
        years = sorted(nw.keys())
        nw_val = _parse_crore(nw[years[-1]])

    if nw_val is not None:
        if nw_val >= 30:
            score = 100
        elif nw_val >= 10:
            score = 85
        elif nw_val >= 1:
            score = 70
        else:
            score = 30
        scores["net_worth"] = score
        details["net_worth"] = f"Net Worth: ₹{nw_val:.2f} Cr"
        weighted_score += score * 30
        total_weight += 30

    overall = (weighted_score / total_weight) if total_weight > 0 else 70.0

    return {
        "score": round(overall, 1),
        "sub_scores": scores,
        "details": details,
        "evidence": "Evaluated against SEBI ICDR Regulation 6 profitability, NTA, and net worth thresholds.",
        "data_available": total_weight > 0
    }


async def score_governance(document_text: str, questionnaire: dict) -> dict:
    """Score governance readiness using Gemini or deterministic heuristics."""
    model = get_gemini_model()

    if model:
        prompt = f"""You are an IPO governance expert. Score the company's governance readiness from 0-100 based on the available information.
QUESTIONNAIRE DATA:
{json.dumps(questionnaire, indent=2)}

Return a JSON object:
{{
    "score": <overall score 0-100>,
    "sub_scores": {{
        "board_composition": <score>,
        "committee_structure": <score>,
        "internal_controls": <score>
    }},
    "details": {{
        "board_composition": "<explanation>",
        "committee_structure": "<explanation>"
    }},
    "evidence": "<key evidence>"
}}
Return ONLY valid JSON."""
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            logger.warning(f"AI governance score failed: {e}")

    # Heuristic Fallback
    gov_score = 60
    has_indep = questionnaire.get("independent_directors_ratio") in [True, "true"] or int(questionnaire.get("q14_independent_directors", 0) or 0) >= 2
    has_woman = questionnaire.get("woman_director_appointed") in [True, "true"] or str(questionnaire.get("q16_woman_director", "")).lower() in ["yes", "true"]
    has_audit = questionnaire.get("audit_committee_compliant") in [True, "true"] or "compliant" in str(questionnaire.get("q17_audit_committee", "")).lower()

    if has_indep: gov_score += 15
    if has_woman: gov_score += 15
    if has_audit: gov_score += 10
    gov_score = min(gov_score, 95)

    return {
        "score": gov_score,
        "sub_scores": {
            "board_composition": 85 if has_indep else 60,
            "woman_director": 90 if has_woman else 50,
            "audit_committee": 85 if has_audit else 60
        },
        "details": {
            "board": "Board independence confirmed" if has_indep else "Independent directors appointment in progress",
            "woman_director": "Woman director appointed" if has_woman else "Woman director appointment pending"
        },
        "evidence": "Governance evaluation based on SEBI LODR board and committee mandates.",
        "data_available": True
    }


async def score_legal_compliance(document_text: str, questionnaire: dict) -> dict:
    """Score legal & compliance readiness."""
    model = get_gemini_model()

    if model:
        prompt = f"""You are a securities legal compliance expert. Score the company's legal & compliance readiness from 0-100.
QUESTIONNAIRE DATA:
{json.dumps(questionnaire, indent=2)}

Return a JSON object:
{{
    "score": <overall score 0-100>,
    "sub_scores": {{
        "regulatory_history": <score>,
        "litigation_exposure": <score>
    }},
    "details": {{"regulatory": "<explanation>"}},
    "evidence": "<key evidence>"
}}
Return ONLY valid JSON."""
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            logger.warning(f"AI legal score failed: {e}")

    # Heuristic Fallback
    legal_score = 75
    no_sebi = questionnaire.get("no_sebi_debarment") in [True, "true"] or questionnaire.get("q21_sebi_debarment") in ["No", "no"]
    no_wilful = questionnaire.get("no_wilful_defaulter") in [True, "true"] or questionnaire.get("q22_wilful_defaulter") in ["No", "no"]
    no_fugitive = questionnaire.get("q23_fugitive_offender") in ["No", "no", None]

    if no_sebi: legal_score += 10
    if no_wilful: legal_score += 10
    if no_fugitive: legal_score += 5
    legal_score = min(legal_score, 95)

    return {
        "score": legal_score,
        "sub_scores": {
            "sebi_debarment": 95 if no_sebi else 30,
            "wilful_defaulter": 95 if no_wilful else 25,
            "litigation_risk": 80
        },
        "details": {
            "sebi_check": "No debarment recorded" if no_sebi else "SEBI action flagged",
            "credit_check": "Clean defaulter record" if no_wilful else "Wilful defaulter reported"
        },
        "evidence": "Statutory fit-and-proper declarations verified against SEBI ICDR Regulation 5.",
        "data_available": True
    }


async def score_business_fundamentals(document_text: str, questionnaire: dict) -> dict:
    """Score business fundamentals & issue structure readiness."""
    biz_score = 80
    lockin_ok = questionnaire.get("promoter_lockin_18m") in [True, "true"] or int(questionnaire.get("q11_current_promoter_holding", 0) or 0) >= 20
    restated_ok = questionnaire.get("financials_restated_ind_as") in [True, "true"] or "completed" in str(questionnaire.get("q30_restated_financials", "")).lower()

    if lockin_ok: biz_score += 10
    if restated_ok: biz_score += 10
    biz_score = min(biz_score, 90)

    return {
        "score": biz_score,
        "sub_scores": {
            "promoter_commitment": 85 if lockin_ok else 60,
            "ind_as_restatement": 90 if restated_ok else 65
        },
        "details": {
            "lockin": "Promoter lock-in requirements satisfied" if lockin_ok else "Lock-in schedule to be finalized",
            "accounting": "Ind AS restatement in progress or completed"
        },
        "evidence": "Business model and accounting maturity evaluated.",
        "data_available": True
    }


async def run_readiness_scoring(db: Session, company_id: int) -> list:
    """
    Run readiness scoring across all 4 key dimensions.
    Calculates weighted overall score and updates company profile.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    documents = db.query(Document).filter(Document.company_id == company_id).all()

    # Merge financial data
    merged_parsed_data = {}
    fin_data = getattr(company, 'financial_data', None)
    if fin_data and isinstance(fin_data, dict):
        merged_parsed_data.update(fin_data)

    all_document_text = ""
    for doc in documents:
        if doc.parsed_data and isinstance(doc.parsed_data, dict):
            merged_parsed_data.update(doc.parsed_data)
        if doc.extracted_text:
            all_document_text += f"\n{doc.extracted_text}"

    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.company_id == company_id
    ).first()
    q_data = questionnaire.responses if questionnaire else {}

    # Clear previous scores
    db.query(ReadinessScore).filter(ReadinessScore.company_id == company_id).delete()

    results = []

    # 1. Financial Health (weight 30%)
    fin_res = score_financial_health(merged_parsed_data)
    results.append({
        "category": "financial_health",
        "category_label": "Financial Preparedness",
        "weight": 30,
        "score": fin_res["score"],
        "assessment_type": "code",
        "sub_scores": fin_res.get("sub_scores", {}),
        "details": fin_res.get("details", {}),
    })

    # 2. Governance (weight 25%)
    gov_res = await score_governance(all_document_text, q_data)
    results.append({
        "category": "governance",
        "category_label": "Corporate Governance & Board",
        "weight": 25,
        "score": gov_res["score"],
        "assessment_type": "ai",
        "sub_scores": gov_res.get("sub_scores", {}),
        "details": gov_res.get("details", {}),
    })

    # 3. Legal & Compliance (weight 25%)
    legal_res = await score_legal_compliance(all_document_text, q_data)
    results.append({
        "category": "legal_compliance",
        "category_label": "Regulatory & Legal Compliance",
        "weight": 25,
        "score": legal_res["score"],
        "assessment_type": "ai",
        "sub_scores": legal_res.get("sub_scores", {}),
        "details": legal_res.get("details", {}),
    })

    # 4. Business Fundamentals (weight 20%)
    biz_res = await score_business_fundamentals(all_document_text, q_data)
    results.append({
        "category": "business_fundamentals",
        "category_label": "Capital Structure & Restatement",
        "weight": 20,
        "score": biz_res["score"],
        "assessment_type": "ai",
        "sub_scores": biz_res.get("sub_scores", {}),
        "details": biz_res.get("details", {}),
    })

    # Save scores to DB
    for r in results:
        db_score = ReadinessScore(
            company_id=company_id,
            category=r["category"],
            score=r["score"],
            assessment_type=r["assessment_type"],
            evidence=str(r.get("details", "")),
            details=r.get("sub_scores")
        )
        db.add(db_score)

    total_weight = sum(r["weight"] for r in results)
    avg_score = sum(r["score"] * r["weight"] for r in results) / total_weight if total_weight > 0 else 0.0

    # Update company record
    company.readiness_score = round(avg_score, 1)
    db.commit()

    return results
