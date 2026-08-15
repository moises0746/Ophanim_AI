import { ArrowRight, Book, CheckCircle, Database, Flash, Refresh, WarningTriangle } from 'iconoir-react';
import { Link } from 'react-router-dom';
import { ConversationPanel } from '../../components/ConversationPanel';
import { PromptBar } from '../../components/PromptBar';
import type { AssistantWorkspaceState } from '../../hooks/useAssistantWorkspace';
import { ContextPanel } from './ContextPanel';
import { OphanimAssistantVisual, assistantStatePresentation } from './OphanimAssistantVisual';

interface AssistantPageProps {
  workspace: AssistantWorkspaceState;
}

export function AssistantPage({ workspace }: AssistantPageProps) {
  const presentation = assistantStatePresentation[workspace.assistantState];
  const promptDisabled = workspace.sending || workspace.connection !== 'online' || !workspace.selectedModel;
  const disabledReason = workspace.connection !== 'online'
    ? 'Connect the Desktop runtime to message Ophanim…'
    : !workspace.selectedModel
      ? 'Configure a model to message Ophanim…'
      : undefined;

  return (
    <div className="assistant-page">
      <section className="assistant-heading">
        <div>
          <span className="eyebrow">AI coworker</span>
          <h1>Welcome back</h1>
          <p>Delegate a goal, inspect current work, and verify the evidence behind every result.</p>
        </div>
        <div className={`state-pill state-${workspace.assistantState}`}>
          <span aria-hidden />
          <strong>{presentation.label}</strong>
          <small>{workspace.connection === 'online' ? 'Core connected' : 'Core unavailable'}</small>
        </div>
      </section>

      <div className="assistant-grid">
        <section className="assistant-main surface" aria-label="Ophanim Assistant workspace">
          <div className="assistant-presence-row">
            <OphanimAssistantVisual state={workspace.assistantState} statusText={workspace.statusText} />
            <div className="presence-summary">
              <span className="eyebrow">Current state</span>
              <h2>{presentation.label}</h2>
              <p>{workspace.statusText}</p>
              <div className="presence-meta">
                <span><Database width={15} height={15} aria-hidden />{workspace.selectedModel?.display_name ?? 'No model configured'}</span>
                <span><CheckCircle width={15} height={15} aria-hidden />{workspace.events.length} verified event{workspace.events.length === 1 ? '' : 's'}</span>
              </div>
            </div>
            <button type="button" className="quiet-button" onClick={workspace.requestStop} disabled={workspace.connection !== 'online'}>
              <span className="stop-square" aria-hidden /> Stop
            </button>
          </div>

          <ConversationPanel messages={workspace.conversation} />

          {workspace.conversation.length === 0 && (
            <div className="suggestion-row" aria-label="Suggested prompts">
              <button type="button" disabled={promptDisabled} onClick={() => void workspace.sendPrompt('Summarize the current workspace status and known limitations.')}>Summarize workspace</button>
              <button type="button" disabled={promptDisabled} onClick={() => void workspace.sendPrompt('What can you help me with using the currently configured capabilities?')}>Show capabilities</button>
              <Link to="/system-health">Check runtime health <ArrowRight width={14} height={14} aria-hidden /></Link>
            </div>
          )}

          <PromptBar
            onSend={(text) => void workspace.sendPrompt(text)}
            disabled={promptDisabled}
            busy={workspace.sending}
            disabledReason={disabledReason}
          />
        </section>

        <ContextPanel events={workspace.events} citations={workspace.citations} />
      </div>

      <section className="workspace-overview" aria-label="Workspace overview">
        <article className="overview-card surface">
          <header><div><Book width={18} height={18} aria-hidden /><strong>Knowledge Vault</strong></div><Link to="/knowledge">Open <ArrowRight width={14} height={14} aria-hidden /></Link></header>
          <div className="overview-empty">
            <span>{workspace.citations.length}</span>
            <div><strong>verified source{workspace.citations.length === 1 ? '' : 's'}</strong><small>No source is implied until Core returns a citation.</small></div>
          </div>
        </article>

        <article className="overview-card surface">
          <header><div><Flash width={18} height={18} aria-hidden /><strong>Workflow</strong></div><Link to="/automations">Inspect <ArrowRight width={14} height={14} aria-hidden /></Link></header>
          <div className="availability-row"><WarningTriangle width={20} height={20} aria-hidden /><div><strong>Builder unavailable</strong><small>Workflow editing and execution are not connected in this release.</small></div></div>
        </article>

        <article className="overview-card surface">
          <header><div><Refresh width={18} height={18} aria-hidden /><strong>Runtime</strong></div><Link to="/system-health">Details <ArrowRight width={14} height={14} aria-hidden /></Link></header>
          <dl className="runtime-facts">
            <div><dt>Core</dt><dd className={`status-${workspace.connection}`}>{workspace.connection}</dd></div>
            <div><dt>Models</dt><dd>{workspace.models.length}</dd></div>
            <div><dt>Events</dt><dd>{workspace.events.length}</dd></div>
          </dl>
        </article>
      </section>
    </div>
  );
}
