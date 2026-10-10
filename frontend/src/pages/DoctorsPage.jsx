import { useEffect, useState } from 'react';
import { CalendarClock, MapPin, Plus, Stethoscope } from 'lucide-react';
import { apiRequest, getSavedUser } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';

const emptyProfile = { specialty: 'Plant pathology', qualifications: '', region: '', bio: '' };

export default function DoctorsPage() {
  const user = getSavedUser();
  const canPublishProfile = ['doctor', 'plant_pathologist', 'agronomist'].includes(user?.role);
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showProfile, setShowProfile] = useState(false);
  const [busy, setBusy] = useState(false);
  const [profile, setProfile] = useState(emptyProfile);

  async function refresh() {
    setError('');
    try {
      const [doctorResults, appointmentResults] = await Promise.all([apiRequest('/doctors'), apiRequest('/appointments')]);
      setDoctors(doctorResults);
      setAppointments(appointmentResults);
    } catch (requestError) { setError(requestError.message); }
  }

  useEffect(() => { refresh(); }, []);

  async function saveProfile(event) {
    event.preventDefault();
    setBusy(true); setError(''); setSuccess('');
    try {
      await apiRequest('/doctors/profile', { method: 'POST', body: JSON.stringify(profile) });
      setShowProfile(false);
      setSuccess('Your professional profile has been saved.');
      await refresh();
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }

  async function requestAppointment(doctor) {
    const requestedTime = window.prompt('What date and time would you prefer?');
    if (!requestedTime?.trim()) return;
    const message = window.prompt('Briefly describe your plant concern (optional):') || '';
    try {
      await apiRequest('/appointments', { method: 'POST', body: JSON.stringify({ doctor_id: doctor.id, requested_time: requestedTime.trim(), message }) });
      setSuccess('Your appointment request was saved.');
      await refresh();
    } catch (requestError) { setError(requestError.message); }
  }

  return (
    <div className="page-stack">
      <div className="page-intro page-intro-row"><div><span className="eyebrow">EXPERT COMMUNITY</span><h2>Plants do better with a little help.</h2><p>Find plant-health professionals who can help verify symptoms and discuss next steps.</p></div>{canPublishProfile && <button className="button button--primary" onClick={() => setShowProfile((open) => !open)}><Plus size={17} /> Create / edit profile</button>}</div>
      {error && <Notice type="error">{error}</Notice>}{success && <Notice type="success">{success}</Notice>}
      {showProfile && <form className="panel" onSubmit={saveProfile}><div className="panel-heading"><div className="panel-icon tone-mint"><Stethoscope size={19} /></div><div><h3>Professional profile</h3><p>Use accurate qualifications and service-area information.</p></div></div><div className="form-grid">
        <label>Specialty *<input required value={profile.specialty} onChange={(event) => setProfile({ ...profile, specialty: event.target.value })} /></label>
        <label>Qualifications<input value={profile.qualifications} onChange={(event) => setProfile({ ...profile, qualifications: event.target.value })} /></label>
        <label>Region / service area<input value={profile.region} onChange={(event) => setProfile({ ...profile, region: event.target.value })} /></label>
        <label className="form-full">Short bio<textarea rows="3" value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} /></label>
      </div><div className="form-actions"><button type="button" className="button button--secondary" onClick={() => setShowProfile(false)}>Cancel</button><button className="button button--primary" disabled={busy}>{busy ? 'Saving…' : 'Save profile'}</button></div></form>}

      <div className="section-heading"><div><span className="eyebrow">PLANT HEALTH PROFESSIONALS</span><h2>Meet the experts</h2></div><span className="subtle-count">{doctors.length} published profiles</span></div>
      {doctors.length ? <div className="doctor-grid">{doctors.map((doctor) => <article className="doctor-card" key={doctor.id}>
        <div className="doctor-card-top"><div className="doctor-avatar"><Stethoscope size={23} /></div><span className="status-pill">Professional profile</span></div><h3>{doctor.specialty}</h3><p>{doctor.qualifications || 'Qualifications not listed'}</p><p>{doctor.bio || 'This professional has not added a bio yet.'}</p>{doctor.region && <div className="doctor-region"><MapPin size={14} />{doctor.region}</div>}
        <button className="button button--secondary button--wide" onClick={() => requestAppointment(doctor)}><CalendarClock size={16} /> Request an appointment</button>
      </article>)}</div> : <EmptyState title="No professional profiles yet" description="Plant doctors and agronomists can register and publish their own profiles. No fictional professionals are shown here." />}

      <section className="section-block"><div className="section-heading"><div><span className="eyebrow">YOUR FOLLOW-UPS</span><h2>Appointment requests</h2></div></div>{appointments.length ? <div className="report-list">{appointments.map((appointment) => <article className="report-row" key={appointment.id}><div className="report-file-icon"><CalendarClock size={20} /></div><div className="report-info"><b>Appointment request #{appointment.id}</b><span>Requested time: {appointment.requested_time}</span>{appointment.message && <small>{appointment.message}</small>}</div><span className="status-pill">{appointment.status}</span></article>)}</div> : <p className="muted-copy">Your appointment requests will appear here once you make one.</p>}</section>
    </div>
  );
}
