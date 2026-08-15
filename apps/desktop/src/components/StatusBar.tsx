import React from 'react';
import { AssistantSemanticState, PrivacyMode } from '../types/events';

interface StatusBarProps {
  state: AssistantSemanticState;
  model: string;
  privacyMode: PrivacyMode;
  nodeConnected: boolean;
  onEmergencyStop: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  state,
  model,
  privacyMode,
  nodeConnected,
  onEmergencyStop,
}) => {
  return (
    <header className="status-bar glass-panel">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            OPHANIM<span style={{ color: 'var(--accent-cyan)' }}>.AI</span>
          </span>
        </div>

        <div className={`state-badge state-${state}`}>
          <span className="state-dot" />
          <span>{state.replace('_', ' ')}</span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
          <span>Model: <strong style={{ color: 'var(--text-primary)' }}>{model}</strong></span>
          <span>•</span>
          <span style={{
            padding: '2px 8px',
            borderRadius: '4px',
            background: privacyMode === 'LOCAL_ONLY' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)',
            color: privacyMode === 'LOCAL_ONLY' ? 'var(--accent-emerald)' : 'var(--accent-indigo)',
            fontWeight: 600,
            fontSize: '0.75rem'
          }}>
            {privacyMode}
          </span>
          <span>•</span>
          <span>Node: {nodeConnected ? <strong style={{ color: 'var(--accent-emerald)' }}>Online</strong> : <span style={{ color: 'var(--text-muted)' }}>Offline</span>}</span>
        </div>

        <button
          className="btn-emergency-stop"
          onClick={onEmergencyStop}
          title="Immediate Emergency Stop for all running agent tasks"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          </svg>
          STOP
        </button>
      </div>
    </header>
  );
};
