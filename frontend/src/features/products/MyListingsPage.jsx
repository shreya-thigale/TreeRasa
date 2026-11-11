import { useEffect, useState } from 'react'
import { PackagePlus, Trash2, ImagePlus, X } from 'lucide-react'
import { productsApi } from '../../api/products.api'
import { API_BASE } from '../../api/client'
import { useAuth } from '../../context/AuthContext'

const MAX_IMAGE_SIZE = 8 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export default function MyListingsPage(){
 const {user}=useAuth()
 const [items,setItems]=useState([])
 const [error,setError]=useState('')
 const [saving,setSaving]=useState(false)
 const [image,setImage]=useState(null)
 const [preview,setPreview]=useState('')
 const [form,setForm]=useState({title:'',description:'',listing_type:user?.role==='farmer'?'produce':'supply',category:user?.role==='farmer'?'vegetable':'fertilizer',price:'',unit:user?.role==='farmer'?'kg':'bag',stock:''})
 async function load(){try{setItems(await productsApi.mine())}catch(e){setError(e.message)}}
 useEffect(()=>{load()},[])
 useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview)},[preview])
 function change(e){setForm({...form,[e.target.name]:e.target.value})}
 function selectImage(e){
  const file=e.target.files?.[0]||null
  e.target.value=''
  setError('')
  if(!file)return
  if(!IMAGE_TYPES.includes(file.type)){setError('Please choose a JPG, PNG or WEBP image.');return}
  if(file.size>MAX_IMAGE_SIZE){setError('Image must be smaller than 8 MB.');return}
  if(preview)URL.revokeObjectURL(preview)
  setImage(file);setPreview(URL.createObjectURL(file))
 }
 async function submit(e){
  e.preventDefault();setSaving(true);setError('')
  try{
   await productsApi.createWithImage({...form,price:Number(form.price),stock:Number(form.stock)},image)
   setForm({...form,title:'',description:'',price:'',stock:''})
   if(preview)URL.revokeObjectURL(preview)
   setImage(null);setPreview('')
   await load()
  }catch(e){setError(e.message)}finally{setSaving(false)}
 }
 async function remove(id){try{await productsApi.remove(id);await load()}catch(e){setError(e.message)}}
 const imageSrc=(url)=>url?(`${API_BASE.replace(/\\/$/,'').replace(/\\/api$/,'')}${url}`):''
 return <div className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]">
  <section className="h-fit rounded-2xl border border-stone-200/70 bg-white p-6 dark:border-white/10 dark:bg-[#17251b]">
   <div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-forest-50 text-forest-700 dark:bg-forest-900/50 dark:text-forest-100"><PackagePlus/></span><div><h1 className="font-display text-xl font-extrabold">Add a listing</h1><p className="text-sm text-stone-500">Publish products to the marketplace.</p></div></div>
   {error&&<p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
   <form onSubmit={submit} className="mt-5 space-y-4">
    <div><label className="text-sm font-semibold">Product name</label><input required name="title" value={form.title} onChange={change} className="field" placeholder="e.g. Fresh pomegranate"/></div>
    <div><label className="text-sm font-semibold">Category</label><select name="category" value={form.category} onChange={change} className="field">{(user?.role==='farmer'?['fruit','vegetable','grain','pomegranate','wheat','sugarcane','cotton','other']:['fertilizer','seeds','pesticide','equipment','other']).map(x=><option key={x} value={x}>{x}</option>)}</select></div>
    <div><label className="text-sm font-semibold">Description</label><textarea name="description" value={form.description} onChange={change} className="field" rows="3" placeholder="Quality, variety, packaging or usage details"/></div>
    <div><label className="text-sm font-semibold">Product image (optional)</label><label className="mt-2 flex min-h-36 cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed border-stone-300 bg-stone-50 p-3 text-center dark:border-white/20 dark:bg-white/5">{preview?<><img src={preview} alt="Product preview" className="max-h-44 w-full rounded-lg object-contain"/><span className="mt-2 text-xs text-stone-500">{image?.name}</span></>:<><ImagePlus className="mb-2 text-forest-700" size={28}/><span className="text-sm font-semibold">Choose product image</span><span className="text-xs text-stone-500">JPG, PNG or WEBP · max 8 MB</span></>}<input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={selectImage}/></label>{preview&&<button type="button" onClick={()=>{URL.revokeObjectURL(preview);setPreview('');setImage(null)}} className="mt-2 inline-flex items-center gap-1 text-xs text-red-600"><X size={14}/> Remove image</button>}</div>
    <div className="grid grid-cols-3 gap-3"><div><label className="text-sm font-semibold">Price ₹</label><input required type="number" min="0" step=".01" name="price" value={form.price} onChange={change} className="field"/></div><div><label className="text-sm font-semibold">Unit</label><input required name="unit" value={form.unit} onChange={change} className="field"/></div><div><label className="text-sm font-semibold">Stock</label><input required type="number" min="0" name="stock" value={form.stock} onChange={change} className="field"/></div></div>
    <button disabled={saving} className="w-full rounded-xl bg-forest-700 px-4 py-3 font-bold text-white disabled:opacity-50">{saving?'Publishing…':'Publish listing'}</button>
   </form>
  </section>
  <section><div className="mb-4"><h2 className="font-display text-xl font-extrabold">Your listings</h2><p className="mt-1 text-sm text-stone-500">Listings and product images are saved in PostgreSQL.</p></div><div className="grid gap-3 sm:grid-cols-2">{items.map(p=><article key={p.id} className="overflow-hidden rounded-2xl border border-stone-200/70 bg-white dark:border-white/10 dark:bg-[#17251b]">{p.image_url?<img src={imageSrc(p.image_url)} alt={p.title} className="h-40 w-full bg-stone-50 object-cover"/>:<div className="grid h-32 place-items-center bg-stone-50 text-4xl dark:bg-white/5">🌱</div>}<div className="flex items-center justify-between gap-3 p-4"><div><p className="font-bold">{p.title}</p><p className="mt-1 text-xs capitalize text-stone-500">{p.category} · {p.stock} {p.unit} available</p><b className="mt-2 inline-block">₹{p.price}</b></div><button onClick={()=>remove(p.id)} title="Remove listing" className="rounded-lg p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"><Trash2 size={17}/></button></div></article>)}{!items.length&&<div className="col-span-full rounded-2xl border border-dashed border-stone-300 p-10 text-center text-sm text-stone-500 dark:border-white/20">You haven't published any listings yet.</div>}</div></section>
 </div>
}
