import { api, json } from './client'
export const ordersApi = {
  mine: () => api('/orders/mine'),
  checkout: (payload) => api('/orders/checkout', json('POST', payload)),
  updateStatus: (id, status) => api(`/orders/${id}/status`, json('PATCH', {status})),
  review: (payload) => api('/orders/reviews', json('POST', payload)),
}
