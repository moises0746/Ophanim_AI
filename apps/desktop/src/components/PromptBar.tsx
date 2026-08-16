import { Attachment, Microphone, SendDiagonal } from 'iconoir-react';
import React, { useState } from 'react';

interface PromptBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  busy?: boolean;
  disabledReason?: string;
}

export const PromptBar: React.FC<PromptBarProps> = ({
  onSend,
  disabled,
  busy = false,
  disabledReason,
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div className="prompt-region">
      <form onSubmit={handleSubmit} className="prompt-composer">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
          disabled={disabled}
          rows={2}
          aria-label="Message Ophanim"
          placeholder={disabledReason ?? 'Ask Ophanim or delegate a bounded goal…'}
        />
        <div className="composer-actions">
          <div>
            <button type="button" className="icon-button" disabled title="Attachments are not implemented" aria-label="Attachments unavailable"><Attachment width={18} height={18} aria-hidden /></button>
            <button type="button" className="icon-button" disabled title="Voice capture is not implemented" aria-label="Voice capture unavailable"><Microphone width={18} height={18} aria-hidden /></button>
            <span className="composer-hint">Enter to send · Shift + Enter for a new line</span>
          </div>
          <button className="send-button" type="submit" disabled={disabled || !input.trim()}>
            <span>{busy ? 'Sending' : 'Send'}</span>
            <SendDiagonal width={17} height={17} aria-hidden />
          </button>
        </div>
      </form>
    </div>
  );
};
