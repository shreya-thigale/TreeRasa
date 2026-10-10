import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, RefreshCw, Plus } from 'lucide-react';
import { apiRequest } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';
import 'leaflet/dist/leaflet.css';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Vite serves Leaflet's marker assets from its package rather than assuming public folder paths.
L.Icon.Default.mergeOptions({ iconRetinaUrl: markerIcon2x, iconUrl: markerIcon, shadowUrl: markerShadow });

export default function GISMapPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function refresh() {
    setLoading(true); setError('');
    try { setRecords(await apiRequest('/workspace/gis-observations/records')); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, []);
  const mappedRecords = records.filter((record) => {
    const latitude = Number(record.data?.latitude);
    const longitude = Number(record.data?.longitude);
    return Number.isFinite(latitude) && Number.isFinite(longitude) && latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180;
  });
  const center = mappedRecords.length ? [Number(mappedRecords[0].data.latitude), Number(mappedRecords[0].data.longitude)] : [20.5937, 78.9629];

  return <div className="page-stack">
    <div className="page-intro page-intro-row"><div><span className="eyebrow">GEOSPATIAL OBSERVATIONS</span><h2>Field observations map</h2><p>Map markers are generated only from coordinates saved in your own GIS observation records. No sample hotspots are fabricated.</p></div><div className="toolbar-actions"><button className="button button--secondary" onClick={refresh}><RefreshCw size={14}/> Refresh</button><Link className="button button--primary" to="/workspace/gis-observations"><Plus size={15}/> Add observation</Link></div></div>
    {error && <Notice type="error">{error}</Notice>}
    <section className="panel"><div className="panel-heading"><div className="panel-icon tone-mint"><MapPin size={19}/></div><div><h3>Saved field locations</h3><p>{mappedRecords.length} of {records.length} observations have usable coordinates</p></div></div>
      {loading ? <div className="loading-panel">Loading geospatial records…</div> : <div className="gis-map"><MapContainer center={center} zoom={mappedRecords.length ? 10 : 4} scrollWheelZoom style={{ height: '470px', width: '100%' }} key={`${center[0]}-${center[1]}`}><TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />{mappedRecords.map((record) => <Marker key={record.id} position={[Number(record.data.latitude), Number(record.data.longitude)]}><Popup><b>{record.title}</b><br/>{record.data.observation_type || 'Field observation'}<br/>{record.data.severity || 'Severity not recorded'}<br/>Record #{record.id}</Popup></Marker>)}</MapContainer></div>}
      {!loading && !mappedRecords.length && <div className="map-empty-note"><EmptyState title="No mapped observations yet" description="Create a GIS observation and enter a valid latitude and longitude. The map will place a marker from that saved record." action={<Link className="button button--primary" to="/workspace/gis-observations"><Plus size={15}/> Add coordinates</Link>}/></div>}
    </section>
    {mappedRecords.length > 0 && <section className="panel"><div className="section-heading"><div><span className="eyebrow">MAPPED RECORDS</span><h2>Observation list</h2></div></div><div className="report-list">{mappedRecords.map((record)=><article className="report-row" key={record.id}><div className="report-file-icon"><MapPin size={18}/></div><div className="report-info"><b>{record.title}</b><span>{record.data.observation_type || 'Field observation'} · {record.data.severity || 'Severity not recorded'}</span><small>{record.data.latitude}, {record.data.longitude}</small></div></article>)}</div></section>}
    <p className="disclaimer-line">Map tiles are served by OpenStreetMap. Sensor feeds, remote-sensing layers, protected-area overlays and automated hotspot detection are not connected yet.</p>
  </div>;
}
