import {
  ActivityEventItem,
  ApprovalRequest,
  AssistantSemanticState,
  CoreAssistantSemanticState,
  EventEnvelope,
} from '../types/events';

export interface EventStreamHandlers {
  onStateChange?: (state: AssistantSemanticState, summary: string) => void;
  onActivityEvent?: (event: ActivityEventItem) => void;
  onApprovalRequest?: (request: ApprovalRequest) => void;
  onConnectionChange?: (connected: boolean) => void;
  onError?: (err: Error) => void;
}

export type AuthorizationProvider = () => Promise<string>;

const CORE_TO_PRESENTATION_STATE: Record<CoreAssistantSemanticState, AssistantSemanticState> = {
  idle: 'DORMANT',
  listening: 'LISTENING',
  understanding: 'THINKING',
  planning: 'THINKING',
  delegating: 'EXECUTING',
  working: 'EXECUTING',
  waiting_for_tool: 'EXECUTING',
  waiting_for_approval: 'AWAITING_APPROVAL',
  speaking: 'SPEAKING',
  completed: 'COMPLETED',
  blocked: 'BLOCKED',
  error: 'ERROR',
};

const CORE_STATES = new Set<CoreAssistantSemanticState>(
  Object.keys(CORE_TO_PRESENTATION_STATE) as CoreAssistantSemanticState[],
);

export function projectSemanticState(state: CoreAssistantSemanticState): AssistantSemanticState {
  return CORE_TO_PRESENTATION_STATE[state];
}

function activityStatus(envelope: EventEnvelope): ActivityEventItem['status'] {
  if (envelope.event_type === 'approval.requested') return 'approval_required';
  if (
    envelope.event_type.endsWith('.failed') ||
    envelope.event_type.endsWith('.denied') ||
    envelope.event_type.endsWith('.cancelled')
  ) {
    return 'failed';
  }
  if (
    envelope.event_type.endsWith('.requested') ||
    envelope.event_type.endsWith('.started') ||
    envelope.event_type.endsWith('.progressed')
  ) {
    return 'running';
  }
  return 'completed';
}

function parseApproval(envelope: EventEnvelope): ApprovalRequest | null {
  if (envelope.event_type !== 'approval.requested' || !envelope.approval_id || !envelope.task_id) {
    return null;
  }
  const { payload } = envelope;
  const riskLevel = payload.risk_level;
  if (
    typeof payload.tool_name !== 'string' ||
    !['low', 'medium', 'high', 'critical'].includes(String(riskLevel))
  ) {
    return null;
  }
  return {
    approvalId: envelope.approval_id,
    taskId: envelope.task_id,
    toolName: payload.tool_name,
    parameters:
      typeof payload.safe_parameters === 'object' && payload.safe_parameters !== null
        ? (payload.safe_parameters as Record<string, unknown>)
        : {},
    riskLevel: riskLevel as ApprovalRequest['riskLevel'],
    description: envelope.display_summary,
  };
}

export class AssistantEventStreamClient {
  private abortController: AbortController | null = null;
  private handlers: EventStreamHandlers;
  private readonly seenEventIds = new Set<string>();
  private readonly latestSequenceByScope = new Map<string, number>();

  constructor(
    private readonly baseUrl: string,
    private readonly workspaceId: string,
    private readonly authorizationProvider: AuthorizationProvider,
    handlers: EventStreamHandlers = {},
    private readonly fetchImpl: typeof fetch = fetch,
  ) {
    this.handlers = handlers;
  }

  public setHandlers(handlers: EventStreamHandlers): void {
    this.handlers = handlers;
  }

  public connect(): void {
    if (this.abortController) return;
    this.abortController = new AbortController();
    void this.consume(this.abortController.signal);
  }

  public disconnect(): void {
    this.abortController?.abort();
    this.abortController = null;
    this.handlers.onConnectionChange?.(false);
  }

  private async consume(signal: AbortSignal): Promise<void> {
    try {
      const bearerToken = await this.authorizationProvider();
      const url = `${this.baseUrl}/api/v1/assistant/events/stream?workspace_id=${encodeURIComponent(this.workspaceId)}`;
      const response = await this.fetchImpl(url, {
        headers: { Authorization: `Bearer ${bearerToken}`, Accept: 'text/event-stream' },
        signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(`Assistant event stream failed with HTTP ${response.status}`);
      }

      this.handlers.onConnectionChange?.(true);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (!signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() ?? '';
        for (const frame of frames) this.handleSseFrame(frame);
      }
    } catch (error) {
      if (!signal.aborted) this.handlers.onError?.(error as Error);
    } finally {
      if (!signal.aborted) this.handlers.onConnectionChange?.(false);
      this.abortController = null;
    }
  }

  public handleSseFrame(frame: string): void {
    const eventName = frame
      .split(/\r?\n/)
      .find((line) => line.startsWith('event:'))
      ?.slice(6)
      .trim();
    if (eventName === 'ping') return;

    const data = frame
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n');
    if (!data) return;

    try {
      this.handleEnvelope(JSON.parse(data) as EventEnvelope);
    } catch (error) {
      this.handlers.onError?.(error as Error);
    }
  }

  public handleEnvelope(envelope: EventEnvelope): void {
    if (envelope.workspace_id !== this.workspaceId || this.seenEventIds.has(envelope.event_id)) return;

    const sequenceScope = envelope.task_id ?? envelope.workspace_id;
    if (envelope.sequence !== null && envelope.sequence !== undefined) {
      const latest = this.latestSequenceByScope.get(sequenceScope);
      if (latest !== undefined && envelope.sequence <= latest) return;
      this.latestSequenceByScope.set(sequenceScope, envelope.sequence);
    }
    this.seenEventIds.add(envelope.event_id);

    const coreState = envelope.payload.state;
    if (
      envelope.event_type === 'assistant.state.changed' &&
      typeof coreState === 'string' &&
      CORE_STATES.has(coreState as CoreAssistantSemanticState)
    ) {
      this.handlers.onStateChange?.(
        projectSemanticState(coreState as CoreAssistantSemanticState),
        envelope.display_summary,
      );
    }

    const evidenceHash = envelope.payload.evidence_hash;
    this.handlers.onActivityEvent?.({
      id: envelope.event_id,
      timestampUtc: envelope.occurred_at,
      type: envelope.event_type,
      title: envelope.display_summary,
      details: envelope.payload,
      evidenceHash: typeof evidenceHash === 'string' ? evidenceHash : undefined,
      status: activityStatus(envelope),
    });

    const approval = parseApproval(envelope);
    if (approval) this.handlers.onApprovalRequest?.(approval);
  }
}
