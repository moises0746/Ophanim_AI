import React from 'react';
import { ActivityEventItem } from '../types/events';

interface ActivityFeedProps {
  events: ActivityEventItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ events }) => {
  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Activity & Evidence Stream
        </h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {events.length} events
        </span>
      </div>

      {events.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No activity recorded yet.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {events.map((evt) => (
            <div
              key={evt.id}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{evt.title}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {new Date(evt.timestampUtc).toLocaleTimeString()}
                </span>
              </div>

              {evt.evidenceHash && (
                <div style={{
                  marginTop: '6px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--accent-cyan)',
                  background: 'rgba(6, 182, 212, 0.08)',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  wordBreak: 'break-all'
                }}>
                  Receipt: {evt.evidenceHash}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
