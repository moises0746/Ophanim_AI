import { Cloud, Database, Lock, WarningTriangle } from 'iconoir-react';
import type { AssistantModel, RuntimeConnectionState } from '../../types/events';
import { PageScaffold } from '../shared/PageScaffold';

interface ModelsPageProps {
  models: AssistantModel[];
  selectedModelKey: string;
  connection: RuntimeConnectionState;
  onSelect: (modelKey: string) => void;
}

export function ModelsPage({ models, selectedModelKey, connection, onSelect }: ModelsPageProps) {
  return (
    <PageScaffold eyebrow="Models & runtimes" title="Model routing" description="Configured local and cloud models returned by the authenticated Ophanim Core runtime.">
      <div className="model-layout">
        <section className="surface section-card">
          <header className="section-header"><div><h2>Available models</h2><p>{models.length} returned by Core</p></div><span className={`connection-chip status-${connection}`}>{connection}</span></header>
          {models.length === 0 ? (
            <div className="large-empty"><WarningTriangle width={28} height={28} aria-hidden /><h3>No models available</h3><p>Start the Desktop runtime and configure LM Studio, OpenAI, Gemini, or Anthropic in Core. Provider credentials never belong in this UI.</p></div>
          ) : (
            <div className="model-cards">
              {models.map((model) => {
                const key = `${model.provider}:${model.model_id}`;
                const ModelIcon = model.is_local ? Database : Cloud;
                return (
                  <button key={key} type="button" className={`model-card${selectedModelKey === key ? ' is-selected' : ''}`} onClick={() => onSelect(key)} aria-pressed={selectedModelKey === key}>
                    <span className="model-icon"><ModelIcon width={20} height={20} aria-hidden /></span>
                    <div><strong>{model.display_name}</strong><span>{model.provider.replace('_', ' ')} · {model.is_local ? 'Local runtime' : 'Cloud provider'}</span><small>{model.capabilities.join(' · ') || 'Capabilities not reported'}</small></div>
                    <span className="model-status">{selectedModelKey === key ? 'Active' : 'Select'}</span>
                  </button>
                );
              })}
            </div>
          )}
        </section>
        <aside className="surface section-card policy-card">
          <Lock width={22} height={22} aria-hidden />
          <h2>Credential boundary</h2>
          <p>React receives model metadata and bounded responses only. Tauri owns the ephemeral Core credential; provider secrets resolve inside Core at execution time.</p>
          <dl><div><dt>Local privacy</dt><dd>Loopback-only</dd></div><div><dt>Cloud privacy</dt><dd>Explicit selection</dd></div><div><dt>Secret values</dt><dd>Never rendered</dd></div></dl>
        </aside>
      </div>
    </PageScaffold>
  );
}
