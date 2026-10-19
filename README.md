# 🏛️ IPO Readiness Assessment & Consulting Agent

An AI-powered capital markets advisory platform and consulting agent designed to evaluate private company readiness for an Initial Public Offering (IPO) on Indian stock exchanges (BSE / NSE) under the **SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018**.

---

## 🌟 Key Features

### 1. SEBI ICDR 2018 Statutory Evaluation Engine
- **Dual-Route Analysis**:
  - **Regulation 6(1) — Profitability Route**:
    - Net Tangible Assets $\ge$ ₹3 Cr in each of preceding 3 full years.
    - Monetary assets limit $\le$ 50% of NTA.
    - Operating Profit $\ge$ ₹15 Cr in at least 3 of preceding 5 years.
    - Net Worth $\ge$ ₹1 Cr in each of preceding 3 full years.
    - Issue size limitation $\le$ 5x pre-issue net worth.
  - **Regulation 6(2) — QIB / Alternative Route**:
    - 100% Book Building Process with mandatory 75% Qualified Institutional Buyers (QIB) allotment.
- **Promoter Lock-in & Contribution Verification**:
  - Minimum 20% post-issue promoter contribution.
  - 18-month lock-in compliance verification.
- **Corporate Governance & LODR Regulation 17**:
  - Board composition analysis (Executive vs Non-Executive Chairman independence ratio).
  - Mandatory woman director appointment.
  - Audit Committee, NRC, and SRC compliance checks.
- **Regulation 5 Fit & Proper Disqualifications**:
  - SEBI debarment, wilful defaulter, and fugitive economic offender background checks.

### 2. Multi-Format Document Parsing & Extraction
- Automated ingestion of PDF financial statements (`pdfplumber`) and Excel spreadsheets (`openpyxl`, `pandas`).
- Structured metric extraction (P&L, Balance Sheet, Cap Table, DRHP drafts) using **Gemini AI** with built-in deterministic heuristic fallbacks.

### 3. Dynamic Statutory Questionnaire
- 30-question interactive corporate governance intake covering Company Background, Financial History, Promoter Group, Governance & Committees, Legal & Litigation Disclosures, and IPO Objectives.

### 4. 4-Pillar Weighted Readiness Scorecard
- Multi-dimensional scoring model:
  - **Financial Preparedness (30%)**
  - **Corporate Governance & Board Composition (25%)**
  - **Regulatory & Legal Compliance (25%)**
  - **Capital Structure & Restatement Maturity (20%)**
- Prioritized gap matrix with statutory remedies and actionable timelines.

### 5. AI-Generated IPO Advisory Reports
- Markdown-rendered strategic reports synthesizing executive summaries, SEBI compliance matrices, dimensional scorecards, key risk factors, and a month-by-month 12-month roadmap to listing.
- Interactive clipboard export and print-to-PDF support.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic |
| **AI / LLM** | Google Gemini API (`google-generativeai`), Gemini 2.0 Flash |
| **Document Processing** | `pdfplumber`, `openpyxl`, `pandas`, `aiofiles`, `python-multipart` |
| **Frontend** | React 18, Vite, React Router DOM, React Markdown |
| **Styling** | Custom Vanilla CSS Design System with dark glassmorphic UI |

---

## 📂 Project Structure

```text
IPO Consulting agent/
├── backend/
│   ├── database/
│   │   ├── models.py            # SQLAlchemy database models
│   │   ├── seed_rules.py        # 22 permanent statutory SEBI ICDR rules
│   │   └── session.py           # SQLite session & database engine
│   ├── routers/
│   │   ├── companies.py         # Company management API
│   │   ├── documents.py         # File upload & extraction API
│   │   ├── questionnaire.py     # 30-question ICDR intake API
│   │   ├── eligibility.py       # SEBI ICDR compliance check API
│   │   ├── readiness.py         # Readiness scoring & gap matrix API
│   │   └── reports.py           # AI advisory report API
│   ├── services/
│   │   ├── document_parser.py   # PDF & Excel extraction service
│   │   ├── eligibility_engine.py# Deterministic statutory rule engine
│   │   ├── gemini_service.py    # LLM extraction & synthesis service
│   │   ├── readiness_scorer.py  # 4-pillar readiness calculation
│   │   └── report_generator.py  # Advisory report compiler
│   ├── config.py                # Environment configuration
│   ├── main.py                  # FastAPI application entrypoint
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx       # Header with action slot
│   │   │   └── Sidebar.jsx      # Navigation sidebar
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # Company metrics & assessment cards
│   │   │   ├── NewCompany.jsx   # Assessment intake & route selector
│   │   │   ├── CompanyWorkspace.jsx # 6-tab assessment workspace
│   │   │   └── RulesLibrary.jsx # SEBI ICDR 2018 regulation explorer
│   │   ├── api.js               # Centralized API client
│   │   ├── App.jsx              # Main router
│   │   ├── index.css            # Custom glassmorphic design system
│   │   └── main.jsx             # React entrypoint
│   ├── package.json
│   └── vite.config.js           # Vite dev server with proxy
├── .gitignore
├── Instructions.md              # Project specifications
├── migrate_db.py                # Schema migration helper
├── test_integration.py          # End-to-end integration test suite
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (with npm)
- (Optional) Google Gemini API Key

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# (Optional) Set up your Gemini API Key in backend/.env
cp backend/.env.example backend/.env
# Edit backend/.env and add: GEMINI_API_KEY=your_key_here

# Initialize database and start FastAPI server
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will start at `http://127.0.0.1:8000`.  
Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
The web application will open at `http://localhost:5173/`.

### 4. Running Integration Tests
To test the complete statutory assessment pipeline:
```bash
python test_integration.py
```

---

## 📄 API Documentation Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/companies` | List all companies with status & scores |
| `POST` | `/api/companies` | Create a new company assessment profile |
| `GET` | `/api/eligibility/rules` | Retrieve all 22 statutory SEBI ICDR rules |
| `POST` | `/api/eligibility/check/{id}` | Run deterministic SEBI ICDR checks |
| `POST` | `/api/documents/upload/{id}` | Upload financial statements (PDF/Excel) |
| `POST` | `/api/documents/extract/{doc_id}` | Extract structured metrics with Gemini |
| `GET` | `/api/questionnaire/schema` | Fetch 30-question statutory schema |
| `POST` | `/api/questionnaire/{id}` | Save governance questionnaire responses |
| `POST` | `/api/readiness/score/{id}` | Calculate 4-pillar readiness scorecard |
| `POST` | `/api/reports/generate/{id}` | Generate comprehensive AI advisory report |

---

## ⚖️ Disclaimer
*This application is an automated diagnostic and advisory tool built for preliminary IPO readiness analysis. It does not constitute formal legal or underwriting counsel. Consult SEBI-registered Merchant Bankers and Legal Counsel prior to filing a Draft Red Herring Prospectus (DRHP).*

---

## 📝 License
MIT License.
