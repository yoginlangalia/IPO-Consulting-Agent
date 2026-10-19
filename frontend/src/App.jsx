import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import NewCompany from './pages/NewCompany';
import CompanyWorkspace from './pages/CompanyWorkspace';
import RulesLibrary from './pages/RulesLibrary';

export default function App() {
  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new" element={<NewCompany />} />
            <Route path="/company/:id" element={<CompanyWorkspace />} />
            <Route path="/rules" element={<RulesLibrary />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
