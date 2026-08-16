import {
  CheckCircle,
  Clock,
  Lock,
  Microphone,
  WarningCircle,
} from 'iconoir-react';
import type { AssistantSemanticState } from '../../types/events';

export const assistantStatePresentation: Record<AssistantSemanticState, {
  label: string;
  detail: string;
  icon: typeof Clock;
}> = {
  idle: { label: 'Ready', detail: 'Waiting for a goal', icon: CheckCircle },
  listening: { label: 'Listening', detail: 'Microphone capture is active', icon: Microphone },
  understanding: { label: 'Understanding', detail: 'Interpreting the request', icon: Clock },
  planning: { label: 'Planning', detail: 'Preparing a bounded plan', icon: Clock },
  delegating: { label: 'Delegating', detail: 'Assigning approved capabilities', icon: Clock },
  working: { label: 'Working', detail: 'Coordinating active work', icon: Clock },
  waiting_for_tool: { label: 'Waiting for tool', detail: 'A governed tool is pending', icon: Clock },
  waiting_for_approval: { label: 'Approval required', detail: 'A human decision is required', icon: Lock },
  speaking: { label: 'Speaking', detail: 'Audio playback is active', icon: Microphone },
  completed: { label: 'Completed', detail: 'Verified work is complete', icon: CheckCircle },
  blocked: { label: 'Blocked', detail: 'A dependency or decision is needed', icon: WarningCircle },
  error: { label: 'Error', detail: 'The runtime reported a failure', icon: WarningCircle },
};

interface OphanimAssistantVisualProps {
  state: AssistantSemanticState;
  statusText?: string;
  compact?: boolean;
}

export function OphanimAssistantVisual({
  state,
  statusText,
  compact = false,
}: OphanimAssistantVisualProps) {
  const presentation = assistantStatePresentation[state];
  const StateIcon = presentation.icon;

  return (
    <div
      className={`ophanim-visual state-${state}${compact ? ' is-compact' : ''}`}
      role="status"
      aria-live="polite"
      aria-label={`Ophanim state: ${presentation.label}. ${statusText ?? presentation.detail}`}
      data-assistant-state={state}
    >
      <div className="ophanim-presence" aria-hidden>
        <span className="presence-halo" />
        <span className="presence-orbit orbit-a"><i /><i /><i /></span>
        <span className="presence-orbit orbit-b"><i /><i /></span>
        <span className="presence-orbit orbit-c" />
        <span className="presence-core"><span /></span>
      </div>
      {!compact && (
        <div className="ophanim-state-copy">
          <span className="state-icon"><StateIcon width={15} height={15} aria-hidden /></span>
          <div>
            <strong>{presentation.label}</strong>
            <span>{statusText ?? presentation.detail}</span>
          </div>
        </div>
      )}
    </div>
  );
}
