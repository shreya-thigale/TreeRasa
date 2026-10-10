import { useEffect, useState } from 'react';
import { Clock3, FileText, FlaskConical, ShieldAlert, Upload, CheckCircle2, Sparkles } from 'lucide-react';
import { apiRequest } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';

const blankValues = {
  crop_name: '', soil_ph: '', organic_carbon_pct: '', nitrogen: '', phosphorus: '', potassium: '', nutrient_units: '',
};

function optionalNumber(value) {
  return value === '' ? undefined : Number(value);
}

export default function LabReportsPage() {
  const [reports, setReports] = useState([]);
  const [file, setFile] = useState(null);
  const [type, setType] = useState('soil_or_crop_lab');
  const [notes, setNotes] = useState('');
  const [labValues, setLabValues] = useState(blankValues);
  const [interpretingId, setInterpretingId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setReports(await apiRequest('/lab-reports'));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function uploadReport(event) {
    event.preventDefault();
    if (!file) {
      setError('Choose a report file first.');
      return;
    }
    setBusy(true);
    setError('');
    setSuccess('');
    try {
      const body = new FormData();
      body.append('file', file);
      body.append('report_type', type);
      body.append('notes', notes);
      await apiRequest('/lab-reports', { method: 'POST', body });
      setFile(null);
      setNotes('');
      event.target.reset();
      setSuccess('Lab report saved. You can now enter the measured values printed on it for a cautious rule-based summary.');
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function interpretReport(event, reportId) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setSuccess('');
    const payload = {
      crop_name: labValues.crop_name.trim() || undefined,
      soil_ph: optionalNumber(labValues.soil_ph),
      organic_carbon_pct: optionalNumber(labValues.organic_carbon_pct),
      nitrogen: optionalNumber(labValues.nitrogen),
      phosphorus: optionalNumber(labValues.phosphorus),
      potassium: optionalNumber(labValues.potassium),
      nutrient_units: labValues.nutrient_units.trim() || undefined,
    };
    try {
      await apiRequest(`/lab-reports/${reportId}/interpret`, { method: 'POST', body: JSON.stringify(payload) });
      setSuccess('Your entered measurements and educational comments have been saved.');
      setInterpretingId(null);
      setLabValues(blankValues);
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page-stack">
      <div className="page-intro">
        <span className="eyebrow">SOIL & CROP INSIGHTS</span>
        <h2>Bring your lab results together.</h2>
        <p>Upload soil or crop test documents, enter the measured values, and keep cautious educational comments alongside the original report.</p>
      </div>
      {error && <Notice type="error">{error}</Notice>}
      {success && <Notice type="success">{success}</Notice>}

      <div className="lab-layout">
        <form className="panel" onSubmit={uploadReport}>
          <div className="panel-heading"><div className="panel-icon tone-peach"><FlaskConical size={20} /></div><div><h3>Upload a lab report</h3><p>PDF, JPG or PNG · 12 MB maximum</p></div></div>
          <label className="file-picker"><Upload size={19} /><span><b>{file?.name || 'Choose a report from your device'}</b><small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Soil test, crop tissue test or water analysis'}</small></span><input type="file" accept="application/pdf,image/jpeg,image/png" onChange={(event) => setFile(event.target.files?.[0] || null)} /></label>
          <label>Report type<select value={type} onChange={(event) => setType(event.target.value)}><option value="soil_or_crop_lab">Soil or crop laboratory report</option><option value="soil_test">Soil test</option><option value="plant_tissue">Plant tissue analysis</option><option value="water_quality">Irrigation water quality</option><option value="other">Other</option></select></label>
          <label>Notes for review<textarea rows="3" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Crop, sample date, symptoms or questions for an agronomist…" /></label>
          <button className="button button--primary button--wide" disabled={busy}>{busy ? 'Uploading…' : <><Upload size={16} /> Save report</>}</button>
        </form>
        <section className="panel lab-note">
          <div className="panel-icon tone-blue"><ShieldAlert size={19} /></div><h3>How the lab feature works</h3>
          <p>The original file is stored with your account. This version does not automatically read PDF/image text with OCR. You enter values from the report, and TreeRasa saves a transparent, rule-based educational summary.</p>
          {[['1', 'Keep the original', 'The uploaded report remains available as the source document.'], ['2', 'Enter actual measurements', 'Copy values and units exactly as shown by the laboratory.'], ['3', 'Review with an expert', 'Crop-specific fertilizer rates require local interpretation and must not be guessed.']].map(([number, title, copy]) => <div className="lab-step" key={number}><span>{number}</span><div><b>{title}</b><small>{copy}</small></div></div>)}
        </section>
      </div>

      <section className="section-block">
        <div className="section-heading"><div><span className="eyebrow">YOUR RECORDS</span><h2>Uploaded reports</h2></div><span className="subtle-count">{reports.length} saved</span></div>
        {reports.length ? <div className="report-list">{reports.map((report) => <article className="report-row report-row--lab" key={report.id}>
          <div className="report-file-icon"><FileText size={20} /></div>
          <div className="report-info"><b>{report.original_filename}</b><span>{report.report_type.replaceAll('_', ' ')}{report.notes ? ` · ${report.notes}` : ''}</span><small><Clock3 size={13} /> Uploaded {new Date(report.created_at).toLocaleString()}</small></div>
          <span className="status-pill">{report.interpretation_status.replaceAll('_', ' ')}</span>
          <button className="button button--secondary lab-value-button" onClick={() => { setInterpretingId(interpretingId === report.id ? null : report.id); setLabValues(report.interpretation ? { ...blankValues, crop_name: report.interpretation.crop_name || '', ...Object.fromEntries(Object.entries(report.interpretation.values || {}).map(([key, value]) => [key, String(value)])) } : blankValues); }}><Sparkles size={14} />{report.interpretation ? 'Update values' : 'Enter lab values'}</button>
          {interpretingId === report.id && <form className="lab-values-form" onSubmit={(event) => interpretReport(event, report.id)}>
            <h4>Enter measurements from this report</h4>
            <p>Leave a field blank if the report does not contain that measurement. Do not guess units.</p>
            <div className="form-grid">
              <label>Crop name<input value={labValues.crop_name} onChange={(event) => setLabValues({ ...labValues, crop_name: event.target.value })} placeholder="e.g. Tomato" /></label>
              <label>Soil pH<input type="number" min="0" max="14" step="0.1" value={labValues.soil_ph} onChange={(event) => setLabValues({ ...labValues, soil_ph: event.target.value })} placeholder="As printed on report" /></label>
              <label>Organic carbon (%)<input type="number" min="0" step="0.01" value={labValues.organic_carbon_pct} onChange={(event) => setLabValues({ ...labValues, organic_carbon_pct: event.target.value })} /></label>
              <label>Nitrogen value<input type="number" step="any" value={labValues.nitrogen} onChange={(event) => setLabValues({ ...labValues, nitrogen: event.target.value })} /></label>
              <label>Phosphorus value<input type="number" step="any" value={labValues.phosphorus} onChange={(event) => setLabValues({ ...labValues, phosphorus: event.target.value })} /></label>
              <label>Potassium value<input type="number" step="any" value={labValues.potassium} onChange={(event) => setLabValues({ ...labValues, potassium: event.target.value })} /></label>
              <label className="form-full">NPK units / lab method<input value={labValues.nutrient_units} onChange={(event) => setLabValues({ ...labValues, nutrient_units: event.target.value })} placeholder="Copy the units and extraction method from the report" /></label>
            </div>
            <div className="form-actions"><button type="button" className="button button--secondary" onClick={() => setInterpretingId(null)}>Cancel</button><button className="button button--primary" disabled={busy}>{busy ? 'Saving…' : 'Save values and review'}</button></div>
          </form>}
          {report.interpretation?.guidance && <div className="lab-interpretation"><h4><CheckCircle2 size={16} /> {report.interpretation.guidance.title}</h4><ul>{(report.interpretation.guidance.suggestions || []).map((suggestion, index) => <li key={index}>{suggestion}</li>)}</ul><p>{report.interpretation.guidance.limitations}</p></div>}
        </article>)}</div> : <EmptyState title="No reports uploaded yet" description="Your saved lab documents and interpretations will appear here." />}
      </section>
    </div>
  );
}
