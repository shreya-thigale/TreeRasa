import { useEffect, useRef, useState } from 'react';
import { Camera, CheckCircle2, ImagePlus, Leaf, ScanLine, ShieldAlert, Sprout, Upload, X } from 'lucide-react';
import { apiRequest } from '../api/client.js';
import Notice from '../components/Notice.jsx';

export default function ScanPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [part, setPart] = useState('leaf');
  const [analysisType, setAnalysisType] = useState('disease');
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [cameraError, setCameraError] = useState('');
  const [busy, setBusy] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const fileRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    apiRequest('/plants').then(setPlants).catch(() => { /* Plant linking is optional. */ });
    return stopCamera;
  }, []);

  useEffect(() => {
    if (cameraOpen && videoRef.current && streamRef.current) videoRef.current.srcObject = streamRef.current;
  }, [cameraOpen]);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function chooseFile(nextFile) {
    if (!nextFile) return;
    if (!nextFile.type.startsWith('image/')) {
      setError('Choose a valid image file.');
      return;
    }
    if (preview) URL.revokeObjectURL(preview);
    setFile(nextFile);
    setPreview(URL.createObjectURL(nextFile));
    setResult(null);
    setError('');
  }

  async function openCamera() {
    setCameraError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
      streamRef.current = stream;
      setCameraOpen(true);
    } catch {
      setCameraError('Camera access is unavailable. Check browser permissions or upload a photo instead.');
    }
  }

  function capturePhoto() {
    const video = videoRef.current;
    if (!video?.videoWidth) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) chooseFile(new File([blob], 'treerasa-camera-capture.jpg', { type: 'image/jpeg' }));
      setCameraOpen(false);
      stopCamera();
    }, 'image/jpeg', 0.92);
  }

  async function analyse(event) {
    event.preventDefault();
    if (!file) {
      setError('Upload or capture a plant image first.');
      return;
    }
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const body = new FormData();
      body.append('image', file);
      body.append('plant_part', part);
      body.append('analysis_type', analysisType);
      if (plantId) body.append('plant_id', plantId);
      setResult(await apiRequest('/scans', { method: 'POST', body }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  const scanStatus = result?.scan?.status;
  const resultNeedsReview = ['model_not_trained', 'unsupported_part', 'low_confidence'].includes(scanStatus);

  return (
    <div className="page-stack">
      <div className="page-intro"><span className="eyebrow">COMPUTER VISION WORKSPACE</span><h2>Look closer. Care smarter.</h2><p>Upload a photo or use your camera. Disease and insect-pest classifiers are separate models and each must be trained before predictions are enabled.</p></div>
      {error && <Notice type="error">{error}</Notice>}{cameraError && <Notice type="error">{cameraError}</Notice>}

      <div className="scan-layout">
        <section className="panel scan-panel">
          <div className="panel-heading"><div className="panel-icon tone-mint"><ScanLine size={20} /></div><div><h3>Plant image</h3><p>Use a clear, well-lit image for a more useful scan.</p></div></div>
          {cameraOpen ? <div className="camera-stage"><video ref={videoRef} autoPlay playsInline muted /><div className="button-row"><button type="button" className="button button--primary" onClick={capturePhoto}><Camera size={17} /> Capture photo</button><button type="button" className="button button--secondary" onClick={() => { setCameraOpen(false); stopCamera(); }}>Cancel</button></div></div>
            : preview ? <div className="image-preview"><img src={preview} alt="Plant selected for analysis" /><button type="button" className="remove-image" onClick={() => { URL.revokeObjectURL(preview); setFile(null); setPreview(''); setResult(null); }} aria-label="Remove image"><X size={17} /></button><div className="image-preview-label"><CheckCircle2 size={15} /> Image ready for analysis</div></div>
              : <button type="button" className="upload-dropzone" onClick={() => fileRef.current?.click()}><span className="upload-icon"><ImagePlus size={26} /></span><b>Choose a plant image</b><span>Browse files from your device</span><small>JPG, PNG or WebP · Up to 12 MB</small></button>}
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(event) => chooseFile(event.target.files?.[0])} />
          {!cameraOpen && <div className="button-row upload-buttons"><button type="button" className="button button--secondary" onClick={() => fileRef.current?.click()}><Upload size={16} /> Upload image</button><button type="button" className="button button--secondary" onClick={openCamera}><Camera size={16} /> Use camera</button></div>}

          <form className="scan-form" onSubmit={analyse}>
            <div className="form-grid">
              <label>Analysis type<select value={analysisType} onChange={(event) => setAnalysisType(event.target.value)}><option value="disease">Plant disease</option><option value="pest">Insect pest</option></select></label>
              <label>Plant part<select value={part} onChange={(event) => setPart(event.target.value)}><option value="leaf">Leaf</option><option value="stem">Stem</option><option value="fruit">Fruit</option><option value="flower">Flower</option><option value="root">Root</option><option value="whole_plant">Whole plant</option><option value="other">Other</option></select></label>
              <label className="form-full">Link a plant record<select value={plantId} onChange={(event) => setPlantId(event.target.value)}><option value="">No linked plant</option>{plants.map((plant) => <option key={plant.id} value={plant.id}>{plant.name}</option>)}</select></label>
            </div>
            <button className="button button--primary button--wide" disabled={busy || !file}>{busy ? 'Saving and checking model…' : <><ScanLine size={17} /> Analyse plant image</>}</button>
          </form>
        </section>

        <aside className="scan-side">
          <section className="panel tips-panel"><span className="eyebrow">BETTER SCANS</span><h3>Help your plant tell its story.</h3><ul className="tip-list"><li><span>01</span><div><b>Find natural light</b><p>Avoid strong shadows and blurry photos.</p></div></li><li><span>02</span><div><b>Focus on the symptom</b><p>Include the affected area and some healthy tissue.</p></div></li><li><span>03</span><div><b>Capture useful context</b><p>Photograph both sides of the leaf when possible.</p></div></li></ul></section>
          <section className="panel privacy-panel"><ShieldAlert size={20} /><div><b>AI results need confirmation</b><p>A whole-image classifier does not outline diseased pixels and cannot diagnose plant parts it was not trained on.</p></div></section>
        </aside>
      </div>

      {result && <section className="panel scan-result">
        <div className="result-heading"><div className="panel-icon tone-mint"><Leaf size={20} /></div><div><span className="eyebrow">SCAN SAVED</span><h3>Plant analysis result</h3></div><span className="result-id">Scan #{result.scan.id}</span></div>
        {resultNeedsReview ? <Notice><b>{result.guidance.title}</b> {result.guidance.summary}</Notice> : <><div className="prediction-card"><span className="eyebrow">PREDICTED {result.scan.analysis_type === 'pest' ? 'PEST CLASS' : 'DISEASE CLASS'}</span><h2>{result.guidance.title}</h2><div className="confidence-track"><span style={{ width: `${Math.max(0, Math.min(100, (result.scan.confidence || 0) * 100))}%` }} /></div><small>Model confidence: {((result.scan.confidence || 0) * 100).toFixed(1)}% · not diagnostic certainty</small></div><p>{result.guidance.summary}</p></>}
        <div className="guidance-block"><h4><Sprout size={17} /> Suggested next steps</h4><ul>{result.guidance.actions.map((action, index) => <li key={index}>{action}</li>)}</ul><p className="safety-note"><ShieldAlert size={16} />{result.guidance.safety_note}</p></div>
      </section>}
    </div>
  );
}
