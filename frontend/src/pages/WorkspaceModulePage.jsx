import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ClipboardList, Edit3, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';
import { apiRequest, downloadApiFile, getSavedUser } from '../api/client.js';
import EmptyState from '../components/EmptyState.jsx';
import Notice from '../components/Notice.jsx';

/**
 * Shared CRUD screen for operational modules whose record fields are defined by the API.
 * Keeping one reusable form makes it easier for a beginner team to add or change modules.
 */
export default function WorkspaceModulePage() {
  const { moduleKey } = useParams();
  const user = getSavedUser();
  const [moduleInfo, setModuleInfo] = useState(null);
  const [records, setRecords] = useState([]);
  const [query, setQuery] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');
  const [values, setValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [exportFormat, setExportFormat] = useState('csv');

  const isReadOnly = moduleKey === 'audit-logs';
  const filteredRecords = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return records;
    return records.filter((record) => `${record.title} ${record.notes || ''} ${JSON.stringify(record.data || {})}`.toLowerCase().includes(normalized));
  }, [records, query]);

  async function refresh() {
    setLoading(true);
    setError('');
    try {
      const modules = await apiRequest('/workspace/modules');
      const selected = modules.find((item) => item.key === moduleKey);
      if (!selected) throw new Error('This module is not available for your account role.');
      setModuleInfo(selected);
      setRecords(await apiRequest(`/workspace/${moduleKey}/records`));
    } catch (requestError) {
      setError(requestError.message);
      setModuleInfo(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setFormOpen(false);
    setEditingId(null);
    setQuery('');
    refresh();
  }, [moduleKey]);

  function resetForm() {
    setFormOpen(false);
    setEditingId(null);
    setTitle('');
    setNotes('');
    setValues({});
  }

  function beginEdit(record) {
    setEditingId(record.id);
    setTitle(record.title);
    setNotes(record.notes || '');
    setValues(record.data || {});
    setFormOpen(true);
    setSuccess('');
  }

  function beginCreate() {
    setEditingId(null);
    setTitle('');
    setNotes('');
    setValues({});
    setFormOpen(true);
    setSuccess('');
  }

  async function saveRecord(event) {
    event.preventDefault();
    if (!title.trim()) {
      setError('Please add a clear record title.');
      return;
    }
    setBusy(true);
    setError('');
    setSuccess('');
    const data = {};
    for (const field of moduleInfo.fields) {
      const value = values[field.name];
      if (value === '' || value === undefined || value === null) continue;
      data[field.name] = field.type === 'number' ? Number(value) : value;
    }
    try {
      const payload = { title: title.trim(), notes: notes.trim() || null, data };
      const path = editingId
        ? `/workspace/${moduleKey}/records/${editingId}`
        : `/workspace/${moduleKey}/records`;
      await apiRequest(path, { method: editingId ? 'PATCH' : 'POST', body: JSON.stringify(payload) });
      setSuccess(editingId ? 'Record updated and saved to your database.' : 'Record saved to your database.');
      resetForm();
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function exportRecords() {
    setError('');
    try { await downloadApiFile(`/workspace/${moduleKey}/export?format=${exportFormat}`, `treerasa_${moduleKey}.${exportFormat}`); }
    catch (requestError) { setError(requestError.message); }
  }

  async function deleteRecord(record) {
    if (!window.confirm(`Delete “${record.title}”? This cannot be undone.`)) return;
    setError('');
    setSuccess('');
    try {
      await apiRequest(`/workspace/${moduleKey}/records/${record.id}`, { method: 'DELETE' });
      setSuccess('Record deleted.');
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  if (loading && !moduleInfo) {
    return <div className="loading-panel">Loading module and database records…</div>;
  }

  return (
    <div className="page-stack">
      <section className="page-intro page-intro-row">
        <div>
          <span className="eyebrow">TREE RASA WORKSPACE</span>
          <h2>{moduleInfo?.title || 'Workspace module'}</h2>
          <p>{moduleInfo?.description || 'Records are loaded from the TreeRasa API.'}</p>
          <div className="module-meta"><span><ClipboardList size={13} /> {records.length} saved records</span><span>Account role: {user?.role?.replaceAll('_', ' ') || 'unknown'}</span><span>PostgreSQL-backed API</span></div>
        </div>
        {!isReadOnly && moduleInfo && <button className="button button--primary" onClick={formOpen ? resetForm : beginCreate}><Plus size={16} /> {formOpen ? 'Close form' : 'Add record'}</button>}
      </section>

      {error && <Notice type="error">{error}</Notice>}
      {success && <Notice type="success">{success}</Notice>}

      {formOpen && moduleInfo && (
        <form className="panel workspace-form" onSubmit={saveRecord}>
          <div className="panel-heading"><div className="panel-icon tone-mint"><Edit3 size={18} /></div><div><h3>{editingId ? 'Edit record' : 'Create a record'}</h3><p>Complete only the fields you know. The information is saved to your account database.</p></div></div>
          <label>Record title *<input required maxLength="180" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="A short, descriptive title" /></label>
          <div className="form-grid">
            {moduleInfo.fields.map((field) => (
              <label className={field.type === 'textarea' ? 'form-full' : ''} key={field.name}>
                {field.label}
                {field.type === 'textarea'
                  ? <textarea rows="3" value={values[field.name] ?? ''} onChange={(event) => setValues({ ...values, [field.name]: event.target.value })} />
                  : <input type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'} step={field.type === 'number' ? 'any' : undefined} value={values[field.name] ?? ''} onChange={(event) => setValues({ ...values, [field.name]: event.target.value })} />}
              </label>
            ))}
            <label className="form-full">Additional notes<textarea rows="2" maxLength="4000" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Optional context, source, or follow-up notes" /></label>
          </div>
          <div className="form-actions"><button type="button" className="button button--secondary" onClick={resetForm}>Cancel</button><button className="button button--primary" disabled={busy}>{busy ? 'Saving…' : editingId ? 'Save changes' : 'Save record'}</button></div>
        </form>
      )}

      <section className="panel">
        <div className="section-heading"><div><span className="eyebrow">SAVED IN YOUR ACCOUNT</span><h2>Records</h2><p>Only records returned by the backend are shown. New accounts start empty.</p></div><div className="toolbar-actions"><select aria-label="Export format" value={exportFormat} onChange={(event) => setExportFormat(event.target.value)}><option value="csv">CSV</option><option value="xlsx">Excel</option><option value="pdf">PDF</option></select><button className="button button--secondary" onClick={exportRecords}>Export</button><button className="button button--secondary" onClick={refresh}><RefreshCw size={14} /> Refresh</button></div></div>
        <div className="toolbar" style={{ margin: '18px 0 14px' }}><div className="toolbar-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search records" /></div><span className="subtle-count">{filteredRecords.length} shown</span></div>
        {loading ? <div className="loading-panel">Refreshing records…</div> : filteredRecords.length ? (
          <div className="record-list">
            {filteredRecords.map((record) => {
              const entries = Object.entries(record.data || {}).filter(([, value]) => value !== '' && value !== null && value !== undefined);
              return <article className="workspace-record" key={record.id}>
                <div className="panel-icon tone-mint"><ClipboardList size={17} /></div>
                <div className="workspace-record-main"><h4>{record.title}</h4>
                  {entries.length > 0 && <dl>{entries.slice(0, 8).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}</dl>}
                  {record.notes && <p className="plant-notes">{record.notes}</p>}
                  <div className="module-meta"><span>Record #{record.id}</span><span>Saved {record.created_at ? new Date(record.created_at).toLocaleString() : '—'}</span></div>
                </div>
                {!isReadOnly && <div className="record-actions"><button title="Edit record" onClick={() => beginEdit(record)}><Edit3 size={14} /></button><button title="Delete record" onClick={() => deleteRecord(record)}><Trash2 size={14} /></button></div>}
              </article>;
            })}
          </div>
        ) : <EmptyState title={query ? 'No matching records' : 'No records saved yet'} description={query ? 'Try another search term.' : 'Add your first record to start building a real TreeRasa dataset. Nothing is pre-filled with fictional farm data.'} action={!isReadOnly && <button className="button button--primary" onClick={beginCreate}><Plus size={15} /> Add first record</button>} />}
      </section>
    </div>
  );
}
