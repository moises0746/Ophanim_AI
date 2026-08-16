import { InfoCircle as InfoEmpty, ShieldCheck, WarningTriangle } from 'iconoir-react';
import type { ApprovalRequest } from '../../types/events';
import { PageScaffold } from '../shared/PageScaffold';

interface ApprovalsPageProps { request: ApprovalRequest | null; onDismiss: (approvalId: string) => void; }

export function ApprovalsPage({ request, onDismiss }: ApprovalsPageProps) {
  return (
    <PageScaffold eyebrow="Attention" title="Approvals" description="Human decisions projected from authoritative Core events.">
      <section className="surface section-card">
        <header className="section-header"><div><h2>Needs attention</h2><p>{request ? '1 active request' : 'No active requests'}</p></div><ShieldCheck width={21} height={21} aria-hidden /></header>
        {!request ? <div className="large-empty"><InfoEmpty width={28} height={28} aria-hidden /><h3>No approvals pending</h3><p>Approval requests appear only after an authorized Core event. The Desktop cannot grant authority by itself.</p></div> : <article className="approval-card"><WarningTriangle width={22} height={22} aria-hidden /><div><span>{request.riskLevel} risk</span><h3>{request.description}</h3><p>{request.toolName} · task {request.taskId}</p></div><button type="button" className="quiet-button" onClick={() => onDismiss(request.approvalId)}>Review in modal</button></article>}
      </section>
    </PageScaffold>
  );
}
