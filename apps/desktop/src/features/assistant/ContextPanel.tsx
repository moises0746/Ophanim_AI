import { useState } from 'react';
import { CheckCircle, Clock, Database, InfoCircle as InfoEmpty, Tools, WarningCircle } from 'iconoir-react';
import type { ActivityEventItem, CitationItem } from '../../types/events';

type ContextTab = 'activity' | 'sources' | 'steps' | 'tools';

interface ContextPanelProps {
  events: ActivityEventItem[];
  citations: CitationItem[];
}

const EmptyContext = ({ title, body }: { title: string; body: string }) => (
  <div className="context-empty">
    <InfoEmpty width={22} height={22} aria-hidden />
    <strong>{title}</strong>
    <span>{body}</span>
  </div>
);

export function ContextPanel({ events, citations }: ContextPanelProps) {
  const [tab, setTab] = useState<ContextTab>('activity');
  const tabs: Array<{ id: ContextTab; label: string; count?: number }> = [
    { id: 'activity', label: 'Activity', count: events.length },
    { id: 'sources', label: 'Sources', count: citations.length },
    { id: 'steps', label: 'Steps' },
    { id: 'tools', label: 'Tools' },
  ];
  const toolEvents = events.filter((event) => event.type.startsWith('tool.'));
  const stepEvents = events.filter((event) => event.type.startsWith('task.') || event.type.startsWith('agent.'));

  return (
    <aside className="context-panel surface" aria-label="Assistant context">
      <div className="context-tabs" role="tablist" aria-label="Assistant context views">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            className={tab === item.id ? 'is-active' : ''}
            onClick={() => setTab(item.id)}
          >
            {item.label}{item.count !== undefined && <span>{item.count}</span>}
          </button>
        ))}
      </div>

      <div className="context-content" role="tabpanel">
        {tab === 'activity' && (events.length === 0 ? (
          <EmptyContext title="No activity yet" body="Core events will appear here when work begins." />
        ) : (
          <ol className="activity-list">
            {events.map((event) => {
              const Icon = event.status === 'failed' ? WarningCircle : event.status === 'completed' ? CheckCircle : Clock;
              return (
                <li key={event.id}>
                  <span className={`activity-icon status-${event.status}`}><Icon width={15} height={15} aria-hidden /></span>
                  <div><strong>{event.title}</strong><span>{new Date(event.timestampUtc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>
                </li>
              );
            })}
          </ol>
        ))}

        {tab === 'sources' && (citations.length === 0 ? (
          <EmptyContext title="No verified sources" body="Citations appear only when Core returns authorized evidence." />
        ) : (
          <ul className="source-list">
            {citations.map((citation) => (
              <li key={citation.citationId}><Database width={17} height={17} aria-hidden /><div><strong>{citation.documentTitle}</strong><span>{citation.headerPath}</span></div></li>
            ))}
          </ul>
        ))}

        {tab === 'steps' && (stepEvents.length === 0 ? (
          <EmptyContext title="No active plan" body="Authoritative task and agent steps will be shown here." />
        ) : (
          <ol className="step-list">
            {stepEvents.map((event, index) => <li key={event.id}><span>{index + 1}</span><div><strong>{event.title}</strong><small>{event.type}</small></div></li>)}
          </ol>
        ))}

        {tab === 'tools' && (toolEvents.length === 0 ? (
          <EmptyContext title="No tool calls" body="Governed tool lifecycle events will appear here; no tool access is implied." />
        ) : (
          <ul className="source-list">
            {toolEvents.map((event) => <li key={event.id}><Tools width={17} height={17} aria-hidden /><div><strong>{event.title}</strong><span>{event.status}</span></div></li>)}
          </ul>
        ))}
      </div>
    </aside>
  );
}
