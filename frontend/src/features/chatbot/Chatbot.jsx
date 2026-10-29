import { useState } from 'react'
import { chatbotApi } from '../../api/chatbot.api'

export default function Chatbot() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])

  async function sendMessage() {
    if (!message.trim()) return

    const userMessage = message

    setMessages((prev) => [
      ...prev,
      { sender: 'user', text: userMessage }
    ])

    setMessage('')

    try {
      const data = await chatbotApi.chat(userMessage)

      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: data.response }
      ])

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: error.message }
      ])
    }
  }

  return (
    <div className="p-6">

      <h2 className="text-xl font-bold mb-4">
        PlantCare AI
      </h2>

      <div className="border rounded p-4 h-96 overflow-y-auto mb-4">

        {messages.map((msg, index) => (
          <div key={index} className="mb-3">
            <b>
              {msg.sender === 'user' ? 'You' : 'PlantCare AI'}:
            </b>{' '}
            {msg.text}
          </div>
        ))}

      </div>


      <div className="flex gap-2">

        <input
          className="border p-2 flex-1 rounded"
          value={message}
          onChange={(e)=>setMessage(e.target.value)}
          placeholder="Ask about plant diseases..."
        />

        <button
          className="bg-green-600 text-white px-4 rounded"
          onClick={sendMessage}
        >
          Send
        </button>

      </div>

    </div>
  )
}