import { useEffect, useState } from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Tooltip, Legend, Filler,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { Activity, BarChart3, CheckCircle2, RefreshCw, ScanLine, ShieldAlert } from 'lucide-react';
import { apiRequest } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Tooltip, Legend, Filler);

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0 } } },
};

function EmptyChart({ description }) {
  return <EmptyState title="Not enough records to chart" description={description} />;
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setError('');
    try { setAnalytics(await apiRequest('/dashboard/analytics')); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }

  useEffect(() => { refresh(); }, []);

  const dailyChart = analytics ? {
    labels: analytics.scans_by_day.map((item) => item.date.slice(5)),
    datasets: [{ label: 'Saved scans', data: analytics.scans_by_day.map((item) => item.count), backgroundColor: '#78a981', borderRadius: 5 }],
  } : null;
  const classChart = analytics ? {
    labels: analytics.class_distribution.map((item) => item.label.replaceAll('___', ' · ').replaceAll('_', ' ')),
    datasets: [{ label: 'Scans', data: analytics.class_distribution.map((item) => item.count), backgroundColor: '#8a83bb', borderRadius: 5 }],
  } : null;
  const statusChart = analytics ? {
    labels: analytics.status_distribution.map((item) => item.label.replaceAll('_', ' ')),
    datasets: [{ label: 'Scans', data: analytics.status_distribution.map((item) => item.count), backgroundColor: '#d8a16c', borderRadius: 5 }],
  } : null;

  return (
    <div className="page-stack">
      <div className="page-intro page-intro-row"><div><span className="eyebrow">MEASURE WHAT YOU RECORD</span><h2>Plant health analytics</h2><p>Charts are calculated from your actual saved scan records. TreeRasa does not invent historical detections or accuracy scores.</p></div><button className="button button--secondary" onClick={refresh}><RefreshCw size={14} /> Refresh analytics</button></div>
      {error && <Notice type="error">{error}</Notice>}
      {loading ? <div className="loading-panel">Calculating analytics from your account…</div> : analytics && <>
        <div className="metric-grid">
          <article className="metric-card"><div className="metric-icon tone-mint"><ScanLine size={19} /></div><div className="metric-value">{analytics.total_scans}</div><div className="metric-label">Saved plant scans</div></article>
          <article className="metric-card"><div className="metric-icon tone-blue"><CheckCircle2 size={19} /></div><div className="metric-value">{analytics.predicted_scans}</div><div className="metric-label">Model predictions saved</div></article>
          <article className="metric-card"><div className="metric-icon tone-peach"><ShieldAlert size={19} /></div><div className="metric-value">{analytics.needs_review}</div><div className="metric-label">Scans requiring review</div></article>
          <article className="metric-card"><div className="metric-icon tone-lavender"><Activity size={19} /></div><div className="metric-value">{analytics.class_distribution.length}</div><div className="metric-label">Distinct predicted classes</div></article>
        </div>
        <div className="workspace-grid">
          <section className="panel"><div className="panel-heading"><div className="panel-icon tone-mint"><BarChart3 size={19} /></div><div><h3>Scans by day</h3><p>Last 14 calendar days from your database</p></div></div>{analytics.scans_by_day.some((item) => item.count > 0) ? <div className="chart-canvas"><Line data={dailyChart} options={{ ...chartOptions, plugins: { legend: { display: false } } }} /></div> : <EmptyChart description="Save plant scans and this chart will use those records." />}</section>
          <section className="panel"><div className="panel-heading"><div className="panel-icon tone-lavender"><Activity size={19} /></div><div><h3>Prediction classes</h3><p>Only scans with a saved model label</p></div></div>{analytics.class_distribution.length ? <div className="chart-canvas"><Bar data={classChart} options={{ ...chartOptions, indexAxis: 'y', scales: { x: { beginAtZero: true, ticks: { precision: 0 } }, y: { grid: { display: false } } } }} /></div> : <EmptyChart description="Class counts will appear after a trained model has made predictions." />}</section>
          <section className="panel"><div className="panel-heading"><div className="panel-icon tone-peach"><ShieldAlert size={19} /></div><div><h3>Scan status</h3><p>Includes untrained and unsupported-part scans</p></div></div>{analytics.status_distribution.length ? <div className="chart-canvas"><Bar data={statusChart} options={chartOptions} /></div> : <EmptyChart description="Save scans to see the actual status distribution." />}</section>
          <section className="panel"><div className="panel-heading"><div className="panel-icon tone-blue"><CheckCircle2 size={19} /></div><div><h3>How to interpret this page</h3><p>Evidence over impressive-looking numbers</p></div></div><p className="panel-copy">These charts summarize activity for your account; they are not model accuracy metrics. Accuracy, precision, recall and F1 are reported by the training pipeline on its held-out test split.</p><p className="panel-copy">A model confidence score is not the probability that a diagnosis is correct. Confirm important crop decisions with a qualified local expert.</p></section>
        </div>
      </>}
    </div>
  );
}
