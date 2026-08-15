import React from 'react';
import { CitationItem } from '../types/events';

interface CitationDrawerProps {
  citations: CitationItem[];
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({ citations }) => {
  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Knowledge Citations
        </h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {citations.length} sources
        </span>
      </div>

      {citations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No knowledge references in current session.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {citations.map((c) => (
            <div
              key={c.citationId}
              style={{
                padding: '10px 12px',
                borderRadius: '8px',
                background: 'rgba(99, 102, 241, 0.04)',
                border: '1px solid rgba(99, 102, 241, 0.15)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                  {c.documentTitle}
                </span>
                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  color: 'var(--accent-indigo)',
                  background: 'rgba(99, 102, 241, 0.15)',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}>
                  Score: {c.score}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '6px' }}>
                {c.uriRef}
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4, fontStyle: 'italic' }}>
                "{c.excerpt}"
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
