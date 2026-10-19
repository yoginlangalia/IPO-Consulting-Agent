import { NavLink, useLocation } from 'react-router-dom';

const navItems = [
  { section: 'Overview', items: [
    { path: '/', icon: '📊', label: 'Dashboard' },
  ]},
  { section: 'Assessment', items: [
    { path: '/new', icon: '➕', label: 'New Assessment' },
  ]},
  { section: 'Analysis', items: [
    { path: '/rules', icon: '📜', label: 'SEBI ICDR Rules' },
  ]},
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">IP</div>
        <div>
          <h1>IPO Readiness</h1>
          <span>Assessment Agent</span>
        </div>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.section}>
            <div className="sidebar-section-title">{section.section}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              >
                <span className="sidebar-link-icon">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
