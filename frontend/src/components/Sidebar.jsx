import { NavLink } from 'react-router-dom';
import {
  Activity, Sprout, ScanLine, ShoppingBag, FlaskConical, Stethoscope, BookOpen,
  Leaf, CircleHelp, Tractor, Bug, CloudSun, Plane, MapPin, Layers, CalendarDays,
  Flower2, Lightbulb, Globe2, ClipboardList, Bell, Settings, GraduationCap,
  BarChart3, ShieldCheck,
} from 'lucide-react';
import Brand from './Brand.jsx';
import { getSavedUser } from '../api/client.js';

// Keep navigation labels and destinations in one place so the team can extend the app easily.
const groups = [
  {
    label: 'CORE WORKSPACE',
    links: [
      { to: '/', label: 'Overview', icon: Activity },
      { to: '/scan', label: 'Plant health AI scan', icon: ScanLine },
      { to: '/plants', label: 'Plant repository', icon: Sprout },
      { to: '/marketplace', label: 'Care marketplace', icon: ShoppingBag },
      { to: '/lab-reports', label: 'Lab reports', icon: FlaskConical },
      { to: '/doctors', label: 'Plant doctors', icon: Stethoscope },
      { to: '/learning', label: 'Learning centre', icon: BookOpen },
      { to: '/analytics', label: 'Analytics dashboard', icon: BarChart3 },
    ],
  },
  {
    label: 'FIELD OPERATIONS',
    links: [
      { to: '/workspace/farms', label: 'Farms & fields', icon: Tractor },
      { to: '/workspace/nurseries', label: 'Nursery management', icon: Sprout },
      { to: '/workspace/pest-lifecycle', label: 'Pest lifecycle', icon: Bug },
      { to: '/workspace/environment', label: 'Environment & sensors', icon: CloudSun },
      { to: '/workspace/drone-surveys', label: 'Drone surveys', icon: Plane },
      { to: '/gis-map', label: 'GIS observation map', icon: MapPin },
      { to: '/workspace/gis-observations', label: 'Manage GIS records', icon: Layers },
      { to: '/workspace/soil-analyses', label: 'Soil health records', icon: Layers },
      { to: '/workspace/crop-plans', label: 'Crop protection planner', icon: CalendarDays },
    ],
  },
  {
    label: 'INSIGHTS & IMPACT',
    links: [
      { to: '/workspace/explainability', label: 'AI explainability notes', icon: ScanLine },
      { to: '/workspace/biodiversity', label: 'Biodiversity monitoring', icon: Flower2 },
      { to: '/workspace/recommendations', label: 'Recommendations', icon: Lightbulb },
      { to: '/workspace/sdg15', label: 'SDG 15 tracker', icon: Globe2 },
      { to: '/workspace/learning-progress', label: 'Learning progress', icon: GraduationCap },
      { to: '/workspace/reports', label: 'Reports register', icon: BarChart3 },
    ],
  },
  {
    label: 'ACCOUNT & SYSTEM',
    links: [
      { to: '/workspace/notifications', label: 'Notifications', icon: Bell },
      { to: '/workspace/audit-logs', label: 'Audit logs', icon: ShieldCheck },
      { to: '/workspace/settings', label: 'Workspace settings', icon: Settings },
    ],
  },
];

export default function Sidebar() {
  const user = getSavedUser();
  const adminLinks = user?.role === 'administrator' ? [{ to: '/admin/users', label: 'User & role management', icon: ShieldCheck }] : [];
  return (
    <aside className="sidebar">
      <div className="sidebar-brand"><Brand /></div>
      <div className="workspace-chip"><span><Leaf size={16} /></span><div><b>My growing space</b><small>Personal workspace</small></div></div>
      <nav>
        {groups.map((group) => (
          <section className="nav-group" key={group.label}>
            <p>{group.label}</p>
            {group.links.map(({ to, label, icon: Icon }) => (
              <NavLink end={to === '/'} to={to} key={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <Icon size={17} /><span>{label}</span>
              </NavLink>
            ))}
          </section>
        ))}
        {adminLinks.length > 0 && <section className="nav-group"><p>ADMINISTRATION</p>{adminLinks.map(({ to, label, icon: Icon }) => <NavLink to={to} key={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><Icon size={17}/><span>{label}</span></NavLink>)}</section>}
      </nav>
    <div className="sidebar-bottom">
        <div className="sdg-card"><Leaf size={20} /><div><b>Growing a greener future</b><small>Small actions. Living ecosystems.</small></div></div>
        <a className="nav-link" href="https://sdgs.un.org/goals/goal15" target="_blank" rel="noreferrer"><CircleHelp size={17} />About SDG 15</a>
        <small className="sidebar-foot">● Records are loaded from your account</small>
      </div>
    </aside>
  );
}
