import { useEffect, useRef, useState } from 'react'
import { Bot, ChevronDown, Leaf, LoaderCircle, MessageCircle, Send, Sparkles, X } from 'lucide-react'
import { api, json } from '../../api/client'
import { useLanguage } from '../../context/LanguageContext'

const prompts = {
  en: ['How can I improve soil health?', 'What should I do about yellow leaves?', 'How do I use the TreeRasa plant scan?', 'How can I find affordable seeds?'],
  hi: ['मिट्टी की सेहत कैसे सुधारें?', 'पत्तियाँ पीली हो रही हैं, क्या करूँ?', 'ट्रीरसा प्लांट स्कैन कैसे इस्तेमाल करें?', 'किफायती बीज कैसे खोजें?'],
  mr: ['मातीची सुपीकता कशी वाढवू?', 'पाने पिवळी पडत आहेत, काय करू?', 'ट्रीरसा प्लांट स्कॅन कसा वापरू?', 'परवडणारी बियाणे कशी शोधू?'],
}

export default function ChatbotWidget() {
  const { language, setLanguage, t } = useLanguage()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  useEffect(() => { if (open) endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading, open])

  async function sendMessage(text = input) {
    const message = text.trim()
    if (!message || loading) return
    const previous = messages
    const next = [...previous, { role: 'user', content: message }]
    setMessages(next)
    setInput('')
    setError('')
    setLoading(true)
    try {
      const data = await api('/chatbot', json('POST', {
        message,
        language,
        history: previous.slice(-8).map(({ role, content }) => ({ role, content })),
      }))
      setMessages(current => [...current, { role: 'assistant', content: data.response }])
    } catch (err) {
      setError(err.message || t('chatError'))
    } finally {
      setLoading(false)
    }
  }

  const suggestions = prompts[language] || prompts.en
  const greeting = t('chatGreeting')
  const subtitle = t('chatSubtitle')

  return <>
    {open && <section className="fixed bottom-24 right-4 z-[100] flex h-[min(680px,calc(100dvh-7.5rem))] w-[min(410px,calc(100vw-2rem))] flex-col overflow-hidden rounded-3xl border border-emerald-900/10 bg-white shadow-2xl dark:border-white/10 dark:bg-[#14231a]" aria-label={t('chatTitle')}>
      <header className="flex items-center gap-3 bg-gradient-to-r from-[#145c3a] to-[#28784e] px-4 py-4 text-white">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15"><Bot size={23}/></div>
        <div className="min-w-0 flex-1">
          <div className="font-bold">{t('chatTitle')}</div>
          <div className="mt-0.5 flex items-center gap-1.5 text-xs text-emerald-50/90"><span className="h-2 w-2 rounded-full bg-lime-300"/> {t('chatAvailable')}</div>
        </div>
        <select aria-label={t('language')} value={language} onChange={e => setLanguage(e.target.value)} className="max-w-[112px] rounded-xl border border-white/25 bg-white/10 px-2 py-2 text-xs text-white outline-none [&>option]:text-stone-900">
          <option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option>
        </select>
        <button onClick={() => setOpen(false)} aria-label={t('closeChat')} className="rounded-xl p-2 transition hover:bg-white/15"><ChevronDown size={20}/></button>
      </header>

      <div className="flex items-center gap-2 border-b border-stone-100 bg-emerald-50/70 px-4 py-2.5 text-xs text-emerald-900 dark:border-white/10 dark:bg-emerald-950/40 dark:text-emerald-100">
        <Leaf size={14}/><span>{subtitle}</span><span className="ml-auto inline-flex items-center gap-1"><Sparkles size={13}/>{t('chatAi')}</span>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto bg-[#fbfdfb] p-4 dark:bg-[#101b14]">
        <div className="flex items-start gap-2.5">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100"><Bot size={17}/></div>
          <div className="max-w-[86%] rounded-2xl rounded-tl-md bg-white px-3.5 py-3 text-sm leading-relaxed text-stone-700 shadow-sm dark:bg-[#1d3024] dark:text-stone-100">{greeting}</div>
        </div>
        {messages.map((item, index) => <div key={index} className={item.role === 'user' ? 'flex justify-end' : 'flex items-start gap-2.5'}>
          {item.role === 'assistant' && <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100"><Bot size={17}/></div>}
          <div className={item.role === 'user' ? 'max-w-[86%] whitespace-pre-wrap rounded-2xl rounded-tr-md bg-emerald-700 px-3.5 py-3 text-sm leading-relaxed text-white' : 'max-w-[86%] whitespace-pre-wrap rounded-2xl rounded-tl-md bg-white px-3.5 py-3 text-sm leading-relaxed text-stone-700 shadow-sm dark:bg-[#1d3024] dark:text-stone-100'}>{item.content}</div>
        </div>)}
        {loading && <div className="flex items-center gap-2 pl-10 text-sm text-stone-500"><LoaderCircle size={16} className="animate-spin"/>{t('chatThinking')}</div>}
        {messages.length === 0 && <div className="space-y-2 pl-10">
          <div className="text-xs font-semibold uppercase tracking-wide text-stone-400">{t('chatTryAsking')}</div>
          {suggestions.map(suggestion => <button key={suggestion} onClick={() => sendMessage(suggestion)} className="block w-full rounded-xl border border-emerald-100 bg-white px-3 py-2 text-left text-xs text-emerald-900 transition hover:border-emerald-300 hover:bg-emerald-50 dark:border-emerald-900 dark:bg-[#1d3024] dark:text-emerald-100 dark:hover:bg-emerald-950">{suggestion}</button>)}
        </div>}
        {error && <div role="alert" className="ml-10 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-100">{error}</div>}
        <div ref={endRef}/>
      </div>

      <form onSubmit={e => { e.preventDefault(); sendMessage() }} className="flex items-end gap-2 border-t border-stone-100 bg-white p-3 dark:border-white/10 dark:bg-[#14231a]">
        <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }} rows={1} maxLength={1800} placeholder={t('chatPlaceholder')} aria-label={t('chatPlaceholder')} className="max-h-28 min-h-11 flex-1 resize-y rounded-2xl border border-stone-200 bg-stone-50 px-3.5 py-3 text-sm text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 dark:border-white/10 dark:bg-[#1d3024] dark:text-white dark:focus:ring-emerald-900"/>
        <button type="submit" disabled={!input.trim() || loading} aria-label={t('sendMessage')} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-700 text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-40"><Send size={18}/></button>
      </form>
      <div className="bg-white pb-2 text-center text-[10px] text-stone-400 dark:bg-[#14231a]">{t('chatDisclaimer')}</div>
    </section>}

    <button onClick={() => setOpen(value => !value)} aria-label={open ? t('closeChat') : t('openChat')} className="fixed bottom-5 right-5 z-[100] flex h-14 items-center gap-2 rounded-full bg-emerald-800 px-5 text-white shadow-xl shadow-emerald-950/20 transition hover:-translate-y-0.5 hover:bg-emerald-900 focus:outline-none focus:ring-4 focus:ring-emerald-200 dark:focus:ring-emerald-900">
      {open ? <X size={21}/> : <MessageCircle size={21}/>}
      <span className="text-sm font-semibold">{t('chatTitle')}</span>
    </button>
  </>
}
