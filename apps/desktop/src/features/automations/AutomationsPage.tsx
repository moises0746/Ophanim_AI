import { Flash, InfoCircle as InfoEmpty, Lock } from 'iconoir-react';
import { PageScaffold } from '../shared/PageScaffold';

export function AutomationsPage() {
  return (
    <PageScaffold eyebrow="Automations" title="Workflow Builder" description="Design surface reserved for governed, typed workflows.">
      <section className="surface workflow-empty">
        <div className="workflow-canvas" aria-hidden><span><Flash width={28} height={28} /></span></div>
        <div><span className="availability-badge"><InfoEmpty width={15} height={15} aria-hidden /> Not connected</span><h2>Workflow editing is unavailable</h2><p>The runtime does not yet expose workflow authoring, validation, persistence, or execution contracts. This screen intentionally provides no demo execution path.</p><div className="guardrail-note"><Lock width={18} height={18} aria-hidden /><span>Future workflows must remain typed, policy checked, approval-aware, cancellable, and auditable.</span></div></div>
      </section>
    </PageScaffold>
  );
}
