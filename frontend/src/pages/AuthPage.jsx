import { useState } from 'react';
import { ArrowRight, Eye, EyeOff, Leaf } from 'lucide-react';
import Brand from '../components/Brand.jsx';
import Notice from '../components/Notice.jsx';

const initialForm = { full_name: '', email: '', password: '', role: 'farmer' };

export default function AuthPage({ onSubmit, error }) {
  const [mode, setMode] = useState('login');
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState(initialForm);

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function submitForm(event) {
    event.preventDefault();
    setBusy(true);
    try { await onSubmit(mode, form); }
    catch { /* The parent displays the authentication error. */ }
    finally { setBusy(false); }
  }

  function changeMode(nextMode) {
    setMode(nextMode);
    setForm(initialForm);
  }

  return (
    <div className="auth-page">
      <section className="auth-art">
        <Brand />
        <div className="auth-art-copy"><span className="pill"><Leaf size={13} /> GROW WITH CONFIDENCE</span><h1>Better care for<br /><em>every growing thing.</em></h1><p>Understand your plants, find sustainable care, and connect with people who help them thrive.</p><div className="auth-decoration"><Leaf size={150} /></div><div className="auth-note"><Leaf size={18} /><span><b>Rooted in sustainability</b><small>Supporting SDG 15 · Life on Land</small></span></div></div>
        <div className="auth-art-footer">Plant knowledge for everyone <span>✳</span></div>
      </section>

      <section className="auth-form-side"><div className="auth-form-wrap">
        <div className="mobile-brand"><Brand /></div>
        <span className="eyebrow">YOUR GROWING JOURNEY STARTS HERE</span>
        <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
        <p className="auth-subtitle">{mode === 'login' ? 'Sign in to continue caring for your plants.' : 'Join a community growing a little more sustainably.'}</p>
        {error && <Notice type="error">{error}</Notice>}
        <form className="auth-form" onSubmit={submitForm}>
          {mode === 'register' && <>
            <label>Full name<input name="full_name" value={form.full_name} onChange={updateField} placeholder="Your full name" minLength="2" required autoComplete="name" /></label>
            <label>I am joining as<select name="role" value={form.role} onChange={updateField}>
              <option value="farmer">Farmer</option><option value="gardener">Home gardener</option><option value="vendor">Fertilizer / product vendor</option><option value="doctor">Plant doctor</option><option value="plant_pathologist">Plant pathologist</option><option value="agronomist">Agronomist</option><option value="nursery_manager">Nursery manager</option><option value="agricultural_extension_officer">Agricultural extension officer</option><option value="forest_officer">Forest officer</option><option value="research_scientist">Research scientist</option><option value="delivery_partner">Delivery partner</option><option value="student">Student</option>
            </select></label>
          </>}
          <label>Email address<input type="email" name="email" value={form.email} onChange={updateField} placeholder="you@example.com" autoComplete="email" required /></label>
          <label>Password<span className="password-field"><input type={showPassword ? 'text' : 'password'} name="password" value={form.password} onChange={updateField} placeholder={mode === 'register' ? 'At least 8 characters' : 'Enter your password'} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} minLength={mode === 'register' ? 8 : 1} required /><button type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label="Toggle password visibility">{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></span></label>
          <button className="button button--primary button--wide" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'} <ArrowRight size={17} /></button>
        </form>
        <p className="auth-switch">{mode === 'login' ? 'New to TreeRasa?' : 'Already have an account?'} <button onClick={() => changeMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p>
        <p className="auth-legal">AI plant-care results are informational and may require confirmation by a qualified expert.</p>
      </div></section>
    </div>
  );
}
