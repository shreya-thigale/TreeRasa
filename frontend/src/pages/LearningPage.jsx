import { BookOpen, Bug, ExternalLink, FlaskConical, Leaf, ShieldCheck, Sprout } from 'lucide-react';

// These are links to real public learning resources, not invented course records or completion data.
const resources = [
  { icon: Bug, title: 'Integrated Pest Management', copy: 'Monitor, identify, prevent and choose controls proportionate to the problem.', tag: 'Pest management', url: 'https://www.fao.org/pest-and-pesticide-management/ipm/integrated-pest-management/en/' },
  { icon: Leaf, title: 'Plant health and biodiversity', copy: 'Learn why diverse, resilient ecosystems matter for sustainable agriculture.', tag: 'Biodiversity', url: 'https://sdgs.un.org/goals/goal15' },
  { icon: FlaskConical, title: 'Soil health fundamentals', copy: 'Understand how soil testing supports nutrient and soil-condition decisions.', tag: 'Soil care', url: 'https://www.fao.org/soils-portal/en/' },
  { icon: ShieldCheck, title: 'Pesticide safety', copy: 'Read official guidance and follow locally applicable product labels.', tag: 'Safety', url: 'https://www.fao.org/pest-and-pesticide-management/en/' },
];

export default function LearningPage() {
  return (
    <div className="page-stack">
      <div className="page-intro"><span className="eyebrow">LEARN & GROW</span><h2>Knowledge is part of plant care.</h2><p>Curated public resources to help you build sound habits. This page links to external material rather than inventing course completions.</p></div>
      <div className="learning-banner"><div><BookOpen size={24} /></div><section><span className="eyebrow">A GOOD PLACE TO START</span><h3>Observe first. Identify carefully. Act responsibly.</h3><p>Healthy growing begins with monitoring, prevention and thoughtful use of resources.</p></section></div>
      <div className="learning-grid">{resources.map((resource) => {
        const Icon = resource.icon;
        return <article className="learning-card" key={resource.title}><div className="learning-card-icon"><Icon size={21} /></div><span className="resource-tag">{resource.tag}</span><h3>{resource.title}</h3><p>{resource.copy}</p><a href={resource.url} target="_blank" rel="noreferrer">Read resource <ExternalLink size={14} /></a></article>;
      })}</div>
      <p className="disclaimer-line"><Sprout size={14} /> Learning resources are external and may be updated by their publishers.</p>
    </div>
  );
}
