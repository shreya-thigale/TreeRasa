import { Languages, ChevronDown } from 'lucide-react'
import { useLanguage } from '../../context/LanguageContext'

const choices=[{value:'en',label:'English',native:'English'},{value:'hi',label:'Hindi',native:'हिन्दी'},{value:'mr',label:'Marathi',native:'मराठी'}]
export default function LanguageSelector({compact=false}){
 const {language,setLanguage,t}=useLanguage()
 return <label className="relative inline-flex items-center gap-2 rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm font-semibold text-stone-700 shadow-sm transition hover:border-emerald-300 focus-within:ring-2 focus-within:ring-emerald-600/20 dark:border-white/10 dark:bg-white/5 dark:text-stone-100">
  <Languages size={17} className="shrink-0 text-emerald-700 dark:text-emerald-300"/>
  {!compact&&<span className="hidden text-xs text-stone-500 sm:inline">{t('language')}</span>}
  <select aria-label={t('language')} value={language} onChange={e=>setLanguage(e.target.value)} className="max-w-28 cursor-pointer appearance-none bg-transparent pr-5 text-sm font-bold outline-none">
   {choices.map(item=><option key={item.value} value={item.value}>{item.native}</option>)}
  </select>
  <ChevronDown size={14} className="pointer-events-none absolute right-2 text-stone-400"/>
 </label>
}
