import { useEffect, useRef, useState } from 'react'
import {
  ScanLine, UploadCloud, Leaf, Clock3, ImagePlus, CheckCircle2, Camera,
  AlertTriangle, Activity, Sprout, RefreshCw, Trash2
} from 'lucide-react'
import { scansApi } from '../../api/scans.api'
import { apiBlob } from '../../api/client'

const MAX_FILE_SIZE = 8 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const CROPS = [
  { value: 'Pomegranate', label: 'Pomegranate', detail: 'Dedicated pomegranate disease model' },
  { value: 'Sugarcane', label: 'Sugarcane', detail: 'Dedicated sugarcane disease model' },
  { value: 'Cotton', label: 'Cotton', detail: 'Dedicated cotton disease model' },
  { value: 'Wheat', label: 'Wheat', detail: 'Dedicated wheat disease model' },
  { value: 'Other / PlantVillage', label: 'Other supported crops', detail: 'PlantVillage model: tomato, potato, grape, apple, strawberry and more' },
]

function formatStatus(status) {
  return (status || 'unknown').replaceAll('_', ' ')
}

export default function ScanPage() {
  const cameraInputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [crop, setCrop] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [previewUrl, setPreviewUrl] = useState('')
  const [historyImages, setHistoryImages] = useState({})

  async function loadHistory() {
    try {
      const scans = await scansApi.mine()
      setHistory(scans)
      const imageEntries = await Promise.all(scans.map(async (scan) => {
        if (!scan.image_url) return [scan.id, '']
        try {
          const imagePath = scan.image_url.startsWith('/api') ? scan.image_url.slice(4) : scan.image_url
          const blob = await apiBlob(imagePath)
          return [scan.id, URL.createObjectURL(blob)]
        } catch {
          return [scan.id, '']
        }
      }))
      setHistoryImages((previous) => {
        Object.values(previous).forEach((url) => { if (url) URL.revokeObjectURL(url) })
        return Object.fromEntries(imageEntries)
      })
      setHistoryError('')
    } catch (err) {
      setHistoryError(err.message || 'Could not load scan history.')
    }
  }

  useEffect(() => {
    loadHistory()
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      Object.values(historyImages).forEach((url) => { if (url) URL.revokeObjectURL(url) })
    }
  }, [])

  function selectFile(event) {
    const selected = event.target.files?.[0] || null
    event.target.value = ''
    setError('')
    setResult(null)
    if (!selected) return

    if (!ALLOWED_TYPES.includes(selected.type)) {
      setError('Please select a JPG, PNG or WEBP image.')
      return
    }
    if (selected.size > MAX_FILE_SIZE) {
      setError('The image must be smaller than 8 MB.')
      return
    }

    setFile(selected)
    setPreviewUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous)
      return URL.createObjectURL(selected)
    })
  }

  function clearImage() {
    setFile(null)
    setResult(null)
    setPreviewUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous)
      return ''
    })
  }

  async function deleteOneScan(scanId) {
    if (!window.confirm('Delete this scan and its saved image?')) return
    try { await scansApi.remove(scanId); await loadHistory() }
    catch (err) { setHistoryError(err.message || 'Could not delete this scan.') }
  }

  async function deleteAllScans() {
    if (!window.confirm('Delete all your scan history and saved images? This cannot be undone.')) return
    try { await scansApi.removeAll(); setHistory([]); setHistoryImages((previous) => { Object.values(previous).forEach((url) => { if (url) URL.revokeObjectURL(url) }); return {} }); setResult(null) }
    catch (err) { setHistoryError(err.message || 'Could not delete scan history.') }
  }

  async function submit(event) {
    event.preventDefault()
    if (!file || !crop || busy) return

    setBusy(true)
    setError('')
    setResult(null)
    try {
      const data = await scansApi.create(file, crop)
      setResult(data)
      await loadHistory()
    } catch (err) {
      setError(err.message || 'The scan failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const selectedCrop = CROPS.find((item) => item.value === crop)
  const isUncertain = result?.status === 'low_confidence' || result?.status === 'inference_error'
  const confidence = result?.confidence == null ? null : Math.max(0, Math.min(100, result.confidence * 100))

  return (
    <div className="space-y-7 pb-8">
      <header className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#123f2b] via-[#1b6543] to-[#2b8053] px-6 py-7 text-white shadow-sm sm:px-8">
        <div className="pointer-events-none absolute -right-10 -top-16 h-56 w-56 rounded-full border-[28px] border-white/5" />
        <div className="relative flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold tracking-wide text-emerald-50">
              <Sprout size={14} /> TREERASA PLANT INTELLIGENCE
            </div>
            <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">Plant health scan</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-emerald-50/85">
              Upload a clear crop image and get an AI-assisted disease prediction with practical next steps.
            </p>
          </div>
          <div className="hidden h-20 w-20 shrink-0 items-center justify-center rounded-2xl border border-white/20 bg-white/10 sm:flex">
            <Leaf size={42} strokeWidth={1.5} />
          </div>
        </div>
      </header>

      <div className="grid items-start gap-5 xl:grid-cols-[1.05fr_.95fr]">
        <form onSubmit={submit} className="rounded-2xl border border-stone-200/70 bg-white p-5 shadow-sm sm:p-6 dark:border-white/10 dark:bg-[#17251b]">
          <div className="mb-6 flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-50 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200">
              <ImagePlus size={21} />
            </span>
            <div>
              <h2 className="font-display text-lg font-extrabold">Start a new scan</h2>
              <p className="text-sm text-stone-500">JPG, PNG or WEBP · maximum 8 MB</p>
            </div>
          </div>

          <label htmlFor="crop" className="block text-sm font-bold">1. Choose your crop</label>
          <select
            id="crop"
            required
            value={crop}
            onChange={(event) => { setCrop(event.target.value); setResult(null) }}
            className="field mt-2"
          >
            <option value="" disabled>Select the crop in your photo</option>
            {CROPS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
          {selectedCrop && (
            <p className="mt-2 flex items-start gap-2 text-xs leading-5 text-stone-500">
              <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-emerald-700" />
              {selectedCrop.detail}
            </p>
          )}

          <div className="mt-6 flex items-center justify-between">
            <label className="block text-sm font-bold">2. Add a plant photo</label>
            {file && <button type="button" onClick={clearImage} className="text-xs font-semibold text-rose-600 hover:underline">Remove photo</button>}
          </div>
          <label className="mt-2 flex min-h-64 cursor-pointer flex-col items-center justify-center overflow-hidden rounded-2xl border-2 border-dashed border-emerald-300 bg-emerald-50/40 p-4 text-center transition hover:border-emerald-600 hover:bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/20">
            {previewUrl ? (
              <>
                <img src={previewUrl} alt="Selected plant preview" className="max-h-64 w-full rounded-xl object-contain" />
                <span className="mt-3 max-w-full break-all text-sm font-bold text-stone-800 dark:text-stone-100">{file?.name}</span>
                <span className="mt-1 text-xs text-stone-500">Click to choose a different image</span>
              </>
            ) : (
              <>
                <span className="mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-white text-emerald-800 shadow-sm dark:bg-white/10 dark:text-emerald-200"><UploadCloud size={27} /></span>
                <span className="font-bold text-stone-800 dark:text-stone-100">Choose an image to upload</span>
                <span className="mt-1 text-xs text-stone-500">Use a focused, well-lit photo of the affected leaf</span>
                <span className="mt-4 rounded-lg border border-emerald-800/20 bg-white px-4 py-2 text-xs font-bold text-emerald-900 dark:bg-white/10 dark:text-emerald-100">Browse files</span>
              </>
            )}
            <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={selectFile} />
          </label>
          <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={selectFile} />
          <button type="button" onClick={() => cameraInputRef.current?.click()} className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-700/30 bg-white px-4 py-3 text-sm font-bold text-emerald-900 transition hover:bg-emerald-50 dark:border-emerald-700 dark:bg-white/5 dark:text-emerald-100 dark:hover:bg-emerald-950/30">
            <Camera size={18}/> Take photo with camera
          </button>

          {error && <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-200">{error}</p>}

          <button
            type="submit"
            disabled={!file || !crop || busy}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-800 px-4 py-3.5 font-bold text-white shadow-sm transition hover:bg-emerald-900 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? <><RefreshCw size={17} className="animate-spin" /> Analyzing your plant…</> : <><ScanLine size={18} /> Analyze and save scan</>}
          </button>
          <p className="mt-3 text-center text-xs text-stone-500">Your uploaded image is saved in your PostgreSQL database.</p>
        </form>

        <section className="rounded-2xl border border-stone-200/70 bg-white p-5 shadow-sm sm:p-6 dark:border-white/10 dark:bg-[#17251b]">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200"><Activity size={20} /></span>
              <div>
                <h2 className="font-display text-lg font-extrabold">Analysis report</h2>
                <p className="text-xs text-stone-500">Your latest scan result</p>
              </div>
            </div>
            {result && <span className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${isUncertain ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>{formatStatus(result.status)}</span>}
          </div>

          {busy ? (
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <span className="grid h-16 w-16 animate-pulse place-items-center rounded-2xl bg-emerald-50 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200"><ScanLine size={32} /></span>
              <p className="mt-5 font-bold">Analyzing your plant image</p>
              <p className="mt-1 text-sm text-stone-500">Matching the image with the selected crop model…</p>
            </div>
          ) : result ? (
            <div className="mt-6 space-y-5">
              <div className="rounded-2xl bg-stone-50 p-4 dark:bg-white/5">
                <p className="text-xs font-bold uppercase tracking-wider text-stone-500">Predicted condition</p>
                <h3 className="mt-2 break-words text-2xl font-extrabold text-stone-900 dark:text-white">{result.predicted_disease}</h3>
                <p className="mt-2 text-sm text-stone-500">Crop model: {selectedCrop?.label || result.crop_name || 'Not specified'}</p>
              </div>

              {confidence !== null && (
                <div>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-semibold">Model confidence</span>
                    <span className="font-extrabold tabular-nums">{confidence.toFixed(1)}%</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-stone-100 dark:bg-white/10">
                    <div className="h-full rounded-full bg-emerald-600 transition-all" style={{ width: `${confidence}%` }} />
                  </div>
                  <p className="mt-2 text-xs leading-5 text-stone-500">Confidence is the model's score, not a verified measure of diagnostic accuracy.</p>
                </div>
              )}

              <div className="rounded-2xl border border-emerald-900/10 bg-emerald-50/60 p-4 dark:border-emerald-100/10 dark:bg-emerald-950/20">
                <h4 className="flex items-center gap-2 text-sm font-extrabold text-emerald-950 dark:text-emerald-100"><Leaf size={16} /> Management guidance</h4>
                <p className="mt-2 whitespace-pre-line text-sm leading-6 text-stone-700 dark:text-stone-300">{result.recommendations || 'No recommendations are available for this result.'}</p>
              </div>

              {isUncertain ? (
                <div className="flex gap-2 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800 dark:bg-amber-950/30 dark:text-amber-200"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> The model could not make a reliable prediction. Try a clearer photo and confirm the crop selection.</div>
              ) : (
                <div className="flex gap-2 rounded-xl bg-sky-50 p-3 text-xs leading-5 text-sky-800 dark:bg-sky-950/30 dark:text-sky-200"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> AI-assisted result only. Confirm the diagnosis with a local agricultural expert before applying treatment.</div>
              )}
            </div>
          ) : (
            <div className="flex min-h-80 flex-col items-center justify-center rounded-2xl border border-dashed border-stone-200 bg-stone-50/70 px-6 text-center dark:border-white/10 dark:bg-white/[.03]">
              <span className="grid h-16 w-16 place-items-center rounded-2xl bg-white text-stone-400 shadow-sm dark:bg-white/10"><ScanLine size={30} /></span>
              <h3 className="mt-4 font-bold">Your report will appear here</h3>
              <p className="mt-1 max-w-xs text-sm leading-6 text-stone-500">Choose the correct crop, upload a clear photo and start your scan to see the AI analysis.</p>
            </div>
          )}
        </section>
      </div>

      <section className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">Your activity</p>
            <h2 className="mt-1 font-display text-xl font-extrabold">Recent scan history</h2>
          </div>
          <div className="flex items-center gap-3"><span className="text-xs text-stone-500">{history.length} saved {history.length === 1 ? 'scan' : 'scans'}</span>{history.length > 0 && <button type="button" onClick={deleteAllScans} className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 px-3 py-2 text-xs font-bold text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300"><Trash2 size={14}/> Delete all</button>}</div>
        </div>

        {historyError && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{historyError}</p>}
        {history.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {history.map((scan) => (
              <article key={scan.id} className="flex min-w-0 flex-wrap items-center gap-4 rounded-2xl border border-stone-200/70 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-[#17251b]">
                {historyImages[scan.id] ? <img src={historyImages[scan.id]} alt={scan.crop_name || 'Scanned plant'} className="h-20 w-20 shrink-0 rounded-xl bg-stone-100 object-cover" /> : <span className="grid h-20 w-20 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200"><Clock3 size={24} /></span>}
                <div className="min-w-0 flex-1">
                  <p className="truncate font-bold">{scan.predicted_disease}</p>
                  <p className="mt-1 text-xs capitalize text-stone-500">{scan.crop_name || 'Crop not specified'}</p>
                  <p className="mt-1 text-xs text-stone-400">{new Date(scan.created_at).toLocaleString()}</p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-2"><span className={`rounded-full px-2.5 py-1 text-[10px] font-bold capitalize ${scan.status === 'success' ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : 'bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200'}`}>{formatStatus(scan.status)}</span><button type="button" onClick={() => deleteOneScan(scan.id)} aria-label="Delete scan" className="rounded-lg p-2 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30"><Trash2 size={15}/></button></div>
                <details className="basis-full border-t border-stone-100 pt-2 text-sm dark:border-white/10"><summary className="cursor-pointer font-semibold text-emerald-800 dark:text-emerald-200">View diagnosis & recommendations</summary><div className="mt-3 space-y-2 text-stone-600 dark:text-stone-300"><p><b>Diagnosis:</b> {scan.predicted_disease}</p><p><b>Confidence:</b> {scan.confidence == null ? 'Not available' : `${(scan.confidence * 100).toFixed(1)}%`}</p><p className="whitespace-pre-line"><b>Recommendations:</b> {scan.recommendations || 'No recommendations were saved for this scan.'}</p><p className="text-xs text-stone-400">AI-assisted result; confirm with an agricultural expert before treatment.</p></div></details>
              </article>
            ))}
          </div>
        ) : (
          !historyError && <div className="rounded-2xl border border-dashed border-stone-300 p-8 text-center text-sm text-stone-500 dark:border-white/20">No scans saved yet. Your completed scans will appear here.</div>
        )}
      </section>
    </div>
  )
}
