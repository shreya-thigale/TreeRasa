import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Bell, Moon, Sun, LogOut, Menu } from 'lucide-react';
import Sidebar from './Sidebar.jsx';
import { getSavedUser } from '../api/client.js';

const titles = {
  '/': 'A healthier way to grow',
  '/scan': 'Plant health analysis',
  '/plants': 'My plant library',
  '/marketplace': 'Sustainable care marketplace',
  '/lab-reports': 'Lab reports',
  '/doctors': 'Connect with plant experts',
  '/learning': 'Learn, grow, protect',
  '/analytics': 'Plant health analytics',
  '/gis-map': 'GIS observation map',
  '/admin/users': 'User & role management',
  '/workspace/farms': 'Farm & field management',
  '/workspace/nurseries': 'Nursery management',
  '/workspace/pest-lifecycle': 'Pest lifecycle intelligence',
  '/workspace/environment': 'Environmental monitoring',
  '/workspace/drone-surveys': 'Drone surveillance',
  '/workspace/gis-observations': 'GIS pest distribution',
  '/workspace/soil-analyses': 'Soil health records',
  '/workspace/crop-plans': 'Crop protection planner',
  '/workspace/explainability': 'AI explainability',
  '/workspace/biodiversity': 'Biodiversity monitoring',
  '/workspace/recommendations': 'AI recommendation centre',
  '/workspace/sdg15': 'SDG 15 sustainability tracker',
  '/workspace/learning-progress': 'Learning progress',
  '/workspace/reports': 'Reports register',
  '/workspace/notifications': 'Notification centre',
  '/workspace/audit-logs': 'Audit logs',
  '/workspace/settings': 'Workspace settings',
};

export default function AppShell({ onSignOut }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const location = useLocation();
  const user = getSavedUser();

  function toggleTheme() {
    setDark((wasDark) => !wasDark);
    document.documentElement.dataset.theme = dark ? 'light' : 'dark';
  }

  return (
    <div className="app-shell">
      <div className={`sidebar-wrap ${menuOpen ? 'sidebar-wrap--open' : ''}`}><Sidebar /></div>
      {menuOpen && <button className="mobile-overlay" onClick={() => setMenuOpen(false)} aria-label="Close menu" />}
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open menu"><Menu size={19} /></button>
          <div><span className="eyebrow">TREE RASA WORKSPACE</span><h1>{titles[location.pathname] || 'TreeRasa workspace'}</h1></div>
          <div className="topbar-actions">
            <button className="icon-button" onClick={toggleTheme} title="Toggle theme">{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
            <Link className="icon-button" title="Notifications" to="/workspace/notifications"><Bell size={18} /></Link>
            <div className="user-chip"><span>{(user?.full_name || 'TR').split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()}</span><div><b>{user?.full_name || 'Guest'}</b><small>{(user?.role || 'visitor').replaceAll('_', ' ')}</small></div></div>
            <button className="icon-button signout" onClick={onSignOut} title="Sign out"><LogOut size={16} /></button>
          </div>
        </header>
        <div className="page-content"><Outlet /></div>
        <footer className="app-footer"><span>© TreeRasa · Plant health, naturally</span><span>Built for sustainable growing ✳</span></footer>
      </main>
    </div>
  );
}
