import { useState, useEffect } from 'react';
import Header from '../components/Header';
import { getSebiRules } from '../api';

export default function RulesLibrary() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [trackFilter, setTrackFilter] = useState('ALL');

  useEffect(() => {
    async function loadRules() {
      try {
        setLoading(true);
        const data = await getSebiRules();
        setRules(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch SEBI rules');
      } finally {
        setLoading(false);
      }
    }
    loadRules();
  }, []);

  const filteredRules = rules.filter((rule) => {
    const matchesSearch =
      rule.title?.toLowerCase().includes(search.toLowerCase()) ||
      rule.regulation_ref?.toLowerCase().includes(search.toLowerCase()) ||
      rule.description?.toLowerCase().includes(search.toLowerCase()) ||
      rule.rule_code?.toLowerCase().includes(search.toLowerCase());

    const matchesCategory = categoryFilter === 'ALL' || rule.category === categoryFilter;
    const matchesTrack =
      trackFilter === 'ALL' ||
      rule.applicable_track === 'BOTH' ||
      rule.applicable_track === trackFilter;

    return matchesSearch && matchesCategory && matchesTrack;
  });

  const categories = ['ALL', 'ELIGIBILITY', 'PROMOTER', 'GOVERNANCE', 'DISCLOSURE', 'ALLOTMENT'];

  return (
    <div>
      <Header
        title="SEBI ICDR Regulations 2018 Library"
        subtitle="Permanent compliance rulebook and statutory criteria for Mainboard Initial Public Offerings"
      />

      <div className="page-container">
        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 24 }}>
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Top Filter Bar */}
        <div className="card" style={{ marginBottom: 24, padding: '16px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 260 }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search regulations (e.g. Reg 6(1), promoter lock-in, tangible assets)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div style={{ width: 180 }}>
              <select
                className="form-select"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="ALL">All Categories</option>
                <option value="ELIGIBILITY">Eligibility</option>
                <option value="PROMOTER">Promoter & Group</option>
                <option value="GOVERNANCE">Governance & Board</option>
                <option value="DISCLOSURE">Disclosure & Legal</option>
                <option value="ALLOTMENT">Allotment & QIB</option>
              </select>
            </div>
            <div style={{ width: 220 }}>
              <select
                className="form-select"
                value={trackFilter}
                onChange={(e) => setTrackFilter(e.target.value)}
              >
                <option value="ALL">All Tracks</option>
                <option value="REG_6_1">Reg 6(1) Profitability</option>
                <option value="REG_6_2">Reg 6(2) QIB Route</option>
                <option value="BOTH">Universal (Both)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stats on Rules */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Showing <strong>{filteredRules.length}</strong> of <strong>{rules.length}</strong> statutory rules
          </div>
        </div>

        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <span>Loading SEBI ICDR 2018 rule database...</span>
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="card empty-state">
            <div className="empty-state-icon">📜</div>
            <div className="empty-state-title">No Rules Match Query</div>
            <div className="empty-state-text">Try modifying your search or filter options.</div>
          </div>
        ) : (
          <div>
            {filteredRules.map((rule) => (
              <div key={rule.id || rule.rule_code} className="rule-card">
                <div className="rule-card-header">
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <span className="rule-card-title">{rule.title}</span>
                      <span className="badge badge-info" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                        {rule.regulation_ref}
                      </span>
                    </div>
                    <div className="rule-card-regulation">
                      Code: {rule.rule_code} • Track: {rule.applicable_track}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <span className={`badge ${rule.is_mandatory ? 'badge-danger' : 'badge-warning'}`}>
                      {rule.is_mandatory ? 'Mandatory' : 'Optional / Advisory'}
                    </span>
                    <span className="badge badge-draft">
                      {rule.rule_type === 'QUANTITATIVE' ? '📊 Quantitative' : '📝 Qualitative'}
                    </span>
                  </div>
                </div>

                <div className="rule-card-description">
                  {rule.description}
                </div>

                {rule.threshold_criteria && (
                  <div style={{
                    marginTop: 12,
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 14px',
                    fontSize: 12,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--accent-primary-light)',
                  }}>
                    <span>📏 Statutory Threshold:</span>
                    <span>{typeof rule.threshold_criteria === 'object' ? JSON.stringify(rule.threshold_criteria) : rule.threshold_criteria}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
