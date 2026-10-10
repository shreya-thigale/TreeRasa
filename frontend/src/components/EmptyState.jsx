import { Sprout } from 'lucide-react';
export default function EmptyState({ title, description, action }) {
  return <div className="empty-state"><span><Sprout size={24} /></span><h3>{title}</h3><p>{description}</p>{action}</div>;
}
