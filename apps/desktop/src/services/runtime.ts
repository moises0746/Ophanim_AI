import { invoke } from '@tauri-apps/api/tauri';
import { Event, listen, UnlistenFn } from '@tauri-apps/api/event';
import {
  AssistantModel,
  ChatCompletion,
  ChatMessage,
  PrivacyMode,
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
  privacyMode: PrivacyMode;
  provider: string;
  modelId: string;
  maxTokens?: number;
}

export interface AssistantRuntimeClient {
  getConfig(): Promise<RuntimeConfig>;
  listModels(): Promise<AssistantModel[]>;
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

export function toCorePrivacyMode(mode: PrivacyMode): 'local_only' | 'private' | 'standard' {
  if (mode === 'LOCAL_ONLY') return 'local_only';
  if (mode === 'PRIVATE') return 'private';
  return 'standard';
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

  public sendChat(request: ChatRequest): Promise<ChatCompletion> {
    return this.invokeImpl<ChatCompletion>('assistant_chat', {
      request: {
        messages: request.messages,
        privacyMode: toCorePrivacyMode(request.privacyMode),
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
