import { describe, expect, it, vi } from 'vitest';
import {
  AssistantEventStreamClient,
  projectSemanticState,
} from '../services/eventStream';
import { EventEnvelope } from '../types/events';

const WORKSPACE_ID = '00000000-0000-0000-0000-000000000000';

function envelope(overrides: Partial<EventEnvelope> = {}): EventEnvelope {
  return {
    event_id: 'evt-123',
    event_type: 'assistant.state.changed',
    event_schema_version: '1.0.0',
    occurred_at: '2026-08-15T12:00:00Z',
    emitted_at: '2026-08-15T12:00:01Z',
    producer: 'ophanim.core',
    correlation_id: '00000000-0000-0000-0000-000000000001',
    workspace_id: WORKSPACE_ID,
    environment: 'test',
    data_scope: WORKSPACE_ID,
    visibility_classification: 'internal',
    display_summary: 'Assistant is planning',
    payload: { state: 'planning' },
    task_id: '00000000-0000-0000-0000-000000000002',
    sequence: 1,
    evidence_refs: [],
    artifact_refs: [],
    ...overrides,
  };
}

function client(handlers: ConstructorParameters<typeof AssistantEventStreamClient>[3] = {}) {
  return new AssistantEventStreamClient(
    'http://localhost:8000',
    WORKSPACE_ID,
    async () => 'test-token',
    handlers,
  );
}

describe('AssistantEventStreamClient', () => {
  it('projects the canonical Core state and dispatches a truthful activity row', () => {
    const onStateChange = vi.fn();
    const onActivityEvent = vi.fn();
    const stream = client({ onStateChange, onActivityEvent });

    stream.handleSseFrame(`event: assistant.state.changed\ndata: ${JSON.stringify(envelope())}`);

    expect(onStateChange).toHaveBeenCalledWith('planning', 'Assistant is planning');
    expect(onActivityEvent).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'evt-123', type: 'assistant.state.changed' }),
    );
  });

  it('ignores duplicate, stale, and cross-workspace events', () => {
    const onActivityEvent = vi.fn();
    const stream = client({ onActivityEvent });

    stream.handleEnvelope(envelope({ event_id: 'evt-new', sequence: 3 }));
    stream.handleEnvelope(envelope({ event_id: 'evt-new', sequence: 3 }));
    stream.handleEnvelope(envelope({ event_id: 'evt-stale', sequence: 2 }));
    stream.handleEnvelope(
      envelope({ event_id: 'evt-other', workspace_id: '00000000-0000-0000-0000-000000000099' }),
    );

    expect(onActivityEvent).toHaveBeenCalledTimes(1);
  });

  it('projects a bounded approval request from an authoritative event', () => {
    const onApprovalRequest = vi.fn();
    const stream = client({ onApprovalRequest });

    stream.handleEnvelope(
      envelope({
        event_id: 'evt-approval',
        event_type: 'approval.requested',
        approval_id: '00000000-0000-0000-0000-000000000003',
        payload: {
          tool_name: 'db.query_diagnostic',
          risk_level: 'medium',
          safe_parameters: { table: 'transactions' },
        },
      }),
    );

    expect(onApprovalRequest).toHaveBeenCalledWith(
      expect.objectContaining({ toolName: 'db.query_diagnostic', riskLevel: 'medium' }),
    );
  });

  it('preserves all canonical Core states without a competing presentation vocabulary', () => {
    expect(projectSemanticState('idle')).toBe('idle');
    expect(projectSemanticState('waiting_for_approval')).toBe('waiting_for_approval');
    expect(projectSemanticState('error')).toBe('error');
  });
});
