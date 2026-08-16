import { Activity, CheckCircle, Clock, InfoCircle as InfoEmpty, WarningCircle } from 'iconoir-react';
import type { ActivityEventItem } from '../../types/events';
import { PageScaffold } from '../shared/PageScaffold';

export function ActivityPage({ events }: { events: ActivityEventItem[] }) {
  return (
    <PageScaffold eyebrow="Audit & evidence" title="Activity" description="Sanitized, authoritative events received during the current Desktop session.">
      <section className="surface section-card">
        <header className="section-header"><div><h2>Session timeline</h2><p>{events.length} event{events.length === 1 ? '' : 's'}</p></div><Activity width={21} height={21} aria-hidden /></header>
        {events.length === 0 ? <div className="large-empty"><InfoEmpty width={28} height={28} aria-hidden /><h3>No activity received</h3><p>Connect Core and begin authorized work. This timeline never simulates task, agent, tool, evidence, or approval events.</p></div> : <ol className="full-activity-list">{events.map((event) => { const Icon = event.status === 'failed' ? WarningCircle : event.status === 'completed' ? CheckCircle : Clock; return <li key={event.id}><span className={`activity-icon status-${event.status}`}><Icon width={16} height={16} aria-hidden /></span><div><strong>{event.title}</strong><span>{event.type}</span></div><time dateTime={event.timestampUtc}>{new Date(event.timestampUtc).toLocaleString()}</time></li>; })}</ol>}
      </section>
    </PageScaffold>
  );
}
