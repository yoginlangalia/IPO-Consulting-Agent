import urllib.request
import json

BASE = 'http://127.0.0.1:8000/api'

# 1. Check rules
req = urllib.request.urlopen(f'{BASE}/eligibility/rules')
rules = json.loads(req.read().decode())
print(f'1. Rules verified: {len(rules)} rules in DB')

# 2. Create company
payload = json.dumps({
    'name': 'TechVision Cloud Dynamics Limited',
    'sector': 'Technology & SaaS',
    'incorporation_year': 2019,
    'target_track': 'REG_6_1',
    'target_ipo_date': 'Q3 FY26',
    'description': 'Enterprise SaaS cloud infrastructure optimization platform.',
    'financial_data': {
        'net_tangible_assets': 28.5,
        'operating_profit': 19.2,
        'net_worth': 42.0,
        'pre_ipo_capital': 15.0,
        'proposed_issue_size': 450.0
    }
}).encode('utf-8')

req = urllib.request.Request(f'{BASE}/companies', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
res = urllib.request.urlopen(req)
company = json.loads(res.read().decode())
cid = company['id']
print(f'2. Company created: ID {cid}, Name: {company["name"]}')

# 3. Save questionnaire responses
q_payload = json.dumps({
    'responses': {
        'q1_company_name': 'TechVision Cloud Dynamics Limited',
        'q3_is_public_company': 'Yes',
        'q4_industry': 'Technology & SaaS',
        'q5_name_changed': 'No',
        'q6_proposed_issue_size': 450.0,
        'q8_current_net_worth': 42.0,
        'q11_current_promoter_holding': 65.0,
        'q12_post_issue_promoter_holding': 48.0,
        'q14_total_directors': 6,
        'q14_independent_directors': 3,
        'q15_chairman_type': 'Non-Executive',
        'q16_woman_director': 'Yes',
        'q17_audit_committee': 'Yes, fully compliant',
        'q18_nrc': 'Yes',
        'q19_src': 'Yes',
        'q20_compliance_officer': 'Yes',
        'q21_sebi_debarment': 'No',
        'q22_wilful_defaulter': 'No',
        'q23_fugitive_offender': 'No',
        'q26_ipo_purpose': 'Business expansion',
        'q27_target_timeline': 'Q3 FY26',
        'q28_raise_amount': 450.0,
        'q29_brlm_appointed': 'In discussions',
        'q30_restated_financials': 'Yes, completed',
        'promoter_contribution_min_20': True,
        'promoter_lockin_18m': True,
        'independent_directors_ratio': True,
        'woman_director_appointed': True,
        'audit_committee_compliant': True,
        'financials_restated_ind_as': True,
        'no_sebi_debarment': True,
        'no_wilful_defaulter': True
    }
}).encode('utf-8')
req = urllib.request.Request(f'{BASE}/questionnaire/{cid}', data=q_payload, headers={'Content-Type': 'application/json'}, method='POST')
res = urllib.request.urlopen(req)
print('3. Questionnaire submitted successfully')

# 4. Run Eligibility Check
req = urllib.request.Request(f'{BASE}/eligibility/check/{cid}', method='POST')
res = urllib.request.urlopen(req)
eligibility = json.loads(res.read().decode())
print(f'4. Eligibility Check Results: Status={eligibility.get("overall_status")}, Passed={eligibility.get("passed")}/{eligibility.get("total_rules")}, Reg 6(1) Eligible={eligibility.get("route_summary", {}).get("reg_6_1_eligible")}')

# 5. Run Readiness Scoring
req = urllib.request.Request(f'{BASE}/readiness/score/{cid}', method='POST')
res = urllib.request.urlopen(req)
readiness = json.loads(res.read().decode())
print(f'5. Readiness Scoring Results: Overall Score={readiness.get("overall_score")}%, Tier={readiness.get("readiness_tier")}, Dimensions={len(readiness.get("dimensions", {}))}')

# 6. Generate Report
req = urllib.request.Request(f'{BASE}/reports/generate/{cid}', method='POST')
res = urllib.request.urlopen(req)
report = json.loads(res.read().decode())
print(f'6. Advisory Report Generated: ID {report.get("id")}, Title: "{report.get("title")}", Length: {len(report.get("content", ""))} chars')

# 7. Check updated company record
req = urllib.request.urlopen(f'{BASE}/companies/{cid}')
comp_updated = json.loads(req.read().decode())
print(f'7. Updated Company Profile: Readiness Score={comp_updated.get("readiness_score")}%, Eligibility Status={comp_updated.get("eligibility_status")}')
