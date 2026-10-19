"""Report generator service — assembles data and calls Gemini for the final report."""
import json
from sqlalchemy.orm import Session
from database.models import (
    Company, Document, QuestionnaireResponse,
    EligibilityResult, ReadinessScore, Report, SebiRule
)
from services.gemini_service import generate_report_content


async def generate_report(db: Session, company_id: int) -> dict:
    """Generate a comprehensive IPO readiness report for a company."""

    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValueError(f"Company with id {company_id} not found")

    # Get eligibility results with rule details
    eligibility_results = []
    results = db.query(EligibilityResult, SebiRule).join(
        SebiRule, EligibilityResult.rule_id == SebiRule.id
    ).filter(
        EligibilityResult.company_id == company_id
    ).all()

    for result, rule in results:
        eligibility_results.append({
            "rule_code": rule.rule_code,
            "title": rule.title,
            "regulation": rule.regulation,
            "category": rule.category,
            "threshold": rule.threshold_value,
            "status": result.status,
            "actual_value": result.actual_value,
            "evidence": result.evidence,
        })

    # Get readiness scores
    readiness_scores = []
    scores = db.query(ReadinessScore).filter(
        ReadinessScore.company_id == company_id
    ).all()

    for score in scores:
        readiness_scores.append({
            "category": score.category,
            "score": score.score,
            "assessment_type": score.assessment_type,
            "evidence": score.evidence,
            "details": score.details,
        })

    # Get questionnaire data
    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.company_id == company_id
    ).first()
    q_data = questionnaire.responses if questionnaire else {}

    # Get document summaries
    documents = db.query(Document).filter(
        Document.company_id == company_id
    ).all()

    docs_summary = ""
    for doc in documents:
        docs_summary += f"\n--- {doc.doc_type}: {doc.filename} ---\n"
        if doc.extracted_text:
            docs_summary += doc.extracted_text[:5000] + "\n"

    # Generate report via Gemini
    report_content = await generate_report_content(
        company_name=company.name,
        eligibility_results=eligibility_results,
        readiness_scores=readiness_scores,
        questionnaire_data=q_data,
        documents_summary=docs_summary
    )

    # Calculate summary stats
    total_rules = len(eligibility_results)
    passed = sum(1 for r in eligibility_results if r["status"] == "pass")
    failed = sum(1 for r in eligibility_results if r["status"] == "fail")
    insufficient = sum(1 for r in eligibility_results if r["status"] == "insufficient_data")

    avg_readiness = 0
    if readiness_scores:
        avg_readiness = sum(s["score"] for s in readiness_scores) / len(readiness_scores)

    summary = (
        f"Eligibility: {passed}/{total_rules} passed, {failed} failed, {insufficient} insufficient data. "
        f"Average readiness score: {avg_readiness:.0f}/100."
    )

    # Save report
    report = Report(
        company_id=company_id,
        report_content=report_content,
        summary=summary
    )
    db.add(report)

    # Update company status
    company.status = "completed"
    db.commit()
    db.refresh(report)

    return {
        "id": report.id,
        "company_id": company_id,
        "company_name": company.name,
        "report_content": report_content,
        "content": report_content,
        "title": f"IPO Readiness Advisory Report — {company.name}",
        "summary": summary,
        "eligibility_summary": {
            "total": total_rules,
            "passed": passed,
            "failed": failed,
            "insufficient_data": insufficient
        },
        "readiness_summary": {
            "average_score": round(avg_readiness, 1),
            "scores": readiness_scores
        },
        "generated_at": report.generated_at.isoformat()
    }
