import { useEffect, useState } from 'react';
import { ShieldCheck, Save, RefreshCw, Users } from 'lucide-react';
import { apiRequest, getSavedUser } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';

const roles = ['farmer', 'gardener', 'vendor', 'doctor', 'plant_pathologist', 'nursery_manager', 'agricultural_extension_officer', 'forest_officer', 'research_scientist', 'delivery_partner', 'agronomist', 'student', 'administrator'];

export default function AdminUsersPage() {
  const currentUser = getSavedUser();
  const [users, setUsers] = useState([]);
  const [changes, setChanges] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  async function refresh() {
    setLoading(true); setError('');
    try { setUsers(await apiRequest('/admin/users')); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, []);
  function changeUser(user, patch) {
    setChanges((current) => ({ ...current, [user.id]: { role: user.role, is_active: user.is_active, ...current[user.id], ...patch } }));
  }
  async function saveUser(user) {
    const update = changes[user.id] || { role: user.role, is_active: user.is_active };
    setError(''); setSuccess('');
    try {
      await apiRequest(`/admin/users/${user.id}`, { method: 'PATCH', body: JSON.stringify(update) });
      setSuccess(`Updated permissions for ${user.email}.`);
      setChanges((current) => { const next = { ...current }; delete next[user.id]; return next; });
      await refresh();
    } catch (requestError) { setError(requestError.message); }
  }
  if (currentUser?.role !== 'administrator') return <Notice type="error">Administrator permission is required. The first administrator is created through the backend command-line utility.</Notice>;
  return <div className="page-stack"><div className="page-intro page-intro-row"><div><span className="eyebrow">ACCESS CONTROL</span><h2>User & role management</h2><p>Review registered accounts, update roles and suspend or reactivate access. New users cannot self-register as administrators.</p></div><button className="button button--secondary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div>{error&&<Notice type="error">{error}</Notice>}{success&&<Notice type="success">{success}</Notice>}<section className="panel"><div className="panel-heading"><div className="panel-icon tone-mint"><Users size={19}/></div><div><h3>Registered accounts</h3><p>{users.length} accounts returned by the database</p></div></div>{loading?<div className="loading-panel">Loading accounts…</div>:users.length?<div className="data-table-wrap"><table className="data-table"><thead><tr><th>Name / email</th><th>Role</th><th>Status</th><th>Joined</th><th>Save</th></tr></thead><tbody>{users.map((user)=><tr key={user.id}><td><b>{user.full_name}</b><br/><span>{user.email}</span></td><td><select value={(changes[user.id]||user).role} onChange={(event)=>changeUser(user,{role:event.target.value})}>{roles.map((role)=><option value={role} key={role}>{role.replaceAll('_',' ')}</option>)}</select></td><td><select value={String((changes[user.id]||user).is_active)} onChange={(event)=>changeUser(user,{is_active:event.target.value==='true'})}><option value="true">Active</option><option value="false">Suspended</option></select></td><td>{new Date(user.created_at).toLocaleDateString()}</td><td><button className="button button--secondary" disabled={!changes[user.id]} onClick={()=>saveUser(user)}><Save size={13}/> Save</button></td></tr>)}</tbody></table></div>:<EmptyState title="No accounts found" description="Registered TreeRasa accounts will appear here."/>}</section><p className="disclaimer-line"><ShieldCheck size={14}/> Assign only the permissions needed for a person's work. Administrator access should be limited to trusted maintainers.</p></div>;
}
