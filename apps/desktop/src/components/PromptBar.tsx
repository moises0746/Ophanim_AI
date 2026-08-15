import React, { useState } from 'react';

interface PromptBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export const PromptBar: React.FC<PromptBarProps> = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  const handleQuickAction = (action: string) => {
    if (disabled) return;
    onSend(action);
  };

  return (
    <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => handleQuickAction('Investigate failed transaction order #TXN-90214')}
          disabled={disabled}
          style={{
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            color: 'var(--accent-cyan)',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '0.75rem',
            cursor: disabled ? 'not-allowed' : 'pointer',
          }}
        >
          🔍 Investigate TXN-90214
        </button>
        <button
          type="button"
          onClick={() => handleQuickAction('Run device node diagnostic health check')}
          disabled={disabled}
          style={{
            background: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.25)',
            color: '#38bdf8',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '0.75rem',
            cursor: disabled ? 'not-allowed' : 'pointer',
          }}
        >
          ⚡ Node Health Check
        </button>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel" style={{ display: 'flex', padding: '6px 8px', borderRadius: '12px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
          placeholder="Ask Ophanim AI or request an automated investigation..."
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            padding: '8px 12px',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
            fontFamily: 'var(--font-sans)',
          }}
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          style={{
            background: 'linear-gradient(135deg, var(--accent-indigo) 0%, var(--accent-cyan) 100%)',
            border: 'none',
            borderRadius: '8px',
            color: '#ffffff',
            padding: '8px 16px',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
            opacity: disabled || !input.trim() ? 0.5 : 1,
            transition: 'all 0.2s ease',
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
};
