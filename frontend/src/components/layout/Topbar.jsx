import { useEffect, useState } from 'react'
import { Bell, Moon, Sun, Search, Menu, LogOut, CheckCheck } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../api/client'

export default function Topbar({onMenu}) {
 const {theme,toggleTheme}=useTheme()
 const {user,logout}=useAuth()
 const [open,setOpen]=useState(false)
 const [notifications,setNotifications]=useState([])
 const [noticeError,setNoticeError]=useState('')
 async function loadNotifications(){
  try{setNotifications(await api('/notifications/mine'));setNoticeError('')}
  catch(e){setNoticeError(e.message||'Notifications could not be loaded.')}
 }
 useEffect(()=>{loadNotifications()},[])
 const unread=notifications.filter(n=>!n.is_read).length
 async function markAllRead(){
  try{await api('/notifications/read-all',{method:'PATCH'});setNotifications(items=>items.map(n=>({...n,is_read:true})))}
  catch(e){setNoticeError(e.message)}
 }
 async function markRead(item){
  if(item.is_read)return
  try{await api(`/notifications/${item.id}/read`,{method:'PATCH'});setNotifications(items=>items.map(n=>n.id===item.id?{...n,is_read:true}:n))}
  catch(e){setNoticeError(e.message)}
 }
 return <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-stone-200/80 bg-[#f8faf7]/90 px-4 backdrop-blur-xl dark:border-white/10 dark:bg-[#101a14]/90 sm:px-7">
  <div className="flex items-center gap-3"><button onClick={onMenu} className="rounded-xl p-2 hover:bg-stone-100 dark:hover:bg-white/10 lg:hidden" aria-label="Open menu"><Menu size={20}/></button><div className="relative hidden sm:block"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" size={17}/><input placeholder="Search your workspace…" className="w-64 rounded-xl border-0 bg-white py-2.5 pl-10 pr-4 text-sm outline-none ring-1 ring-stone-200 focus:ring-forest-500 dark:bg-white/5 dark:ring-white/10"/></div></div>
  <div className="flex items-center gap-2">
   <button onClick={toggleTheme} className="rounded-xl p-2.5 hover:bg-stone-100 dark:hover:bg-white/10" aria-label="Toggle theme">{theme==='dark'?<Sun size={19}/>:<Moon size={19}/>}</button>
   <div className="relative">
    <button onClick={()=>{setOpen(v=>!v);if(!open)loadNotifications()}} className="relative rounded-xl p-2.5 hover:bg-stone-100 dark:hover:bg-white/10" aria-label={`Notifications, ${unread} unread`}><Bell size={19}/>{unread>0&&<><i className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500"/><span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-rose-600 px-1 text-[9px] font-bold leading-4 text-white">{unread>9?'9+':unread}</span></>}</button>
    {open&&<><button aria-label="Close notifications" className="fixed inset-0 z-30 cursor-default" onClick={()=>setOpen(false)}/><section className="absolute right-0 z-40 mt-2 w-[min(92vw,380px)] overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-xl dark:border-white/10 dark:bg-[#17251b]">
     <div className="flex items-center justify-between border-b border-stone-100 p-4 dark:border-white/10"><div><h3 className="font-bold">Notifications</h3><p className="text-xs text-stone-500">{unread} unread</p></div><button onClick={markAllRead} disabled={!unread} className="inline-flex items-center gap-1 text-xs font-bold text-emerald-800 disabled:opacity-40 dark:text-emerald-200"><CheckCheck size={14}/> Mark all read</button></div>
     {noticeError&&<p className="p-3 text-xs text-rose-600">{noticeError}</p>}
     <div className="max-h-96 overflow-y-auto">{notifications.length?notifications.map(item=><button key={item.id} onClick={()=>markRead(item)} className={`block w-full border-b border-stone-100 p-4 text-left last:border-0 hover:bg-stone-50 dark:border-white/5 dark:hover:bg-white/5 ${item.is_read?'opacity-70':'bg-emerald-50/50 dark:bg-emerald-950/20'}`}><div className="flex items-start gap-3"><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${item.is_read?'bg-stone-300':'bg-emerald-600'}`}/><span className="min-w-0"><b className="block text-sm">{item.title}</b><span className="mt-1 block text-xs leading-5 text-stone-600 dark:text-stone-300">{item.message}</span><time className="mt-2 block text-[10px] text-stone-400">{new Date(item.created_at).toLocaleString()}</time></span></div></button>):<div className="p-8 text-center"><Bell className="mx-auto text-stone-300" size={26}/><p className="mt-2 text-sm font-semibold">You're all caught up</p><p className="mt-1 text-xs text-stone-500">New order and account updates will appear here.</p></div>}</div>
    </section></>}
   </div>
   <div className="ml-1 hidden h-9 w-9 place-items-center rounded-full bg-forest-100 font-bold text-forest-800 sm:grid">{user?.full_name?.slice(0,1)?.toUpperCase()||'T'}</div><div className="hidden sm:block"><p className="max-w-36 truncate text-sm font-bold">{user?.full_name}</p><p className="text-xs capitalize text-stone-500">{user?.role}</p></div><button onClick={logout} title="Sign out" className="rounded-xl p-2.5 text-stone-500 hover:bg-stone-100 dark:hover:bg-white/10"><LogOut size={18}/></button>
  </div>
 </header>
}
