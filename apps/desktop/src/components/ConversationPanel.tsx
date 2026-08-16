import { CheckCircle, Copy, MoreHoriz } from 'iconoir-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../types/events';

interface ConversationPanelProps {
  messages: ChatMessage[];
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({ messages }) => (
  <section
    className="conversation-panel"
    aria-label="Assistant conversation"
    aria-live="polite"
  >
    {messages.length === 0 ? (
      <div className="conversation-empty">
        <span className="empty-kicker"><CheckCircle width={16} height={16} aria-hidden /> Ready when you are</span>
        <h2>What would you like to work on?</h2>
        <p>Ask a question, delegate a bounded goal, or inspect the connected runtime. Ophanim will only show activity confirmed by Core.</p>
      </div>
    ) : (
      <div className="message-list">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`message-row role-${message.role}`}
          >
            <div className="message-avatar" aria-hidden>{message.role === 'user' ? 'M' : 'O'}</div>
            <article className="message-card">
              <header>
                <strong>{message.role === 'user' ? 'You' : 'Ophanim'}</strong>
                <span>Current session</span>
                <button type="button" aria-label="Message options" title="Message actions are not available"><MoreHoriz width={18} height={18} aria-hidden /></button>
              </header>
              <div className="markdown-body">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  skipHtml
                  components={{
                    a: ({ href, children }) => (
                      <a href={href?.startsWith('https://') ? href : undefined} rel="noreferrer">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              {message.citations && message.citations.length > 0 && (
                <div className="message-citations" style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 0.5rem 0' }}>Sources</h4>
                  <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    {message.citations.map((citation, i) => (
                      <li key={i} style={{ fontSize: '0.85rem' }}>
                        <a href={citation.uriRef ?? undefined} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none', color: 'var(--text-secondary)' }}>
                          <span style={{ background: 'var(--surface-3)', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.75rem' }}>[{i + 1}]</span>
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{citation.documentTitle || citation.citationId}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {message.role === 'assistant' && (
                <footer>
                  <div className="message-provenance" style={{ display: 'flex', flexGrow: 1, color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
                    {message.provider && message.modelId ? (
                      <span>Produced by {message.provider} ({message.modelId})</span>
                    ) : (
                      <span>Produced by Core</span>
                    )}
                  </div>
                  <button type="button" title="Copy is not connected yet"><Copy width={15} height={15} aria-hidden /> Copy</button>
                </footer>
              )}
            </article>
          </div>
        ))}
      </div>
    )}
  </section>
);
