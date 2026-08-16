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
              {message.role === 'assistant' && (
                <footer>
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
