export default function Header({ title, subtitle, children }) {
  return (
    <header className="header">
      <div>
        <div className="header-title">{title}</div>
        {subtitle && <div className="header-subtitle">{subtitle}</div>}
      </div>
      <div className="header-actions">
        {children}
      </div>
    </header>
  );
}
