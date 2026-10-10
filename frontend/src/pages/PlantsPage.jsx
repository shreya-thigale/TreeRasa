import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, MapPin, Plus, Search, Sprout, Trash2 } from 'lucide-react';
import { apiRequest } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';

const emptyForm = { name: '', species: '', crop_type: '', location: '', notes: '' };

export default function PlantsPage() {
  const [plants, setPlants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [query, setQuery] = useState('');
  const [form, setForm] = useState(emptyForm);

  async function refresh() {
    setLoading(true);
    try { setPlants(await apiRequest('/plants')); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }

  useEffect(() => { refresh(); }, []);

  async function savePlant(event) {
    event.preventDefault();
    setError('');
    try {
      await apiRequest('/plants', { method: 'POST', body: JSON.stringify(form) });
      setForm(emptyForm);
      setShowForm(false);
      await refresh();
    } catch (requestError) { setError(requestError.message); }
  }

  async function deletePlant(plantId) {
    if (!window.confirm('Delete this plant record?')) return;
    try {
      await apiRequest(`/plants/${plantId}`, { method: 'DELETE' });
      await refresh();
    } catch (requestError) { setError(requestError.message); }
  }

  const filteredPlants = useMemo(() => plants.filter((plant) =>
    [plant.name, plant.species, plant.crop_type, plant.location].join(' ').toLowerCase().includes(query.toLowerCase())), [plants, query]);

  return (
    <div className="page-stack">
      <div className="page-intro page-intro-row"><div><span className="eyebrow">YOUR GROWING SPACE</span><h2>My plant library</h2><p>Keep plant records in one place and link future scans to a plant you care for.</p></div><button className="button button--primary" onClick={() => setShowForm((open) => !open)}><Plus size={17} /> Add a plant</button></div>
      {error && <Notice type="error">{error}</Notice>}

      {showForm && <form className="panel" onSubmit={savePlant}>
        <div className="panel-heading"><div className="panel-icon tone-mint"><Sprout size={19} /></div><div><h3>Add plant record</h3><p>Start with what you know; you can add more details later.</p></div></div>
        <div className="form-grid">
          <label>Plant name *<input required maxLength="120" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="e.g. Balcony tomato" /></label>
          <label>Scientific name<input value={form.species} onChange={(event) => setForm({ ...form, species: event.target.value })} placeholder="e.g. Solanum lycopersicum" /></label>
          <label>Crop / plant type<input value={form.crop_type} onChange={(event) => setForm({ ...form, crop_type: event.target.value })} placeholder="e.g. Vegetable" /></label>
          <label>Location<input value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} placeholder="e.g. Terrace garden" /></label>
          <label className="form-full">Notes<textarea rows="2" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Variety, planting date, observations…" /></label>
        </div>
        <div className="form-actions"><button type="button" className="button button--secondary" onClick={() => setShowForm(false)}>Cancel</button><button className="button button--primary">Save plant record</button></div>
      </form>}

      <div className="toolbar"><div className="toolbar-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your plants" /></div><span className="subtle-count">{plants.length} saved {plants.length === 1 ? 'plant' : 'plants'}</span></div>
      {loading ? <div className="loading-panel">Loading your plant records…</div> : filteredPlants.length ? <div className="plant-grid">
        {filteredPlants.map((plant, index) => <article className="plant-card" key={plant.id}>
          <div className={`plant-art plant-art-${index % 4}`}><Sprout size={34} /><span>PLANT {String(plant.id).padStart(3, '0')}</span></div>
          <div className="plant-card-body"><div className="plant-card-title"><h3>{plant.name}</h3><button className="icon-button danger-icon" title="Delete plant" onClick={() => deletePlant(plant.id)}><Trash2 size={16} /></button></div>
            <p className="scientific-name">{plant.species || 'Scientific name not added'}</p>
            <div className="plant-meta">{plant.crop_type && <span><Sprout size={14} />{plant.crop_type}</span>}{plant.location && <span><MapPin size={14} />{plant.location}</span>}<span><CalendarDays size={14} />Added {new Date(plant.created_at).toLocaleDateString()}</span></div>
            {plant.notes && <p className="plant-notes">{plant.notes}</p>}
          </div>
        </article>)}
      </div> : <EmptyState title={query ? 'No matching plants' : 'Your plant library is ready to grow'} description={query ? 'Try a different search.' : 'Add your first plant to keep records and link future image scans.'} action={!query && <button className="button button--primary" onClick={() => setShowForm(true)}><Plus size={16} /> Add your first plant</button>} />}
    </div>
  );
}
