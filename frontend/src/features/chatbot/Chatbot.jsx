import { useEffect, useRef, useState } from 'react'
import { Bot, Send, Sprout, UserRound, LoaderCircle, RotateCcw, Sparkles, AlertCircle } from 'lucide-react'
import { chatbotApi } from '../../api/chatbot.api'
import { useLanguage } from '../../context/LanguageContext'

const suggestions = {
  en: ['How can I improve soil health?', 'What causes yellow leaves on tomato plants?', 'How do I manage pests safely?', 'How do I use TreeRasa plant scanning?'],
  hi: ['मैं मिट्टी की सेहत कैसे सुधारूँ?', 'टमाटर के पत्ते पीले क्यों हो रहे हैं?', 'कीटों का सुरक्षित प्रबंधन कैसे करूँ?', 'TreeRasa में पौधों की जाँच कैसे करें?'],
  mr: ['मी मातीची सुपीकता कशी वाढवू?', 'टोमॅटोची पाने पिवळी का पडतात?', 'किडींचे सुरक्षित व्यवस्थापन कसे करावे?', 'TreeRasa मध्ये पीक तपासणी कशी करावी?'],
}
const copy = {
  en: { intro:'Practical crop, soil and plant-health guidance for Indian farms.', welcome:'Namaste! I’m PlantCare AI. Ask me about crops, soil, irrigation, plant health or TreeRasa.', placeholder:'Ask a farming or TreeRasa question…', send:'Send message', thinking:'Preparing a helpful answer…', empty:'Your conversation will appear here.', error:'I could not get a response. Please try again.', retry:'Try again', clear:'New conversation', you:'You', assistant:'PlantCare AI', note:'AI guidance can be imperfect. Confirm important crop decisions with a local agriculture expert.' },
  hi: { intro:'भारतीय किसानों के लिए फसल, मिट्टी और पौधों की सेहत से जुड़ी उपयोगी जानकारी।', welcome:'नमस्ते! मैं PlantCare AI हूँ। फसल, मिट्टी, सिंचाई, पौधों की सेहत या TreeRasa के बारे में पूछें।', placeholder:'खेती या TreeRasa के बारे में पूछें…', send:'संदेश भेजें', thinking:'उत्तर तैयार हो रहा है…', empty:'आपकी बातचीत यहाँ दिखाई देगी।', error:'उत्तर नहीं मिल पाया। कृपया फिर कोशिश करें।', retry:'फिर कोशिश करें', clear:'नई बातचीत', you:'आप', assistant:'PlantCare AI', note:'AI की सलाह में त्रुटि हो सकती है। महत्वपूर्ण निर्णय स्थानीय कृषि विशेषज्ञ से जाँचें।' },
  mr: { intro:'भारतीय शेतकऱ्यांसाठी पीक, माती आणि वनस्पती आरोग्यविषयक उपयुक्त मार्गदर्शन.', welcome:'नमस्कार! मी PlantCare AI आहे. पीक, माती, सिंचन, वनस्पती आरोग्य किंवा TreeRasa बद्दल विचारा.', placeholder:'शेती किंवा TreeRasa बद्दल विचारा…', send:'संदेश पाठवा', thinking:'उत्तर तयार होत आहे…', empty:'तुमचा संवाद येथे दिसेल.', error:'उत्तर मिळू शकले नाही. कृपया पुन्हा प्रयत्न करा.', retry:'पुन्हा प्रयत्न करा', clear:'नवीन संवाद', you:'तुम्ही', assistant:'PlantCare AI', note:'AI मार्गदर्शनात चुका असू शकतात. महत्त्वाचे निर्णय स्थानिक कृषी तज्ज्ञांकडून तपासून घ्या.' },
}

