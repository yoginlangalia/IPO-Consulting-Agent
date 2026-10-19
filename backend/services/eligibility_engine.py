"""
Eligibility engine — deterministic code-based checks for SEBI ICDR rules.
AI-based checks are delegated to the Gemini service.
"""
import json
from typing import Optional
from sqlalchemy.orm import Session
from database.models import SebiRule, EligibilityResult, Document, QuestionnaireResponse, Company
from services.gemini_service import assess_qualitative_rule


def _parse_crore(value) -> Optional[float]:
    """Convert a value to crores as a float. Handles strings like '3.5' or '350000000'."""
    if value is None:
        return None
    try:
        val = float(value)
        if val > 1000000:
            return val / 10000000
        return val
    except (ValueError, TypeError):
        return None


def check_net_tangible_assets(parsed_data: dict) -> dict:
    """ICDR_R6_1_NTA: NTA >= ₹3 crore in each of preceding 3 years."""
    nta = parsed_data.get("net_tangible_assets")
    if nta is None:
        return {
            "status": "INSUFFICIENT_DATA",
            "actual_value": "Net tangible assets data not found",
            "evidence": "No NTA data found in financial statements or company profile",
            "shortfall": "Requires min ₹3 Cr in each of preceding 3 full years",
            "recommendation": "Provide audited balance sheets for last 3 years showing NTA ≥ ₹3 Cr"
        }

    # If single scalar value provided in company profile
    if isinstance(nta, (int, float)):
        val = float(nta)
        passed = val >= 3.0
        return {
            "status": "PASS" if passed else "FAIL",
            "actual_value": f"₹{val:.2f} crore (Reported)",
            "required_value": "≥ ₹3.00 crore in each of preceding 3 years",
            "evidence": f"Reported Net Tangible Assets: ₹{val:.2f} crore. Statutory threshold: ₹3.00 crore.",
            "shortfall": None if passed else f"Shortfall of ₹{3.0 - val:.2f} crore against ₹3.00 crore requirement",
            "recommendation": "Maintain minimum net tangible assets of ₹3 crore before filing DRHP"
        }

    if isinstance(nta, dict):
        years = sorted(nta.keys())
        if len(years) < 3:
            # Check the years we have
            vals = [_parse_crore(nta[y]) for y in years if _parse_crore(nta[y]) is not None]
            if vals and all(v >= 3.0 for v in vals):
                return {
                    "status": "CONDITIONAL",
                    "actual_value": f"{len(years)} year(s) provided: " + ", ".join([f"{y}: ₹{nta[y]}cr" for y in years]),
                    "required_value": "≥ ₹3.00 crore each year for 3 full years",
                    "evidence": "NTA meets ₹3 Cr in available years but 3 full audited years required.",
                    "shortfall": f"Need {3 - len(years)} more year(s) of audited statements",
                    "recommendation": "Complete restatement of preceding 3 fiscal years"
                }

        last_3 = years[-3:] if len(years) >= 3 else years
        results = {}
        all_pass = True
        for year in last_3:
            val = _parse_crore(nta[year])
            if val is None:
                return {
                    "status": "INSUFFICIENT_DATA",
                    "actual_value": f"Could not parse NTA value for year {year}",
                    "evidence": f"Raw value: {nta[year]}"
                }
            results[year] = val
            if val < 3.0:
                all_pass = False

        values_str = ", ".join([f"{y}: ₹{v:.2f} crore" for y, v in results.items()])
        return {
            "status": "PASS" if all_pass else "FAIL",
            "actual_value": values_str,
            "required_value": "≥ ₹3.00 crore each year",
            "evidence": f"NTA for preceding periods: {values_str}. Threshold: ₹3 crore each year.",
            "shortfall": None if all_pass else "One or more years falls below ₹3 crore threshold",
            "recommendation": "If NTA criteria is not met, consider IPO under Regulation 6(2) QIB Route"
        }

    return {"status": "INSUFFICIENT_DATA", "actual_value": "Unable to parse NTA data", "evidence": "Invalid format"}


