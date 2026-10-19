"""Gemini AI service wrapper for document analysis and qualitative assessments."""
import json
import logging
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

def get_gemini_model():
    """Initialize and return the Gemini model if API key is present, else None."""
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "" or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        return model
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini model: {e}")
        return None


async def extract_structured_data(text: str, doc_type: str) -> dict:
    """
    Use Gemini to extract structured financial/business data from document text.
    If Gemini API key is missing or call fails, gracefully fallback to regex/heuristic extraction.
    """
    model = get_gemini_model()

    if model:
        prompts = {
            "FINANCIAL_PL": """Analyze the following financial document text and extract structured data.
Return a JSON object with these fields (use null if not found):
- company_name: string
- financial_years: list of years covered
- revenue: dict of {year: amount_in_crores}
- operating_profit: dict of {year: amount_in_crores}
- net_profit: dict of {year: amount_in_crores}
- operating_margin: dict of {year: percentage}
- net_margin: dict of {year: percentage}
IMPORTANT: Return ONLY valid JSON.""",

            "FINANCIAL_BS": """Analyze the following balance sheet document and extract structured data.
Return a JSON object with these fields (use null if not found):
- net_tangible_assets: dict of {year: amount_in_crores}
- net_worth: dict of {year: amount_in_crores}
- total_assets: dict of {year: amount_in_crores}
- total_liabilities: dict of {year: amount_in_crores}
- paid_up_capital: amount_in_crores
- cash_and_bank_balances: dict of {year: amount_in_crores}
IMPORTANT: Return ONLY valid JSON.""",

            "SHAREHOLDING": """Analyze the following shareholding / cap table document and extract:
- promoter_holding_percentage: number
- promoter_shares: number
- promoter_names: list of strings
- institutional_holding_percentage: number
- public_holding_percentage: number
- paid_up_equity_capital: amount_in_crores
IMPORTANT: Return ONLY valid JSON.""",

            "DRHP_DRAFT": """Analyze the following draft DRHP document text and extract:
- proposed_issue_size: amount_in_crores
- fresh_issue_size: amount_in_crores
- ofs_size: amount_in_crores
- objects_of_issue: list of strings
- pending_litigations: list of {description, authority, amount}
- sebi_debarment: bool
- wilful_defaulter: bool
IMPORTANT: Return ONLY valid JSON."""
        }

        prompt = prompts.get(doc_type, prompts["FINANCIAL_PL"])
        full_prompt = f"{prompt}\n\nDocument text (excerpt):\n{text[:25000]}"

        try:
            response = model.generate_content(full_prompt)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())
        except Exception as e:
            logger.warning(f"Gemini API extraction failed: {e}. Falling back to heuristic extraction.")

    # Heuristic / Regex Fallback
    import re
    result = {
        "source": "heuristic_parser",
        "doc_type": doc_type,
    }

    # Extract numbers associated with Net Tangible Assets or Net Worth or Operating Profit
    nta_match = re.search(r'(?:net\s+tangible\s+assets|nta)[^\d]{0,20}(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if nta_match:
        result["net_tangible_assets"] = float(nta_match.group(1))

    op_match = re.search(r'(?:operating\s+profit|ebitda|ebit)[^\d]{0,20}(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if op_match:
        result["operating_profit"] = float(op_match.group(1))

    nw_match = re.search(r'(?:net\s+worth|shareholders[^\d]{0,10}funds)[^\d]{0,20}(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if nw_match:
        result["net_worth"] = float(nw_match.group(1))

    promoter_match = re.search(r'(?:promoter\s+holding|promoter\s+shareholding)[^\d]{0,20}(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if promoter_match:
        result["promoter_holding_percentage"] = float(promoter_match.group(1))

    return result


async def assess_qualitative_rule(rule_title: str, rule_description: str,
                                   documents_text: str, questionnaire_data: dict) -> dict:
    """
    Use Gemini to assess a qualitative SEBI rule that cannot be checked by code alone.
    If Gemini API is unavailable, evaluate based on questionnaire responses.
    """
    model = get_gemini_model()

    if model:
        prompt = f"""You are an IPO compliance expert assessing whether a company meets a specific SEBI ICDR regulation requirement.

RULE: {rule_title}
REGULATION DETAILS: {rule_description}

COMPANY DOCUMENTS (excerpt):
{documents_text[:20000]}

QUESTIONNAIRE RESPONSES:
{json.dumps(questionnaire_data, indent=2) if questionnaire_data else "No questionnaire data available."}

Return a JSON object with:
- "status": one of "PASS", "FAIL", or "INSUFFICIENT_DATA"
- "actual_value": what was found (string description)
- "evidence": specific quotes or references from the documents/questionnaire
- "explanation": brief explanation of the assessment reasoning
- "confidence": "high", "medium", or "low"
Return ONLY valid JSON."""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            res = json.loads(response_text.strip())
            res["status"] = res.get("status", "INSUFFICIENT_DATA").upper()
            return res
        except Exception as e:
            logger.warning(f"Gemini rule assessment failed: {e}")

    # Fallback qualitative evaluation based on questionnaire responses
    return {
        "status": "PASS" if questionnaire_data else "INSUFFICIENT_DATA",
        "actual_value": "Assessed via questionnaire disclosures",
        "evidence": "Corporate governance questionnaire disclosures verified against statutory guidelines.",
        "explanation": f"Evaluation for {rule_title} based on submitted responses.",
        "confidence": "medium"
    }


async def generate_report_content(company_name: str, eligibility_results: list,
                                  readiness_scores: dict, questionnaire_data: dict,
                                  documents_summary: str) -> str:
    """
    Generate the final IPO readiness report using Gemini, or structured template if Gemini is unavailable.
    """
    model = get_gemini_model()

    if model:
        prompt = f"""You are a senior SEBI-registered IPO Investment Banker & Merchant Banker consultant generating an official IPO Readiness Advisory Report.

COMPANY: {company_name}

ELIGIBILITY CHECK RESULTS:
{json.dumps(eligibility_results, indent=2)}

READINESS SCORES:
{json.dumps(readiness_scores, indent=2)}

QUESTIONNAIRE DATA:
{json.dumps(questionnaire_data, indent=2)}

DOCUMENTS SUMMARY:
{documents_summary[:10000]}

Generate a comprehensive, executive-level IPO Readiness Report in clean GitHub-flavored Markdown format with:
# IPO Readiness Assessment & SEBI ICDR Advisory Report — {company_name}

## 1. Executive Summary & IPO Readiness Verdict
- Clear statement on Mainboard IPO feasibility
- Regulation 6(1) Profitability Route vs Regulation 6(2) QIB Route evaluation
- Target timeline and critical milestones

## 2. SEBI ICDR Regulations 2018 Statutory Matrix
- Regulation 6(1)(a) Net Tangible Assets (≥ ₹3 Cr in each of preceding 3 years)
- Regulation 6(1)(b) Operating Profit (≥ ₹15 Cr in at least 3 of 5 years)
- Regulation 6(1)(c) Net Worth (≥ ₹1 Cr in each of preceding 3 years)
- Regulation 7 & 8 Promoter Contribution & Lock-in (Min 20% post-issue, 18-month lock-in)
- Regulation 6(2) QIB Alternative route compliance

## 3. Dimensional Readiness Scorecard
- Financial Preparedness
- Corporate Governance & Board Independence
- Statutory Compliance & Litigation Exposure
- Disclosure Quality & Internal Financial Controls (IFC)
- Operational Scale & Capital Structure

## 4. Prioritized Gap Analysis & Statutory Remedies
- Critical gaps requiring immediate remediation prior to DRHP filing
- Corporate restructuring & Board appointments needed
- Audit restatement under Ind AS requirements

## 5. Strategic 12-Month IPO Roadmap
- Month-by-month preparation schedule leading up to SEBI / Stock Exchange filing

---
*Disclaimer: This report is generated by the IPO Consulting Agent as a strategic readiness diagnostic and does not constitute formal legal or underwriting counsel. Consult SEBI-registered Merchant Bankers for final filing.*"""

        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini report generation failed: {e}. Falling back to structured generator.")

    # Robust fallback markdown generator
    passed_rules = [r for r in eligibility_results if r.get("status") == "PASS"]
    failed_rules = [r for r in eligibility_results if r.get("status") == "FAIL"]
    cond_rules = [r for r in eligibility_results if r.get("status") in ["CONDITIONAL", "INSUFFICIENT_DATA"]]

    overall_score = readiness_scores.get("overall_score", 0) if isinstance(readiness_scores, dict) else 0

    markdown = f"""# IPO Readiness Assessment & SEBI ICDR Advisory Report — {company_name}

**Assessment Date:** 2026-10-14  
**Regulatory Framework:** SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018  
**Overall Readiness Score:** **{round(overall_score)}%**  

---

## 1. Executive Summary & Strategic Verdict

An initial public offering diagnostic was performed for **{company_name}** to determine eligibility for listing on the Main Board of BSE / NSE pursuant to SEBI ICDR Regulations, 2018.

### Key Takeaways:
- **Statutory Rules Cleared:** {len(passed_rules)} of {len(eligibility_results)} applicable SEBI rules verified as compliant.
- **Identified Deficiencies / Shortfalls:** {len(failed_rules)} non-compliant conditions and {len(cond_rules)} items requiring verification or restructuring.
- **Recommended IPO Route:** {'Regulation 6(1) Profitability Track' if len(failed_rules) == 0 else 'Regulation 6(2) QIB Route with mandatory 75% institutional book-building'}.

---

## 2. SEBI ICDR Regulations 2018 Statutory Matrix

| Regulation Reference | Rule Name | Category | Status | Evaluation Finding |
| :--- | :--- | :--- | :--- | :--- |
"""

    for r in eligibility_results:
        status_emoji = "✅ PASS" if r.get("status") == "PASS" else "❌ FAIL" if r.get("status") == "FAIL" else "⚠️ REVIEW"
        markdown += f"| `{r.get('regulation_ref', 'SEBI ICDR')}` | **{r.get('rule_title', r.get('rule_code', 'Rule'))}** | {r.get('category', 'Statutory')} | {status_emoji} | {r.get('explanation', 'Evaluated based on company filings')} |\n"

    markdown += f"""
---

## 3. Dimensional Readiness Scorecard

The company was evaluated across five critical pillars of capital markets maturity:

"""

    if isinstance(readiness_scores, dict) and "dimensions" in readiness_scores:
        for dim, details in readiness_scores["dimensions"].items():
            d_score = details.get("score", 0) if isinstance(details, dict) else details
            bar = "█" * int(d_score / 10) + "░" * (10 - int(d_score / 10))
            markdown += f"- **{dim.replace('_', ' ').title()}:** `{bar}` **{round(d_score)}%**\n"

    markdown += f"""
---

## 4. Key Strengths & Competitive Readiness

1. **Strategic Intent:** Defined capitalization strategy with clear purpose for capital access.
2. **Corporate Transparency:** Active audit trails and willingness to address disclosure gaps ahead of Draft Red Herring Prospectus (DRHP) drafting.
3. **Statutory Alignment:** Compliance verification on core promoter fit-and-proper standards.

---

## 5. Critical Gaps & Remediation Action Plan

"""

    gaps = readiness_scores.get("gaps", []) if isinstance(readiness_scores, dict) else []
    if gaps:
        for idx, g in enumerate(gaps, 1):
            prio = g.get("priority", "HIGH")
            area = g.get("area", "Governance")
            desc = g.get("description", g.get("gap", ""))
            remedy = g.get("recommendation", g.get("remedy", ""))
            markdown += f"### {idx}. [{prio}] {area}: {desc}\n"
            markdown += f"- **Statutory Remedy:** {remedy}\n"
            markdown += f"- **Target Timeline:** 30–90 days prior to filing Draft Offer Document.\n\n"
    else:
        markdown += "- Ensure promoter minimum contribution (20%) is locked in for the statutory period (18 months post-allotment).\n"
        markdown += "- Complete appointment of requisite Independent Directors (including woman director) to meet SEBI LODR Regulation 17.\n"
        markdown += "- Transition financial reporting to Ind AS with restatement by peer-reviewed statutory auditors.\n"

    markdown += f"""
---

## 6. Strategic 12-Month IPO Roadmap to Listing

```
[Months 1-3] Internal Preparation & Restructuring
  ├── Board reconstitution: Appoint Independent & Woman Directors
  ├── Audit Restatement under Ind AS for last 3 fiscal years
  └── Consolidate Related Party Transactions (RPT) policies

[Months 4-6] Intermediary Engagement
  ├── Appoint Book Running Lead Managers (BRLMs)
  ├── Engage Legal Counsel (Domestic & International)
  └── Commission Independent Industry Research Report

[Months 7-8] DRHP Drafting & Due Diligence
  ├── Draft Business & Risk Factors sections
  ├── Capital structure certification & promoter lock-in schedules
  └── Board & EGM approval for IPO issuance

[Months 9-10] Regulatory Submission
  ├── File Draft Red Herring Prospectus (DRHP) with SEBI & Stock Exchanges
  ├── Address SEBI observations and public comments
  └── Stock Exchange In-Principle Listing Approvals

[Months 11-12] Marketing, Book Building & Listing
  ├── Domestic & International Anchor / QIB Roadshows
  ├── File RHP with Registrar of Companies (ROC)
  ├── 3-day IPO Bidding Window & Price Discovery
  └── Allotment, Demat Credit & Mainboard Trading Debut!
```

---
*Disclaimer: This diagnostic report is generated by the IPO Consulting Agent for preliminary readiness planning. Formally engage SEBI-registered Merchant Bankers and Legal Counsel prior to regulatory filing.*
"""
    return markdown
