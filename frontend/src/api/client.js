const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const getToken = () => localStorage.getItem('treerasa_token');
export const getSavedUser = () => {
  try { return JSON.parse(localStorage.getItem('treerasa_user') || 'null'); }
  catch { return null; }
};
export function saveSession(token, user) {
  localStorage.setItem('treerasa_token', token);
  localStorage.setItem('treerasa_user', JSON.stringify(user));
}
export function clearSession() {
  localStorage.removeItem('treerasa_token');
  localStorage.removeItem('treerasa_user');
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (getToken()) headers.set('Authorization', `Bearer ${getToken()}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

/** Download an authenticated file generated from real API records. */
export async function downloadApiFile(path, filename) {
  const headers = new Headers();
  if (getToken()) headers.set('Authorization', `Bearer ${getToken()}`);
  const response = await fetch(`${API_BASE}${path}`, { headers });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Download failed (${response.status})`);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