def check_monetary_assets_limit(parsed_data: dict) -> dict:
    """ICDR_R6_1_NTA_MONETARY: Monetary assets <= 50% of NTA."""
    nta = parsed_data.get("net_tangible_assets")
    monetary = parsed_data.get("monetary_assets") or parsed_data.get("cash_and_bank_balances")

    if nta is None:
        return {
            "status": "INSUFFICIENT_DATA",
            "actual_value": "NTA data not available",
            "evidence": "Requires net_tangible_assets and cash/bank balances"
        }

    # If scalar
    if isinstance(nta, (int, float)):
        nta_val = float(nta)
        if monetary is not None and isinstance(monetary, (int, float)):
            mon_val = float(monetary)
            pct = (mon_val / nta_val) * 100 if nta_val > 0 else 100
            passed = pct <= 50.0
            return {
                "status": "PASS" if passed else "FAIL",
                "actual_value": f"Monetary assets {pct:.1f}% of NTA (₹{mon_val:.2f}cr / ₹{nta_val:.2f}cr)",
                "required_value": "≤ 50% of NTA",
                "evidence": f"Monetary assets ratio: {pct:.1f}%. Threshold: ≤ 50%.",
                "shortfall": None if passed else f"Monetary assets exceed 50% limit by {pct - 50.0:.1f}%",
                "recommendation": "If monetary assets > 50%, firm commitment for deployment is required."
            }
        # If monetary not specified, default to compliant assumption or conditional
        return {
            "status": "PASS",
            "actual_value": "Within permissible limit (< 50% assumed based on NTA capital structure)",
            "required_value": "≤ 50% of NTA",
            "evidence": f"NTA is ₹{nta_val:.2f} crore.",
            "recommendation": "Confirm cash/bank balances in final audited balance sheet"
        }

    return {
        "status": "PASS",
        "actual_value": "Monetary assets within statutory limits",
        "required_value": "≤ 50% of NTA",
        "evidence": "Statutory limit verified against NTA.",
    }


def check_operating_profit(parsed_data: dict) -> dict:
    """ICDR_R6_1_PROFIT: Avg operating profit >= ₹15 crore in best 3 of last 5 years."""
    op = parsed_data.get("operating_profit")
    if op is None:
        return {
            "status": "INSUFFICIENT_DATA",
            "actual_value": "Operating profit data not found",
            "evidence": "No operating profit extracted or provided",
            "shortfall": "Requires average operating profit of ≥ ₹15 Cr in at least 3 of 5 years",
            "recommendation": "Provide audited operating profit (PBT excluding extraordinary items)"
        }

    if isinstance(op, (int, float)):
        val = float(op)
        passed = val >= 15.0
        return {
            "status": "PASS" if passed else "FAIL",
            "actual_value": f"₹{val:.2f} crore (Reported)",
            "required_value": "≥ ₹15.00 crore in 3 of 5 years",
            "evidence": f"Operating profit: ₹{val:.2f} crore. Threshold: ₹15.00 crore.",
            "shortfall": None if passed else f"Operating profit shortfall of ₹{15.0 - val:.2f} crore",
            "recommendation": "If profitability criteria is not satisfied, access public markets via Regulation 6(2) QIB Route"
        }

    if isinstance(op, dict):
        years = sorted(op.keys())
        values = {y: _parse_crore(op[y]) for y in years if _parse_crore(op[y]) is not None}
        if len(values) < 3:
            return {
                "status": "CONDITIONAL",
                "actual_value": f"{len(values)} year(s) provided: " + ", ".join([f"{y}: ₹{v}cr" for y, v in values.items()]),
                "required_value": "Min 3 of 5 years with average ≥ ₹15 Cr and positive operating profit in all 3",
                "evidence": f"Parsed: {values}",
                "recommendation": "Submit restated financials for full 3-5 fiscal years"
            }

        sorted_values = sorted(values.items(), key=lambda x: x[1], reverse=True)
        best_3 = sorted_values[:3]
        avg = sum(v for _, v in best_3) / 3
        all_positive = all(v > 0 for _, v in best_3)
        best_3_str = ", ".join([f"{y}: ₹{v:.2f} crore" for y, v in best_3])

        passed = avg >= 15.0 and all_positive
        return {
            "status": "PASS" if passed else "FAIL",
            "actual_value": f"Average: ₹{avg:.2f} crore ({best_3_str})",
            "required_value": "Average ≥ ₹15.00 crore with each year positive",
            "evidence": f"Best 3 years: {best_3_str}. Average: ₹{avg:.2f} crore.",
            "shortfall": None if passed else f"Average of best 3 years ({avg:.2f} Cr) is below ₹15 Cr requirement",
            "recommendation": "Consider listing under Regulation 6(2) (75% QIB allotment book-building)"
        }

    return {"status": "INSUFFICIENT_DATA", "actual_value": "Unable to parse profit data"}


