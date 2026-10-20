
import { api } from './client'

export const scansApi = {
  mine: () => api('/scans/mine'),

  create: (file, cropName) => {
    const form = new FormData()
    form.append('file', file)

    const query = cropName
      ? `?crop_name=${encodeURIComponent(cropName)}`
      : ''

    return api(`/scans${query}`, {
      method: 'POST',
      body: form,
    })
  },
}
