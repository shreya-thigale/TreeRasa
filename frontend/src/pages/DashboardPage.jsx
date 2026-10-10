import { useEffect, useState } from 'react';
import {
  Activity, ArrowRight, CircleHelp, FlaskConical, Leaf, ScanLine,
  ShieldCheck, ShoppingBag, Sprout, Stethoscope,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../api/client.js';
import Notice from '../components/Notice.jsx';

const quickActions = [
  { to: '/scan', icon: ScanLine, title: 'Scan a plant', copy: 'Upload a photo or use your camera to start an analysis.', tone: 'mint' },
  { to: '/plants', icon: Sprout, title: 'Add a plant', copy: 'Keep your growing space and scan history organised.', tone: 'peach' },
  { to: '/marketplace', icon: ShoppingBag, title: 'Explore care products', copy: 'Browse products listed by real vendor accounts.', tone: 'lavender' },
  { to: '/doctors', icon: Stethoscope, title: 'Ask an expert', copy: 'Find a plant doctor and request an appointment.', tone: 'blue' },
];

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest('/dashboard/summary')
      .then(setSummary)
      .catch((requestError) => setError(requestError.message));
  }, []);

  const metrics = summary ? [
    ['Plants in your library', summary.plants, Sprout, 'mint'],
    ['Plant scans saved', summary.scans, ScanLine, 'lavender'],
    ['Lab reports uploaded', summary.lab_reports, FlaskConical, 'peach'],
    ['Appointments', summary.appointments, Stethoscope, 'blue'],
  ] : [];

  return (
    <div className="page-stack">
      <section className="welcome-banner">
        <div className="welcome-copy">
          <span className="pill"><Leaf size={13} /> YOUR PLANT CARE SPACE</span>
          <h2>Let's help your plants<br />feel <em>at home.</em></h2>
          <p>Good growing starts with noticing. Keep plant records, check symptoms and make informed care choices.</p>
          <div className="welcome-buttons">
            <Link className="button button--light" to="/scan"><ScanLine size={17} /> Start a plant scan <ArrowRight size={16} /></Link>
            <Link className="text-link text-link--light" to="/plants">View plant library</Link>
          </div>
        </div>
        <div className="hero-plant" aria-hidden="true">
          <span className="hero-sun" /><span className="hero-stem stem-one" /><span className="hero-stem stem-two" /><span className="hero-stem stem-three" />
          <span className="hero-leaf leaf-one" /><span className="hero-leaf leaf-two" /><span className="hero-leaf leaf-three" /><span className="hero-leaf leaf-four" /><span className="hero-pot" />
        </div>
        <div className="banner-foot"><span><i /> Your personal growing space</span><span>Care thoughtfully. Grow sustainably. ✳</span></div>
      </section>

      {error && <Notice type="error">{error}</Notice>}

      <div className="section-heading section-heading--spaced">
        <div><span className="eyebrow">YOUR OVERVIEW</span><h2>A little progress goes a long way</h2><p>These numbers come from your saved TreeRasa records.</p></div>
        <span className="live-chip"><Activity size={14} /> Live account data</span>
      </div>
      <div className="metric-grid">
        {metrics.length ? metrics.map(([label, value, Icon, tone]) => (
          <article className="metric-card" key={label}>
            <div className={`metric-icon tone-${tone}`}><Icon size={19} /></div>
            <div className="metric-value">{value}</div>
            <div className="metric-label">{label}</div>
          </article>
        )) : [1, 2, 3, 4].map((item) => <div className="metric-card" key={item}><div className="skeleton" /><div className="skeleton skeleton-wide" /></div>)}
      </div>

      <section className="section-block">
        <div className="section-heading"><div><span className="eyebrow">YOUR NEXT STEP</span><h2>What would you like to do?</h2></div><span className="subtle-count">Four ways to get started</span></div>
        <div className="action-grid">{quickActions.map(({ to, icon: Icon, title, copy, tone }) => (
          <Link className="action-card" to={to} key={to}><div className={`action-icon tone-${tone}`}><Icon size={20} /></div><h3>{title}</h3><p>{copy}</p><span className="action-arrow"><ArrowRight size={17} /></span></Link>
        ))}</div>
      </section>

      <div className="bottom-grid">
        <section className="panel">
          <div className="panel-heading"><div className="panel-icon tone-mint"><ShieldCheck size={19} /></div><div><h3>AI model status</h3><p>Honest status of the disease classifier</p></div></div>
          <span className={`model-status ${summary?.trained_model_available ? 'ready' : ''}`}><i />{summary?.trained_model_available ? 'Model artifact detected' : 'Training not completed yet'}</span>
          <p className="panel-copy">{summary?.trained_model_available ? 'A model file was found. Validate it on independent field images before trusting it for crop decisions.' : 'Images can be saved now. Predictions remain disabled until a trained model and class-label file are installed.'}</p>
          <Link className="text-link" to="/scan">Open plant analysis <ArrowRight size={15} /></Link>
        </section>
        <section className="panel">
          <div className="panel-heading"><div className="panel-icon tone-peach"><Leaf size={19} /></div><div><h3>Growing with nature</h3><p>Our guiding principle</p></div></div>
          <p className="panel-copy">Observe carefully, protect beneficial insects, and confirm a diagnosis before treatment. Natural does not always mean harmless.</p>
          <a className="text-link" href="https://sdgs.un.org/goals/goal15" target="_blank" rel="noreferrer">Explore SDG 15 <ArrowRight size={15} /></a>
        </section>
      </div>
      <p className="disclaimer-line"><CircleHelp size={14} /> TreeRasa offers educational plant-care information. It does not replace a qualified plant pathologist or local agricultural advice.</p>
    </div>
  );
}
