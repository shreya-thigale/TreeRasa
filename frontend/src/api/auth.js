import { apiRequest, saveSession, clearSession } from './client.js';

export async function signIn(email, password) {
  const result = await apiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
  saveSession(result.access_token, result.user);
  return result.user;
}
export async function signUp(form) {
  const result = await apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(form) });
  saveSession(result.access_token, result.user);
  return result.user;
}
export function signOut() { clearSession(); }
