import { api, json } from './client'

export const chatbotApi = {
  chat: (message, language = 'en', history = []) =>
    api('/chatbot', json('POST', {
      message,
      language,
      history: history.slice(-8),
    })),
}
