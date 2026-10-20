import { api, json } from './client'
export const productsApi = {
  list: (params = {}) => api(`/products?${new URLSearchParams(Object.entries(params).filter(([,v])=>v))}`),
  mine: () => api('/products/mine'),
  create: (payload) => api('/products', json('POST', payload)),
  remove: (id) => api(`/products/${id}`, { method:'DELETE' }),
}