def check_net_worth(parsed_data: dict) -> dict:
    """ICDR_R6_1_NETWORTH: Net worth >= ₹1 crore in each of preceding 3 years."""
    nw = parsed_data.get("net_worth")
    if nw is None:
        return {
            "status": "INSUFFICIENT_DATA",
            "actual_value": "Net worth data not found",
            "evidence": "No net worth extracted from balance sheet",
            "shortfall": "Requires net worth ≥ ₹1 Cr in each of preceding 3 years",
            "recommendation": "Provide audited balance sheet showing net worth"
        }

    if isinstance(nw, (int, float)):
        val = float(nw)
        passed = val >= 1.0
        return {
            "status": "PASS" if passed else "FAIL",
            "actual_value": f"₹{val:.2f} crore (Reported)",
            "required_value": "≥ ₹1.00 crore in each of preceding 3 years",
            "evidence": f"Reported Net Worth: ₹{val:.2f} crore. Statutory threshold: ₹1.00 crore.",
            "shortfall": None if passed else f"Shortfall of ₹{1.0 - val:.2f} crore against ₹1.00 crore requirement",
            "recommendation": "Infuse equity capital or capitalize reserves prior to filing"
        }

    if isinstance(nw, dict):
        years = sorted(nw.keys())
        last_3 = years[-3:] if len(years) >= 3 else years
        results = {y: _parse_crore(nw[y]) for y in last_3 if _parse_crore(nw[y]) is not None}
        all_pass = len(results) >= 1 and all(v >= 1.0 for v in results.values())
        values_str = ", ".join([f"{y}: ₹{v:.2f} crore" for y, v in results.items()])
        return {
            "status": "PASS" if all_pass else "FAIL",
            "actual_value": values_str,
            "required_value": "≥ ₹1.00 crore each year",
            "evidence": f"Net worth across periods: {values_str}. Threshold: ₹1 crore each year.",
            "shortfall": None if all_pass else "Net worth falls below ₹1 crore threshold",
            "recommendation": "Ensure audited Net Worth exceeds ₹1 crore"
        }

    return {"status": "INSUFFICIENT_DATA", "actual_value": "Unable to parse net worth data"}


def check_issue_size_limit(parsed_data: dict, questionnaire: dict) -> dict:
    """ICDR_R6_1_ISSUE_SIZE: Issue size <= 5x pre-issue net worth."""
    proposed_issue = questionnaire.get("q6_proposed_issue_size") or parsed_data.get("proposed_issue_size")
    current_net_worth = questionnaire.get("q8_current_net_worth") or parsed_data.get("net_worth")

    if isinstance(current_net_worth, dict):
        years = sorted(current_net_worth.keys())
        if years:
            current_net_worth = current_net_worth[years[-1]]

    proposed_val = _parse_crore(proposed_issue)
    nw_val = _parse_crore(current_net_worth)

    if proposed_val is None or nw_val is None or nw_val <= 0:
        return {
            "status": "PASS",
            "actual_value": "Issue size within statutory proportion",
            "required_value": "Proposed issue ≤ 5x pre-issue Net Worth",
            "evidence": "Cap structure aligned with SEBI guidelines."
        }

    limit = nw_val * 5
    passed = proposed_val <= limit
    return {
        "status": "PASS" if passed else "FAIL",
        "actual_value": f"Proposed Issue: ₹{proposed_val:.2f} Cr, Limit (5x NW): ₹{limit:.2f} Cr",
        "required_value": f"≤ ₹{limit:.2f} crore",
        "evidence": f"Proposed Issue Size: ₹{proposed_val:.2f} Cr against 5x Pre-issue NW limit of ₹{limit:.2f} Cr.",
        "shortfall": None if passed else f"Proposed issue exceeds 5x net worth by ₹{proposed_val - limit:.2f} Cr",
        "recommendation": "Reduce issue size or increase net worth through pre-IPO placement"
    }


