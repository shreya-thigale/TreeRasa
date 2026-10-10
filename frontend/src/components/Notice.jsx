import { AlertCircle, CheckCircle2 } from 'lucide-react';
export default function Notice({ type = 'info', children }) {
  const Icon = type === 'success' ? CheckCircle2 : AlertCircle;
  return <div className={`notice notice--${type}`} role="status"><Icon size={18} /><div>{children}</div></div>;
}
