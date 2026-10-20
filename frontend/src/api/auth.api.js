import { api, json } from './client'
export const authApi = {
  register: (payload) => api('/auth/register', json('POST', payload)),
  login: (payload) => api('/auth/login', json('POST', payload)),
  me: () => api('/auth/me'),
  updateProfile: (payload) => api('/profile', json('PATCH', payload)),
}