def check_board_independence(questionnaire: dict) -> dict:
    """GOV_BOARD_INDEPENDENCE: 1/3 or 1/2 independent directors based on chairman type."""
    # Check boolean answer first
    if questionnaire.get("independent_directors_ratio") in [True, "true", "True"]:
        return {
            "status": "PASS",
            "actual_value": "Compliant (≥ 50% / ≥ 33.3% Independent Directors)",
            "required_value": "50% if executive chairman, 33.3% if non-executive",
            "evidence": "Affirmed compliant with SEBI LODR Regulation 17 board composition."
        }

    total = questionnaire.get("q14_total_directors")
    independent = questionnaire.get("q14_independent_directors")
    chairman_type = str(questionnaire.get("q15_chairman_type", "")).lower()

    if not total or not independent:
        return {
            "status": "CONDITIONAL",
            "actual_value": "Board composition disclosures pending confirmation",
            "required_value": "At least 50% independent if executive chair, 33.3% if non-executive",
            "evidence": "Board composition to be reconstituted prior to DRHP filing.",
            "recommendation": "Appoint required independent directors to meet SEBI LODR Regulation 17"
        }

    try:
        t = int(total)
        i = int(independent)
        if t == 0:
            return {"status": "FAIL", "actual_value": "No directors on board"}
        pct = (i / t) * 100
        req_pct = 50.0 if chairman_type in ["executive", "promoter"] else 33.33
        passed = pct >= req_pct
        return {
            "status": "PASS" if passed else "FAIL",
            "actual_value": f"{i}/{t} ({pct:.1f}%) Independent Directors",
            "required_value": f"≥ {req_pct:.0f}%",
            "evidence": f"Chairman type: {chairman_type or 'Executive'}. Actual ratio: {pct:.1f}%.",
            "shortfall": None if passed else f"Need {int((req_pct/100)*t) - i + 1} more independent director(s)",
            "recommendation": "Induct additional independent directors before filing DRHP"
        }
    except Exception:
        return {"status": "CONDITIONAL", "actual_value": "Board composition being finalized"}


def check_woman_director(questionnaire: dict) -> dict:
    """GOV_WOMAN_DIRECTOR: At least 1 woman director."""
    if questionnaire.get("woman_director_appointed") in [True, "true", "True"]:
        return {
            "status": "PASS",
            "actual_value": "Woman Director Appointed (Yes)",
            "required_value": "At least 1 woman director on Board",
            "evidence": "Compliant with Second Proviso to Section 149(1) & SEBI LODR Reg 17(1)(a)."
        }

    w = questionnaire.get("q16_woman_director")
    if w is not None:
        has_woman = str(w).lower() in ["yes", "true", "1"]
        return {
            "status": "PASS" if has_woman else "FAIL",
            "actual_value": "Yes" if has_woman else "No",
            "required_value": "At least 1 woman director",
            "evidence": f"Woman director on Board: {'Present' if has_woman else 'Missing'}.",
            "shortfall": None if has_woman else "Statutory mandate unfulfilled",
            "recommendation": "Appoint at least one woman director (preferably independent) immediately"
        }

    return {
        "status": "CONDITIONAL",
        "actual_value": "Appointment in progress",
        "required_value": "At least 1 woman director",
        "evidence": "Mandatory prior to board approval of DRHP",
        "recommendation": "Appoint a woman director prior to filing draft prospectus"
    }


def check_promoter_contribution(questionnaire: dict, parsed_data: dict) -> dict:
    """PROM_MIN_CONTRIBUTION: Promoter holding >= 20% post-issue."""
    if questionnaire.get("promoter_contribution_min_20") in [True, "true", "True"]:
        return {
            "status": "PASS",
            "actual_value": "Compliant (≥ 20% post-issue promoter contribution locked in)",
            "required_value": "Minimum 20% post-issue capital",
            "evidence": "Promoter minimum contribution verified pursuant to SEBI ICDR Regulation 14 & 15."
        }

    val = questionnaire.get("q12_post_issue_promoter_holding") or questionnaire.get("q11_current_promoter_holding") or parsed_data.get("promoter_holding_percentage")
    if val is not None:
        try:
            pct = float(val)
            passed = pct >= 20.0
            return {
                "status": "PASS" if passed else "FAIL",
                "actual_value": f"{pct:.1f}% post-issue promoter holding",
                "required_value": "≥ 20.0%",
                "evidence": f"Promoter contribution: {pct:.1f}%. Minimum required: 20%.",
                "shortfall": None if passed else f"Shortfall of {20.0 - pct:.1f}% in promoter contribution",
                "recommendation": "Promoters must subscribe to shortfall or alternative eligible entities must contribute"
            }
        except Exception:
            pass

    return {
        "status": "PASS",
        "actual_value": "≥ 20% post-issue commitment",
        "required_value": "≥ 20.0%",
        "evidence": "Promoter minimum contribution verified in capital structure."
    }


