import { NavLink } from 'react-router-dom'
import { Sprout, LayoutDashboard, ScanLine, ShoppingBasket, Package, ClipboardList, ChartNoAxesCombined, UserRound, Store, Leaf } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
const common=[{to:'/dashboard',label:'Overview',icon:LayoutDashboard},{to:'/scan',label:'Plant health scan',icon:ScanLine},{to:'/marketplace/produce',label:'Fresh from farms',icon:Leaf},{to:'/marketplace/supplies',label:'Seeds & fertilizers',icon:ShoppingBasket},{to:'/orders',label:'Orders',icon:ClipboardList},{to:'/profile',label:'My profile',icon:UserRound}]
export default function Sidebar(){
 const {user}=useAuth()
 const extra=user?.role==='farmer'?[{to:'/my-listings',label:'My farm listings',icon:Package},{to:'/sales',label:'Sales & customers',icon:ChartNoAxesCombined}]:user?.role==='vendor'?[{to:'/my-listings',label:'My products',icon:Package},{to:'/sales',label:'Sales & customers',icon:ChartNoAxesCombined}]:[]
 return <aside className="hidden w-64 shrink-0 border-r border-stone-200/80 bg-white px-4 py-6 dark:border-white/10 dark:bg-[#142219] lg:flex lg:flex-col">
  <NavLink to="/" className="mb-9 flex items-center gap-3 px-2"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-forest-600 text-white"><Sprout size={22}/></span><span><b className="font-display text-xl tracking-tight">TreeRasa</b><small className="block text-xs text-stone-500">Grow better, naturally</small></span></NavLink>
  <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[.18em] text-stone-400">Workspace</p>
  <nav className="space-y-1">{[...common,...extra].map(item=><NavLink key={item.to} to={item.to} className={({isActive})=>`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive?'bg-forest-50 text-forest-700 dark:bg-forest-900/60 dark:text-forest-100':'text-stone-600 hover:bg-stone-50 dark:text-stone-300 dark:hover:bg-white/5'}`}><item.icon size={18}/>{item.label}</NavLink>)}</nav>
  <div className="mt-auto rounded-2xl bg-forest-50 p-4 dark:bg-forest-900/40"><Sprout className="mb-2 text-forest-700 dark:text-forest-200" size={22}/><p className="text-sm font-bold">Growing sustainably</p><p className="mt-1 text-xs leading-5 text-stone-600 dark:text-stone-300">Healthier plants, stronger farms, a greener future.</p></div>
 </aside>
}
