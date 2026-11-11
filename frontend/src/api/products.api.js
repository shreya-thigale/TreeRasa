import { api, json } from './client'

export const productsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(
        ([, value]) => value !== "" && value !== null && value !== undefined
      )
    ).toString()

    return api(`/products?${query}`)
  },

  mine: () => api('/products/mine'),

    reviews: (id) => api(`/orders/reviews/product/${id}`),
  create: (payload) => api('/products', json('POST', payload)),
  createWithImage: (payload, image) => {
    const form = new FormData()
    Object.entries(payload).forEach(([key, value]) => form.append(key, String(value)))
    if (image) form.append('image', image)
    return api('/products/with-image', { method: 'POST', body: form })
  },
  remove: (id) => api(`/products/${id}`, { method: 'DELETE' }),
}