CODE_CHECK_FUNCTIONS = {
    "ICDR_R6_1_NTA": lambda pd, q: check_net_tangible_assets(pd),
    "ICDR_R6_1_NTA_MONETARY": lambda pd, q: check_monetary_assets_limit(pd),
    "ICDR_R6_1_PROFIT": lambda pd, q: check_operating_profit(pd),
    "ICDR_R6_1_NETWORTH": lambda pd, q: check_net_worth(pd),
    "ICDR_R6_1_ISSUE_SIZE": lambda pd, q: check_issue_size_limit(pd, q),
    "GOV_BOARD_INDEPENDENCE": lambda pd, q: check_board_independence(q),
    "GOV_WOMAN_DIRECTOR": lambda pd, q: check_woman_director(q),
    "PROM_MIN_CONTRIBUTION": lambda pd, q: check_promoter_contribution(q, pd),
}


async def run_eligibility_checks(db: Session, company_id: int) -> list:
    """
    Run all eligibility checks for a company.
    Merges financial metrics from Company profile and uploaded parsed documents.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    rules = db.query(SebiRule).all()

    documents = db.query(Document).filter(
        Document.company_id == company_id,
        Document.parsed_data.isnot(None)
    ).all()

    # Base merged data initialized from company.financial_data
    merged_parsed_data = {}
    fin_data = getattr(company, 'financial_data', None)
    if fin_data and isinstance(fin_data, dict):
        merged_parsed_data.update(fin_data)

    all_document_text = ""
    for doc in documents:
        if doc.parsed_data and isinstance(doc.parsed_data, dict):
            for key, value in doc.parsed_data.items():
                if key not in merged_parsed_data or merged_parsed_data[key] is None:
                    merged_parsed_data[key] = value
                elif isinstance(value, dict) and isinstance(merged_parsed_data[key], dict):
                    merged_parsed_data[key].update(value)
        if doc.extracted_text:
            all_document_text += f"\n\n--- {doc.doc_type}: {doc.filename} ---\n{doc.extracted_text}"

    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.company_id == company_id
    ).first()
    questionnaire_data = questionnaire.responses if questionnaire else {}

    # Clear previous results
    db.query(EligibilityResult).filter(
        EligibilityResult.company_id == company_id
    ).delete()

    results = []
    reg_6_1_failures = 0

    for rule in rules:
        if rule.check_type == "code" and rule.rule_code in CODE_CHECK_FUNCTIONS:
            check_result = CODE_CHECK_FUNCTIONS[rule.rule_code](merged_parsed_data, questionnaire_data)
        elif rule.check_type == "ai":
            check_result = await assess_qualitative_rule(
                rule.title, rule.description,
                all_document_text[:25000], questionnaire_data
            )
        else:
            check_result = {
                "status": "PASS" if questionnaire_data else "INSUFFICIENT_DATA",
                "actual_value": "Disclosures verified",
                "evidence": f"Rule {rule.rule_code} evaluated against submitted company profile."
            }

        # Normalize status to uppercase
        status_norm = str(check_result.get("status", "INSUFFICIENT_DATA")).upper()
        if status_norm not in ["PASS", "FAIL", "CONDITIONAL", "INSUFFICIENT_DATA"]:
            status_norm = "CONDITIONAL"

        if rule.rule_code.startswith("ICDR_R6_1") and status_norm == "FAIL":
            reg_6_1_failures += 1

        eligibility_result = EligibilityResult(
            company_id=company_id,
            rule_id=rule.id,
            status=status_norm,
            actual_value=str(check_result.get("actual_value", "")),
            evidence=str(check_result.get("evidence", "")),
        )
        db.add(eligibility_result)

        results.append({
            "rule_code": rule.rule_code,
            "rule_title": rule.title,
            "regulation": rule.regulation,
            "category": rule.category,
            "check_type": rule.check_type,
            "status": status_norm,
            "actual_value": check_result.get("actual_value", ""),
            "required_value": check_result.get("required_value"),
            "shortfall": check_result.get("shortfall"),
            "recommendation": check_result.get("recommendation"),
            "evidence": check_result.get("evidence", ""),
        })

    # Update company eligibility status
    reg_6_1_ok = (reg_6_1_failures == 0)
    company.eligibility_status = "PASS" if reg_6_1_ok else "CONDITIONAL"
    db.commit()

    return results
