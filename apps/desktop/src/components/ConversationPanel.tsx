import React from 'react';
import { ChatMessage } from '../types/events';

interface ConversationPanelProps {
  messages: ChatMessage[];
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({ messages }) => (
  <section
    className="glass-panel"
    aria-label="Assistant conversation"
    aria-live="polite"
    style={{ padding: '16px', minHeight: '150px', maxHeight: '260px', overflowY: 'auto' }}
  >
    <h2 style={{ fontSize: '0.9rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>
      Conversation
    </h2>
    {messages.length === 0 ? (
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        Choose an available model and ask Ophanim a question.
      </p>
    ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            style={{
              alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              padding: '9px 12px',
              borderRadius: '10px',
              background:
                message.role === 'user'
                  ? 'rgba(99, 102, 241, 0.22)'
                  : 'rgba(6, 182, 212, 0.12)',
              whiteSpace: 'pre-wrap',
              overflowWrap: 'anywhere',
              fontSize: '0.88rem',
              lineHeight: 1.45,
            }}
          >
            <strong
              style={{
                display: 'block',
                marginBottom: '3px',
                color:
                  message.role === 'user'
                    ? 'var(--accent-indigo)'
                    : 'var(--accent-cyan)',
              }}
            >
              {message.role === 'user' ? 'You' : 'Ophanim'}
            </strong>
            {message.content}
          </div>
        ))}
      </div>
    )}
  </section>
);