export default function Chatbot() {
  const { language } = useLanguage()
  const text = copy[language] || copy.en
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, loading])

  async function sendMessage(value = input) {
    const message = value.trim()
    if (!message || loading) return
    const history = messages.slice(-8).map(({ role, content }) => ({ role, content }))
    setMessages(current => [...current, { role: 'user', content: message }])
    setInput('')
    setError('')
    setLoading(true)
    try {
      const data = await chatbotApi.chat(message, language, history)
      if (!data?.response) throw new Error('The assistant returned an empty response.')
      setMessages(current => [...current, { role: 'assistant', content: data.response }])
    } catch (err) {
      setError(err.message || text.error)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function resetChat() {
    setMessages([])
    setError('')
    setInput('')
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5 pb-8">
      <header className="overflow-hidden rounded-3xl bg-gradient-to-br from-[#123f2b] via-[#1b6543] to-[#2b8053] p-6 text-white shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="grid h-12 w-12 place-items-center rounded-2xl border border-white/20 bg-white/10"><Bot size={26}/></span>
            <div><p className="text-xs font-bold uppercase tracking-[.18em] text-emerald-100">TREERASA AI</p><h1 className="font-display text-2xl font-extrabold sm:text-3xl">PlantCare AI</h1></div>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-2 text-xs font-semibold"><span className="h-2 w-2 rounded-full bg-lime-300"/> Agriculture assistant</div>
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-emerald-50/90">{text.intro}</p>
      </header>

      <section className="overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#17251b]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-100 px-5 py-4 dark:border-white/10">
          <div className="flex items-center gap-2 text-sm font-bold"><Sparkles size={17} className="text-emerald-700 dark:text-emerald-300"/> Your farming assistant</div>
          <button type="button" onClick={resetChat} className="inline-flex items-center gap-2 rounded-xl border border-stone-200 px-3 py-2 text-xs font-semibold text-stone-600 transition hover:bg-stone-50 dark:border-white/10 dark:text-stone-200 dark:hover:bg-white/5"><RotateCcw size={14}/>{text.clear}</button>
        </div>

        <div className="min-h-[390px] max-h-[min(62vh,650px)] space-y-5 overflow-y-auto bg-[#fbfdfb] p-4 sm:p-6 dark:bg-[#101b14]">
          <div className="flex items-start gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-100"><Sprout size={18}/></span>
            <div className="max-w-[88%] rounded-2xl rounded-tl-md border border-emerald-100 bg-white px-4 py-3 text-sm leading-6 text-stone-700 shadow-sm dark:border-white/10 dark:bg-[#1d3024] dark:text-stone-100">{text.welcome}</div>
          </div>

          {messages.map((msg, index) => (
            <div key={index} className={msg.role === 'user' ? 'flex justify-end gap-3' : 'flex items-start gap-3'}>
              {msg.role === 'assistant' && <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-100"><Bot size={18}/></span>}
              <div className={msg.role === 'user' ? 'max-w-[88%] rounded-2xl rounded-tr-md bg-emerald-800 px-4 py-3 text-sm leading-6 text-white' : 'max-w-[88%] whitespace-pre-wrap rounded-2xl rounded-tl-md border border-stone-100 bg-white px-4 py-3 text-sm leading-6 text-stone-700 shadow-sm dark:border-white/10 dark:bg-[#1d3024] dark:text-stone-100'}>
                <p className="mb-1 text-[10px] font-bold uppercase tracking-wider opacity-65">{msg.role === 'user' ? text.you : text.assistant}</p>{msg.content}
              </div>
              {msg.role === 'user' && <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-stone-100 text-stone-600 dark:bg-white/10 dark:text-stone-200"><UserRound size={17}/></span>}
            </div>
          ))}

          {messages.length === 0 && <div className="ml-12 space-y-3"><p className="text-xs font-bold uppercase tracking-wider text-stone-400">Suggested questions</p><div className="grid gap-2 sm:grid-cols-2">{(suggestions[language] || suggestions.en).map(item => <button key={item} type="button" onClick={() => sendMessage(item)} disabled={loading} className="rounded-xl border border-emerald-100 bg-white px-4 py-3 text-left text-sm font-medium text-emerald-900 transition hover:border-emerald-300 hover:bg-emerald-50 disabled:opacity-50 dark:border-emerald-900 dark:bg-[#1d3024] dark:text-emerald-100 dark:hover:bg-emerald-950/40">{item}</button>)}</div></div>}

          {loading && <div className="flex items-center gap-2 pl-12 text-sm text-stone-500"><LoaderCircle size={17} className="animate-spin"/>{text.thinking}</div>}
          {error && <div role="alert" className="ml-12 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100"><div className="flex items-start gap-2"><AlertCircle size={17} className="mt-0.5 shrink-0"/><p>{error}</p></div><button type="button" onClick={() => sendMessage(messages.filter(item => item.role === 'user').at(-1)?.content || '')} className="mt-3 text-xs font-bold underline">{text.retry}</button></div>}
          <div ref={bottomRef}/>
        </div>

        <form onSubmit={event => { event.preventDefault(); sendMessage() }} className="flex items-end gap-2 border-t border-stone-100 bg-white p-3 sm:p-4 dark:border-white/10 dark:bg-[#17251b]">
          <textarea ref={inputRef} rows={2} maxLength={1800} value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage() } }} placeholder={text.placeholder} aria-label={text.placeholder} className="min-h-12 flex-1 resize-y rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 dark:border-white/10 dark:bg-[#1d3024] dark:text-white"/>
          <button type="submit" disabled={!input.trim() || loading} className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-2xl bg-emerald-800 px-4 text-sm font-bold text-white transition hover:bg-emerald-900 disabled:cursor-not-allowed disabled:opacity-40"><Send size={17}/><span className="hidden sm:inline">{text.send}</span></button>
        </form>
        <p className="border-t border-stone-100 px-4 py-3 text-center text-[11px] text-stone-400 dark:border-white/10">{text.note}</p>
      </section>
    </div>
  )
}
