import { useState } from 'react';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import AppShell from './components/AppShell.jsx';
import AuthPage from './pages/AuthPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import ScanPage from './pages/ScanPage.jsx';
import PlantsPage from './pages/PlantsPage.jsx';
import MarketplacePage from './pages/MarketplacePage.jsx';
import LabReportsPage from './pages/LabReportsPage.jsx';
import DoctorsPage from './pages/DoctorsPage.jsx';
import LearningPage from './pages/LearningPage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';
import AdminUsersPage from './pages/AdminUsersPage.jsx';
import GISMapPage from './pages/GISMapPage.jsx';
import WorkspaceModulePage from './pages/WorkspaceModulePage.jsx';
import { getToken } from './api/client.js';
import { signIn, signOut, signUp } from './api/auth.js';

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(getToken()));
  const [authError, setAuthError] = useState('');
  const navigate = useNavigate();

  async function submitAuth(mode, form) {
    setAuthError('');
    try {
      if (mode === 'login') await signIn(form.email, form.password);
      else await signUp(form);
      setAuthenticated(true);
      navigate('/');
    } catch (error) {
      setAuthError(error.message);
      throw error;
    }
  }

  function handleSignOut() {
    signOut();
    setAuthenticated(false);
    navigate('/');
  }

  if (!authenticated) return <AuthPage onSubmit={submitAuth} error={authError} />;

  return (
    <Routes>
      <Route element={<AppShell onSignOut={handleSignOut} />}>
        <Route index element={<DashboardPage />} />
        <Route path="scan" element={<ScanPage />} />
        <Route path="plants" element={<PlantsPage />} />
        <Route path="marketplace" element={<MarketplacePage />} />
        <Route path="lab-reports" element={<LabReportsPage />} />
        <Route path="doctors" element={<DoctorsPage />} />
        <Route path="learning" element={<LearningPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="gis-map" element={<GISMapPage />} />
        <Route path="admin/users" element={<AdminUsersPage />} />
        <Route path="workspace/:moduleKey" element={<WorkspaceModulePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
