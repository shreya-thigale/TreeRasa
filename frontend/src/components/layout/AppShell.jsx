import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { X } from 'lucide-react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
export default function AppShell(){
 const [mobileOpen,setMobileOpen]=useState(false)
 return <div className="min-h-screen bg-[#f6f8f4] text-stone-800 dark:bg-[#101a14] dark:text-stone-100 lg:flex">
  <Sidebar/><div className="min-w-0 flex-1"><Topbar onMenu={()=>setMobileOpen(true)}/><main className="mx-auto max-w-[1600px] p-4 sm:p-7 xl:p-9"><Outlet/></main></div>
  {mobileOpen&&<div className="fixed inset-0 z-50 lg:hidden"><button className="absolute inset-0 bg-black/40" onClick={()=>setMobileOpen(false)} aria-label="Close menu"/><div className="absolute inset-y-0 left-0 w-72"><button onClick={()=>setMobileOpen(false)} className="absolute right-3 top-3 z-10 rounded-lg p-2"><X/></button><Sidebar/></div></div>}
 </div>
}
