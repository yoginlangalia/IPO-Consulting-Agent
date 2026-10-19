import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import Header from '../components/Header';
import {
  getCompany,
  updateCompany,
  getDocuments,
  uploadDocument,
  deleteDocument,
  extractDocumentData,
  getQuestionnaireSchema,
  getQuestionnaireResponses,
  saveQuestionnaireResponses,
  runEligibilityCheck,
  getEligibilityResults,
  runReadinessScoring,
  getReadinessResults,
  generateReport,
  getReports,
  getReport,
  deleteReport,
} from '../api';

export default function CompanyWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Tab State: 'overview' | 'documents' | 'questionnaire' | 'eligibility' | 'readiness' | 'reports'
  const [activeTab, setActiveTab] = useState('overview');

  // Company State
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Documents State
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [extractingId, setExtractingId] = useState(null);
  const [docType, setDocType] = useState('FINANCIAL_PL');
  const fileInputRef = useRef(null);

  // Questionnaire State
  const [schema, setSchema] = useState([]);
  const [responses, setResponses] = useState({});
  const [savingQuestionnaire, setSavingQuestionnaire] = useState(false);

  // Eligibility State
  const [eligibilityData, setEligibilityData] = useState(null);
  const [checkingEligibility, setCheckingEligibility] = useState(false);

  // Readiness State
  const [readinessData, setReadinessData] = useState(null);
  const [scoringReadiness, setScoringReadiness] = useState(false);

  // Reports State
  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  // Flash message timer
  const showSuccess = (msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  // Load initial company data
  const loadCompany = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCompany(id);
      setCompany(data);
    } catch (err) {
      setError(err.message || 'Failed to load company details');
    } finally {
      setLoading(false);
    }
  };

  // Load tab-specific data on tab switch
  useEffect(() => {
    loadCompany();
  }, [id]);

  useEffect(() => {
    if (!company) return;

    if (activeTab === 'documents') {
      getDocuments(id).then(setDocuments).catch(console.error);
    } else if (activeTab === 'questionnaire') {
      Promise.all([getQuestionnaireSchema(), getQuestionnaireResponses(id)])
        .then(([s, r]) => {
          setSchema(s);
          setResponses(r.responses || {});
        })
        .catch(console.error);
    } else if (activeTab === 'eligibility') {
      getEligibilityResults(id).then(setEligibilityData).catch(console.error);
    } else if (activeTab === 'readiness') {
      getReadinessResults(id).then(setReadinessData).catch(console.error);
    } else if (activeTab === 'reports') {
      getReports(id).then((reps) => {
        setReports(reps);
        if (reps.length > 0 && !activeReport) {
          getReport(reps[0].id).then(setActiveReport).catch(console.error);
        }
      }).catch(console.error);
    }
  }, [activeTab, company?.id]);

  // Handle Document Upload
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      await uploadDocument(id, file, docType);
      showSuccess(`File "${file.name}" uploaded successfully!`);
      const docs = await getDocuments(id);
      setDocuments(docs);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  // Handle Data Extraction
  const handleExtract = async (docId) => {
    try {
      setExtractingId(docId);
      await extractDocumentData(docId);
      showSuccess('AI extraction completed! Extracted metrics updated in company profile.');
      const [docs, comp] = await Promise.all([getDocuments(id), getCompany(id)]);
      setDocuments(docs);
      setCompany(comp);
    } catch (err) {
      setError(err.message || 'Extraction failed');
    } finally {
      setExtractingId(null);
    }
  };

  // Handle Document Delete
  const handleDeleteDoc = async (docId) => {
    if (!window.confirm('Delete this document?')) return;
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      showSuccess('Document deleted.');
    } catch (err) {
      setError(err.message || 'Failed to delete');
    }
  };

  // Handle Questionnaire Response Change
  const handleQuestionChange = (questionId, value) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  // Save Questionnaire
  const handleSaveQuestionnaire = async () => {
    try {
      setSavingQuestionnaire(true);
      await saveQuestionnaireResponses(id, { responses });
      showSuccess('Questionnaire responses saved successfully!');
    } catch (err) {
      setError(err.message || 'Failed to save questionnaire');
    } finally {
      setSavingQuestionnaire(false);
    }
  };

  // Run SEBI ICDR Eligibility Check
  const handleRunEligibility = async () => {
    try {
      setCheckingEligibility(true);
      const res = await runEligibilityCheck(id);
      setEligibilityData(res);
      showSuccess('SEBI ICDR 2018 Eligibility check completed!');
      loadCompany();
    } catch (err) {
      setError(err.message || 'Eligibility check failed');
    } finally {
      setCheckingEligibility(false);
    }
  };

  // Run Readiness Scoring
  const handleRunReadiness = async () => {
    try {
      setScoringReadiness(true);
      const res = await runReadinessScoring(id);
      setReadinessData(res);
      showSuccess('IPO Readiness scoring completed!');
      loadCompany();
    } catch (err) {
      setError(err.message || 'Scoring failed');
    } finally {
      setScoringReadiness(false);
    }
  };

  // Generate Report
  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      const newRep = await generateReport(id);
      showSuccess('AI IPO Advisory Report generated successfully!');
      const reps = await getReports(id);
      setReports(reps);
      setActiveReport(newRep);
    } catch (err) {
      setError(err.message || 'Report generation failed');
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Header title="Company Workspace" />
        <div className="page-container">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <span>Loading company assessment data...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div>
        <Header title="Company Workspace" />
        <div className="page-container">
          <div className="alert alert-danger">Company not found.</div>
          <Link to="/" className="btn btn-secondary">← Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  const score = company.readiness_score != null ? Math.round(company.readiness_score) : null;

  return (
    <div>
      <Header
        title={company.name}
        subtitle={`${company.sector || 'General Sector'} • ${company.target_track === 'REG_6_2' ? 'Regulation 6(2) QIB Route' : 'Regulation 6(1) Profitability Route'}`}
      >
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setActiveTab('reports')}
          >
            📑 Reports ({reports.length})
          </button>
          <Link to="/" className="btn btn-secondary btn-sm">
            ← Dashboard
          </Link>
        </div>
      </Header>

      <div className="page-container">
        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 20 }}>
            <span>⚠️ {error}</span>
            <button
              onClick={() => setError(null)}
              style={{ background: 'transparent', border: 'none', color: 'inherit', marginLeft: 'auto', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>
        )}

        {successMsg && (
          <div className="alert alert-success" style={{ marginBottom: 20 }}>
            <span>✅ {successMsg}</span>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📊 Overview
          </button>
          <button
            className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            📁 Document Vault
          </button>
          <button
            className={`tab ${activeTab === 'questionnaire' ? 'active' : ''}`}
            onClick={() => setActiveTab('questionnaire')}
          >
            📝 ICDR Questionnaire
          </button>
          <button
            className={`tab ${activeTab === 'eligibility' ? 'active' : ''}`}
            onClick={() => setActiveTab('eligibility')}
          >
            ⚖️ SEBI ICDR Engine
          </button>
          <button
            className={`tab ${activeTab === 'readiness' ? 'active' : ''}`}
            onClick={() => setActiveTab('readiness')}
          >
            🎯 Readiness Score
          </button>
          <button
            className={`tab ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            📑 Advisory Report
          </button>
        </div>

        {/* ==================== TAB 1: OVERVIEW ==================== */}
        {activeTab === 'overview' && (
          <div>
            {/* Top Metrics Cards */}
            <div className="grid-4" style={{ marginBottom: 24 }}>
              <div className="stat-card">
                <div className="stat-card-icon">🎯</div>
                <div className="stat-card-value" style={{
                  color: score >= 75 ? 'var(--success-light)' : score >= 50 ? 'var(--warning-light)' : 'var(--accent-primary-light)'
                }}>
                  {score != null ? `${score}%` : 'Pending'}
                </div>
                <div className="stat-card-label">Readiness Score</div>
              </div>

              <div className="stat-card">
                <div className="stat-card-icon">⚖️</div>
                <div className="stat-card-value" style={{ fontSize: 20, color: 'var(--text-primary)' }}>
                  {company.eligibility_status === 'PASS' ? (
                    <span style={{ color: 'var(--success-light)' }}>Eligible</span>
                  ) : company.eligibility_status === 'CONDITIONAL' ? (
                    <span style={{ color: 'var(--warning-light)' }}>Conditional</span>
                  ) : company.eligibility_status === 'FAIL' ? (
                    <span style={{ color: 'var(--danger-light)' }}>Ineligible</span>
                  ) : (
                    'Not Evaluated'
                  )}
                </div>
                <div className="stat-card-label">SEBI ICDR Status</div>
              </div>

              <div className="stat-card">
                <div className="stat-card-icon">📑</div>
                <div className="stat-card-value">
                  {company.target_track === 'REG_6_2' ? 'Reg 6(2)' : 'Reg 6(1)'}
                </div>
                <div className="stat-card-label">
                  {company.target_track === 'REG_6_2' ? 'QIB Alternative Route' : 'Profitability Route'}
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-icon">⏱️</div>
                <div className="stat-card-value" style={{ fontSize: 20 }}>
                  {company.target_ipo_date || 'FY 2025-26'}
                </div>
                <div className="stat-card-label">Target IPO Timeline</div>
              </div>
            </div>

            {/* Assessment Workflow Steps */}
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">IPO Assessment Progress</div>
                  <div className="card-subtitle">Follow the end-to-end statutory evaluation workflow</div>
                </div>
              </div>

              <div className="grid-4">
                <div
                  style={{
                    background: 'var(--bg-tertiary)',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    borderLeft: '4px solid var(--accent-primary)',
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('documents')}
                >
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                    1. Upload Financials
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Upload P&L, Balance Sheet, Shareholding docs for AI extraction.
                  </p>
                </div>

                <div
                  style={{
                    background: 'var(--bg-tertiary)',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    borderLeft: '4px solid var(--info)',
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('questionnaire')}
                >
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                    2. Governance Check
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Complete SEBI ICDR Board, Promoters, and Litigations questionnaire.
                  </p>
                </div>

                <div
                  style={{
                    background: 'var(--bg-tertiary)',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    borderLeft: '4px solid var(--warning)',
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('eligibility')}
                >
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                    3. Run SEBI Engine
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Auto-check Reg 6(1) / 6(2), promoter lock-in, and statutory rules.
                  </p>
                </div>

                <div
                  style={{
                    background: 'var(--bg-tertiary)',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    borderLeft: '4px solid var(--success)',
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveTab('reports')}
                >
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                    4. Generate Report
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Produce comprehensive AI IPO advisory report for stakeholders.
                  </p>
                </div>
              </div>
            </div>

            {/* Financial Summary & Extracted Metrics */}
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Extracted Financial Profile & Key Metrics</div>
                  <div className="card-subtitle">
                    Core figures utilized for SEBI ICDR Regulation 6 threshold verification
                  </div>
                </div>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setActiveTab('documents')}
                >
                  📁 Manage Documents
                </button>
              </div>

              <div className="grid-3" style={{ marginBottom: 16 }}>
                <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Net Tangible Assets (NTA)</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                    {company.financial_data?.net_tangible_assets != null
                      ? `₹ ${company.financial_data.net_tangible_assets} Cr`
                      : 'Not Provided'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                    SEBI 6(1)(a) Req: Min ₹3 Cr each of 3 yrs
                  </div>
                </div>

                <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Operating Profit (Avg / Min)</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                    {company.financial_data?.operating_profit != null
                      ? `₹ ${company.financial_data.operating_profit} Cr`
                      : 'Not Provided'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                    SEBI 6(1)(b) Req: Min ₹15 Cr in 3 of 5 yrs
                  </div>
                </div>

                <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Net Worth</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                    {company.financial_data?.net_worth != null
                      ? `₹ ${company.financial_data.net_worth} Cr`
                      : 'Not Provided'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                    SEBI 6(1)(c) Req: Min ₹1 Cr each of 3 yrs
                  </div>
                </div>
              </div>

              {company.financial_data && Object.keys(company.financial_data).length > 0 && (
                <div style={{
                  background: 'var(--bg-tertiary)',
                  padding: 16,
                  borderRadius: 'var(--radius-md)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--text-secondary)',
                  overflowX: 'auto',
                }}>
                  <pre>{JSON.stringify(company.financial_data, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== TAB 2: DOCUMENT VAULT ==================== */}
        {activeTab === 'documents' && (
          <div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">Upload Financial Statements & Filing Documents</div>
                  <div className="card-subtitle">
                    Upload PDF or Excel files (Audited P&L, Balance Sheet, Cap Table, DRHP draft) for automatic AI data extraction
                  </div>
                </div>
              </div>

              <div className="grid-2" style={{ marginBottom: 20 }}>
                <div className="form-group">
                  <label className="form-label form-required">Document Classification</label>
                  <select
                    className="form-select"
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                  >
                    <option value="FINANCIAL_PL">Audited Profit & Loss Statement (3-5 Years)</option>
                    <option value="FINANCIAL_BS">Audited Balance Sheet (3-5 Years)</option>
                    <option value="SHAREHOLDING">Cap Table & Shareholding Pattern (Promoter Group)</option>
                    <option value="DRHP_DRAFT">Draft Red Herring Prospectus (DRHP / RHP Draft)</option>
                    <option value="OTHER">Other Compliance / Governance Disclosures</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Select File (PDF, XLSX, XLS)</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="form-input"
                    accept=".pdf,.xlsx,.xls"
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </div>
              </div>

              {uploading && (
                <div className="loading-spinner" style={{ padding: 12 }}>
                  <div className="spinner"></div>
                  <span>Uploading and registering document...</span>
                </div>
              )}
            </div>

            {/* Document List */}
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Uploaded Documents ({documents.length})</div>
                  <div className="card-subtitle">Manage files and run Gemini AI structured data extraction</div>
                </div>
              </div>

              {documents.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📄</div>
                  <div className="empty-state-title">No Documents Uploaded</div>
                  <div className="empty-state-text">
                    Upload the company's financial statements or draft prospectuses to automatically extract metrics.
                  </div>
                </div>
              ) : (
                <div>
                  {documents.map((doc) => (
                    <div key={doc.id} className="file-item">
                      <div className="file-icon">
                        {doc.filename?.endsWith('.pdf') ? '📕' : '📊'}
                      </div>
                      <div className="file-info">
                        <div className="file-name">{doc.filename}</div>
                        <div className="file-meta">
                          Type: <strong>{doc.doc_type}</strong> • Size: {Math.round((doc.file_size || 0) / 1024)} KB • Uploaded:{' '}
                          {new Date(doc.created_at).toLocaleDateString()} • Status:{' '}
                          <span style={{ color: doc.parsed_status === 'EXTRACTED' ? 'var(--success-light)' : 'var(--text-secondary)' }}>
                            {doc.parsed_status || 'PENDING'}
                          </span>
                        </div>

                        {doc.extracted_data && (
                          <div style={{
                            marginTop: 10,
                            padding: '8px 12px',
                            background: 'var(--bg-tertiary)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 12,
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--text-secondary)',
                            maxHeight: 120,
                            overflowY: 'auto',
                          }}>
                            <pre>{JSON.stringify(doc.extracted_data, null, 2)}</pre>
                          </div>
                        )}
                      </div>

                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleExtract(doc.id)}
                          disabled={extractingId === doc.id}
                        >
                          {extractingId === doc.id ? 'Extracting...' : '🤖 Extract with AI'}
                        </button>
                        <button
                          className="btn btn-danger btn-sm btn-icon"
                          title="Delete Document"
                          onClick={() => handleDeleteDoc(doc.id)}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== TAB 3: ICDR QUESTIONNAIRE ==================== */}
        {activeTab === 'questionnaire' && (
          <div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">SEBI ICDR 2018 Governance & Compliance Questionnaire</div>
                  <div className="card-subtitle">
                    Assess qualitative parameters including promoter lock-in, board composition, and legal disclosures
                  </div>
                </div>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={handleSaveQuestionnaire}
                  disabled={savingQuestionnaire}
                >
                  {savingQuestionnaire ? 'Saving...' : '💾 Save Responses'}
                </button>
              </div>

              {schema.length === 0 ? (
                <div className="loading-spinner">
                  <div className="spinner"></div>
                  <span>Loading questionnaire schema...</span>
                </div>
              ) : (
                <div>
                  {schema.map((section, sIdx) => (
                    <div key={section.section_id || sIdx} className="questionnaire-section">
                      <div className="questionnaire-section-title">
                        <div className="questionnaire-section-number">{sIdx + 1}</div>
                        <span>{section.title}</span>
                      </div>

                      {section.questions?.map((q) => (
                        <div key={q.id} className="form-group" style={{ marginBottom: 20 }}>
                          <label className="form-label">
                            {q.label}
                            {q.regulation_ref && (
                              <span style={{
                                marginLeft: 8,
                                fontSize: 11,
                                fontFamily: 'var(--font-mono)',
                                color: 'var(--accent-primary-light)',
                              }}>
                                [{q.regulation_ref}]
                              </span>
                            )}
                          </label>

                          {q.type === 'BOOLEAN' ? (
                            <div style={{ display: 'flex', gap: 20, marginTop: 6 }}>
                              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                                <input
                                  type="radio"
                                  name={q.id}
                                  value="true"
                                  checked={responses[q.id] === true || responses[q.id] === 'true'}
                                  onChange={() => handleQuestionChange(q.id, true)}
                                />
                                <span>Yes / Compliant</span>
                              </label>
                              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                                <input
                                  type="radio"
                                  name={q.id}
                                  value="false"
                                  checked={responses[q.id] === false || responses[q.id] === 'false'}
                                  onChange={() => handleQuestionChange(q.id, false)}
                                />
                                <span>No / Non-compliant</span>
                              </label>
                            </div>
                          ) : q.type === 'SELECT' ? (
                            <select
                              className="form-select"
                              value={responses[q.id] || ''}
                              onChange={(e) => handleQuestionChange(q.id, e.target.value)}
                            >
                              <option value="">-- Select option --</option>
                              {q.options?.map((opt) => (
                                <option key={opt.value || opt} value={opt.value || opt}>
                                  {opt.label || opt}
                                </option>
                              ))}
                            </select>
                          ) : q.type === 'TEXTAREA' ? (
                            <textarea
                              className="form-textarea"
                              placeholder={q.placeholder || 'Enter details...'}
                              value={responses[q.id] || ''}
                              onChange={(e) => handleQuestionChange(q.id, e.target.value)}
                              rows={2}
                            />
                          ) : (
                            <input
                              type={q.type === 'NUMBER' ? 'number' : 'text'}
                              className="form-input"
                              placeholder={q.placeholder || ''}
                              value={responses[q.id] || ''}
                              onChange={(e) => handleQuestionChange(q.id, e.target.value)}
                            />
                          )}

                          {q.hint && <div className="form-hint">{q.hint}</div>}
                        </div>
                      ))}
                    </div>
                  ))}

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24 }}>
                    <button
                      className="btn btn-primary btn-lg"
                      onClick={handleSaveQuestionnaire}
                      disabled={savingQuestionnaire}
                    >
                      {savingQuestionnaire ? 'Saving...' : '💾 Save All Responses'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== TAB 4: SEBI ICDR ELIGIBILITY ENGINE ==================== */}
        {activeTab === 'eligibility' && (
          <div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">SEBI ICDR Regulations 2018 Statutory Eligibility Engine</div>
                  <div className="card-subtitle">
                    Automated verification against Regulation 6(1) Profitability route, Regulation 6(2) QIB route, promoter lock-in, and governance mandates
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={handleRunEligibility}
                  disabled={checkingEligibility}
                >
                  {checkingEligibility ? 'Evaluating Rules...' : '⚡ Run Eligibility Check'}
                </button>
              </div>

              {eligibilityData?.route_summary && (
                <div className="grid-2" style={{ marginBottom: 24 }}>
                  <div style={{
                    padding: 20,
                    borderRadius: 'var(--radius-md)',
                    background: eligibilityData.route_summary.reg_6_1_eligible ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                    border: eligibilityData.route_summary.reg_6_1_eligible ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <strong style={{ fontSize: 16, color: 'var(--text-primary)' }}>
                        Regulation 6(1) — Profitability Route
                      </strong>
                      <span className={`badge ${eligibilityData.route_summary.reg_6_1_eligible ? 'badge-pass' : 'badge-fail'}`}>
                        {eligibilityData.route_summary.reg_6_1_eligible ? 'Eligible' : 'Ineligible'}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      Requires ₹3 Cr NTA, ₹15 Cr Operating Profit (3/5 yrs), ₹1 Cr Net Worth.
                    </p>
                  </div>

                  <div style={{
                    padding: 20,
                    borderRadius: 'var(--radius-md)',
                    background: eligibilityData.route_summary.reg_6_2_eligible ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                    border: eligibilityData.route_summary.reg_6_2_eligible ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <strong style={{ fontSize: 16, color: 'var(--text-primary)' }}>
                        Regulation 6(2) — QIB Route (Alternative)
                      </strong>
                      <span className={`badge ${eligibilityData.route_summary.reg_6_2_eligible ? 'badge-pass' : 'badge-fail'}`}>
                        {eligibilityData.route_summary.reg_6_2_eligible ? 'Available Route' : 'Ineligible'}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      100% Book Building Process with mandatory 75% QIB allotment.
                    </p>
                  </div>
                </div>
              )}

              {/* Individual Rules Matrix */}
              <div>
                <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
                  Rule-by-Rule Compliance Matrix
                </div>

                {!eligibilityData?.results || eligibilityData.results.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">⚖️</div>
                    <div className="empty-state-title">No Evaluation Completed Yet</div>
                    <div className="empty-state-text">
                      Click the "Run Eligibility Check" button above to evaluate this company against all SEBI ICDR 2018 rules.
                    </div>
                  </div>
                ) : (
                  <div>
                    {eligibilityData.results.map((r, idx) => {
                      const isPass = r.status === 'PASS';
                      const isFail = r.status === 'FAIL';
                      const isWarning = r.status === 'CONDITIONAL' || r.status === 'INSUFFICIENT_DATA';

                      return (
                        <div key={r.rule_code || idx} className="rule-card">
                          <div className="rule-card-header">
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span className="rule-card-title">{r.rule_title || r.rule_code}</span>
                                {r.regulation_ref && (
                                  <span className="badge badge-info" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                                    {r.regulation_ref}
                                  </span>
                                )}
                              </div>
                              <div className="rule-card-regulation">
                                Category: {r.category} • Track: {r.applicable_track}
                              </div>
                            </div>
                            <div>
                              <span className={`badge ${isPass ? 'badge-pass' : isFail ? 'badge-fail' : 'badge-warning'}`}>
                                {r.status}
                              </span>
                            </div>
                          </div>

                          <div className="rule-card-description">
                            {r.explanation || r.rule_description}
                          </div>

                          {/* Evidence & Shortfall details */}
                          {(r.actual_value != null || r.shortfall || r.recommendation) && (
                            <div className="rule-card-evidence">
                              {r.actual_value != null && (
                                <div style={{ marginBottom: 4 }}>
                                  <strong>Company Actual:</strong> {typeof r.actual_value === 'object' ? JSON.stringify(r.actual_value) : String(r.actual_value)}
                                  {r.required_value && ` (Required: ${r.required_value})`}
                                </div>
                              )}
                              {r.shortfall && (
                                <div style={{ color: 'var(--danger-light)', marginBottom: 4 }}>
                                  <strong>Shortfall:</strong> {r.shortfall}
                                </div>
                              )}
                              {r.recommendation && (
                                <div style={{ color: 'var(--accent-primary-light)' }}>
                                  <strong>Remedy / Action Plan:</strong> {r.recommendation}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ==================== TAB 5: READINESS SCORING & GAPS ==================== */}
        {activeTab === 'readiness' && (
          <div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">Comprehensive IPO Readiness Scoring & Gap Breakdown</div>
                  <div className="card-subtitle">
                    Weighted 5-dimension evaluation across Financials, Governance, Compliance, Disclosures, and Operations
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={handleRunReadiness}
                  disabled={scoringReadiness}
                >
                  {scoringReadiness ? 'Calculating Score...' : '🎯 Calculate Readiness Score'}
                </button>
              </div>

              {!readinessData?.overall_score && readinessData?.overall_score !== 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">🎯</div>
                  <div className="empty-state-title">No Readiness Score Calculated Yet</div>
                  <div className="empty-state-text">
                    Click the "Calculate Readiness Score" button to run the multi-dimensional scoring model.
                  </div>
                </div>
              ) : (
                <div>
                  {/* Overall Score Highlight */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 32,
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-lg)',
                    padding: 24,
                    marginBottom: 28,
                  }}>
                    <div>
                      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1 }}>
                        Overall IPO Readiness Score
                      </div>
                      <div style={{
                        fontSize: 48,
                        fontWeight: 800,
                        lineHeight: 1.1,
                        marginTop: 4,
                        color: readinessData.overall_score >= 75
                          ? 'var(--success-light)'
                          : readinessData.overall_score >= 50
                          ? 'var(--warning-light)'
                          : 'var(--danger-light)',
                      }}>
                        {Math.round(readinessData.overall_score)}%
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                        Readiness Tier:{' '}
                        <strong>
                          {readinessData.overall_score >= 80
                            ? 'High Readiness (Ready for Merchant Banker)'
                            : readinessData.overall_score >= 60
                            ? 'Moderate Readiness (6-12 Months Runway)'
                            : 'Early Stage (Substantial Restructuring Needed)'}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {/* Dimension Breakdown */}
                  <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
                    Dimension-Wise Preparedness
                  </div>

                  <div className="grid-2" style={{ marginBottom: 28 }}>
                    {readinessData.dimensions &&
                      Object.entries(readinessData.dimensions).map(([dimName, dimVal]) => {
                        const dimScore = typeof dimVal === 'object' ? dimVal.score : dimVal;
                        const weight = typeof dimVal === 'object' ? dimVal.weight : null;

                        return (
                          <div key={dimName} style={{ background: 'var(--bg-tertiary)', padding: 18, borderRadius: 'var(--radius-md)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 14 }}>
                              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                {dimName.replace(/_/g, ' ').toUpperCase()}
                              </span>
                              <strong style={{ color: dimScore >= 75 ? 'var(--success-light)' : dimScore >= 50 ? 'var(--warning-light)' : 'var(--danger-light)' }}>
                                {Math.round(dimScore)}% {weight ? `(Weight: ${weight}%)` : ''}
                              </strong>
                            </div>
                            <div style={{ height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden' }}>
                              <div style={{
                                width: `${dimScore}%`,
                                height: '100%',
                                background: dimScore >= 75 ? 'var(--success)' : dimScore >= 50 ? 'var(--warning)' : 'var(--accent-primary)',
                                transition: 'width 0.6s ease',
                              }} />
                            </div>
                          </div>
                        );
                      })}
                  </div>

                  {/* Gaps and Recommendations */}
                  {readinessData.gaps && readinessData.gaps.length > 0 && (
                    <div>
                      <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
                        Identified Gaps & Strategic Recommendations
                      </div>
                      <div className="table-container">
                        <table>
                          <thead>
                            <tr>
                              <th>Priority</th>
                              <th>Area / Dimension</th>
                              <th>Gap Description</th>
                              <th>Statutory Remedy / Action Required</th>
                            </tr>
                          </thead>
                          <tbody>
                            {readinessData.gaps.map((gap, gIdx) => (
                              <tr key={gIdx}>
                                <td>
                                  <span className={`badge ${
                                    gap.priority === 'CRITICAL' || gap.priority === 'HIGH'
                                      ? 'badge-fail'
                                      : gap.priority === 'MEDIUM'
                                      ? 'badge-warning'
                                      : 'badge-info'
                                  }`}>
                                    {gap.priority || 'MEDIUM'}
                                  </span>
                                </td>
                                <td><strong>{gap.area || gap.dimension}</strong></td>
                                <td>{gap.description || gap.gap}</td>
                                <td>{gap.recommendation || gap.remedy}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== TAB 6: ADVISORY REPORT ==================== */}
        {activeTab === 'reports' && (
          <div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">SEBI ICDR IPO Readiness Advisory Report</div>
                  <div className="card-subtitle">
                    Comprehensive strategic advisory document generated using Gemini AI synthesizing all quantitative & qualitative data
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={handleGenerateReport}
                  disabled={generatingReport}
                >
                  {generatingReport ? 'Synthesizing with Gemini AI...' : '✨ Generate Full Advisory Report'}
                </button>
              </div>

              {reports.length > 1 && (
                <div style={{ display: 'flex', gap: 10, marginBottom: 20, overflowX: 'auto', paddingBottom: 4 }}>
                  {reports.map((rep, idx) => (
                    <button
                      key={rep.id}
                      className={`btn btn-sm ${activeReport?.id === rep.id ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => getReport(rep.id).then(setActiveReport)}
                    >
                      Report #{reports.length - idx} ({new Date(rep.created_at).toLocaleDateString()})
                    </button>
                  ))}
                </div>
              )}

              {!activeReport ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📑</div>
                  <div className="empty-state-title">No Report Generated Yet</div>
                  <div className="empty-state-text">
                    Click "Generate Full Advisory Report" to produce an executive-ready SEBI ICDR 2018 readiness document.
                  </div>
                </div>
              ) : (
                <div>
                  {/* Actions Bar */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 20,
                    padding: '12px 16px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                  }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                      Generated on: <strong>{new Date(activeReport.created_at).toLocaleString()}</strong>
                    </div>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => window.print()}
                      >
                        🖨️ Print / Save PDF
                      </button>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          navigator.clipboard.writeText(activeReport.content || '');
                          showSuccess('Report markdown copied to clipboard!');
                        }}
                      >
                        📋 Copy Markdown
                      </button>
                    </div>
                  </div>

                  {/* Render Markdown Content */}
                  <div className="report-content card" style={{ padding: 36 }}>
                    <ReactMarkdown>{activeReport.content || ''}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
