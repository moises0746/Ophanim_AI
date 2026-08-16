import { CheckCircle, Database, InfoCircle as InfoEmpty, WarningTriangle, Wifi } from 'iconoir-react';
import type { AssistantModel, RuntimeConnectionState } from '../../types/events';
import { PageScaffold } from '../shared/PageScaffold';

interface SystemHealthPageProps { connection: RuntimeConnectionState; models: AssistantModel[]; eventCount: number; }

export function SystemHealthPage({ connection, models, eventCount }: SystemHealthPageProps) {
  const online = connection === 'online';
  return (
    <PageScaffold eyebrow="Operations" title="System health" description="Live signals available to the Desktop client. Unknown metrics remain unavailable.">
      <div className="health-grid">
        <article className="health-card surface"><span className={`health-icon status-${connection}`}>{online ? <CheckCircle width={20} height={20} aria-hidden /> : <WarningTriangle width={20} height={20} aria-hidden />}</span><div><small>Ophanim Core</small><strong>{connection}</strong><p>{online ? 'Authenticated event transport is available.' : 'Start the Desktop runtime to restore Core connectivity.'}</p></div></article>
        <article className="health-card surface"><span className="health-icon"><Database width={20} height={20} aria-hidden /></span><div><small>Configured models</small><strong>{models.length}</strong><p>Count returned by the authenticated model endpoint.</p></div></article>
        <article className="health-card surface"><span className="health-icon"><Wifi width={20} height={20} aria-hidden /></span><div><small>Session events</small><strong>{eventCount}</strong><p>Authorized events observed in this Desktop session.</p></div></article>
      </div>
      <section className="surface section-card unavailable-metrics"><header className="section-header"><div><h2>Resource and service metrics</h2><p>CPU, memory, latency, queue depth, and success-rate telemetry are not exposed to Desktop yet.</p></div></header><div className="large-empty compact"><InfoEmpty width={24} height={24} aria-hidden /><h3>Metrics unavailable</h3><p>No synthetic charts or placeholder percentages are shown.</p></div></section>
    </PageScaffold>
  );
}
