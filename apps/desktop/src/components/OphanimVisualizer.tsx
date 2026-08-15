import React from 'react';
import { AssistantSemanticState } from '../types/events';

interface OphanimVisualizerProps {
  state: AssistantSemanticState;
  subText?: string;
}

export const OphanimVisualizer: React.FC<OphanimVisualizerProps> = ({ state, subText }) => {
  return (
    <div className={`visualizer-container state-${state}`}>
      <div className="ophanim-core-orb">
        <div className="ophanim-ring ring-outer" />
        <div className="ophanim-ring ring-middle" />
        <div className="ophanim-ring ring-inner" />
        <div className="ophanim-center-eye" />
      </div>
      <div style={{ marginTop: '18px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
          {state.replace('_', ' ')}
        </h2>
        {subText && (
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {subText}
          </p>
        )}
      </div>
    </div>
  );
};
