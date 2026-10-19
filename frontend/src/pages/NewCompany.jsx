import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Header from '../components/Header';
import { createCompany } from '../api';

export default function NewCompany() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    sector: 'Technology & SaaS',
    incorporation_year: new Date().getFullYear() - 5,
    target_track: 'REG_6_1',
    target_ipo_date: 'FY 2025-26',
    description: '',
    net_tangible_assets: '',
    operating_profit: '',
    net_worth: '',
    pre_ipo_capital: '',
    proposed_issue_size: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Company name is required.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Clean payload
      const payload = {
        name: formData.name.trim(),
        sector: formData.sector,
        incorporation_year: formData.incorporation_year ? parseInt(formData.incorporation_year, 10) : null,
        target_track: formData.target_track,
        target_ipo_date: formData.target_ipo_date || null,
        description: formData.description || null,
        financial_data: {
          net_tangible_assets: formData.net_tangible_assets ? parseFloat(formData.net_tangible_assets) : null,
          operating_profit: formData.operating_profit ? parseFloat(formData.operating_profit) : null,
          net_worth: formData.net_worth ? parseFloat(formData.net_worth) : null,
          pre_ipo_capital: formData.pre_ipo_capital ? parseFloat(formData.pre_ipo_capital) : null,
          proposed_issue_size: formData.proposed_issue_size ? parseFloat(formData.proposed_issue_size) : null,
        },
      };

      const newCompany = await createCompany(payload);
      navigate(`/company/${newCompany.id}`);
    } catch (err) {
      setError(err.message || 'Failed to create company');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header
        title="Start New IPO Assessment"
        subtitle="Register the company entity and select the applicable SEBI ICDR 2018 route"
      >
        <Link to="/" className="btn btn-secondary btn-sm">
          ← Back to Dashboard
        </Link>
      </Header>

      <div className="page-container" style={{ maxWidth: 900 }}>
        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 24 }}>
            <span>⚠️ {error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Company Core Details */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Corporate Information</div>
                <div className="card-subtitle">Basic details required for SEBI compliance profiling</div>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label form-required">Company Legal Name</label>
              <input
                type="text"
                name="name"
                className="form-input"
                placeholder="e.g. Acme FinTech Technologies Limited"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label form-required">Sector / Industry</label>
                <select
                  name="sector"
                  className="form-select"
                  value={formData.sector}
                  onChange={handleChange}
                >
                  <option value="Technology & SaaS">Technology & SaaS</option>
                  <option value="Fintech & Payments">Fintech & Payments</option>
                  <option value="Manufacturing & Industrial">Manufacturing & Industrial</option>
                  <option value="Healthcare & Pharma">Healthcare & Pharma</option>
                  <option value="Consumer & Retail">Consumer & Retail</option>
                  <option value="Energy & Infrastructure">Energy & Infrastructure</option>
                  <option value="Banking & NBFC">Banking & NBFC</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Year of Incorporation</label>
                <input
                  type="number"
                  name="incorporation_year"
                  className="form-input"
                  min="1900"
                  max="2026"
                  value={formData.incorporation_year}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Target IPO Timeline</label>
                <input
                  type="text"
                  name="target_ipo_date"
                  className="form-input"
                  placeholder="e.g. Q4 FY25 or H1 2026"
                  value={formData.target_ipo_date}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Proposed Issue Size (₹ Crores)</label>
                <input
                  type="number"
                  step="any"
                  name="proposed_issue_size"
                  className="form-input"
                  placeholder="e.g. 500"
                  value={formData.proposed_issue_size}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Business Overview / Description</label>
              <textarea
                name="description"
                className="form-textarea"
                placeholder="Brief summary of business operations, principal revenue streams, and market position..."
                value={formData.description}
                onChange={handleChange}
                rows={3}
              />
            </div>
          </div>

          {/* SEBI ICDR Track Selection */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Target SEBI ICDR 2018 Track</div>
                <div className="card-subtitle">Choose the intended route under SEBI ICDR Regulations</div>
              </div>
            </div>

            <div className="grid-2" style={{ marginBottom: 16 }}>
              {/* Track 1: Reg 6(1) */}
              <div
                onClick={() => setFormData((prev) => ({ ...prev, target_track: 'REG_6_1' }))}
                style={{
                  border: formData.target_track === 'REG_6_1' ? '2px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                  background: formData.target_track === 'REG_6_1' ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  padding: 20,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <input
                    type="radio"
                    name="target_track"
                    value="REG_6_1"
                    checked={formData.target_track === 'REG_6_1'}
                    onChange={handleChange}
                  />
                  <strong style={{ fontSize: 15, color: 'var(--text-primary)' }}>
                    Regulation 6(1) — Profitability Route
                  </strong>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  The standard track for companies with a consistent track record of profits:
                </p>
                <ul style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8, paddingLeft: 18, lineHeight: 1.6 }}>
                  <li>Net Tangible Assets ≥ ₹3 Cr in each of preceding 3 years</li>
                  <li>Average Operating Profit ≥ ₹15 Cr in at least 3 of preceding 5 years</li>
                  <li>Net Worth ≥ ₹1 Cr in each of preceding 3 years</li>
                </ul>
              </div>

              {/* Track 2: Reg 6(2) */}
              <div
                onClick={() => setFormData((prev) => ({ ...prev, target_track: 'REG_6_2' }))}
                style={{
                  border: formData.target_track === 'REG_6_2' ? '2px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                  background: formData.target_track === 'REG_6_2' ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  padding: 20,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <input
                    type="radio"
                    name="target_track"
                    value="REG_6_2"
                    checked={formData.target_track === 'REG_6_2'}
                    onChange={handleChange}
                  />
                  <strong style={{ fontSize: 15, color: 'var(--text-primary)' }}>
                    Regulation 6(2) — QIB / Alternative Route
                  </strong>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Alternative track for high-growth tech / pre-profit companies unable to satisfy Reg 6(1):
                </p>
                <ul style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8, paddingLeft: 18, lineHeight: 1.6 }}>
                  <li>Issue must be made through 100% Book Building Process</li>
                  <li>At least <strong>75%</strong> of the net offer must be allotted to Qualified Institutional Buyers (QIBs)</li>
                  <li>Non-QIB retail quota capped at 10% & NII at 15%</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Optional Pre-fill Financials */}
          <div className="card" style={{ marginBottom: 32 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Initial Financial Metrics (Optional)</div>
                <div className="card-subtitle">
                  You can enter known values now or upload P&L / Balance Sheet documents later for AI extraction
                </div>
              </div>
            </div>

            <div className="grid-3">
              <div className="form-group">
                <label className="form-label">Net Tangible Assets (₹ Cr)</label>
                <input
                  type="number"
                  step="any"
                  name="net_tangible_assets"
                  className="form-input"
                  placeholder="e.g. 25.5"
                  value={formData.net_tangible_assets}
                  onChange={handleChange}
                />
                <div className="form-hint">Reg 6(1) min: ₹3 Cr each yr</div>
              </div>

              <div className="form-group">
                <label className="form-label">Average Operating Profit (₹ Cr)</label>
                <input
                  type="number"
                  step="any"
                  name="operating_profit"
                  className="form-input"
                  placeholder="e.g. 18.2"
                  value={formData.operating_profit}
                  onChange={handleChange}
                />
                <div className="form-hint">Reg 6(1) min: ₹15 Cr in 3 of 5 yrs</div>
              </div>

              <div className="form-group">
                <label className="form-label">Net Worth (₹ Cr)</label>
                <input
                  type="number"
                  step="any"
                  name="net_worth"
                  className="form-input"
                  placeholder="e.g. 45.0"
                  value={formData.net_worth}
                  onChange={handleChange}
                />
                <div className="form-hint">Reg 6(1) min: ₹1 Cr each yr</div>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 16 }}>
            <Link to="/" className="btn btn-secondary">
              Cancel
            </Link>
            <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
              {loading ? 'Creating Assessment...' : 'Create Assessment & Open Workspace →'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
