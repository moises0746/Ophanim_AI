import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { Event, UnlistenFn } from '@tauri-apps/api/event';
import {
  TauriAssistantRuntimeClient,
  HttpAssistantRuntimeClient,
  toCoreRoutingMode,
  isTauri,
  resolveRuntimeClient,
} from '../services/runtime';

describe('Tauri Assistant runtime bridge', () => {
  it('maps Desktop routing modes to Core values', () => {
    expect(toCoreRoutingMode('LOCAL_ONLY')).toBe('local_only');
    expect(toCoreRoutingMode('CLOUD_ONLY')).toBe('cloud_only');
    expect(toCoreRoutingMode('HYBRID_ROUTED')).toBe('hybrid_routed');
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
      routingMode: 'HYBRID_ROUTED',
      provider: 'openai',
      modelId: 'cloud-model',
    });

    expect(response.content).toBe('Hello');
    expect(calls[0].command).toBe('assistant_chat');
    expect(JSON.stringify(calls[0])).not.toMatch(/token|authorization|apiKey/i);
    expect(calls[0].args).toEqual({
      request: {
        messages: [{ role: 'user', content: 'Hello' }],
        routing_mode: 'hybrid_routed',
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

describe('Runtime Client Resolution', () => {
  beforeEach(() => {
    vi.stubGlobal('window', {});
    vi.stubEnv('VITE_OPHANIM_CORE_URL', 'http://test-core');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('resolves HttpAssistantRuntimeClient when not in Tauri', () => {
    expect(isTauri()).toBe(false);
    const client = resolveRuntimeClient();
    expect(client).toBeInstanceOf(HttpAssistantRuntimeClient);
  });

  it('resolves TauriAssistantRuntimeClient when in Tauri', () => {
    vi.stubGlobal('window', { __TAURI_IPC__: vi.fn() });
    expect(isTauri()).toBe(true);
    const client = resolveRuntimeClient();
    expect(client).toBeInstanceOf(TauriAssistantRuntimeClient);
  });
});

describe('HttpAssistantRuntimeClient', () => {
  let fetchMock: any;
  let client: HttpAssistantRuntimeClient;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    client = new HttpAssistantRuntimeClient('http://test-core');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetches models via HTTP', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => [{ model_id: 'test-model' }]
    });

    const models = await client.listModels();
    expect(models).toEqual([{ model_id: 'test-model' }]);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://test-core/api/v1/assistant/models?workspace_id=00000000-0000-0000-0000-000000000002',
      { headers: { Authorization: 'Bearer dev-token-123' } },
    );
  });

  it('handles offline core cleanly via getConfig', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 503 });

    await expect(client.getConfig()).rejects.toThrow('Core unavailable: HTTP 503');
  });

  it('maps sendChat payload correctly', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ content: 'response' })
    });

    const res = await client.sendChat({
      messages: [{ role: 'user', content: 'hello' }],
      routingMode: 'LOCAL_ONLY',
      provider: 'lm_studio',
      modelId: 'test-model'
    });

    expect(res.content).toBe('response');
    expect(fetchMock).toHaveBeenCalledWith('http://test-core/api/v1/assistant/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer dev-token-123',
      },
      body: JSON.stringify({
        workspace_id: '00000000-0000-0000-0000-000000000002',
        messages: [{ role: 'user', content: 'hello' }],
        routing_mode: 'local_only',
        provider: 'lm_studio',
        model_id: 'test-model',
      })
    });
  });
});
