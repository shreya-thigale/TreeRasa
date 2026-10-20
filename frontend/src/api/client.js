const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
export function getToken(){ return localStorage.getItem('treerasa_token') }
export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type','application/json')
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = response.status === 204 ? null : await response.json().catch(()=>null)
  if (!response.ok) throw new Error(data?.detail || 'Request failed. Please try again.')
  return data
}
export const json = (method, body) => ({ method, body: JSON.stringify(body) })
