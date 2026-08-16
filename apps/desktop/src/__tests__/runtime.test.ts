import { describe, expect, it } from 'vitest';
import { Event, UnlistenFn } from '@tauri-apps/api/event';
import {
  TauriAssistantRuntimeClient,
  toCorePrivacyMode,
} from '../services/runtime';

describe('Tauri Assistant runtime bridge', () => {
  it('maps Desktop privacy modes to Core values', () => {
    expect(toCorePrivacyMode('LOCAL_ONLY')).toBe('local_only');
    expect(toCorePrivacyMode('PRIVATE')).toBe('private');
    expect(toCorePrivacyMode('CLOUD_ASSISTED')).toBe('standard');
  });

  it('sends only a typed chat request and never adds credentials', async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const invoke = async <T>(
      command: string,
      args?: Record<string, unknown>,
    ): Promise<T> => {
      calls.push({ command, args });
      return {
        correlation_id: 'corr-1',
        content: 'Hello',
        provider: 'openai',
        model_id: 'cloud-model',
        finish_reason: 'completed',
        usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
        latency_ms: 1,
      } as T;
    };
    const listen = async <T>(
      _event: string,
      _handler: (event: Event<T>) => void,
    ): Promise<UnlistenFn> => () => {};
    const client = new TauriAssistantRuntimeClient(invoke, listen);

    const response = await client.sendChat({
      messages: [{ role: 'user', content: 'Hello' }],
      privacyMode: 'CLOUD_ASSISTED',
      provider: 'openai',
      modelId: 'cloud-model',
    });

    expect(response.content).toBe('Hello');
    expect(calls[0].command).toBe('assistant_chat');
    expect(JSON.stringify(calls[0])).not.toMatch(/token|authorization|apiKey/i);
    expect(calls[0].args).toEqual({
      request: {
        messages: [{ role: 'user', content: 'Hello' }],
        privacyMode: 'standard',
        provider: 'openai',
        modelId: 'cloud-model',
        maxTokens: undefined,
      },
    });
  });

  it('projects Tauri SSE frames through the existing typed event reducer', async () => {
    const listeners = new Map<string, (event: Event<string>) => void>();
    const invoke = async <T>(_command: string): Promise<T> => undefined as T;
    const listen = async <T>(
      event: string,
      handler: (payload: Event<T>) => void,
    ): Promise<UnlistenFn> => {
      listeners.set(event, handler as (payload: Event<string>) => void);
      return () => listeners.delete(event);
    };
    const states: string[] = [];
    const client = new TauriAssistantRuntimeClient(invoke, listen);
    const disconnect = await client.connectEvents('workspace-1', {
      onStateChange: (state) => states.push(state),
    });
    listeners.get('ophanim://assistant-event')?.({
      event: 'ophanim://assistant-event',
      id: 1,
      windowLabel: 'main',
      payload:
        'event: assistant.state.changed\n' +
        'data: {"event_id":"evt-1","event_type":"assistant.state.changed",' +
        '"event_schema_version":"1.0.0","occurred_at":"2026-08-15T00:00:00Z",' +
        '"emitted_at":"2026-08-15T00:00:00Z","producer":"ophanim.core",' +
        '"correlation_id":"corr-1","workspace_id":"workspace-1","environment":"local",' +
        '"data_scope":"workspace-1","visibility_classification":"internal",' +
        '"display_summary":"Working","payload":{"state":"working"},' +
        '"evidence_refs":[],"artifact_refs":[]}\n\n',
    });

    expect(states).toEqual(['working']);
    disconnect();
    expect(listeners.size).toBe(0);
  });
});
