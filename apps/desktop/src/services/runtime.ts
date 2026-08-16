import { invoke } from '@tauri-apps/api/tauri';
import { Event, listen, UnlistenFn } from '@tauri-apps/api/event';
import {
  AssistantModel,
  ChatCompletion,
  ChatMessage,
  RoutingMode,
  ProviderStatus,
} from '../types/events';
import {
  AssistantEventStreamClient,
  EventStreamHandlers,
} from './eventStream';

export interface RuntimeConfig {
  configured: boolean;
  coreBaseUrl: string;
  workspaceId: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  routingMode: RoutingMode;
  provider: string;
  modelId: string;
  maxTokens?: number;
}

export interface AssistantRuntimeClient {
  getConfig(): Promise<RuntimeConfig>;
  listModels(): Promise<AssistantModel[]>;
  getProviderStatus(): Promise<ProviderStatus>;
  sendChat(request: ChatRequest): Promise<ChatCompletion>;
  connectEvents(
    workspaceId: string,
    handlers: EventStreamHandlers,
  ): Promise<() => void>;
}

type InvokeFn = <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
type ListenFn = <T>(
  event: string,
  handler: (event: Event<T>) => void,
) => Promise<UnlistenFn>;

export function toCoreRoutingMode(mode: RoutingMode): 'local_only' | 'cloud_only' | 'hybrid_routed' {
  switch (mode) {
    case 'LOCAL_ONLY':
      return 'local_only';
    case 'CLOUD_ONLY':
      return 'cloud_only';
    case 'HYBRID_ROUTED':
      return 'hybrid_routed';
  }
}

export class TauriAssistantRuntimeClient implements AssistantRuntimeClient {
  constructor(
    private readonly invokeImpl: InvokeFn = invoke,
    private readonly listenImpl: ListenFn = listen,
  ) {}

  public getConfig(): Promise<RuntimeConfig> {
    return this.invokeImpl<RuntimeConfig>('runtime_config');
  }

  public listModels(): Promise<AssistantModel[]> {
    return this.invokeImpl<AssistantModel[]>('assistant_models');
  }

  public getProviderStatus(): Promise<ProviderStatus> {
    return this.invokeImpl<ProviderStatus>('provider_status');
  }

  public sendChat(request: ChatRequest): Promise<ChatCompletion> {
    return this.invokeImpl<ChatCompletion>('assistant_chat', {
      request: {
        messages: request.messages,
        routing_mode: toCoreRoutingMode(request.routingMode),
        provider: request.provider,
        modelId: request.modelId,
        maxTokens: request.maxTokens,
      },
    });
  }

  public async connectEvents(
    workspaceId: string,
    handlers: EventStreamHandlers,
  ): Promise<() => void> {
    const projector = new AssistantEventStreamClient(
      '',
      workspaceId,
      async () => '',
      handlers,
    );
    const unlistenEvent = await this.listenImpl<string>(
      'ophanim://assistant-event',
      (event) => projector.handleSseFrame(event.payload),
    );
    const unlistenError = await this.listenImpl<string>(
      'ophanim://runtime-error',
      (event) => handlers.onError?.(new Error(event.payload)),
    );
    try {
      await this.invokeImpl<void>('start_assistant_events');
      handlers.onConnectionChange?.(true);
    } catch (error) {
      unlistenEvent();
      unlistenError();
      throw error;
    }
    return () => {
      unlistenEvent();
      unlistenError();
      handlers.onConnectionChange?.(false);
    };
  }
}

export function isTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI_IPC__' in window;
}

export class HttpAssistantRuntimeClient implements AssistantRuntimeClient {
  private readonly baseUrl: string;
  private readonly token: string;

  constructor(baseUrl?: string) {
    const configuredUrl = baseUrl ?? import.meta.env.VITE_OPHANIM_CORE_URL;
    if (!configuredUrl) {
      throw new Error('VITE_OPHANIM_CORE_URL is not configured');
    }
    this.baseUrl = configuredUrl as string;
    this.token = (import.meta.env.VITE_OPHANIM_DESKTOP_API_TOKEN as string) ?? 'dev-token-123';
  }

  public async getConfig(): Promise<RuntimeConfig> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`Core unavailable: HTTP ${res.status}`);
    }
    return {
      configured: true,
      coreBaseUrl: this.baseUrl,
      workspaceId: '00000000-0000-0000-0000-000000000002',
    };
  }

  public async listModels(): Promise<AssistantModel[]> {
    const res = await fetch(`${this.baseUrl}/api/v1/assistant/models?workspace_id=00000000-0000-0000-0000-000000000002`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    });
    if (!res.ok) {
      throw new Error(`Failed to list models: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async getProviderStatus(): Promise<ProviderStatus> {
    const res = await fetch(`${this.baseUrl}/status/providers`);
    if (!res.ok) {
      throw new Error(`Failed to get provider status: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async sendChat(request: ChatRequest): Promise<ChatCompletion> {
    const res = await fetch(`${this.baseUrl}/api/v1/assistant/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        workspace_id: '00000000-0000-0000-0000-000000000002',
        messages: request.messages,
        routing_mode: toCoreRoutingMode(request.routingMode),
        provider: request.provider,
        model_id: request.modelId,
        max_tokens: request.maxTokens,
      }),
    });
    if (!res.ok) {
      throw new Error(`Failed to send chat: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async connectEvents(
    workspaceId: string,
    handlers: EventStreamHandlers,
  ): Promise<() => void> {
    const projector = new AssistantEventStreamClient(
      this.baseUrl,
      workspaceId,
      async () => this.token,
      handlers,
    );
    projector.connect();
    return () => {
      projector.disconnect();
    };
  }
}

export function resolveRuntimeClient(): AssistantRuntimeClient {
  if (isTauri()) {
    return new TauriAssistantRuntimeClient();
  }
  return new HttpAssistantRuntimeClient();
}
