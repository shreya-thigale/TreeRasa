
import { useEffect, useState } from 'react'
import { ScanLine, UploadCloud, Leaf, Clock3 } from 'lucide-react'
import { scansApi } from '../../api/scans.api'

const MAX_FILE_SIZE = 8 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export default function ScanPage() {
  const [file, setFile] = useState(null)
  const [crop, setCrop] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')

  async function loadHistory() {
    try {
      setHistory(await scansApi.mine())
      setHistoryError('')
    } catch (err) {
      setHistoryError(err.message || 'Could not load scan history.')
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  function selectFile(event) {
    const selected = event.target.files?.[0] || null
    event.target.value = ''

    setError('')
    setResult(null)

    if (!selected) return

    if (!ALLOWED_TYPES.includes(selected.type)) {
      setFile(null)
      setError('Please select a JPG, PNG or WEBP image.')
      return
    }

    if (selected.size > MAX_FILE_SIZE) {
      setFile(null)
      setError('The image must be smaller than 8 MB.')
      return
    }

    setFile(selected)
  }

  async function submit(event) {
    event.preventDefault()
    if (!file || busy) return

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

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-bold uppercase tracking-[.18em] text-forest-700 dark:text-forest-200">
          Plant health
        </p>
        <h1 className="mt-2 font-display text-3xl font-extrabold">
          AI plant scan
        </h1>
        <p className="mt-2 text-sm text-stone-500">
          Upload a clear plant image to receive a prediction and management guidance.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_.8fr]">
        <form
          onSubmit={submit}
          className="rounded-2xl border border-stone-200/70 bg-white p-6 dark:border-white/10 dark:bg-[#17251b]"
        >
          <div className="mb-5 flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-forest-50 text-forest-700 dark:bg-forest-900/50 dark:text-forest-100">
              <ScanLine />
            </span>
            <div>
              <h2 className="font-display text-lg font-extrabold">
                Start a new scan
              </h2>
              <p className="text-sm text-stone-500">
                JPG, PNG or WEBP · max 8 MB
              </p>
            </div>
          </div>

          <label htmlFor="crop" className="block text-sm font-semibold">
            Select crop
          </label>
          <select
            id="crop"
            value={crop}
            onChange={(event) => {
              setCrop(event.target.value)
              setResult(null)
            }}
            className="field mt-2"
          >
            <option value="Pomegranate">Pomegranate</option>
            <option value="Sugarcane">Sugarcane</option>
            <option value="Cotton">Cotton</option>
            <option value="Wheat">Wheat</option>
            <option value="">Other</option>
          </select>

          <label className="mt-5 flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-stone-300 bg-stone-50/70 p-6 text-center hover:border-forest-500 dark:border-white/20 dark:bg-white/5">
            <UploadCloud
              className="mb-3 text-forest-700 dark:text-forest-200"
              size={32}
            />
            <span className="break-all font-bold">
              {file ? file.name : 'Choose a plant image'}
            </span>
            <span className="mt-1 text-xs text-stone-500">
              Use a clear, well-lit photo of a leaf
            </span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="sr-only"
              onChange={selectFile}
            />
          </label>

          {error && (
            <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!file || busy}
            className="mt-5 w-full rounded-xl bg-forest-700 px-4 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? 'Analyzing image…' : 'Analyze and save scan'}
          </button>
        </form>

        <div className="rounded-2xl border border-stone-200/70 bg-white p-6 dark:border-white/10 dark:bg-[#17251b]">
          <div className="flex items-center gap-3">
            <Leaf className="text-forest-700 dark:text-forest-200" />
            <h2 className="font-display text-lg font-extrabold">
              Scan result
            </h2>
          </div>

          {result ? (
            <div className="mt-5 space-y-4">
              <span className="inline-flex rounded-full bg-forest-50 px-3 py-1 text-xs font-bold capitalize text-forest-700 dark:bg-forest-900/50 dark:text-forest-100">
                {(result.status || 'unknown').replaceAll('_', ' ')}
              </span>

              <h3 className="break-words text-2xl font-extrabold">
                {result.predicted_disease}
              </h3>

              <p className="text-sm text-stone-500">
                Selected model: {result.crop_name || crop || 'PlantVillage'}
              </p>

              {result.confidence != null && (
                <p className="text-sm text-stone-500">
                  Model confidence: {(result.confidence * 100).toFixed(1)}%
                </p>
              )}

              <div className="rounded-xl bg-stone-50 p-4 dark:bg-white/5">
                <p className="text-sm font-bold">
                  Fertilizer and management guidance
                </p>
                <p className="mt-2 whitespace-pre-line text-sm leading-6 text-stone-600 dark:text-stone-300">
                  {result.recommendations || result.fertilizer || 'No guidance available.'}
                </p>
              </div>

              <p className="text-xs leading-5 text-amber-700 dark:text-amber-200">
                AI predictions are not confirmed diagnoses. Confirm with an agricultural expert before applying fertilizer or treatment.
              </p>
            </div>
          ) : (
            <div className="mt-12 text-center text-sm text-stone-500">
              <ScanLine className="mx-auto mb-3 opacity-40" size={36} />
              Your scan result will appear here.
            </div>
          )}
        </div>
      </div>

      <section>
        <h2 className="font-display text-xl font-extrabold">Scan history</h2>

        {historyError && (
          <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {historyError}
          </p>
        )}

        <div className="mt-4 space-y-3">
          {history.map((scan) => (
            <div
              key={scan.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200/70 bg-white p-4 dark:border-white/10 dark:bg-[#17251b]"
            >
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-forest-50 text-forest-700 dark:bg-forest-900/50 dark:text-forest-100">
                  <Clock3 size={18} />
                </span>
                <div>
                  <p className="font-bold">{scan.predicted_disease}</p>
                  <p className="text-xs text-stone-500">
                    {scan.crop_name || 'Crop not specified'} ·{' '}
                    {new Date(scan.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold capitalize dark:bg-white/10">
                {(scan.status || 'unknown').replaceAll('_', ' ')}
              </span>
            </div>
          ))}

          {!history.length && !historyError && (
            <p className="rounded-xl border border-dashed border-stone-300 p-6 text-center text-sm text-stone-500 dark:border-white/20">
              No scans saved yet.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
