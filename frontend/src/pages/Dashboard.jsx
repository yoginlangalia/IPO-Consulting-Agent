import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { getCompanies, deleteCompany } from '../api';

export default function Dashboard() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTrack, setFilterTrack] = useState('ALL');
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCompanies();
      setCompanies(data);
    } catch (err) {
      setError(err.message || 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id, name, e) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete "${name}" and all associated documents, questionnaires, and reports?`)) {
      return;
    }
    try {
      await deleteCompany(id);
      setCompanies((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      alert(`Error deleting company: ${err.message}`);
    }
  };

  const filteredCompanies = companies.filter((c) => {
    const matchesSearch = c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          c.sector?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTrack = filterTrack === 'ALL' || c.target_track === filterTrack;
    return matchesSearch && matchesTrack;
  });

  // Calculate aggregates
  const totalCompanies = companies.length;
  const scoredCompanies = companies.filter((c) => c.readiness_score != null);
  const avgScore = scoredCompanies.length > 0
    ? Math.round(scoredCompanies.reduce((acc, c) => acc + (c.readiness_score || 0), 0) / scoredCompanies.length)
    : 0;
  const eligibleCount = companies.filter((c) => c.eligibility_status === 'PASS' || c.eligibility_status === 'ELIGIBLE').length;
  const reportCount = companies.reduce((acc, c) => acc + (c.reports_count || 0), 0);

  const getScoreColor = (score) => {
    if (score == null) return 'var(--text-tertiary)';
    if (score >= 75) return 'var(--success-light)';
    if (score >= 50) return 'var(--warning-light)';
    return 'var(--danger-light)';
  };

  const getEligibilityBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'PASS':
      case 'ELIGIBLE':
        return <span className="badge badge-pass">Eligible</span>;
      case 'CONDITIONAL':
        return <span className="badge badge-warning">Conditional</span>;
      case 'FAIL':
      case 'INELIGIBLE':
        return <span className="badge badge-fail">Ineligible</span>;
      default:
        return <span className="badge badge-draft">Pending Check</span>;
    }
  };

  return (
    <div>
      <Header
        title="IPO Readiness Dashboard"
        subtitle="Manage companies, evaluate SEBI ICDR 2018 compliance, and track IPO preparedness"
      >
        <Link to="/new" className="btn btn-primary">
          <span>➕</span> New Assessment
        </Link>
      </Header>

      <div className="page-container">
        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 24 }}>
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Aggregate Stats */}
        <div className="grid-4" style={{ marginBottom: 32 }}>
          <div className="stat-card">
            <div className="stat-card-icon">🏢</div>
            <div className="stat-card-value">{totalCompanies}</div>
            <div className="stat-card-label">Assessed Companies</div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon">🎯</div>
            <div className="stat-card-value" style={{ color: avgScore > 0 ? getScoreColor(avgScore) : 'var(--text-primary)' }}>
              {avgScore > 0 ? `${avgScore}%` : 'N/A'}
            </div>
            <div className="stat-card-label">Average Readiness Score</div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon">⚖️</div>
            <div className="stat-card-value" style={{ color: 'var(--success-light)' }}>
              {eligibleCount}
            </div>
            <div className="stat-card-label">SEBI ICDR Cleared</div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon">📑</div>
            <div className="stat-card-value" style={{ color: 'var(--accent-primary-light)' }}>
              {reportCount}
            </div>
            <div className="stat-card-label">Advisory Reports</div>
          </div>
        </div>

        {/* Filter & Controls */}
        <div className="card" style={{ marginBottom: 24, padding: '16px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 240 }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search by company name, sector..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div style={{ width: 220 }}>
              <select
                className="form-select"
                value={filterTrack}
                onChange={(e) => setFilterTrack(e.target.value)}
              >
                <option value="ALL">All Tracks</option>
                <option value="REG_6_1">Reg 6(1) Profitability Route</option>
                <option value="REG_6_2">Reg 6(2) QIB Route</option>
              </select>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadData} title="Refresh">
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Company Cards List */}
        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <span>Loading company assessments...</span>
          </div>
        ) : filteredCompanies.length === 0 ? (
          <div className="card empty-state">
            <div className="empty-state-icon">📋</div>
            <div className="empty-state-title">
              {companies.length === 0 ? 'No Company Assessments Yet' : 'No Companies Matching Filters'}
            </div>
            <div className="empty-state-text">
              {companies.length === 0
                ? 'Create a new assessment to evaluate SEBI ICDR 2018 eligibility, upload documents, and generate IPO readiness reports.'
                : 'Try adjusting your search criteria or clear the filters.'}
            </div>
            {companies.length === 0 && (
              <Link to="/new" className="btn btn-primary">
                ➕ Start First Assessment
              </Link>
            )}
          </div>
        ) : (
          <div className="grid-2">
            {filteredCompanies.map((company) => {
              const score = company.readiness_score != null ? Math.round(company.readiness_score) : null;
              const trackLabel = company.target_track === 'REG_6_2'
                ? 'Reg 6(2) — QIB Route'
                : 'Reg 6(1) — Profitability Route';

              return (
                <div
                  key={company.id}
                  className="card"
                  style={{
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                  onClick={() => navigate(`/company/${company.id}`)}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                      <div>
                        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                          {company.name}
                        </div>
                        <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>
                          {company.sector || 'General Sector'} {company.incorporation_year ? `• Est. ${company.incorporation_year}` : ''}
                        </div>
                      </div>
                      <div>
                        {getEligibilityBadge(company.eligibility_status)}
                      </div>
                    </div>

                    <p style={{
                      fontSize: 13,
                      color: 'var(--text-secondary)',
                      lineHeight: 1.5,
                      marginBottom: 16,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}>
                      {company.description || 'No description provided.'}
                    </p>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontSize: 12,
                      color: 'var(--text-tertiary)',
                      background: 'var(--bg-tertiary)',
                      padding: '6px 12px',
                      borderRadius: 'var(--radius-sm)',
                      marginBottom: 16,
                    }}>
                      <span>🎯 Track:</span>
                      <strong style={{ color: 'var(--accent-primary-light)' }}>{trackLabel}</strong>
                    </div>

                    {/* Readiness Score bar */}
                    <div style={{ marginBottom: 16 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>IPO Readiness Score</span>
                        <strong style={{ color: getScoreColor(score) }}>
                          {score != null ? `${score}%` : 'Not Scored'}
                        </strong>
                      </div>
                      <div style={{
                        height: 6,
                        background: 'var(--bg-tertiary)',
                        borderRadius: 'var(--radius-full)',
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${score || 0}%`,
                          background: score >= 75
                            ? 'var(--success)'
                            : score >= 50
                            ? 'var(--warning)'
                            : 'var(--accent-primary)',
                          transition: 'width 0.6s ease',
                        }} />
                      </div>
                    </div>
                  </div>

                  {/* Card Footer Actions */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: 12,
                    borderTop: '1px solid var(--border-subtle)',
                  }}>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      Updated: {new Date(company.updated_at || company.created_at).toLocaleDateString()}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/company/${company.id}`);
                        }}
                      >
                        Open Workspace →
                      </button>
                      <button
                        className="btn btn-danger btn-sm btn-icon"
                        title="Delete Company"
                        onClick={(e) => handleDelete(company.id, company.name, e)}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
