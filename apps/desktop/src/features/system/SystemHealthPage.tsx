import { CheckCircle, Database, InfoCircle as InfoEmpty, WarningTriangle, Wifi } from 'iconoir-react';
import type { AssistantModel, RuntimeConnectionState, ProviderStatus } from '../../types/events';
import { PageScaffold } from '../shared/PageScaffold';

interface SystemHealthPageProps { connection: RuntimeConnectionState; models: AssistantModel[]; eventCount: number; providerStatus: ProviderStatus | null; }

export function SystemHealthPage({ connection, models, eventCount, providerStatus }: SystemHealthPageProps) {
  const online = connection === 'online';
  return (
    <PageScaffold eyebrow="Operations" title="System health" description="Live signals available to the Desktop client. Unknown metrics remain unavailable.">
      <div className="health-grid">
        <article className="health-card surface"><span className={`health-icon status-${connection}`}>{online ? <CheckCircle width={20} height={20} aria-hidden /> : <WarningTriangle width={20} height={20} aria-hidden />}</span><div><small>Ophanim Core</small><strong>{connection}</strong><p>{online ? 'Authenticated event transport is available.' : 'Start the Desktop runtime to restore Core connectivity.'}</p></div></article>
        <article className="health-card surface"><span className="health-icon"><Database width={20} height={20} aria-hidden /></span><div><small>Configured models</small><strong>{models.length}</strong><p>Count returned by the authenticated model endpoint.</p></div></article>
        <article className="health-card surface"><span className="health-icon"><Wifi width={20} height={20} aria-hidden /></span><div><small>Session events</small><strong>{eventCount}</strong><p>Authorized events observed in this Desktop session.</p></div></article>
        {providerStatus && (
          <>
            <article className="health-card surface">
              <span className={`health-icon status-${providerStatus.lmstudio.status === 'available' ? 'online' : 'error'}`}>
                {providerStatus.lmstudio.status === 'available' ? <CheckCircle width={20} height={20} aria-hidden /> : <WarningTriangle width={20} height={20} aria-hidden />}
              </span>
              <div>
                <small>LM Studio</small>
                <strong>{providerStatus.lmstudio.status}</strong>
                <p>Local inference provider status.</p>
              </div>
            </article>
            <article className="health-card surface">
              <span className={`health-icon status-${providerStatus.anythingllm.status === 'available' ? 'online' : 'error'}`}>
                {providerStatus.anythingllm.status === 'available' ? <CheckCircle width={20} height={20} aria-hidden /> : <WarningTriangle width={20} height={20} aria-hidden />}
              </span>
              <div>
                <small>AnythingLLM</small>
                <strong>{providerStatus.anythingllm.status}</strong>
                <p>Local RAG / vector DB provider status.</p>
              </div>
            </article>
            {providerStatus.cloud_models.map(cm => (
              <article key={cm.provider} className="health-card surface">
                <span className={`health-icon status-${cm.status === 'available' ? 'online' : 'error'}`}>
                  {cm.status === 'available' ? <CheckCircle width={20} height={20} aria-hidden /> : <WarningTriangle width={20} height={20} aria-hidden />}
                </span>
                <div>
                  <small>Cloud: {cm.provider}</small>
                  <strong>{cm.status}</strong>
                  <p>{cm.models.length} models available.</p>
                </div>
              </article>
            ))}
          </>
        )}
      </div>
      <section className="surface section-card unavailable-metrics"><header className="section-header"><div><h2>Resource and service metrics</h2><p>CPU, memory, latency, queue depth, and success-rate telemetry are not exposed to Desktop yet.</p></div></header><div className="large-empty compact"><InfoEmpty width={24} height={24} aria-hidden /><h3>Metrics unavailable</h3><p>No synthetic charts or placeholder percentages are shown.</p></div></section>
    </PageScaffold>
  );
}
