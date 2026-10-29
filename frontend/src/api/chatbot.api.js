import { api } from './client'

export const chatbotApi = {
  chat: (message) =>
    api('/chatbot', {
      method: 'POST',
      body: JSON.stringify({
        message
      }),
    }),
}